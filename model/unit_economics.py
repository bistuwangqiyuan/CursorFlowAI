"""单位经济学：LTV、贡献毛利、盈亏平衡、以及用工时计价的真实 CAC。

本模块的核心主张（也是本 BP 与常见 SaaS 计划书最大的不同）：
  **对一个零广告预算、单人运营的项目，用美元计的 CAC 接近 0，这个数字毫无意义。
    真正的 CAC 是工时。必须用工时计价，否则单位经济学是自欺。**

所有输入来自 assumptions.py。
复现：python model/unit_economics.py
"""

from __future__ import annotations

import json
from pathlib import Path

try:
    from . import assumptions as A
except ImportError:
    import assumptions as A  # type: ignore

OUT_DIR = Path(__file__).resolve().parent.parent / "outputs"


# --------------------------------------------------------------------------
# 一、每客户经济学
# --------------------------------------------------------------------------

def per_customer(price: float = A.ARPU_USD, llm_cost_per_op: float | None = None,
                 ops_per_month: float = 20.0) -> dict:
    """单客户月度损益。

    llm_cost_per_op 默认取 assumptions 中头号候选 C12 的值（0，纯规则分析）。
    传入 A.LLM_COST_AGENTIC_USD 可切换到 agentic 产品形态做对照。
    """
    if llm_cost_per_op is None:
        llm_cost_per_op = A.LLM_COST_PER_OP_USD

    gross = price
    refund_loss = gross * A.REFUND_RATE
    billable = gross - refund_loss
    mor_fee = billable * A.mor_effective_rate(price)
    cogs_llm = llm_cost_per_op * ops_per_month
    contribution = billable - mor_fee - cogs_llm

    life = A.customer_lifetime_months()
    return {
        "price_usd": price,
        "ops_per_month": ops_per_month,
        "llm_cost_per_op": llm_cost_per_op,
        "gross_revenue": round(gross, 4),
        "refund_loss": round(refund_loss, 4),
        "mor_fee": round(mor_fee, 4),
        "mor_effective_rate": round(A.mor_effective_rate(price), 4),
        "cogs_llm": round(cogs_llm, 4),
        "contribution_margin_usd": round(contribution, 4),
        "contribution_margin_pct": round(contribution / gross, 4),
        "lifetime_months": round(life, 2),
        "ltv_usd": round(contribution * life, 2),
    }


def price_ladder(prices=(9, 19, 29, 49, 99)) -> list[dict]:
    """客单价阶梯：说明为什么 $9 档在结构上不可行。"""
    rows = []
    for p in prices:
        pc = per_customer(price=float(p))
        rows.append({
            "price": p,
            "mor_effective_rate": pc["mor_effective_rate"],
            "contribution_usd": pc["contribution_margin_usd"],
            "contribution_pct": pc["contribution_margin_pct"],
            "ltv_usd": pc["ltv_usd"],
            "customers_to_cover_infra": round(A.INFRA_MONTHLY_USD / pc["contribution_margin_usd"], 2),
        })
    return rows


def product_form_comparison() -> list[dict]:
    """三种产品形态的边际成本对照，用于说明 C12「零推理」优势的量级。

    数据更正记录：先前误把 Ellipsis 的售价 $0.74 当作成本，导致得出
    「低价席位制结构上无毛利」的错误结论。见 research/sources.md §4.1。
    """
    forms = [
        ("C12 纯规则分析（零推理）", A.LLM_COST_PER_OP_USD),
        ("单次推理式审查（Sonnet 5 推算）", A.LLM_COST_SINGLE_PASS_USD),
        ("agentic 审查（Ellipsis 生产均值）", A.LLM_COST_AGENTIC_USD),
        ("agentic 未优化（朴素全上下文实现）", 1.65),  # Ellipsis 博客区间 $0.80–2.50 的中值
    ]
    out = []
    for name, cost in forms:
        pc = per_customer(llm_cost_per_op=cost)
        out.append({
            "form": name,
            "llm_cost_per_op": cost,
            "monthly_cogs_at_20_ops": round(cost * 20, 4),
            "contribution_pct": pc["contribution_margin_pct"],
            "ltv_usd": pc["ltv_usd"],
        })
    return out


# --------------------------------------------------------------------------
# 二、真正的 CAC：用工时计价
# --------------------------------------------------------------------------

def time_based_cac(hours_on_acquisition_per_month: float,
                   customers_acquired_per_month: float) -> dict:
    """把获客工时折算成成本，得到有意义的 CAC 与回收期。

    为什么必须这么做：本项目零广告预算，美元 CAC ≈ $0，
    LTV/CAC 会趋于无穷大 —— 这个数字看似完美，实则毫无信息量，
    还会掩盖「时间才是真正稀缺资源」这一事实。
    """
    if customers_acquired_per_month <= 0:
        return {"error": "月新增客户为 0，CAC 无定义"}
    hours_per_customer = hours_on_acquisition_per_month / customers_acquired_per_month
    cac_usd = hours_per_customer * A.HOURLY_OPPORTUNITY_COST_USD
    contribution = per_customer()["contribution_margin_usd"]
    ltv = per_customer()["ltv_usd"]
    return {
        "hours_on_acquisition_per_month": hours_on_acquisition_per_month,
        "customers_acquired_per_month": round(customers_acquired_per_month, 3),
        "hours_per_customer": round(hours_per_customer, 2),
        "cac_usd_time_priced": round(cac_usd, 2),
        "contribution_per_month": round(contribution, 2),
        "payback_months": round(cac_usd / contribution, 1) if contribution > 0 else None,
        "ltv_usd": ltv,
        "ltv_over_cac": round(ltv / cac_usd, 2) if cac_usd > 0 else None,
        "healthy": bool(cac_usd > 0 and ltv / cac_usd >= 3.0),
    }


# --------------------------------------------------------------------------
# 三、盈亏平衡（现金与工时双轨）
# --------------------------------------------------------------------------

def breakeven() -> dict:
    pc = per_customer()
    contrib = pc["contribution_margin_usd"]

    cash_be_customers = A.INFRA_MONTHLY_USD / contrib
    cash_be_mrr = cash_be_customers * A.ARPU_USD

    monthly_hours = A.HOURS_PER_WEEK * 52 / 12
    monthly_time_cost = monthly_hours * A.HOURLY_OPPORTUNITY_COST_USD
    full_be_customers = (A.INFRA_MONTHLY_USD + monthly_time_cost) / contrib
    full_be_mrr = full_be_customers * A.ARPU_USD

    return {
        "contribution_per_customer_month": round(contrib, 2),
        "cash_breakeven": {
            "description": "只覆盖基础设施现金支出（$60/月）——这是最低、也是最容易误导人的口径",
            "customers": round(cash_be_customers, 2),
            "mrr_usd": round(cash_be_mrr, 2),
            "monthly_visitors_needed": round(A.visitors_needed_for_mrr(cash_be_mrr), 0),
        },
        "full_breakeven": {
            "description": f"同时覆盖基础设施与时间机会成本"
                           f"（{monthly_hours:.0f} 小时/月 × ${A.HOURLY_OPPORTUNITY_COST_USD:.0f}/小时"
                           f" = ${monthly_time_cost:,.0f}/月）——**这才是真实的盈亏平衡**",
            "monthly_hours": round(monthly_hours, 1),
            "monthly_time_cost_usd": round(monthly_time_cost, 2),
            "customers": round(full_be_customers, 2),
            "mrr_usd": round(full_be_mrr, 2),
            "monthly_visitors_needed": round(A.visitors_needed_for_mrr(full_be_mrr), 0),
            "monthly_visitors_needed_with_card": round(
                A.visitors_needed_for_mrr(full_be_mrr, True), 0),
        },
        "ratio": round(full_be_customers / cash_be_customers, 1),
    }


# --------------------------------------------------------------------------

def run() -> dict:
    be = breakeven()
    # 获客工时情景：每月把 20 小时中的 8 小时投入获客
    acq_scenarios = []
    for hours in (4, 8, 12):
        for visitors in (500, 1000, 2000, 2729):
            new_paid = visitors / 1000 * A.paid_per_1000_visitors(False)
            acq_scenarios.append({
                "acquisition_hours_per_month": hours,
                "monthly_visitors": visitors,
                **time_based_cac(hours, new_paid),
            })
    return {
        "per_customer_base": per_customer(),
        "price_ladder": price_ladder(),
        "product_form_comparison": product_form_comparison(),
        "breakeven": be,
        "time_based_cac_scenarios": acq_scenarios,
    }


def main() -> None:
    r = run()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "unit_economics.json").write_text(
        json.dumps(r, ensure_ascii=False, indent=2, default=float), encoding="utf-8")

    pc = r["per_customer_base"]
    print("=" * 78)
    print("单位经济学")
    print("=" * 78)
    print(f"\n【单客户月度损益 @ ${pc['price_usd']:.0f}/月】")
    print(f"  毛收入                    ${pc['gross_revenue']:>8.2f}")
    print(f"  − 退款与坏账 ({A.REFUND_RATE:.0%})       ${pc['refund_loss']:>8.2f}")
    print(f"  − MoR 费用 ({pc['mor_effective_rate']:.2%})     ${pc['mor_fee']:>8.2f}")
    print(f"  − LLM 推理成本            ${pc['cogs_llm']:>8.2f}   （C12 为纯规则分析，零推理）")
    print(f"  = 贡献毛利                ${pc['contribution_margin_usd']:>8.2f}"
          f"   （毛利率 {pc['contribution_margin_pct']:.1%}）")
    print(f"  × 平均生命周期 {pc['lifetime_months']:.1f} 个月")
    print(f"  = LTV                     ${pc['ltv_usd']:>8.2f}")

    print("\n【客单价阶梯：为什么 $9 档不可行】")
    print(f"  {'价格':>6}{'MoR有效费率':>13}{'贡献毛利':>10}{'毛利率':>9}{'LTV':>10}{'覆盖基建所需客户':>18}")
    for row in r["price_ladder"]:
        print(f"  ${row['price']:>5}{row['mor_effective_rate']:>13.2%}"
              f"{row['contribution_usd']:>10.2f}{row['contribution_pct']:>9.1%}"
              f"{row['ltv_usd']:>10.2f}{row['customers_to_cover_infra']:>18.1f}")

    print("\n【产品形态对照：边际成本的量级差异】")
    print(f"  {'形态':<36}{'$/次':>8}{'月COGS':>9}{'毛利率':>9}{'LTV':>10}")
    for f in r["product_form_comparison"]:
        print(f"  {f['form']:<36}{f['llm_cost_per_op']:>8.4f}"
              f"{f['monthly_cogs_at_20_ops']:>9.2f}{f['contribution_pct']:>9.1%}{f['ltv_usd']:>10.2f}")
    print("  注：末行「未优化朴素实现」在 $19 客单价下毛利为负——这正是必须做"
          "分层路由/增量/缓存三件套的原因。")

    be = r["breakeven"]
    print("\n【盈亏平衡：现金与工时双轨】")
    for key in ("cash_breakeven", "full_breakeven"):
        d = be[key]
        print(f"  · {d['description']}")
        print(f"      需要 {d['customers']:.1f} 个客户 = ${d['mrr_usd']:,.0f} MRR"
              f" = 每月 {d['monthly_visitors_needed']:,.0f} 个访客")
    print(f"  → 真实盈亏平衡门槛是现金口径的 {be['ratio']:.0f} 倍。"
          f"\n    **任何只报「$60/月就能打平」的说法都是在隐藏时间成本。**")

    print("\n【用工时计价的真实 CAC】")
    print(f"  {'获客工时/月':>12}{'月访客':>9}{'月新增客户':>11}{'小时/客户':>10}"
          f"{'CAC($)':>9}{'回收期(月)':>11}{'LTV/CAC':>9}{'健康':>6}")
    for s in r["time_based_cac_scenarios"]:
        if "error" in s:
            continue
        print(f"  {s['acquisition_hours_per_month']:>12}{s['monthly_visitors']:>9,}"
              f"{s['customers_acquired_per_month']:>11.2f}{s['hours_per_customer']:>10.1f}"
              f"{s['cac_usd_time_priced']:>9,.0f}{str(s['payback_months']):>11}"
              f"{s['ltv_over_cac']:>9.2f}{'是' if s['healthy'] else '否':>6}")
    print("  判定线：LTV/CAC ≥ 3 视为健康。")
    print(f"\n输出已写入 {OUT_DIR / 'unit_economics.json'}")


if __name__ == "__main__":
    main()
