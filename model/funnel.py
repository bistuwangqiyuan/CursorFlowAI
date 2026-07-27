"""自下而上的漏斗模型：流量 → 注册 → 付费 → 留存 → 稳态 MRR。

本模块回答三个问题：
  1. 给定每月访客数，稳态能到多少 MRR？
  2. 要达到目标 MRR，每月需要多少访客？（本 BP 的主要矛盾）
  3. 「试用是否要求信用卡」这个开关值多少钱？（本模型中最大的单一杠杆）

所有输入来自 assumptions.py，本文件不硬编码任何业务数字。
复现：python model/funnel.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

try:
    from . import assumptions as A
except ImportError:  # 允许直接运行
    import assumptions as A  # type: ignore

OUT_DIR = Path(__file__).resolve().parent.parent / "outputs"


# --------------------------------------------------------------------------
# 一、稳态解析解
# --------------------------------------------------------------------------

def steady_state(monthly_visitors: float, require_card: bool = False) -> dict:
    """稳态 = 月新增客户 / 月流失率。

    推导：设稳态客户数 N，则每月流失 N·c，每月新增 g。稳态时 g = N·c，故 N = g/c。
    """
    v2s, s2p = A.funnel_rates(require_card)
    signups = monthly_visitors * v2s
    new_paid = signups * s2p
    n = new_paid / A.MONTHLY_LOGO_CHURN
    net_pm = A.net_revenue_per_customer_month()
    return {
        "monthly_visitors": monthly_visitors,
        "require_card": require_card,
        "visitor_to_signup": v2s,
        "signup_to_paid": s2p,
        "monthly_signups": signups,
        "monthly_new_paid": new_paid,
        "steady_state_customers": n,
        "steady_state_mrr_gross": n * A.ARPU_USD,
        "steady_state_mrr_net": n * net_pm,
        "steady_state_profit_net": n * net_pm - A.INFRA_MONTHLY_USD,
    }


def visitors_for_target(target_mrr: float, require_card: bool = False) -> float:
    return A.visitors_needed_for_mrr(target_mrr, require_card)


# --------------------------------------------------------------------------
# 二、月度队列仿真（稳态解不足以描述前 24 个月的爬坡）
# --------------------------------------------------------------------------

def simulate(traffic_by_month: np.ndarray, require_card: bool = False) -> dict:
    """逐月推进：客户数 N[t] = N[t-1]·(1−churn) + 新增。

    稳态解假设流量恒定且时间无穷；真实的前两年是爬坡期，
    现金流与工时消耗都发生在爬坡期，因此必须单独仿真。
    """
    v2s, s2p = A.funnel_rates(require_card)
    net_pm = A.net_revenue_per_customer_month()
    months = len(traffic_by_month)

    customers = np.zeros(months)
    new_paid = traffic_by_month * v2s * s2p
    for t in range(months):
        prev = customers[t - 1] if t else 0.0
        customers[t] = prev * (1 - A.MONTHLY_LOGO_CHURN) + new_paid[t]

    mrr_net = customers * net_pm
    profit = mrr_net - A.INFRA_MONTHLY_USD
    return {
        "months": months,
        "traffic": traffic_by_month,
        "new_paid_per_month": new_paid,
        "customers": customers,
        "mrr_net": mrr_net,
        "monthly_profit": profit,
        "cumulative_profit": np.cumsum(profit),
        "peak_cumulative_drawdown": float(np.min(np.cumsum(profit))),
        "final_customers": float(customers[-1]),
        "final_mrr_net": float(mrr_net[-1]),
        "total_net_revenue": float(np.sum(mrr_net)),
    }


def traffic_ramp(months: int, month12: float, month24: float,
                 pulses: dict[int, float] | None = None) -> np.ndarray:
    """构造一条流量轨迹。

    形态依据（全部 A 级，见 assumptions.py）：
      - 第一年 SEO 流量按 0 计（新页面 12 个月内进前十概率仅 1.74%）
      - 有机流量按线性爬坡近似，第 12 月达 month12，第 24 月达 month24
      - 脉冲（HN 头版 / Product Hunt）单月叠加，48 小时内衰减到零，不进入基线
    """
    t = np.arange(1, months + 1)
    base = np.where(t <= 12, month12 * t / 12.0,
                    month12 + (month24 - month12) * (t - 12) / 12.0)
    base = np.minimum(base, month24)
    if pulses:
        for m, uv in pulses.items():
            if 1 <= m <= months:
                base[m - 1] += uv
    return base


# --------------------------------------------------------------------------
# 三、信用卡开关的敏感性分析（本模型最大的单一杠杆）
# --------------------------------------------------------------------------

def card_switch_analysis(monthly_visitors: float = 2000.0) -> dict:
    """对照四种口径，说明这个开关到底值多少。

    诚实提示：要求信用卡会显著提高转化，但也提高了「必须先有信任」的门槛。
    对一个无名新产品，ChartMogul 样本（受访者多已有 $1M+ ARR 与市场团队）的
    要卡转化率很可能不可迁移。本分析给出上下界，不给单点结论。
    """
    rows = []
    for card in (False, True):
        for disc in (True, False):
            v2s, s2p = A.funnel_rates(card, disc)
            per_1000 = 1000 * v2s * s2p
            ss = per_1000 / 1000 * monthly_visitors / A.MONTHLY_LOGO_CHURN
            # 维持 $1,000 MRR 所需月访客：按本行自己的转化率算，不能复用默认口径
            churned = (1000.0 / A.ARPU_USD) * A.MONTHLY_LOGO_CHURN
            uv_for_1k = churned / per_1000 * 1000.0
            rows.append({
                "require_card": card,
                "solo_discount_applied": disc,
                "label": ("要信用卡" if card else "不要信用卡") +
                         ("（含单人折扣）" if disc else "（ChartMogul 原值）"),
                "visitor_to_signup": round(v2s, 5),
                "signup_to_paid": round(s2p, 5),
                "paid_per_1000_visitors": round(per_1000, 3),
                "steady_state_customers": round(ss, 2),
                "steady_state_mrr_net": round(ss * A.net_revenue_per_customer_month(), 2),
                "visitors_for_1000_mrr": round(uv_for_1k, 0),
            })
    base = next(r for r in rows if not r["require_card"] and r["solo_discount_applied"])
    card = next(r for r in rows if r["require_card"] and r["solo_discount_applied"])
    return {
        "at_monthly_visitors": monthly_visitors,
        "rows": rows,
        "lift_multiple": round(card["paid_per_1000_visitors"] / base["paid_per_1000_visitors"], 3),
        "traffic_requirement_reduction": round(
            1 - card["visitors_for_1000_mrr"] / base["visitors_for_1000_mrr"], 4),
    }


# --------------------------------------------------------------------------
# 四、龙卷风图：哪个假设最能左右结果
# --------------------------------------------------------------------------

def tornado(monthly_visitors: float = 2000.0, rel: float = 0.30) -> list[dict]:
    """对每个关键假设做 ±rel 的相对扰动，观察稳态净 MRR 的变化幅度。

    用途：告诉读者「该把有限的验证精力花在哪个数字上」。
    """
    baseline = steady_state(monthly_visitors)["steady_state_mrr_net"]

    def with_override(**kw) -> float:
        saved = {k: getattr(A, k) for k in kw}
        try:
            for k, v in kw.items():
                setattr(A, k, v)
            return steady_state(monthly_visitors)["steady_state_mrr_net"]
        finally:
            for k, v in saved.items():
                setattr(A, k, v)

    knobs = {
        "CM_OPTIN_VISITOR_TO_SIGNUP": ("访客→注册率", A.CM_OPTIN_VISITOR_TO_SIGNUP),
        "CM_OPTIN_SIGNUP_TO_PAID": ("注册→付费率", A.CM_OPTIN_SIGNUP_TO_PAID),
        "SOLO_NO_TOUCH_DISCOUNT": ("单人零触点折扣系数", A.SOLO_NO_TOUCH_DISCOUNT),
        "MONTHLY_LOGO_CHURN": ("月流失率", A.MONTHLY_LOGO_CHURN),
        "ARPU_USD": ("客单价", A.ARPU_USD),
        "REFUND_RATE": ("退款率", A.REFUND_RATE),
    }
    out = []
    for key, (cn, val) in knobs.items():
        lo = with_override(**{key: val * (1 - rel)})
        hi = with_override(**{key: val * (1 + rel)})
        out.append({
            "param": key, "param_cn": cn, "baseline_value": val,
            "low": round(lo, 2), "high": round(hi, 2),
            "swing": round(abs(hi - lo), 2),
            "swing_pct_of_baseline": round(abs(hi - lo) / baseline, 4),
        })
    out.sort(key=lambda r: -r["swing"])
    return out


# --------------------------------------------------------------------------

def run() -> dict:
    targets = [500, 1000, 2000, 5000]
    ramp = traffic_ramp(36, month12=800, month24=2500,
                        pulses={4: A.HN_FRONTPAGE_UV, 9: 3000})
    sim = simulate(ramp)
    sim_card = simulate(ramp, require_card=True)

    return {
        "steady_state_examples": [steady_state(v) for v in (500, 1000, 2000, 2729, 5000)],
        "visitors_required": [
            {"target_mrr": t,
             "visitors_no_card": round(visitors_for_target(t), 0),
             "visitors_with_card": round(visitors_for_target(t, True), 0)}
            for t in targets
        ],
        "card_switch": card_switch_analysis(),
        "tornado": tornado(),
        "ramp_simulation": {
            "description": "36 个月：有机流量第 12 月 800 UV/月、第 24 月 2,500 UV/月封顶；"
                           "第 4 月一次 HN 头版脉冲 15,000 UV，第 9 月一次 3,000 UV 的社群脉冲",
            "no_card": {
                "final_customers": round(sim["final_customers"], 2),
                "final_mrr_net": round(sim["final_mrr_net"], 2),
                "total_net_revenue_36m": round(sim["total_net_revenue"], 2),
                "cumulative_profit_36m": round(float(sim["cumulative_profit"][-1]), 2),
                "peak_cumulative_drawdown": round(sim["peak_cumulative_drawdown"], 2),
                "customers_by_year": [round(float(sim["customers"][i]), 2) for i in (11, 23, 35)],
            },
            "with_card": {
                "final_customers": round(sim_card["final_customers"], 2),
                "final_mrr_net": round(sim_card["final_mrr_net"], 2),
                "total_net_revenue_36m": round(sim_card["total_net_revenue"], 2),
                "cumulative_profit_36m": round(float(sim_card["cumulative_profit"][-1]), 2),
                "customers_by_year": [round(float(sim_card["customers"][i]), 2) for i in (11, 23, 35)],
            },
            "traffic_by_month": [round(float(x), 1) for x in ramp],
            "customers_by_month_no_card": [round(float(x), 3) for x in sim["customers"]],
            "customers_by_month_with_card": [round(float(x), 3) for x in sim_card["customers"]],
            "mrr_by_month_no_card": [round(float(x), 2) for x in sim["mrr_net"]],
            "mrr_by_month_with_card": [round(float(x), 2) for x in sim_card["mrr_net"]],
        },
    }


def main() -> None:
    r = run()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "funnel.json").write_text(json.dumps(r, ensure_ascii=False, indent=2,
                                                    default=float), encoding="utf-8")

    print("=" * 78)
    print("漏斗模型")
    print("=" * 78)
    print("\n【稳态：给定月访客能撑住多少】")
    print(f"  {'月访客':>8} {'月注册':>8} {'月新增付费':>10} {'稳态客户':>9} {'稳态净MRR':>11} {'扣基建后':>10}")
    for s in r["steady_state_examples"]:
        print(f"  {s['monthly_visitors']:>8,.0f} {s['monthly_signups']:>8.1f}"
              f" {s['monthly_new_paid']:>10.2f} {s['steady_state_customers']:>9.1f}"
              f" {s['steady_state_mrr_net']:>11,.0f} {s['steady_state_profit_net']:>10,.0f}")

    print("\n【反向：要达到目标 MRR 需要多少月访客】")
    for v in r["visitors_required"]:
        print(f"  ${v['target_mrr']:>5,} MRR  →  不要卡 {v['visitors_no_card']:>8,.0f} UV/月"
              f"   |   要卡 {v['visitors_with_card']:>8,.0f} UV/月")

    cs = r["card_switch"]
    print(f"\n【信用卡开关：本模型最大的单一杠杆】")
    print(f"  {'口径':<28}{'每千访客付费':>13}{'维持$1k MRR所需UV':>20}")
    for row in cs["rows"]:
        print(f"  {row['label']:<28}{row['paid_per_1000_visitors']:>13.2f}"
              f"{row['visitors_for_1000_mrr']:>20,.0f}")
    print(f"  → 要卡相对不要卡的付费客户提升: {cs['lift_multiple']:.2f} 倍")
    print(f"  → 所需流量下降: {cs['traffic_requirement_reduction']:.1%}")

    print("\n【龙卷风图：±30% 扰动对稳态净 MRR 的影响，按影响排序】")
    for t in r["tornado"]:
        bar = "█" * int(round(t["swing_pct_of_baseline"] * 40))
        print(f"  {t['param_cn']:<18} 摆幅 ${t['swing']:>7,.0f}"
              f" ({t['swing_pct_of_baseline']:>6.1%})  {bar}")

    rs = r["ramp_simulation"]
    print(f"\n【36 个月爬坡仿真】\n  {rs['description']}")
    for tag, key in (("不要卡", "no_card"), ("要卡  ", "with_card")):
        d = rs[key]
        print(f"  {tag}: 第12/24/36月客户数 = {d['customers_by_year']}"
              f" | 36 月末净 MRR ${d['final_mrr_net']:,.0f}"
              f" | 三年累计净收入 ${d['total_net_revenue_36m']:,.0f}")
    print(f"  不要卡情形三年累计利润（已扣基建）: ${rs['no_card']['cumulative_profit_36m']:,.0f}")
    print(f"  期间累计利润最低点（最大现金坑）  : ${rs['no_card']['peak_cumulative_drawdown']:,.0f}")
    print(f"\n输出已写入 {OUT_DIR / 'funnel.json'}")


if __name__ == "__main__":
    main()
