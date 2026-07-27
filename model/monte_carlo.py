"""蒙特卡洛：10 万次三年期模拟，输出结果分布 P10/P50/P90。

本模型与常见创业财务预测最大的三点不同：

  1. **把阶段门做进模拟。** 门的经济意义不是流程管理，而是**截断左尾**：
     Gate 0-B 未过就停手，损失是 26 小时而不是 3,000 小时。
     不建模门，就会系统性高估亏损幅度、低估亏损概率。

  2. **时间按机会成本计价。** 现金上限 $4,500，而 3 年 3,000 小时按 $30/小时
     计价是 $90,000。**真正的赌注 95.2% 是时间。** 只算现金的模型是自欺。

  3. **未花掉的预算算作收回的本金。** 第 3 个月停手时，剩下的 2,900 小时
     仍然是你的。这正是 Kelly 框架所需的口径。

复现：python model/monte_carlo.py   （固定随机种子 20260727）
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

try:
    from . import assumptions as A
except ImportError:
    import assumptions as A  # type: ignore

SEED = 20260727
N_SIMS = 100_000
OUT_DIR = Path(__file__).resolve().parent.parent / "outputs"

HORIZON_MONTHS = 36


# --------------------------------------------------------------------------
# 一、阶段门的通过概率与代价
# --------------------------------------------------------------------------
# 全部为 SELF 级（本人主观估计）。**这是本模型中最主观的一组数字，
# 必须做敏感性分析，且 BP 中不得呈现为客观概率。**

@dataclass(frozen=True)
class GateSpec:
    name: str
    p_pass: float
    hours: float
    cash: float
    rationale: str


GATES = [
    GateSpec("Gate 0-A 收款通道", 0.85, 4, 0.0,
             "Paddle 官方文档在国别与币种两层均支持中国大陆（docs/GATE0.md §1.3），"
             "剩余风险仅为个案 KYC。未过时不终止，转回退路径（另计成本）"),
    GateSpec("Gate 0-B 流量验证", 0.35, 22, 12.0,
             "免费最小工具 14 天内获得 ≥300 UV 且 ≥30 次实际使用。"
             "无先验数据；参照 Show HN 项目中获得实质关注的比例，取约三分之一"),
    GateSpec("Gate 1 付费意愿", 0.30, 26, 0.0,
             "≥3 人真实预付 $99。条件于 Gate 0-B 已过。"
             "取值低于 Gate 0-B 的理由：从「免费愿意用」到「掏钱」的落差是"
             "本领域最大的一道坎（免费开源工具过剩，见 sources.md §4.4）"),
    GateSpec("Gate 2 MVP 交付", 0.85, 240, 0.0,
             "12 周 × 20 小时。C12 为纯规则引擎，工程风险低，"
             "opportunity_scoring 给可交付性 9 分"),
]

GATE0B_MAX_ATTEMPTS = 3   # 允许换 3 个候选赛道各试一次（docs/GATE0.md §3.2）

FALLBACK_ENTITY_CASH = 1000.0   # Gate 0-A 未过时的主体设立成本（美元）
FALLBACK_ENTITY_HOURS = 40.0


# --------------------------------------------------------------------------
# 二、经营期的随机变量
# --------------------------------------------------------------------------

def beta_from_mean_cv(mean: float, cv: float, rng, size: int) -> np.ndarray:
    """按目标均值与变异系数构造 Beta 分布（转化率与流失率用）。"""
    var = (mean * cv) ** 2
    max_var = mean * (1 - mean) * 0.999
    var = min(var, max_var)
    common = mean * (1 - mean) / var - 1
    a, b = mean * common, (1 - mean) * common
    return rng.beta(a, b, size)


TRAFFIC_MEDIAN_MULTIPLIER = 0.70   # SELF：计划流量的中位实现率。<1 反映计划乐观偏差
TRAFFIC_SIGMA = 0.80               # SELF：对数正态标准差。取大值反映 D 级假设的不确定性

# 突破分量：纯对数正态在结构上产不出创业该有的幂律右尾，这是**已知的模型设定错误**，
# 不是保守，而是错。开发者工具的实际结局跨越三个数量级（一端是无人问津，
# 另一端是被写进 awesome-list 与团队默认配置而成为事实标准）。
# 处理：显式加一个小概率的突破分量，并在敏感性里单独给出「关掉它」的对照，
# 让读者自己判断这一分量贡献了多少期望值。
P_BREAKOUT = 0.03                  # SELF：36 个月内成为某个细分事实标准的概率
BREAKOUT_MULT_LOG_MEAN = np.log(8.0)   # SELF：突破时的流量倍数中位数
BREAKOUT_MULT_LOG_SD = 0.60

TERMINAL_MULTIPLE_MIN = 1.5        # SELF/D：微型 SaaS 转让倍数（× ARR）
TERMINAL_MULTIPLE_MODE = 2.5
TERMINAL_MULTIPLE_MAX = 4.0
LIQUIDITY_PROBABILITY = 0.50       # SELF：能真正卖掉的概率。多数微型 SaaS 从未成交

P_BUNDLED_KILL_36M = 0.25          # SELF：36 个月内被平台方打包进免费订阅的概率。
                                   # 依据：Bugbot/Copilot 的历史行为模式（sources.md §4.2）


def simulate(n: int = N_SIMS, seed: int = SEED, require_card: bool = True,
             overrides: dict | None = None) -> dict:
    rng = np.random.default_rng(seed)
    ov = overrides or {}

    def g(key, default):
        return ov.get(key, default)

    # ---- 累计投入（小时 / 现金），初始化 ----
    hours = np.zeros(n)
    cash = np.zeros(n)
    alive = np.ones(n, dtype=bool)
    stop_stage = np.full(n, "运营中", dtype=object)

    # ---- Gate 0-A ----
    ga = GATES[0]
    hours += ga.hours
    passed_a = rng.random(n) < g("p_gate0a", ga.p_pass)
    need_fallback = alive & ~passed_a
    cash[need_fallback] += FALLBACK_ENTITY_CASH
    hours[need_fallback] += FALLBACK_ENTITY_HOURS
    # Gate 0-A 不致命：回退后继续

    # ---- Gate 0-B（最多 3 次尝试，每次换一个候选赛道）----
    gb = GATES[1]
    p_b = g("p_gate0b", gb.p_pass)
    attempts = np.zeros(n)
    passed_b = np.zeros(n, dtype=bool)
    for _ in range(GATE0B_MAX_ATTEMPTS):
        trying = alive & ~passed_b
        attempts[trying] += 1
        hours[trying] += gb.hours
        cash[trying] += gb.cash
        passed_b[trying] = rng.random(trying.sum()) < p_b
    stop_stage[alive & ~passed_b] = "止于 Gate 0-B（流量验证）"
    alive &= passed_b

    # ---- Gate 1 ----
    g1 = GATES[2]
    hours[alive] += g1.hours
    passed_1 = np.zeros(n, dtype=bool)
    passed_1[alive] = rng.random(alive.sum()) < g("p_gate1", g1.p_pass)
    stop_stage[alive & ~passed_1] = "止于 Gate 1（付费意愿）"
    alive &= passed_1

    # ---- Gate 2 ----
    g2 = GATES[3]
    hours[alive] += g2.hours
    passed_2 = np.zeros(n, dtype=bool)
    passed_2[alive] = rng.random(alive.sum()) < g("p_gate2", g2.p_pass)
    stop_stage[alive & ~passed_2] = "止于 Gate 2（MVP 未能交付）"
    alive &= passed_2

    # ---- 经营期 ----
    # 已用工时：门阶段合计；剩余月份把剩下的工时按每月 87 小时投入
    gate_months = 8.0                      # 前四道门约 8 个月日历时间
    op_months = HORIZON_MONTHS - gate_months
    # 用 HOURS_PER_YEAR/12 而非 HOURS_PER_WEEK×52/12：后者会漏掉
    # WEEKS_PER_YEAR=50 中已扣除的 2 周无产出时间，两者相差 4%
    monthly_hours = A.HOURS_PER_YEAR / 12

    # 随机变量
    traffic_mult = rng.lognormal(np.log(g("traffic_median", TRAFFIC_MEDIAN_MULTIPLIER)),
                                 g("traffic_sigma", TRAFFIC_SIGMA), n)
    breakout = rng.random(n) < g("p_breakout", P_BREAKOUT)
    traffic_mult = np.where(
        breakout,
        traffic_mult * rng.lognormal(BREAKOUT_MULT_LOG_MEAN, BREAKOUT_MULT_LOG_SD, n),
        traffic_mult)
    v2s_base, s2p_base = A.funnel_rates(require_card)
    v2s = beta_from_mean_cv(v2s_base, 0.35, rng, n)
    s2p = beta_from_mean_cv(s2p_base, 0.45, rng, n)
    churn = beta_from_mean_cv(g("churn", A.MONTHLY_LOGO_CHURN), 0.30, rng, n)

    # 被平台方打包进免费订阅的月度风险
    lam = -np.log(1 - g("p_bundled_kill", P_BUNDLED_KILL_36M)) / HORIZON_MONTHS
    kill_month = rng.exponential(1 / lam, n)

    # 计划流量曲线（来自 acquisition.py 的复利渠道锚点，线性插值）
    plan = np.interp(np.arange(1, HORIZON_MONTHS + 1),
                     [0, 12, 24, 36], [0.0, 360.0, 1500.0, 2500.0])

    net_pm_unit = (1 - A.REFUND_RATE) * (1 - A.mor_effective_rate(A.ARPU_USD)) * A.ARPU_USD

    customers = np.zeros(n)
    cum_profit = np.zeros(n)
    peak_drawdown = np.zeros(n)
    for m in range(int(gate_months) + 1, HORIZON_MONTHS + 1):
        active = alive & (kill_month > m)
        uv = plan[m - 1] * traffic_mult
        new_paid = np.where(active, uv * v2s * s2p, 0.0)
        customers = np.where(active, customers * (1 - churn) + new_paid, customers)
        rev = np.where(active, customers * net_pm_unit, 0.0)
        cost = np.where(active, A.INFRA_MONTHLY_USD, 0.0)
        cum_profit += rev - cost
        peak_drawdown = np.minimum(peak_drawdown, cum_profit)
        hours += np.where(active, monthly_hours, 0.0)
        cash += np.where(active, A.INFRA_MONTHLY_USD, 0.0)

    killed = alive & (kill_month <= HORIZON_MONTHS)
    stop_stage[killed] = "运营期被平台方打包功能击垮"

    # ---- 终值 ----
    tri = rng.triangular(TERMINAL_MULTIPLE_MIN, TERMINAL_MULTIPLE_MODE,
                         TERMINAL_MULTIPLE_MAX, n)
    liquid = rng.random(n) < g("liquidity_p", LIQUIDITY_PROBABILITY)
    arr = customers * A.ARPU_USD * 12
    terminal = np.where(alive & ~killed & liquid, arr * tri, 0.0)

    # ---- 汇总为收益倍数 ----
    # 全口径预算（若一路走到底）
    full_hours = A.HOURS_PER_YEAR * 3
    full_cash = A.CASH_CAP_USD + A.ENTITY_SETUP_RESERVE_USD
    hourly = g("hourly_cost", A.HOURLY_OPPORTUNITY_COST_USD)
    W = full_cash + full_hours * hourly                     # 全额赌注

    spent = cash + hours * hourly                           # 实际支出
    spent = np.minimum(spent, W)                            # 不允许超预算
    value = cum_profit + terminal                           # 实现价值
    M_full = (W - spent + value) / W                        # 全口径收益倍数

    # 只算现金的对照口径（刻意保留，用于说明它有多误导）
    W_cash = full_cash
    spent_cash = np.minimum(cash, W_cash)
    M_cash = (W_cash - spent_cash + value) / W_cash

    stages, counts = np.unique(stop_stage, return_counts=True)

    def pct(x, q):
        return float(np.percentile(x, q))

    return {
        "meta": {
            "seed": seed, "n_sims": n, "horizon_months": HORIZON_MONTHS,
            "require_card": require_card,
            "full_wager_usd": round(W, 2),
            "full_wager_cash_usd": round(W_cash, 2),
            "hourly_opportunity_cost": hourly,
            "overrides": ov,
        },
        "gates": [
            {"name": s.name, "p_pass": g(f"p_gate{i}", s.p_pass), "hours": s.hours,
             "rationale": s.rationale}
            for i, s in zip(["0a", "0b", "1", "2"], GATES)
        ],
        "stop_distribution": {str(k): int(v) / n for k, v in zip(stages, counts)},
        "survival_to_operation": float(np.mean(alive)),
        "outcomes_full": {
            "P10": pct(M_full, 10), "P25": pct(M_full, 25), "P50": pct(M_full, 50),
            "P75": pct(M_full, 75), "P90": pct(M_full, 90), "P99": pct(M_full, 99),
            "mean": float(np.mean(M_full)),
            "p_gain": float(np.mean(M_full > 1.0)),
            "p_loss_over_50pct": float(np.mean(M_full < 0.5)),
        },
        "outcomes_cash": {
            "P10": pct(M_cash, 10), "P50": pct(M_cash, 50), "P90": pct(M_cash, 90),
            "mean": float(np.mean(M_cash)),
            "p_gain": float(np.mean(M_cash > 1.0)),
        },
        # 条件于「活到经营期末」——这是「假如它真的跑起来了会是什么样」，
        # 与无条件分布并列呈现，防止「幸存者视角」被当成整体预期
        "conditional_on_survival": {
            "share_of_all_paths": float(np.mean(alive & ~killed)),
            "M_P10": pct(M_full[alive & ~killed], 10) if (alive & ~killed).any() else 0.0,
            "M_P50": pct(M_full[alive & ~killed], 50) if (alive & ~killed).any() else 0.0,
            "M_P90": pct(M_full[alive & ~killed], 90) if (alive & ~killed).any() else 0.0,
            "mrr_P10": pct(customers[alive & ~killed] * A.ARPU_USD, 10) if (alive & ~killed).any() else 0.0,
            "mrr_P50": pct(customers[alive & ~killed] * A.ARPU_USD, 50) if (alive & ~killed).any() else 0.0,
            "mrr_P90": pct(customers[alive & ~killed] * A.ARPU_USD, 90) if (alive & ~killed).any() else 0.0,
            "p_gain": float(np.mean(M_full[alive & ~killed] > 1.0)) if (alive & ~killed).any() else 0.0,
        },
        "expected_value_usd": {
            "full_accounting": float((np.mean(M_full) - 1.0) * W),
            "cash_only": float((np.mean(M_cash) - 1.0) * W_cash),
        },
        "business_metrics": {
            "customers_P50": pct(customers, 50), "customers_P90": pct(customers, 90),
            "mrr_P50": pct(customers * A.ARPU_USD, 50),
            "mrr_P90": pct(customers * A.ARPU_USD, 90),
            "mrr_P99": pct(customers * A.ARPU_USD, 99),
            "cum_profit_P10": pct(cum_profit, 10), "cum_profit_P50": pct(cum_profit, 50),
            "cum_profit_P90": pct(cum_profit, 90),
            "hours_spent_P50": pct(hours, 50), "hours_spent_P90": pct(hours, 90),
            "cash_spent_P50": pct(cash, 50), "cash_spent_P90": pct(cash, 90),
            "peak_cash_drawdown_P10": pct(peak_drawdown, 10),
            "p_reach_1000_mrr": float(np.mean(customers * A.ARPU_USD >= 1000)),
            "p_reach_3018_mrr_full_breakeven": float(np.mean(customers * A.ARPU_USD >= 3018)),
        },
        "_samples": M_full,          # 供 kelly.py 使用，不写入 JSON
        "_committed": passed_1,      # 过了 Gate 1 = 真正开始重投入的路径
    }


# --------------------------------------------------------------------------
# 三、收敛性与敏感性
# --------------------------------------------------------------------------

def convergence(seeds: int = 8) -> list[dict]:
    """收敛性必须检验**噪声最大**的统计量，而不是最稳的那个。

    此处用均值而非中位数：本分布的中位数落在「止于 Gate 1」这个确定性质量点上，
    跨种子标准差恒为 0，看着漂亮但毫无信息量。均值由右尾驱动，才是真正的难点。
    """
    out = []
    for n in (1_000, 10_000, 100_000):
        stats = [simulate(n=n, seed=SEED + k)["_samples"] for k in range(seeds)]
        means = [float(np.mean(s)) for s in stats]
        p999 = [float(np.percentile(s, 99.9)) for s in stats]
        out.append({
            "n": n,
            "mean_of_means": float(np.mean(means)),
            "mean_sd_across_seeds": float(np.std(means)),
            "mean_relative_sd": float(np.std(means) / abs(np.mean(means))),
            "P999_mean": float(np.mean(p999)),
            "P999_relative_sd": float(np.std(p999) / abs(np.mean(p999))),
        })
    return out


def sensitivity() -> list[dict]:
    """对最主观的几个输入做扰动，看结论是否稳固。"""
    base = simulate(n=20_000)
    rows = [{"scenario": "基准", "p_gain": base["outcomes_full"]["p_gain"],
             "P50": base["outcomes_full"]["P50"], "mean": base["outcomes_full"]["mean"]}]
    cases = {
        "Gate 0-B 通过率 0.35→0.20": {"p_gate0b": 0.20},
        "Gate 0-B 通过率 0.35→0.55": {"p_gate0b": 0.55},
        "Gate 1 通过率 0.30→0.15": {"p_gate1": 0.15},
        "Gate 1 通过率 0.30→0.50": {"p_gate1": 0.50},
        "流量中位实现率 0.7→0.4": {"traffic_median": 0.40},
        "流量中位实现率 0.7→1.0": {"traffic_median": 1.00},
        "时间机会成本 $30→$15/h": {"hourly_cost": 15.0},
        "时间机会成本 $30→$60/h": {"hourly_cost": 60.0},
        "时间机会成本 $30→$0/h（纯闲暇口径）": {"hourly_cost": 0.0001},
        "月流失 7%→10%": {"churn": 0.10},
        "被打包风险 25%→50%": {"p_bundled_kill": 0.50},
        "关掉突破分量 P=3%→0（纯对数正态）": {"p_breakout": 0.0},
        "突破概率 3%→8%": {"p_breakout": 0.08},
        "乐观组合（各门+流量同时向好）": {
            "p_gate0b": 0.55, "p_gate1": 0.50, "traffic_median": 1.0,
            "churn": 0.05, "p_bundled_kill": 0.15},
    }
    for name, ov in cases.items():
        r = simulate(n=20_000, overrides=ov)
        rows.append({"scenario": name, "p_gain": r["outcomes_full"]["p_gain"],
                     "P50": r["outcomes_full"]["P50"], "mean": r["outcomes_full"]["mean"]})
    return rows


def run() -> dict:
    card = simulate(require_card=True)
    nocard = simulate(require_card=False)
    res = {k: v for k, v in card.items() if not k.startswith("_")}
    res["no_card_comparison"] = {
        "outcomes_full": nocard["outcomes_full"],
        "business_metrics": {k: nocard["business_metrics"][k]
                             for k in ("mrr_P50", "mrr_P90", "p_reach_1000_mrr")},
    }
    res["convergence"] = convergence()
    res["sensitivity"] = sensitivity()
    return res


def main() -> None:
    r = run()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "monte_carlo.json").write_text(
        json.dumps(r, ensure_ascii=False, indent=2, default=float), encoding="utf-8")

    m = r["meta"]
    print("=" * 78)
    print(f"蒙特卡洛  {m['n_sims']:,} 次 × {m['horizon_months']} 个月  种子 {m['seed']}")
    print("=" * 78)
    print(f"  全额赌注（现金 + 时间机会成本）: ${m['full_wager_usd']:,.0f}")
    print(f"  仅现金口径                    : ${m['full_wager_cash_usd']:,.0f}"
          f"   （时间占赌注的 {1 - m['full_wager_cash_usd']/m['full_wager_usd']:.1%}）")

    print("\n【终局分布：项目最后停在哪一步】")
    for k, v in sorted(r["stop_distribution"].items(), key=lambda kv: -kv[1]):
        print(f"  {k:<32} {v:>7.2%}")
    print(f"  → 能走到经营期的比例: {r['survival_to_operation']:.2%}")

    o = r["outcomes_full"]
    print("\n【收益倍数分布（全口径：现金 + 时间，未花掉的预算算收回）】")
    for q in ("P10", "P25", "P50", "P75", "P90", "P99"):
        print(f"  {q:>4}: {o[q]:>7.4f}")
    print(f"  均值: {o['mean']:>7.4f}   （均值 ≠ 中位数，即 Flaw of Averages）")
    print(f"  P(收益 > 1，即不亏): {o['p_gain']:.2%}")
    print(f"  P(损失超过一半)    : {o['p_loss_over_50pct']:.2%}")

    ev = r["expected_value_usd"]
    print(f"  期望值（全口径）: ${ev['full_accounting']:>+10,.0f}")

    oc = r["outcomes_cash"]
    print("\n【对照：只算现金的口径（**刻意保留以说明它有多误导**）】")
    print(f"  P10 {oc['P10']:.3f} | P50 {oc['P50']:.3f} | P90 {oc['P90']:.3f}"
          f" | 均值 {oc['mean']:.3f} | P(不亏) {oc['p_gain']:.2%}")
    print(f"  期望值（仅现金）: ${ev['cash_only']:>+10,.0f}")
    print("  → 只算现金时结论好看得多，因为它把最大的一项投入（时间）当成了免费的。")

    cs = r["conditional_on_survival"]
    print(f"\n【条件于「活到第 36 个月」（占全部路径 {cs['share_of_all_paths']:.2%}）】")
    print(f"  MRR      P10 ${cs['mrr_P10']:>7,.0f} | P50 ${cs['mrr_P50']:>7,.0f}"
          f" | P90 ${cs['mrr_P90']:>8,.0f}")
    print(f"  收益倍数 P10 {cs['M_P10']:>8.3f} | P50 {cs['M_P50']:>8.3f}"
          f" | P90 {cs['M_P90']:>9.3f}")
    print(f"  即便活下来，P(不亏) 也只有 {cs['p_gain']:.2%}"
          f" —— 因为 3,000 小时的机会成本要 $3,018 MRR 才补得回来。")

    b = r["business_metrics"]
    print("\n【经营指标（第 36 月）】")
    print(f"  MRR      P50 ${b['mrr_P50']:>8,.0f} | P90 ${b['mrr_P90']:>8,.0f}"
          f" | P99 ${b['mrr_P99']:>9,.0f}")
    print(f"  三年累计利润 P10 ${b['cum_profit_P10']:>7,.0f} | P50 ${b['cum_profit_P50']:>8,.0f}"
          f" | P90 ${b['cum_profit_P90']:>8,.0f}")
    print(f"  投入工时 P50 {b['hours_spent_P50']:>6,.0f} h | P90 {b['hours_spent_P90']:>6,.0f} h")
    print(f"  投入现金 P50 ${b['cash_spent_P50']:>6,.0f} | P90 ${b['cash_spent_P90']:>6,.0f}")
    print(f"  P(达到 $1,000 MRR)            : {b['p_reach_1000_mrr']:.2%}")
    print(f"  P(达到 $3,018 MRR 真实盈亏平衡): {b['p_reach_3018_mrr_full_breakeven']:.2%}")

    nc = r["no_card_comparison"]
    print("\n【信用卡开关的对照】")
    print(f"  要卡  : P(不亏) {o['p_gain']:.2%} | MRR P50 ${b['mrr_P50']:,.0f}"
          f" | P(达 $1k MRR) {b['p_reach_1000_mrr']:.2%}")
    print(f"  不要卡: P(不亏) {nc['outcomes_full']['p_gain']:.2%}"
          f" | MRR P50 ${nc['business_metrics']['mrr_P50']:,.0f}"
          f" | P(达 $1k MRR) {nc['business_metrics']['p_reach_1000_mrr']:.2%}")

    print("\n【收敛性（检验噪声最大的统计量：均值，由右尾驱动）】")
    for c in r["convergence"]:
        print(f"  n={c['n']:>7,}: 均值 {c['mean_of_means']:.4f}，"
              f"跨 8 个种子相对标准差 {c['mean_relative_sd']:.2%}；"
              f"P99.9 = {c['P999_mean']:.3f}，相对标准差 {c['P999_relative_sd']:.2%}")

    print("\n【敏感性：最主观的输入扰动后结论是否稳固】")
    print(f"  {'情景':<30}{'P(不亏)':>10}{'P50':>9}{'均值':>9}")
    for s in r["sensitivity"]:
        print(f"  {s['scenario']:<30}{s['p_gain']:>10.2%}{s['P50']:>9.4f}{s['mean']:>9.4f}")
    print(f"\n输出已写入 {OUT_DIR / 'monte_carlo.json'}")


if __name__ == "__main__":
    main()
