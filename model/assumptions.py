"""唯一的假设来源。

纪律（对应工作原则第十三条 数据可证）：
  1. 本项目的任何其他文件**不得硬编码数字**，一律从这里 import。
  2. 每个常量必须带 Assumption 元数据：数值、单位、证据等级、出处 URL 或"推测"标记。
  3. 等级为 C 的数据**不得**被任何模型引用；本文件在导入时会强制校验这一点。
  4. 派生量必须写成函数，不得写成常量，以便追溯计算过程。

复现：python model/assumptions.py  （打印全部假设与自检结果）
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

OUT_DIR = Path(__file__).resolve().parent.parent / "outputs"
BASE_DATE = "2026-07-27"

# 证据等级：A 一手权威 / B 有样本量但有偏 / C 内容农场（禁用） / D 无数据需推算 /
#           SELF 本人主观设定（须做敏感性分析）
GRADES = {"A", "B", "C", "D", "SELF"}


@dataclass(frozen=True)
class Assumption:
    value: Any
    unit: str
    grade: str
    note: str
    source: str

    def __post_init__(self) -> None:
        assert self.grade in GRADES, f"未知证据等级 {self.grade}"
        assert self.grade != "C", (
            f"C 级（内容农场）数据禁止进入模型：{self.note}"
        )
        assert self.source, "每个假设必须有出处或明确标记为推测"


A: dict[str, Assumption] = {}


def add(key: str, value, unit: str, grade: str, note: str, source: str):
    A[key] = Assumption(value, unit, grade, note, source)
    return value


# ==========================================================================
# 一、硬约束（来自委托方给定条件，非估计值）
# ==========================================================================
HOURS_PER_WEEK = add(
    "HOURS_PER_WEEK", 20, "小时/周", "SELF",
    "委托方给定的可投入时间上限", "委托方给定条件")

WEEKS_PER_YEAR = add(
    "WEEKS_PER_YEAR", 50, "周/年", "SELF",
    "扣除约 2 周完全无产出的时间（春节、病假等）", "推测")

HOURS_PER_YEAR = add(
    "HOURS_PER_YEAR", 20 * 50, "小时/年", "SELF",
    "= HOURS_PER_WEEK × WEEKS_PER_YEAR = 1,000 小时", "派生")

CASH_CAP_USD = add(
    "CASH_CAP_USD", 4000.0, "美元", "SELF",
    "现金投入上限，占可投资净资产 <5%，破产可承受且不可追加", "委托方给定条件")

INVESTABLE_NET_ASSETS_USD = add(
    "INVESTABLE_NET_ASSETS_USD", 80000.0, "美元", "SELF",
    "由「$4,000 占可投资净资产 <5%」反推的下限；Kelly 的 bankroll 口径。"
    "真实值只有委托方知道，此处取满足约束的最小值，属保守处理", "推测（由给定条件反推）")

ENTITY_SETUP_RESERVE_USD = add(
    "ENTITY_SETUP_RESERVE_USD", 500.0, "美元", "SELF",
    "Gate 0-A 回退时的主体设立预留（个体工商户 ~$0 / 香港公司 ~$1,500 / 美国 LLC ~$500）。"
    "取美国 LLC 档，因其为最可能被采用的回退路径", "docs/GATE0.md §1.4")

HOURLY_OPPORTUNITY_COST_USD = add(
    "HOURLY_OPPORTUNITY_COST_USD", 30.0, "美元/小时", "SELF",
    "个人时间的机会成本。**这是本模型中最重要也最主观的一个数**："
    "按此计价，一年 1,000 小时 = $30,000，是现金投入 $4,000 的 7.5 倍。"
    "**真正的赌注是时间而非金钱**，必须做敏感性分析", "推测（须由委托方替换为真实值）")


# ==========================================================================
# 二、漏斗（ChartMogul 2026，200 个 B2B 软件产品，自报告问卷）
# ==========================================================================
_S_CM = "https://chartmogul.com/reports/saas-conversion-report/"

CM_OPTIN_VISITOR_TO_SIGNUP = add(
    "CM_OPTIN_VISITOR_TO_SIGNUP", 0.045, "比例", "A",
    "free trial（不要信用卡）访客→注册；ChartMogul 原文 45 注册/千访客", _S_CM)

CM_OPTIN_SIGNUP_TO_PAID = add(
    "CM_OPTIN_SIGNUP_TO_PAID", 0.089, "比例", "A",
    "free trial（不要信用卡）注册→付费（6 个月内）；原文 3.6 付费/千访客 ÷ 45 注册", _S_CM)

CM_CARD_VISITOR_TO_SIGNUP = add(
    "CM_CARD_VISITOR_TO_SIGNUP", 0.035, "比例", "A",
    "free trial（**要**信用卡）访客→注册；注册量比不要卡低约 22%", _S_CM)

CM_CARD_SIGNUP_TO_PAID = add(
    "CM_CARD_SIGNUP_TO_PAID", 0.314, "比例", "A",
    "free trial（**要**信用卡）注册→付费；原文 10.5 付费/千访客 ÷ 35 注册", _S_CM)

SOLO_NO_TOUCH_DISCOUNT = add(
    "SOLO_NO_TOUCH_DISCOUNT", 3.0 / 8.9, "倍数", "D",
    "单人零人工触点的折扣系数 ≈ 0.337。推导：BENCHMARKS.md 建议把 ChartMogul 的 8.9% "
    "下调至 3.0% 建模，理由是该样本典型受访者已在 $1M–$10M ARR 且有市场团队，"
    "而 ChartMogul 同时指出 80% 的 free trial 产品仍保留人工触点，本项目按定义不保留。"
    "**这是本模型中偏差最大且无法量化验证的一个系数**",
    "research/BENCHMARKS.md §1.1 与 §9.1②（类比推算，非测量值）")


# ==========================================================================
# 三、流失（ChartMogul SaaS Retention Report，2,100+ 家真实计费数据）
# ==========================================================================
MONTHLY_LOGO_CHURN = add(
    "MONTHLY_LOGO_CHURN", 0.07, "比例/月", "B",
    "客单价 $10–50/月自助订阅的月度客户流失。取 Baremetrics 分档表 $25–50 档的 7.3% "
    "与 <$10 档的 6.2% 之间。单人无任何人工挽留动作，不宜取更低值",
    "https://chartmogul.com/reports/saas-retention-report/ 与 "
    "https://www.vitally.io/post/saas-churn-benchmarks（Baremetrics 二手转述，故降为 B）")

NRR_ABOVE_100_PROBABILITY = add(
    "NRR_ABOVE_100_PROBABILITY", 0.027, "比例", "A",
    "ARPA <$10/月的公司中净收入留存 >100% 的比例仅 2.7%。"
    "**据此模型中一律不假设扩张收入**", "https://chartmogul.com/reports/saas-retention-report/")


# ==========================================================================
# 四、定价与收款
# ==========================================================================
ARPU_USD = add(
    "ARPU_USD", 19.0, "美元/月", "SELF",
    "客单价。下限由 MoR 费率结构决定：$9 档 MoR 有效费率高达 12.1–12.6%，"
    "$19 档降至 7.6–9.6%。上限由竞品价格带（$12–$30）与 Copilot $10 天花板约束",
    "research/BENCHMARKS.md §8.1（费率为 A 级，定价选择为本人判断）")

MOR_RATE_PCT = add(
    "MOR_RATE_PCT", 0.05, "比例", "A",
    "Paddle 基础费率 5%（全包，含国际卡、换汇、订阅附加与全球税务代缴）",
    "https://www.paddle.com/pricing")

MOR_FEE_FIXED_USD = add(
    "MOR_FEE_FIXED_USD", 0.50, "美元/笔", "A",
    "Paddle 每笔固定费", "https://www.paddle.com/pricing")

MOR_FX_MARGIN_PCT = add(
    "MOR_FX_MARGIN_PCT", 0.015, "比例", "A",
    "Paddle 在打款币种与余额币种不同时收取的汇兑价差，最高 1.5%。"
    "选择 CNY 打款到境内银行时适用",
    "https://www.paddle.com/help/manage/get-paid/can-i-be-paid-in-my-local-currency")

MOR_PAYOUT_THRESHOLD_USD = add(
    "MOR_PAYOUT_THRESHOLD_USD", 100.0, "美元", "A",
    "Paddle 最低打款门槛，未达门槛顺延次月。含义：现金回笼最长延迟约 60 天",
    "https://www.paddle.com/help/manage/get-paid/when-and-how-do-i-get-paid")

REFUND_RATE = add(
    "REFUND_RATE", 0.03, "比例", "D",
    "退款与坏账率。无本赛道公开数据；按 SaaS 常见 2–5% 取中值", "推测")


# ==========================================================================
# 五、成本
# ==========================================================================
INFRA_MONTHLY_USD = add(
    "INFRA_MONTHLY_USD", 60.0, "美元/月", "A",
    "标准档：Vercel Pro $20 + Supabase Pro $25 + Cloudflare Workers $5 + 域名与杂项 $10。"
    "在每月几千次调用量级，成本完全由固定订阅费主导",
    "research/BENCHMARKS.md §7.1，各家官方定价页 2026-07-27")

INFRA_MINIMAL_MONTHLY_USD = add(
    "INFRA_MINIMAL_MONTHLY_USD", 10.0, "美元/月", "A",
    "极简档：Cloudflare Workers $5 + Neon 按量约 $4 + 域名分摊 $1",
    "research/BENCHMARKS.md §7.1")

LLM_COST_PER_OP_USD = add(
    "LLM_COST_PER_OP_USD", 0.0, "美元/次", "A",
    "**头号候选 C12 为纯 YAML/AST 规则分析，零推理成本。** "
    "此常量存在的意义是：当敏感性分析切换到含推理的候选时，用 Ellipsis 公布的"
    "生产均值 $0.12/次替换（见 LLM_COST_AGENTIC_USD）",
    "outputs/opportunity_scoring.json C12 边际成本结构 10 分")

LLM_COST_AGENTIC_USD = add(
    "LLM_COST_AGENTIC_USD", 0.12, "美元/次", "A",
    "agentic 代码审查的真实生产均值（已做分层路由+增量处理+缓存三件套后）。"
    "**更正记录：先前误用 $0.74，那是 Ellipsis 的售价（token 透传 $0.37 + 100% 平台费 $0.37），"
    "不是成本。** 未优化的朴素实现为 $0.80–2.50/次",
    "https://www.ellipsis.dev/blog/lessons-from-building-llm-agents （2026-05-01）")

LLM_COST_SINGLE_PASS_USD = add(
    "LLM_COST_SINGLE_PASS_USD", 0.0714, "美元/次", "D",
    "单次推理式审查（Claude Sonnet 5 引导价，10 文件 PR，60% 缓存命中）的自下而上推算。"
    "与 Ellipsis 生产均值 $0.12 相差 1.7 倍，属同一量级，互相印证",
    "research/BENCHMARKS.md §6.3（token 用量为推算，非测量）")

SONNET5_PRICE_HIKE_DATE = add(
    "SONNET5_PRICE_HIKE_DATE", "2026-09-01", "日期", "A",
    "Claude Sonnet 5 由 $2/$10 涨至 $3/$15（+50%）。"
    "**任何跨越 9 月的推理成本测算不得使用现价**",
    "https://platform.claude.com/docs/en/about-claude/pricing")


# ==========================================================================
# 六、时间与成功基础率
# ==========================================================================
PARTTIME_PENALTY = add(
    "PARTTIME_PENALTY", 2.2, "倍数", "B",
    "兼职惩罚系数：全职创始人的公司增速是兼职创始人的 2.2 倍（MicroConf 2024，n=469，p.45）。"
    "推论：所有里程碑耗时乘以 2.0–2.5",
    "https://microconf.com/state-of-indie-saas （PDF 未获取，引用官网带页码摘录，故为 B）")

MEDIAN_MONTHS_TO_1K_MRR_FULLTIME = add(
    "MEDIAN_MONTHS_TO_1K_MRR_FULLTIME", 15.0, "月", "D",
    "全职达到 $1,000 MRR 的中位耗时，取流传区间 12–18 个月的中值。"
    "**原始来源 RockingWeb 2025 为 C 级（无公开数据集与抽样框），故此处降级为 D 级类比推算，"
    "仅用于粗略排期，不得作为概率输入**", "类比推算（原始 C 级来源已隔离）")

PROJECT_ALIVE_12M = add(
    "PROJECT_ALIVE_12M", 0.90, "比例", "B",
    "项目 12 个月后仍在线运行的比例。Show HN 10,000 条提交的年均死亡率约 9%。"
    "**局限：HTTP 200 只证明域名还在，不证明还有收入**",
    "https://antontarasenko.github.io/show-hn/")

PMF_FAILURE_SHARE = add(
    "PMF_FAILURE_SHARE", 0.43, "比例", "A",
    "产品-市场不匹配在失败原因中占 43%（CB Insights，n=431）。"
    "对纯自有资金项目，第一大终局原因「资金耗尽 70%」基本不适用，"
    "真实风险几乎全部集中在 PMF 与时间机会成本上",
    "https://www.cbinsights.com/research/report/startup-failure-reasons-top/")


# ==========================================================================
# 七、获客（本项目的主要矛盾，也是数据最弱的一节）
# ==========================================================================
SEO_TOP10_PROBABILITY_12M = add(
    "SEO_TOP10_PROBABILITY_12M", 0.0174, "比例", "A",
    "新页面 12 个月内进入 Google 前十的概率（100 万随机 URL 追踪）。"
    "英文非空内容筛选后为 6.11%；高搜索量词仅 0.3%。"
    "**据此第一年的 SEO 流量一律按 0 计**",
    "https://ahrefs.com/blog/how-long-does-it-take-to-rank-in-google-and-how-old-are-top-ranking-pages/")

HN_FRONTPAGE_UV = add(
    "HN_FRONTPAGE_UV", 15000, "独立访客/次", "B",
    "一次 Hacker News 头版的 24 小时流量，取 10,000–30,000 区间下沿。"
    "**48 小时内衰减到零，是脉冲不是渠道**", "research/BENCHMARKS.md §3.1")

PRODUCT_HUNT_SIGNUPS = add(
    "PRODUCT_HUNT_SIGNUPS", 125, "注册/次", "D",
    "一次 Product Hunt 发布的 7 日注册量，取 100–150 中值。"
    "**原始来源样本极小（C 级），此处降级为 D 级类比推算**", "类比推算")

MARKETPLACE_INSTALL_TO_PAID = add(
    "MARKETPLACE_INSTALL_TO_PAID", None, "比例", "D",
    "GitHub / VS Code Marketplace 安装→付费转化：**无任何公开可靠数据**。"
    "模型中不使用该路径，或用漏斗基准值替代并明示为类比", "无公开数据")


# ==========================================================================
# 八、金融参数
# ==========================================================================
RF_US_10Y = add(
    "RF_US_10Y", 0.0471, "年化", "A",
    "美国 10 年期国债收益率", "FRED DGS10，2026-07-23")

RF_CN_10Y = add(
    "RF_CN_10Y", 0.0173, "年化", "A",
    "中国 10 年期国债收益率", "中债国债收益率曲线，2026-07-24")

HORIZON_YEARS = add(
    "HORIZON_YEARS", 3.0, "年", "SELF",
    "评估期。选 3 年的理由：与 Show HN 存活曲线（约 6 年后死比活更可能）和"
    "兼职惩罚下达到 $1K MRR 需 24–30 个月这两条相容", "推测")

ANGEL_IRR_BENCHMARK = add(
    "ANGEL_IRR_BENCHMARK", 0.314, "年化 IRR", "A",
    "Wiltbank & Boeker (2007) 天使投资 2.6 倍 / 3.5 年。"
    "**订正记录：原报告写作约 27% 系计算错误，正确值为 2.6^(1/3.5)−1 = 31.4%**",
    "research/RISK_METHODOLOGY.md（含 Right Side Capital 的订正说明）")


# ==========================================================================
# 九、派生函数（不写成常量，以便追溯计算过程）
# ==========================================================================

def funnel_rates(require_card: bool, apply_solo_discount: bool = True
                 ) -> tuple[float, float]:
    """返回 (访客→注册, 注册→付费)。

    require_card 是本模型中对早期收入影响最大的单一杠杆
    （ChartMogul：要卡 10.5 付费/千访客 vs 不要卡 4.0）。
    """
    if require_card:
        v2s, s2p = CM_CARD_VISITOR_TO_SIGNUP, CM_CARD_SIGNUP_TO_PAID
    else:
        v2s, s2p = CM_OPTIN_VISITOR_TO_SIGNUP, CM_OPTIN_SIGNUP_TO_PAID
    if apply_solo_discount:
        s2p *= SOLO_NO_TOUCH_DISCOUNT
    return v2s, s2p


def paid_per_1000_visitors(require_card: bool, apply_solo_discount: bool = True) -> float:
    v2s, s2p = funnel_rates(require_card, apply_solo_discount)
    return 1000.0 * v2s * s2p


def mor_effective_rate(price_usd: float = ARPU_USD, include_fx: bool = True) -> float:
    """MoR 有效费率 = (比例费 + 固定费 [+ 汇兑价差]) / 价格。"""
    fee = price_usd * MOR_RATE_PCT + MOR_FEE_FIXED_USD
    if include_fx:
        fee += price_usd * MOR_FX_MARGIN_PCT
    return fee / price_usd


def net_revenue_per_customer_month(price_usd: float = ARPU_USD) -> float:
    """扣除 MoR 费率与退款后的净收入。"""
    gross = price_usd * (1 - REFUND_RATE)
    return gross * (1 - mor_effective_rate(price_usd))


def customer_lifetime_months() -> float:
    return 1.0 / MONTHLY_LOGO_CHURN


def ltv_usd(price_usd: float = ARPU_USD) -> float:
    return net_revenue_per_customer_month(price_usd) * customer_lifetime_months()


def steady_state_customers(monthly_visitors: float, require_card: bool = False) -> float:
    """稳态客户数 = 月新增 / 月流失率。"""
    new_per_month = monthly_visitors / 1000.0 * paid_per_1000_visitors(require_card)
    return new_per_month / MONTHLY_LOGO_CHURN


def visitors_needed_for_mrr(target_mrr_usd: float, require_card: bool = False) -> float:
    """维持给定 MRR 所需的每月精准访客数（本 BP 最重要的一个派生量）。"""
    customers = target_mrr_usd / ARPU_USD
    churned_per_month = customers * MONTHLY_LOGO_CHURN
    return churned_per_month / paid_per_1000_visitors(require_card) * 1000.0


def total_capital_at_risk_usd(years: float = HORIZON_YEARS) -> dict[str, float]:
    """真正的赌注：现金 + 时间的机会成本。

    **这是本 BP 一个关键的诚实点**：$4,000 的现金上限容易让人低估风险，
    而按 $30/小时计价，3 年 3,000 小时的机会成本是 $90,000，是现金的 22.5 倍。
    """
    cash = CASH_CAP_USD + ENTITY_SETUP_RESERVE_USD
    hours = HOURS_PER_YEAR * years
    time_cost = hours * HOURLY_OPPORTUNITY_COST_USD
    return {
        "cash_usd": cash,
        "hours": hours,
        "time_opportunity_cost_usd": time_cost,
        "total_usd": cash + time_cost,
        "time_share": time_cost / (cash + time_cost),
    }


# ==========================================================================
# 十、自检
# ==========================================================================

def self_check() -> list[str]:
    issues = []
    for k, a in A.items():
        if a.grade == "C":
            issues.append(f"{k}: C 级数据不得入模")
        if a.grade in {"SELF", "D"} and "推测" not in a.source and "类比" not in a.source \
                and "无公开数据" not in a.source and "派生" not in a.source \
                and "给定条件" not in a.source and "docs/" not in a.source \
                and "outputs/" not in a.source and "research/" not in a.source:
            issues.append(f"{k}: 等级为 {a.grade} 但出处未标记为推测/类比/派生")
    # 与 BENCHMARKS.md 的关键派生量对账
    p = paid_per_1000_visitors(require_card=False)
    if abs(p - 1.35) > 0.02:
        issues.append(f"漏斗对账失败：不要卡片应为 1.35 付费/千访客，实得 {p:.3f}")
    v = visitors_needed_for_mrr(1000.0)
    if abs(v - 2729) > 30:
        issues.append(f"访客需求对账失败：应为约 2,729/月，实得 {v:.0f}")
    return issues


def export() -> dict:
    return {
        "base_date": BASE_DATE,
        "assumptions": {k: asdict(a) for k, a in A.items()},
        "grade_counts": {g: sum(1 for a in A.values() if a.grade == g) for g in sorted(GRADES)},
        "derived": {
            "paid_per_1000_no_card": round(paid_per_1000_visitors(False), 4),
            "paid_per_1000_with_card": round(paid_per_1000_visitors(True), 4),
            "paid_per_1000_no_card_undiscounted": round(paid_per_1000_visitors(False, False), 4),
            "paid_per_1000_with_card_undiscounted": round(paid_per_1000_visitors(True, False), 4),
            "mor_effective_rate_at_arpu": round(mor_effective_rate(), 4),
            "net_revenue_per_customer_month": round(net_revenue_per_customer_month(), 4),
            "customer_lifetime_months": round(customer_lifetime_months(), 2),
            "ltv_usd": round(ltv_usd(), 2),
            "visitors_needed_for_1000_mrr_no_card": round(visitors_needed_for_mrr(1000.0), 0),
            "visitors_needed_for_1000_mrr_with_card": round(visitors_needed_for_mrr(1000.0, True), 0),
            "capital_at_risk": {k: round(v, 4) for k, v in total_capital_at_risk_usd().items()},
        },
        "self_check": self_check(),
    }


def main() -> None:
    data = export()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "assumptions.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=" * 78)
    print(f"假设清单  基准日 {BASE_DATE}  共 {len(A)} 项")
    print("=" * 78)
    print("证据等级分布：", ", ".join(f"{g}={n}" for g, n in data["grade_counts"].items() if n))
    print()
    for k, a in A.items():
        v = a.value
        vs = "无数据" if v is None else (f"{v:,.4f}".rstrip("0").rstrip(".") if isinstance(v, float) else str(v))
        print(f"  [{a.grade:<4}] {k:<38} = {vs:>12} {a.unit}")

    d = data["derived"]
    print("\n" + "-" * 78)
    print("派生量")
    print("-" * 78)
    print(f"  每千访客付费客户  不要卡（本模型基准）: {d['paid_per_1000_no_card']:.2f}")
    print(f"                    不要卡（ChartMogul 原值）: {d['paid_per_1000_no_card_undiscounted']:.2f}")
    print(f"                    **要卡**（本模型基准）  : {d['paid_per_1000_with_card']:.2f}")
    print(f"                    **要卡**（ChartMogul 原值）: {d['paid_per_1000_with_card_undiscounted']:.2f}")
    print(f"  MoR 有效费率 @ ${ARPU_USD:.0f}          : {d['mor_effective_rate_at_arpu']:.2%}")
    print(f"  每客户每月净收入                : ${d['net_revenue_per_customer_month']:.2f}")
    print(f"  客户平均生命周期                : {d['customer_lifetime_months']:.1f} 个月")
    print(f"  LTV                             : ${d['ltv_usd']:.2f}")
    print(f"  维持 $1,000 MRR 所需月访客  不要卡: {d['visitors_needed_for_1000_mrr_no_card']:,.0f}")
    print(f"                              要卡  : {d['visitors_needed_for_1000_mrr_with_card']:,.0f}")

    c = d["capital_at_risk"]
    print("\n  真正的赌注（3 年）：")
    print(f"    现金            : ${c['cash_usd']:,.0f}")
    print(f"    工时            : {c['hours']:,.0f} 小时")
    print(f"    时间机会成本    : ${c['time_opportunity_cost_usd']:,.0f}")
    print(f"    合计            : ${c['total_usd']:,.0f}  （时间占 {c['time_share']:.1%}）")

    issues = data["self_check"]
    print("\n" + "-" * 78)
    print("自检：" + ("全部通过" if not issues else f"发现 {len(issues)} 个问题"))
    for i in issues:
        print("  ✗ " + i)
    print(f"\n输出已写入 {OUT_DIR / 'assumptions.json'}")


if __name__ == "__main__":
    main()
