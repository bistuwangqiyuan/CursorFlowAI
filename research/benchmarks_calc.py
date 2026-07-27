"""
CursorFlow AI 基准数据册 —— 可复现计算脚本
Run: python benchmarks_calc.py

本脚本只做「由公开单价 + 明示假设」推导出的派生数值。
所有单价均标注来源（见 BENCHMARKS.md 对应章节），假设均可在 ASSUMPTIONS 中修改。
日期基准：2026-07-27
"""

from dataclasses import dataclass

SEP = "=" * 78


# ---------------------------------------------------------------------------
# 1. LLM 单价（USD / 1M tokens），来源见数据册第 6 节
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Model:
    name: str
    inp: float          # 每百万输入 token 价格
    out: float          # 每百万输出 token 价格
    cache_read: float   # 每百万缓存命中输入 token 价格（无则等于 inp）


MODELS = [
    # 来源：platform.claude.com/docs/en/about-claude/pricing（抓取于 2026-07-27）
    Model("Claude Opus 5",        5.00, 25.00, 0.50),
    Model("Claude Sonnet 5*",     2.00, 10.00, 0.20),   # *2026-08-31 前引导价
    Model("Claude Haiku 4.5",     1.00,  5.00, 0.10),
    # 来源：developers.openai.com/api/docs/models/gpt-5.2
    Model("GPT-5.2",              1.75, 14.00, 0.175),
    # 来源：ai.google.dev/pricing（抓取于 2026-07-27）
    Model("Gemini 3.1 Pro (<=200k)", 2.00, 12.00, 0.20),
    Model("Gemini 3.5 Flash-Lite",   0.30,  2.50, 0.30),
    # 来源：api-docs.deepseek.com/quick_start/pricing
    Model("DeepSeek V4-Flash",    0.14,  0.28, 0.0028),
    Model("DeepSeek V4-Pro",      0.435, 0.87, 0.003625),
    # 来源：openrouter.ai/api/v1/models（抓取于 2026-07-27）
    Model("GLM-4.7 (OpenRouter)", 0.40,  1.75, 0.40),
    Model("Qwen3-Coder-Flash (OR)", 0.195, 0.975, 0.195),
    Model("gpt-oss-120b (OR)",    0.037, 0.17, 0.037),
]


# ---------------------------------------------------------------------------
# 2. 一次 PR 代码审查的 token 消耗 —— 假设（无公开权威测算，见数据册 6.3 的说明）
# ---------------------------------------------------------------------------
ASSUMPTIONS_PR = {
    # 三档 PR 规模。token 数 = (diff + 被引用的上下文文件 + 系统提示/规则) 的近似
    # 依据：CodeRabbit 计费口径为「每审查 1 个文件 $0.25」，隐含单文件级别的处理粒度
    "small":  {"files": 3,  "in_tokens":  12_000, "out_tokens": 1_500},
    "medium": {"files": 10, "in_tokens":  45_000, "out_tokens": 3_000},
    "large":  {"files": 30, "in_tokens": 140_000, "out_tokens": 6_000},
}
CACHE_HIT_RATIO = 0.60   # 假设：仓库上下文/系统提示可命中 prompt cache 的比例


def pr_cost(model: Model, in_tokens: int, out_tokens: int, cache_ratio: float) -> float:
    cached = in_tokens * cache_ratio
    fresh = in_tokens - cached
    return (fresh * model.inp + cached * model.cache_read + out_tokens * model.out) / 1e6


def section_pr_review():
    print(SEP)
    print("§6.3  单次 PR 代码审查的 LLM 成本（USD/次）")
    print(f"      假设 prompt cache 命中率 = {CACHE_HIT_RATIO:.0%}")
    print(SEP)
    header = f"{'模型':<28}" + "".join(f"{k:>12}" for k in ASSUMPTIONS_PR)
    print(header)
    for m in MODELS:
        row = f"{m.name:<28}"
        for _, a in ASSUMPTIONS_PR.items():
            row += f"{pr_cost(m, a['in_tokens'], a['out_tokens'], CACHE_HIT_RATIO):>12.4f}"
        print(row)
    print()
    print("  市场价锚点：CodeRabbit 用量计费 $0.25/文件 → medium(10 文件) = $2.50/次")
    print("            Greptile 超额计费 $1.00/次审查")
    print("  → 以上自建成本 vs 市场售价的毛利空间，即为本产品的成本可行性依据。")
    print()


# ---------------------------------------------------------------------------
# 3. 保守漏斗模型（基准取值见数据册 §1 / §2）
# ---------------------------------------------------------------------------
FUNNEL = {
    "visit_to_signup": 0.045,   # 保守：ChartMogul 2026 opt-in free trial 4.5%
    "signup_to_paid":  0.030,   # 保守：低于 freemium GOOD 区间 3%-5% 的下沿
    "arpa_usd":        19.0,    # 假设定价
    "monthly_logo_churn": 0.07, # 保守：Baremetrics ARPU $10-25 档 user churn 6.6%，取 7%
}


def section_funnel():
    print(SEP)
    print("§1+§2  保守漏斗与稳态 MRR（每 1,000 月访客）")
    print(SEP)
    f = FUNNEL
    signups = 1000 * f["visit_to_signup"]
    paid = signups * f["signup_to_paid"]
    print(f"  1,000 访客 → {signups:.1f} 注册 → {paid:.2f} 付费客户")
    print(f"  新增 MRR = {paid * f['arpa_usd']:.2f} USD/月")
    # 稳态：net_adds = new - churn*base = 0  →  base = new / churn
    base = paid / f["monthly_logo_churn"]
    print(f"  在月流失 {f['monthly_logo_churn']:.0%} 下，稳态客户数上限 = "
          f"{paid:.2f}/{f['monthly_logo_churn']:.2f} = {base:.1f} 客户")
    print(f"  → 稳态 MRR 天花板 = {base * f['arpa_usd']:.0f} USD/月")
    print()
    print("  反推：要达到 $1,000 MRR 稳态，需要的月访客量 =")
    need_customers = 1000 / f["arpa_usd"]
    need_new = need_customers * f["monthly_logo_churn"]
    need_visits = need_new / (f["visit_to_signup"] * f["signup_to_paid"])
    print(f"    稳态客户 {need_customers:.0f} → 每月须净补 {need_new:.1f} 付费客户"
          f" → 每月须 {need_visits:,.0f} 访客")
    print(f"  客户平均生命周期 = 1/{f['monthly_logo_churn']:.2f} = "
          f"{1/f['monthly_logo_churn']:.1f} 个月，LTV(毛) = "
          f"${f['arpa_usd']/f['monthly_logo_churn']:.0f}")
    print()


# ---------------------------------------------------------------------------
# 4. 收款通道有效费率（来源见数据册 §8）
# ---------------------------------------------------------------------------
def section_payments():
    print(SEP)
    print("§8  收款通道有效费率（订阅制、国际卡、客单价敏感度）")
    print(SEP)

    def stripe(x):        # 2.9%+$0.30 +0.5% 国际卡 +1% 换汇 + Stripe Tax 0.5%
        return x * (0.029 + 0.005 + 0.01 + 0.005) + 0.30

    def paddle(x):        # 5% + $0.50，MoR
        return x * 0.05 + 0.50

    def lemon(x):         # 5%+$0.50 base, +1.5% 国际卡, +0.5% 订阅
        return x * (0.05 + 0.015 + 0.005) + 0.50

    def polar_starter(x): # 5%+$0.50, +1.5% 国际卡
        return x * (0.05 + 0.015) + 0.50

    def polar_pro(x):     # 3.8%+$0.40, +1.5% 国际卡（另 $20/月固定费，未计入单笔）
        return x * (0.038 + 0.015) + 0.40

    channels = [("Stripe+Tax(自担MoR)", stripe), ("Paddle", paddle),
                ("Lemon Squeezy", lemon), ("Polar Starter", polar_starter),
                ("Polar Pro(+$20/mo)", polar_pro)]
    prices = [9, 19, 29, 49, 99]
    print(f"{'通道':<24}" + "".join(f"{'$'+str(p):>11}" for p in prices))
    for name, fn in channels:
        print(f"{name:<24}" + "".join(f"{fn(p)/p:>10.1%} " for p in prices))
    print()
    print("  注：Polar Pro 另有 $20/月固定费，官方公布的对 Starter 盈亏平衡点约 $1,379/月流水。")
    print()


# ---------------------------------------------------------------------------
# 5. 无人化基础设施月成本（来源见数据册 §7）
# ---------------------------------------------------------------------------
def section_infra():
    print(SEP)
    print("§7  无人化基础设施月成本（USD/月）")
    print(SEP)
    lean = {
        "Cloudflare Workers Paid (最低月费)": 5.00,
        "Neon Launch（按量，~0.5 CU 常驻等效 + 2GB 存储，估算）": 4.00,
        "域名（摊销 ~$12/年）": 1.00,
        "邮件发送（Resend/Postmark 免费档内）": 0.00,
    }
    standard = {
        "Vercel Pro": 20.00,
        "Supabase Pro（含 $10 compute credit，Micro 实例）": 25.00,
        "Cloudflare Workers Paid": 5.00,
        "Railway Hobby（后台 worker）": 5.00,
        "域名 + 邮件 + 监控": 5.00,
    }
    for label, d in [("极简档（Serverless 全免/低费）", lean),
                     ("标准档（托管平台组合）", standard)]:
        print(f"  {label}")
        for k, v in d.items():
            print(f"    {k:<52} ${v:>7.2f}")
        print(f"    {'小计':<52} ${sum(d.values()):>7.2f}")
        print()

    print("  叠加 LLM 变动成本（每月 N 次 PR 审查，medium 档，Sonnet 5 引导价）：")
    m = next(x for x in MODELS if x.name.startswith("Claude Sonnet"))
    a = ASSUMPTIONS_PR["medium"]
    unit = pr_cost(m, a["in_tokens"], a["out_tokens"], CACHE_HIT_RATIO)
    for n in (300, 1000, 3000, 10000):
        print(f"    {n:>6,} 次/月 × ${unit:.4f} = ${n*unit:>9.2f}"
              f"   → 含标准档基础设施合计 ${n*unit + sum(standard.values()):>9.2f}")
    print()
    print("  同样调用量改用 DeepSeek V4-Flash：")
    m2 = next(x for x in MODELS if x.name.startswith("DeepSeek V4-Flash"))
    unit2 = pr_cost(m2, a["in_tokens"], a["out_tokens"], CACHE_HIT_RATIO)
    for n in (300, 1000, 3000, 10000):
        print(f"    {n:>6,} 次/月 × ${unit2:.4f} = ${n*unit2:>9.2f}"
              f"   → 含标准档基础设施合计 ${n*unit2 + sum(standard.values()):>9.2f}")
    print()


# ---------------------------------------------------------------------------
# 6. 胜率（win rate）基础率合成
# ---------------------------------------------------------------------------
def section_winrate():
    print(SEP)
    print("§4+§5  胜率基础率（base rate）合成 —— 保守估计")
    print(SEP)
    # 各条件概率均来自数据册对应来源，标注为「取值」而非「测量值」
    steps = [
        ("项目在 12 个月后仍在线上运行",      0.90,  "Show HN 10k 样本：年均死亡率约 9%"),
        ("12 个月内产生过任何付费收入",       0.60,  "IndieLaunches 326 项目中 52% 披露收入（下调为保守值）"),
        ("达到 $1,000 MRR（任意时间点）",     0.20,  "多源交叉：~70% 长期低于 $1K MRR"),
        ("达到 $10,000 MRR（任意时间点）",    0.06,  "多源交叉：4%-7%"),
    ]
    print(f"  {'里程碑':<36}{'取值':>8}   依据")
    for label, p, src in steps:
        print(f"  {label:<36}{p:>7.0%}   {src}")
    print()
    joint_1k = steps[0][1] * steps[1][1] * (steps[2][1] / steps[1][1] if steps[1][1] else 0)
    print(f"  说明：上述里程碑并非独立事件，不可简单相乘。")
    print(f"  可直接用于建模的边际概率（对「一个新启动的单人 SaaS」）：")
    print(f"    P(12 个月内有收入)        ≈ 50%-60%")
    print(f"    P(曾达到 $1K MRR)         ≈ 15%-25%   建模取 20%")
    print(f"    P(曾达到 $10K MRR)        ≈  4%-7%    建模取  5%")
    print(f"    P(5 年后企业仍存续)       ≈ 45%-52%   BLS Information 业 5 年存活 ~52%")
    print()
    print("  ※ 兼职（每周 20 小时）会显著拉长时间线：")
    print("    多源二手数据称兼职把时间线拉长 2-3 倍；MicroConf 2024 报告称全职创始人")
    print("    增速为兼职的 2.2 倍。→ 建模时对所有『达标耗时』乘以 2.0-2.5 的惩罚系数。")
    print()


if __name__ == "__main__":
    section_funnel()
    section_pr_review()
    section_infra()
    section_payments()
    section_winrate()
    print(SEP)
    print("所有单价来源见 BENCHMARKS.md；所有假设集中在本文件顶部常量，可自行修改重算。")
    print(SEP)
