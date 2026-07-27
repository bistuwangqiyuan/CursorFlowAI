"""胜率、盈亏比、期望值、Kelly 最优比例，以及三种年化口径。

**本文件的头等任务是防止误用，其次才是算数。** Kelly 在单人创业这个情境下
是失效的，理由不是「不够精确」，而是三条结构性的：

  1. Breiman(1961) 的最优性证明**全部是渐近结论**（n → ∞）。Thorp 自己给的
     量化例子：区分 1.0% 与 1.1% 的优势，需要**两百万次试验**才有 84% 把握。
     一个人一生能下的创业注是个位数，大数律在此完全不工作。
  2. Samuelson 1971(PNAS) / 1979(JBF) 的正式反对：最大化 E[ln] 只有在效用函数
     恰好是对数时才是最优的，它不是一条普适定理。
  3. Kelly 假设赌注可无限分割、可重复、赔率已知。创业三条全不满足：
     不能下 0.37 个产品，不能重来，赔率本身是估出来的。

因此本文件的输出**只能作为「下注规模上限的参照」，绝不能作为承诺或建议**。

禁用清单（均在本文件中以实测数据推翻，见 verify_forbidden_approximations()）：
  - 禁用 g ≈ μ − σ²/2 波动率拖累近似式
  - 禁用「半 Kelly 保留 75% 增长率」的 c(2−c) 连续近似

复现：python model/kelly.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy import optimize

try:
    from . import assumptions as A
    from . import monte_carlo as MC
except ImportError:
    import assumptions as A  # type: ignore
    import monte_carlo as MC  # type: ignore

OUT_DIR = Path(__file__).resolve().parent.parent / "outputs"
EPS = 1e-9

# 结果分档的边界（收益倍数 M）。分档只为叙述方便，
# 所有 Kelly 计算一律直接用 10 万个连续样本，不用分档后的代表值。
BUCKETS = [
    ("全损（回收 <25%）",      -np.inf, 0.25),
    ("重损（25%–75%）",          0.25, 0.75),
    ("轻损（75%–100%）",         0.75, 1.00),
    ("回本至小成（1.0–2.0 倍）",  1.00, 2.00),
    ("中成（2.0–5.0 倍）",       2.00, 5.00),
    ("大成（>5 倍）",            5.00, np.inf),
]


# --------------------------------------------------------------------------
# 一、胜率、盈亏比、期望值
# --------------------------------------------------------------------------

def win_loss_stats(M: np.ndarray) -> dict:
    """胜率 p、盈亏比 b、期望值 E = p·W − q·L。

    口径说明（**这三个词在民间用法混乱，此处一次性钉死**）：
      - 胜率 p    = P(M > 1)，即「拿回来的比投进去的多」的概率
      - 平均盈利 W = E[M − 1 | M > 1]，只在盈利路径上取均值
      - 平均亏损 L = E[1 − M | M ≤ 1]，取正数
      - 盈亏比 b  = W / L
      - 期望值    = p·W − q·L，应与 E[M] − 1 完全相等（本函数自校验）
    """
    wins, losses = M[M > 1.0], M[M <= 1.0]
    p = float(len(wins) / len(M))
    q = 1.0 - p
    W = float(np.mean(wins - 1.0)) if len(wins) else 0.0
    L = float(np.mean(1.0 - losses)) if len(losses) else 0.0
    b = W / L if L > EPS else float("inf")
    ev = p * W - q * L
    ev_direct = float(np.mean(M) - 1.0)
    assert abs(ev - ev_direct) < 1e-9, f"期望值口径自校验失败: {ev} vs {ev_direct}"
    return {
        "win_rate_p": p, "loss_rate_q": q,
        "avg_win_W": W, "avg_loss_L": L, "payoff_ratio_b": b,
        "expected_value": ev,
        "kelly_two_outcome": (b * p - q) / b if b not in (0, float("inf")) else float("nan"),
        "breakeven_win_rate": 1 / (1 + b) if b > 0 and np.isfinite(b) else float("nan"),
    }


def bucket_table(M: np.ndarray) -> list[dict]:
    rows = []
    for name, lo, hi in BUCKETS:
        m = (M > lo) & (M <= hi)
        rows.append({
            "bucket": name, "probability": float(np.mean(m)),
            "mean_multiple": float(np.mean(M[m])) if m.any() else 0.0,
        })
    total = sum(r["probability"] for r in rows)
    assert abs(total - 1.0) < 1e-9, f"分档概率不为 1: {total}"
    return rows


# --------------------------------------------------------------------------
# 二、Kelly：直接对经验分布数值最大化 E[ln(1 + f·X)]
# --------------------------------------------------------------------------

def kelly_full(M: np.ndarray) -> dict:
    """对 10 万个样本直接数值最大化 E[ln(1 + f·X)]，X = M − 1。

    不用两结果闭式解，因为本项目的结果是六档以上的连续分布；
    闭式解 f* = (bp − q)/b 只在「非赢即输、赔率固定」时成立，此处仅作对照。
    """
    X = M - 1.0
    x_min = float(np.min(X))
    # 破产约束：f 必须使 1 + f·x_min > 0
    f_max = (1.0 / -x_min - 1e-6) if x_min < 0 else 10.0
    f_max = min(f_max, 10.0)

    def neg_growth(f: float) -> float:
        v = 1.0 + f * X
        if np.any(v <= 0):
            return 1e9
        return -float(np.mean(np.log(v)))

    if neg_growth(1e-6) >= neg_growth(0.0):
        f_star = 0.0   # 优势为负，Kelly 的答案是「不下注」
    else:
        r = optimize.minimize_scalar(neg_growth, bounds=(0.0, f_max), method="bounded",
                                     options={"xatol": 1e-8})
        f_star = float(r.x)

    return {
        "f_star": f_star,
        "growth_rate_at_f_star": -neg_growth(f_star),
        "growth_rate_at_f_1": -neg_growth(1.0) if f_max >= 1.0 else float("nan"),
        "max_safe_f": f_max,
        "worst_case_multiple": float(np.min(M)),
        "kelly_says_do_not_bet": f_star < 1e-6,
    }


def fractional_kelly_retention(M: np.ndarray, f_star: float) -> list[dict]:
    """分数 Kelly 的增长率保留比例——**必须用本项目的离散分布实测**。

    禁用 Thorp 2006 eq.(7.7) 的 c(2−c) 近似（它假设连续时间/对数正态）。
    此处逐点重算 E[ln(1 + c·f*·X)] 并与峰值相比，得到真实保留比例。
    """
    X = M - 1.0

    def growth(f):
        v = 1.0 + f * X
        return float(np.mean(np.log(v))) if np.all(v > 0) else float("-inf")

    g_star = growth(f_star)
    rows = []
    for c in (0.25, 0.5, 0.75, 1.0, 1.5, 2.0):
        g = growth(c * f_star)
        ruined = not np.isfinite(g)
        rows.append({
            "fraction_c": c,
            "f": c * f_star,
            "growth_rate": g if np.isfinite(g) else None,
            "ruin": ruined,   # 存在一条使 1 + f·X ≤ 0 的路径，即会被打光
            "retention_measured": (None if ruined
                                   else (g / g_star) if abs(g_star) > EPS else None),
            "retention_c2minusc_approx": c * (2 - c),   # 被禁用的近似，仅作对照
        })
    return rows


# --------------------------------------------------------------------------
# 三、三种年化口径（**必须全部并列，不允许只报有利的那一个**）
# --------------------------------------------------------------------------

def annualization_conventions(M: np.ndarray, years: float = 3.0) -> dict:
    Ms = np.maximum(M, EPS)
    survived = Ms[Ms > 0.25]        # 非「全损」路径

    conv = {
        "A_expect_then_annualize": {
            "label": "口径 A：先算期望倍数，再年化",
            "formula": "(E[M])^(1/T) − 1",
            "value": float(np.mean(M)) ** (1 / years) - 1,
            "misleading_because":
                "最容易被误读为「预期年化收益」。它是**均值的年化**，"
                "而均值被极少数右尾路径拉动；中位路径拿不到这个数。",
        },
        "B_annualize_then_expect": {
            "label": "口径 B：各路径先年化，再取期望",
            "formula": "E[M^(1/T)] − 1",
            "value": float(np.mean(Ms ** (1 / years))) - 1,
            "misleading_because":
                "由 Jensen 不等式，恒 ≤ 口径 A。它更贴近「随机抽一条路径的年化」，"
                "但把全损路径的 −100% 也平均了进来，会低估「做成时」的量级。",
        },
        "C_geometric_conditional_on_survival": {
            "label": "口径 C：条件于未全损的几何平均年化",
            "formula": "exp(E[ln M | M > 0.25])^(1/T) − 1",
            "value": float(np.exp(np.mean(np.log(survived)))) ** (1 / years) - 1,
            "misleading_because":
                f"**隐藏了 {float(np.mean(Ms <= 0.25)):.1%} 的全损概率。**"
                "这是创业故事里最常被单独引用的数字，也是最危险的一个。",
        },
        "D_true_geometric_all_paths": {
            "label": "口径 D：全路径几何平均年化（重复下注的真实增长率）",
            "formula": "exp(E[ln M])^(1/T) − 1",
            "value": float(np.exp(np.mean(np.log(Ms)))) ** (1 / years) - 1,
            "misleading_because":
                "这一口径本身不误导，但**只在「能重复下很多次同样的注」时才有意义**。"
                "单人创业一生下注个位数次，此数是理论参照而非可实现收益。",
        },
    }
    conv["_spread_pct_points"] = (max(v["value"] for k, v in conv.items() if k != "_spread_pct_points")
                                  - min(v["value"] for k, v in conv.items()
                                        if k != "_spread_pct_points")) * 100
    conv["_risk_free_comparison"] = {
        "us_10y": A.RF_US_10Y, "cn_10y": A.RF_CN_10Y,
        "note": "同一分布可产出相差数十个百分点的四个「年化」。"
                "BP 中任何一处出现「年化 XX%」，必须紧跟口径名与该口径的误导风险说明。",
    }
    return conv


# --------------------------------------------------------------------------
# 四、被禁用公式的实测反驳（不是引用别人的话，是自己算给自己看）
# --------------------------------------------------------------------------

def verify_forbidden_approximations(M: np.ndarray, f_star: float) -> dict:
    """把两条禁用公式在**本项目自己的数据上**跑一遍，证明它们错在哪。"""
    logM = np.log(np.maximum(M, EPS))
    mu_log, sigma_log = float(np.mean(logM)), float(np.std(logM))
    mu_arith = float(np.mean(M - 1.0))
    sigma_arith = float(np.std(M - 1.0))

    exact_g = mu_log                                   # 精确对数增长率
    approx_g = mu_arith - sigma_arith ** 2 / 2         # 被禁用的近似式

    ret = fractional_kelly_retention(M, f_star) if f_star > EPS else []
    half = next((r for r in ret if r["fraction_c"] == 0.5), None)
    if half is not None and half["retention_measured"] is None:
        half = None

    return {
        "volatility_drag": {
            "exact_log_growth": exact_g,
            "approx_mu_minus_half_sigma2": approx_g,
            "absolute_error": approx_g - exact_g,
            "sign_flipped": (exact_g > 0) != (approx_g > 0),
            "verdict":
                "近似式 g ≈ μ − σ²/2 只在小波动下成立。本项目 σ(算术) = "
                f"{sigma_arith:.3f}，远超其适用范围，误差 {abs(approx_g - exact_g):.4f}。"
                "**禁用，一律用精确式 E[ln M]。**",
        },
        "half_kelly_retention": {
            "measured": half["retention_measured"] if half else None,
            "c2minusc_approx": 0.75,
            "verdict":
                ("Kelly 最优比例为 0（优势为负），分数 Kelly 无从谈起。"
                 if f_star <= EPS else
                 "半 Kelly 处已存在被打光的路径，实测保留比例无定义。"
                 if half is None else
                 f"实测半 Kelly 保留 {half['retention_measured']:.1%}，"
                 f"而流传的 c(2−c) 近似给出 75.0%。**禁用近似，用实测值。**"),
        },
    }


# --------------------------------------------------------------------------
# 五、不作为结论指标的风险调整比率（仅方法论附录用）
# --------------------------------------------------------------------------

def inapplicable_ratios(M: np.ndarray, years: float = 3.0) -> dict:
    """夏普 / 索提诺 / Omega：**算出来是为了说明为什么不能用**。"""
    rf_total = (1 + A.RF_US_10Y) ** years - 1
    excess = (M - 1.0) - rf_total
    sd = float(np.std(M - 1.0))
    downside = M[M - 1.0 < rf_total]
    dsd = float(np.sqrt(np.mean(((downside - 1.0) - rf_total) ** 2))) if len(downside) else EPS
    gains = np.maximum((M - 1.0) - rf_total, 0)
    pains = np.maximum(rf_total - (M - 1.0), 0)
    return {
        "sharpe": float(np.mean(excess)) / sd if sd > EPS else float("nan"),
        "sortino": float(np.mean(excess)) / dsd if dsd > EPS else float("nan"),
        "omega": float(np.mean(gains) / np.mean(pains)) if np.mean(pains) > EPS else float("inf"),
        "skewness": float(np.mean(((M - np.mean(M)) / np.std(M)) ** 3)),
        "excess_kurtosis": float(np.mean(((M - np.mean(M)) / np.std(M)) ** 4) - 3),
        "why_not_reported_as_conclusion":
            "这三个比率均以「收益对称、波动可作为风险代理」为前提。本分布偏度 "
            "与超额峰度都极高（见上），标准差主要由**右尾的好结果**贡献，"
            "于是「波动越大 = 越危险」的解读方向是反的。把它们放进 BP 正文，"
            "只会让读者得到与事实相反的印象。仅在方法论附录中作为反例出现。",
    }


# --------------------------------------------------------------------------

def commitment_view(M: np.ndarray, committed: np.ndarray) -> dict:
    """**防误读专用。**

    无条件胜率会低到 1.81%，但这个数字单独看是误导的：其中 84% 的路径
    是「在 Gate 0-B 或 Gate 1 就停手、只亏掉几十小时」，不是血本无归。
    阶段门的全部意义正在于此——它把「失败」从「破产」降级为「小额学费」。

    因此必须同时给出条件于「过了 Gate 1、真正开始重投入」的分布。
    这一条件下的胜率才是「决定全力投入之后成败几何」的那个数。
    """
    if not committed.any():
        return {}
    Mc = M[committed]
    s = win_loss_stats(Mc)
    return {
        "share_of_paths_committed": float(np.mean(committed)),
        "win_rate_given_commitment": s["win_rate_p"],
        "avg_loss_given_commitment": s["avg_loss_L"],
        "payoff_ratio_given_commitment": s["payoff_ratio_b"],
        "expected_value_given_commitment": s["expected_value"],
        "note":
            "对比无条件胜率可见：阶段门把绝大多数失败拦在了「只亏几十小时」的阶段。"
            "无条件胜率低 ≠ 风险大；真正的风险集中在通过 Gate 1 之后的 240+ 小时。",
    }


def analyse(M: np.ndarray, label: str, bankroll_usd: float, wager_usd: float,
            committed: np.ndarray | None = None) -> dict:
    stats = win_loss_stats(M)
    k = kelly_full(M)
    res = {
        "label": label,
        "bankroll_usd": bankroll_usd,
        "planned_wager_usd": wager_usd,
        "planned_wager_as_fraction_of_bankroll": wager_usd / bankroll_usd,
        "win_loss": stats,
        "buckets": bucket_table(M),
        "kelly": k,
        "kelly_implied_wager_usd": k["f_star"] * bankroll_usd,
        "kelly_exceeds_bankroll": k["f_star"] > 1.0,
        "commitment_view": commitment_view(M, committed) if committed is not None else {},
        "fractional_kelly": fractional_kelly_retention(M, k["f_star"]) if k["f_star"] > EPS else [],
        "annualization": annualization_conventions(M),
        "forbidden_approximations": verify_forbidden_approximations(M, k["f_star"]),
        "inapplicable_ratios": inapplicable_ratios(M),
    }
    return res


def indifference_hourly_rate(lo: float = 0.01, hi: float = 60.0,
                             tol: float = 0.25, n: int = 40_000) -> dict:
    """求「时间机会成本」的无差异点：时薪低于多少，全口径期望值才转正。

    这是整份分析里最可操作的一个数——它把一个抽象的取舍
    （「值不值得做」）翻译成一个可以对着自己回答的问题：
    **「我这 20 小时/周，拿去做别的真能挣到 $X/小时吗？」**

    用二分法。期望值关于时薪单调递减（时薪只出现在成本侧），故二分成立。
    """
    def ev_at(rate: float) -> float:
        r = MC.simulate(n=n, overrides={"hourly_cost": max(rate, 1e-4)})
        return r["outcomes_full"]["mean"] - 1.0

    ev_lo, ev_hi = ev_at(lo), ev_at(hi)
    if ev_lo <= 0:
        return {"exists": False, "reason": f"即便时薪按 ${lo}/h，期望值仍为 {ev_lo:+.4f}",
                "ev_at_lo": ev_lo}
    if ev_hi > 0:
        return {"exists": False, "reason": f"时薪按 ${hi}/h 期望值仍为正 {ev_hi:+.4f}",
                "ev_at_hi": ev_hi}

    a, b = lo, hi
    while b - a > tol:
        mid = (a + b) / 2
        if ev_at(mid) > 0:
            a = mid
        else:
            b = mid
    rate = (a + b) / 2
    return {
        "exists": True,
        "indifference_hourly_usd": rate,
        "annual_equivalent_usd": rate * A.HOURS_PER_YEAR,
        "assumed_hourly_usd": A.HOURLY_OPPORTUNITY_COST_USD,
        "verdict":
            f"全口径期望值在时薪约 ${rate:.1f}/h 处由正转负。"
            f"换算成年：这 1,000 小时/年若能在别处挣到超过 "
            f"${rate * A.HOURS_PER_YEAR:,.0f}/年，就不该做这个项目；挣不到，就该做。"
            f"当前假设值为 ${A.HOURLY_OPPORTUNITY_COST_USD:.0f}/h，"
            f"{'高于' if A.HOURLY_OPPORTUNITY_COST_USD > rate else '低于'}无差异点。",
        "n_sims_per_eval": n,
        "note": "此处用 4 万次/评估以控制二分法的总耗时；"
                "均值的跨种子相对标准差在此规模下约 0.5%，不影响 ±$0.25/h 的分辨率。",
    }


def run() -> dict:
    full = MC.simulate(require_card=True)
    M_full = full["_samples"]

    # 现金口径样本需要重算（monte_carlo 只把全口径样本带出来）
    cash_res = MC.simulate(require_card=True, overrides={"hourly_cost": 0.0001})
    M_cash = cash_res["_samples"]

    W_full = full["meta"]["full_wager_usd"]

    out = {
        "meta": {
            "seed": MC.SEED, "n_sims": MC.N_SIMS,
            "note": "两种口径并列。**全口径是本 BP 的正式口径**；"
                    "现金口径保留是为了展示忽略时间成本会得出多么不同的结论。",
        },
        "full_accounting": analyse(
            M_full, "全口径（现金 + 时间机会成本 $30/h）",
            bankroll_usd=A.INVESTABLE_NET_ASSETS_USD + A.HOURS_PER_YEAR * 3 * A.HOURLY_OPPORTUNITY_COST_USD,
            wager_usd=W_full, committed=full["_committed"]),
        "cash_only": analyse(
            M_cash, "现金口径（时间按 $0 计，即把 20 小时/周当纯闲暇）",
            bankroll_usd=A.INVESTABLE_NET_ASSETS_USD,
            wager_usd=A.CASH_CAP_USD + A.ENTITY_SETUP_RESERVE_USD,
            committed=cash_res["_committed"]),
    }
    # 现金口径的 f* > 1 不是「该加杠杆」，而是该口径本身的归谬证明
    if out["cash_only"]["kelly_exceeds_bankroll"]:
        out["cash_only"]["reductio_ad_absurdum"] = (
            f"现金口径下 Kelly 解出 f* = {out['cash_only']['kelly']['f_star']:.3f} > 1，"
            f"即「押上全部身家的 {out['cash_only']['kelly']['f_star']:.0%} 还不够」。"
            "这是个荒谬的处方，而荒谬恰恰是有用的：它证明**现金口径本身是错的**。"
            "Kelly 之所以敢让你满仓，是因为在该口径下你几乎亏不掉什么"
            f"（最差路径仍回收 {out['cash_only']['kelly']['worst_case_multiple']:.1%}）——"
            "而这只是因为它把三年 3,000 小时当成了免费的。"
            "教训：**一个模型给出「无限加杠杆」的建议时，要怀疑的是模型而不是自己的胆量**。")

    out["indifference_hourly_rate"] = indifference_hourly_rate()
    return out


def _wrap(text: str, width: int, indent: str) -> str:
    """按显示宽度折行（中文按 2 列计），避免终端里长句被硬截。"""
    lines, cur, w = [], "", 0
    for ch in text:
        cw = 2 if ord(ch) > 0x2E80 else 1
        if w + cw > width * 2 and ch in "，。；：、":
            cur += ch
            lines.append(cur)
            cur, w = "", 0
            continue
        cur += ch
        w += cw
    if cur:
        lines.append(cur)
    return "\n".join(indent + ln for ln in lines)


def _print_block(r: dict) -> None:
    print("\n" + "=" * 78)
    print(f"  {r['label']}")
    print("=" * 78)
    wl = r["win_loss"]
    print(f"  胜率 p            : {wl['win_rate_p']:.2%}")
    print(f"  平均盈利 W        : {wl['avg_win_W']:+.4f}   （条件于盈利路径）")
    print(f"  平均亏损 L        : {wl['avg_loss_L']:.4f}   （条件于亏损路径，取正）")
    print(f"  盈亏比 b = W/L    : {wl['payoff_ratio_b']:.3f}")
    print(f"  期望值 p·W − q·L  : {wl['expected_value']:+.4f}")
    print(f"  保本所需胜率 1/(1+b): {wl['breakeven_win_rate']:.2%}"
          f"   （实际胜率 {wl['win_rate_p']:.2%}，"
          f"{'达标' if wl['win_rate_p'] >= wl['breakeven_win_rate'] else '**不达标**'}）")

    cv = r.get("commitment_view") or {}
    if cv:
        print(f"\n  【防误读】上面的胜率 {wl['win_rate_p']:.2%} 不可单独引用。"
              f"典型亏损只有 {wl['avg_loss_L']:.1%}（不是 100%），")
        print(f"  因为 {1 - cv['share_of_paths_committed']:.1%} 的路径在 "
              f"Gate 0-B / Gate 1 就停手，只亏掉几十小时的学费。")
        print(f"  条件于「过了 Gate 1、真正重投入」（占 {cv['share_of_paths_committed']:.2%}）："
              f"胜率 {cv['win_rate_given_commitment']:.2%}，"
              f"盈亏比 {cv['payoff_ratio_given_commitment']:.2f}，"
              f"期望 {cv['expected_value_given_commitment']:+.3f}")

    print("\n  结果分档：")
    for b in r["buckets"]:
        print(f"    {b['bucket']:<24} {b['probability']:>7.2%}   "
              f"档内均值 {b['mean_multiple']:.3f}")

    k = r["kelly"]
    print(f"\n  Kelly 最优比例 f* : {k['f_star']:.4f}"
          f"   （数值最大化 E[ln(1+f·X)]，非闭式解）")
    print(f"  两结果闭式解对照  : {wl['kelly_two_outcome']:.4f}"
          f"   （(bp−q)/b，仅供对照，此处不适用）")
    print(f"  f* 处的对数增长率 : {k['growth_rate_at_f_star']:+.5f}")
    print(f"  Kelly 隐含下注额  : ${r['kelly_implied_wager_usd']:,.0f}"
          f"   vs 计划下注 ${r['planned_wager_usd']:,.0f}")
    if k["kelly_says_do_not_bet"]:
        print("  ** Kelly 的答案是「一分钱都不要下」——因为期望优势为负。 **")
    if r.get("reductio_ad_absurdum"):
        print("\n  ** 归谬 **")
        print(_wrap(r["reductio_ad_absurdum"], width=34, indent="    "))

    if r["fractional_kelly"]:
        print("\n  分数 Kelly 的增长率保留（实测 vs 被禁用的 c(2−c) 近似）：")
        for fr in r["fractional_kelly"]:
            measured = ("**下注过量，存在被打光的路径**" if fr["ruin"]
                        else f"实测保留 {fr['retention_measured']:>7.1%}")
            print(f"    c={fr['fraction_c']:<5} f={fr['f']:.4f}  {measured:<28}"
                  f"近似式 {fr['retention_c2minusc_approx']:>6.1%}")

    print("\n  四种年化口径（全部并列，不允许只报有利的）：")
    for key, v in r["annualization"].items():
        if key.startswith("_"):
            continue
        print(f"    {v['label']:<34} {v['value']:>+9.2%}   {v['formula']}")
    print(f"    → 极差 {r['annualization']['_spread_pct_points']:.1f} 个百分点。"
          f"无风险利率：美 10Y {A.RF_US_10Y:.2%}／中 10Y {A.RF_CN_10Y:.2%}")

    fa = r["forbidden_approximations"]
    vd = fa["volatility_drag"]
    print(f"\n  禁用公式实测：g ≈ μ − σ²/2 得 {vd['approx_mu_minus_half_sigma2']:+.4f}，"
          f"精确值 {vd['exact_log_growth']:+.4f}，"
          f"误差 {vd['absolute_error']:+.4f}"
          f"{'（**连符号都反了**）' if vd['sign_flipped'] else ''}")
    print(f"  {fa['half_kelly_retention']['verdict']}")

    ir = r["inapplicable_ratios"]
    print(f"\n  【方法论附录用，不作结论】夏普 {ir['sharpe']:.3f}／"
          f"索提诺 {ir['sortino']:.3f}／Omega {ir['omega']:.3f}；"
          f"偏度 {ir['skewness']:.2f}，超额峰度 {ir['excess_kurtosis']:.1f}")


def main() -> None:
    r = run()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "kelly.json").write_text(
        json.dumps(r, ensure_ascii=False, indent=2, default=float), encoding="utf-8")

    print("=" * 78)
    print("  胜率 / 盈亏比 / Kelly / 年化口径")
    print("=" * 78)
    print("  Kelly 在本情境下失效，输出仅作「下注规模上限的参照」：")
    print("    · Breiman(1961) 的最优性是渐近结论；Thorp 指出区分 1.0% 与 1.1% 优势")
    print("      需两百万次试验才有 84% 把握。单人创业一生下注个位数次。")
    print("    · Samuelson 1971/1979 正式反对把 E[ln] 当普适最优准则。")
    print("    · Kelly 假设赌注可分割、可重复、赔率已知；创业三条全不满足。")

    _print_block(r["full_accounting"])
    _print_block(r["cash_only"])

    print("\n" + "=" * 78)
    fa_k = r["full_accounting"]["kelly"]["f_star"]
    co_k = r["cash_only"]["kelly"]["f_star"]
    print("  两种口径的结论对比")
    print("=" * 78)
    fa_amt = r["full_accounting"]["kelly_implied_wager_usd"]
    print(f"  全口径（时间 $30/h）: f* = {fa_k:.4f} → "
          f"{'不下注（期望优势为负）' if fa_k < 1e-6 else f'隐含下注 ${fa_amt:,.0f}'}")
    print(f"  现金口径（时间 $0） : f* = {co_k:.4f} → "
          f"隐含下注 ${r['cash_only']['kelly_implied_wager_usd']:,.0f}")
    print("\n  **这个分歧本身就是本项目最重要的结论：**")
    print("  是否值得做，几乎完全取决于「你这 20 小时/周的真实机会成本是多少」。")

    ind = r["indifference_hourly_rate"]
    if ind.get("exists"):
        print(f"\n  无差异时薪 = ${ind['indifference_hourly_usd']:.1f}/小时"
              f"（≈ ${ind['annual_equivalent_usd']:,.0f}/年，按 1,000 小时/年）")
        print(_wrap(ind["verdict"], width=36, indent="    "))
    else:
        print(f"\n  无差异点不存在：{ind['reason']}")

    print("\n  **这个判断只能由委托方本人作出，模型不越俎代庖。**"
          "\n  模型能做的只是把问题问准：不是「这个项目好不好」，"
          "\n  而是「我的 1,000 小时/年，在别处的真实变现能力是多少」。")
    print(f"\n输出已写入 {OUT_DIR / 'kelly.json'}")


if __name__ == "__main__":
    main()
