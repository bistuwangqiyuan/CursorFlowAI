"""获客模型：论证每月 2,729 个精准开发者访客从何而来。

这是本 BP 的主要矛盾，因此本模块的标准比其他模块更严：
  - 每条渠道必须写明**机制**（为什么会有人来），不能只写渠道名
  - 每条渠道必须标注**是否复利**（一次性脉冲不得计入稳态）
  - 每个数字必须能追到 assumptions.py 中的 A 级基准，或明确标记为 D 级假设
  - 必须输出**月度可检验的检查点**，而不是一个三年后的总数

复现：python model/acquisition.py
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np

try:
    from . import assumptions as A
except ImportError:
    import assumptions as A  # type: ignore

OUT_DIR = Path(__file__).resolve().parent.parent / "outputs"


# --------------------------------------------------------------------------
# 一、程序化 SEO 知识库：唯一可用 A 级数据自下而上估算的渠道
# --------------------------------------------------------------------------
# 内容形态：每个 (agent action × 危险模式) 组合一页，说明为什么危险、如何修复。
# 这不是灌水内容——每页对应一个真实的、可复现的配置错误，有修复补丁。

SEO_AGENT_ACTIONS = 15   # [D] 主流 agent action 数量（claude-code-action、codex-action、
                         #     run-gemini-cli、aider、copilot-workspace 等），随生态增长
SEO_DANGER_PATTERNS = 12  # [D] 危险模式数量（pull_request_target、issue_comment 触发、
                          #     write-all 权限、密钥注入环境变量、外发网络未限制 等）


@dataclass
class SeoEstimate:
    pages: int
    top10_rate: float
    top10_rate_grade: str
    uv_per_ranked_page: float
    uv_grade: str
    monthly_uv: float
    note: str


def seo_estimate(pages: int | None = None, uv_per_ranked_page: float = 40.0,
                 use_filtered_rate: bool = True) -> SeoEstimate:
    """自下而上估算程序化 SEO 的稳态流量。

    top10_rate 的两种口径（均来自 Ahrefs 100 万 URL 追踪，A 级）：
      - 1.74%：全部新页面（含大量空页面、非英文页面、垃圾页）
      - 6.11%：筛选出英文非空内容后的比率  ← 本模型采用，因为我们的页面确属此类

    uv_per_ranked_page 为 D 级假设：无公开数据说明「一个排进前十的超长尾技术页面
    每月带来多少访客」。40 UV/月是本人估计，必须做敏感性分析。
    """
    pages = pages or SEO_AGENT_ACTIONS * SEO_DANGER_PATTERNS
    rate = 0.0611 if use_filtered_rate else A.SEO_TOP10_PROBABILITY_12M
    ranked = pages * rate
    return SeoEstimate(
        pages=pages,
        top10_rate=rate,
        top10_rate_grade="A",
        uv_per_ranked_page=uv_per_ranked_page,
        uv_grade="D（本人估计，无公开数据）",
        monthly_uv=ranked * uv_per_ranked_page,
        note=f"{pages} 页 × {rate:.2%} 进前十 = {ranked:.1f} 页 × {uv_per_ranked_page:.0f} UV/月",
    )


def seo_sensitivity() -> list[dict]:
    """对两个不确定参数做网格，说明 SEO 渠道的可信区间有多宽。"""
    rows = []
    for pages in (60, 120, 180, 300):
        for uv in (15, 40, 80):
            e = seo_estimate(pages=pages, uv_per_ranked_page=uv)
            rows.append({"pages": pages, "uv_per_ranked_page": uv,
                         "monthly_uv": round(e.monthly_uv, 1)})
    return rows


# --------------------------------------------------------------------------
# 二、渠道台账
# --------------------------------------------------------------------------

@dataclass
class Channel:
    name: str
    mechanism: str          # 为什么会有人来（缺这条的渠道不予采纳）
    compounding: bool       # 是否复利。非复利者不得计入稳态
    m12_uv: float
    m24_uv: float
    m36_uv: float
    grade: str
    basis: str
    kill_criterion: str     # 什么情况下判定该渠道失败


CHANNELS: list[Channel] = [
    Channel(
        name="免费 GitHub Action 本体（产品即渠道）",
        mechanism="扫描器以免费 GitHub Action 形式发布。每个安装它的仓库都会在 "
                  ".github/workflows/*.yml 里留下一行公开可见的引用，该文件可被 GitHub "
                  "代码搜索索引，也会被该仓库的贡献者读到。安装量本身就是曝光量。",
        compounding=True,
        m12_uv=180, m24_uv=600, m36_uv=1100,
        grade="D",
        basis="无公开的「Action 安装→官网访问」转化数据（assumptions.MARKETPLACE_INSTALL_TO_PAID 为 D 级空缺）。"
              "此处按第 12 月 150 个安装、每安装每月带来约 1.2 次官网访问推算，属本人假设。",
        kill_criterion="第 6 月安装数 < 30，或第 12 月 < 150",
    ),
    Channel(
        name="程序化 SEO 知识库（180 页配置安全条目）",
        mechanism="每个 (agent action × 危险模式) 组合一页，内容是具体的错误配置示例 + "
                  "为什么危险 + 可直接复制的修复补丁。搜索这些具体报错/配置名的人，"
                  "正是处于危险三角中的人。",
        compounding=True,
        m12_uv=0, m24_uv=440, m36_uv=700,
        grade="A（排名概率）/ D（单页流量）",
        basis="Ahrefs 100 万 URL 追踪：英文非空内容 12 个月内进前十 6.11%。"
              "180 页 × 6.11% = 11 页进前十。**第一年按 0 计**（SEO 起量周期 9–18 个月）。"
              "单页 40 UV/月为 D 级假设。",
        kill_criterion="第 18 月自然搜索流量 < 100 UV/月",
    ),
    Channel(
        name="负责任披露飞轮",
        mechanism="持续在公开仓库中发现真实的 agent CI 配置漏洞，私下告知维护者并附修复补丁。"
                  "每次披露产生三样东西：一个被修好的仓库、一个知道你是谁的维护者、"
                  "可能的公开致谢或 advisory 署名。这是本方案中唯一同时满足"
                  "「真实帮到人」与「获客」的动作。",
        compounding=True,
        m12_uv=120, m24_uv=300, m36_uv=450,
        grade="D",
        basis="按每月 10 次披露、30% 回复率、每个回复者平均带来 4 次访问（自己 + 转发）推算。"
              "口碑的重要性有间接支持：IndieLaunches 326 个 HN 项目中，口碑是被提及最多的"
              "主渠道（40 次为主渠道，高于 SEO 的 27 次）。",
        kill_criterion="第 3 月累计披露 < 20 次，或回复率 < 20%",
    ),
    Channel(
        name="被收录进 awesome-list / 他人 README / 安全清单",
        mechanism="安全工具进入 awesome-actions、awesome-ci-security 等清单后获得长期被动引用。",
        compounding=True,
        m12_uv=60, m24_uv=160, m36_uv=250,
        grade="D",
        basis="本人假设，无公开数据。取值刻意保守。",
        kill_criterion="第 12 月被收录清单数 < 2",
    ),
    Channel(
        name="Hacker News / 垂直社群脉冲",
        mechanism="发布原创安全研究（例如「我扫了 5,000 个公开仓库，发现 N 个处于危险三角」）。"
                  "此类内容在本领域传播力最强——微软、CSA、Aikido、Noma 四篇来源本身"
                  "都是靠这个方式传播的。",
        compounding=False,   # ← 关键：脉冲不计入稳态
        m12_uv=0, m24_uv=0, m36_uv=0,
        grade="B",
        basis="HN 头版 10,000–30,000 UV/24h，48 小时内衰减到零。**按定义不计入稳态基线**，"
              "仅作为一次性事件叠加在爬坡曲线上（见 funnel.py 的 pulses 参数）。",
        kill_criterion="三年内 0 次进入 HN 前 30 名",
    ),
]

PULSE_EVENTS = {
    # 月份 -> 单月额外 UV。依据：HN_FRONTPAGE_UV 为 B 级；社群脉冲为 D 级假设
    4: A.HN_FRONTPAGE_UV,
    9: 3000,
    18: A.HN_FRONTPAGE_UV,
    30: 3000,
}


# --------------------------------------------------------------------------
# 三、月度轨迹与检查点
# --------------------------------------------------------------------------

def steady_traffic_curve(months: int = 36) -> np.ndarray:
    """把各复利渠道的 m12/m24/m36 锚点线性插值成月度曲线。"""
    anchors_x = np.array([0, 12, 24, 36])
    total = np.zeros(months)
    for ch in CHANNELS:
        if not ch.compounding:
            continue
        anchors_y = np.array([0.0, ch.m12_uv, ch.m24_uv, ch.m36_uv])
        total += np.interp(np.arange(1, months + 1), anchors_x, anchors_y)
    return total


def full_traffic_curve(months: int = 36) -> np.ndarray:
    curve = steady_traffic_curve(months).copy()
    for m, uv in PULSE_EVENTS.items():
        if 1 <= m <= months:
            curve[m - 1] += uv
    return curve


def checkpoints() -> list[dict]:
    """月度可检验检查点。每个点有客观标准与未达标的处置动作。"""
    steady = steady_traffic_curve(36)
    pts = [3, 6, 12, 18, 24, 36]
    actions = {
        3:  "披露飞轮未启动。检查是不是选错了人群（找的仓库都是玩具项目）。重选 30 个目标仓库重试一次。",
        6:  "免费 Action 无人安装 = 产品本身没有吸引力。这是**比获客更严重的信号**，回到 Gate 1 重验付费意愿。",
        12: "第一年靠的是披露飞轮与 Action 本体，与 SEO 无关。未达标说明这两条机制不成立，"
            "**触发赛道切换**（转 C13）。",
        18: "SEO 未起量。Ahrefs 数据说 9–18 个月是正常周期，18 个月仍为零则内容质量或选题有问题。"
            "停止新增页面，改为深耕已有页面。",
        24: "此时应已接近 995 UV/月（要卡口径的 $1,000 MRR 需求）。未达标则**必须启用信用卡门槛**"
            "或接受 $1,000 MRR 无法达成。",
        36: "未达 2,729 UV/月（不要卡口径）说明纯自然流量路径走不通，"
            "**执行止损：转为免费开源项目，停止商业化投入**。",
    }
    out = []
    for m in pts:
        uv = float(steady[m - 1])
        cust = uv / 1000 * A.paid_per_1000_visitors(False) / A.MONTHLY_LOGO_CHURN
        out.append({
            "month": m,
            "steady_uv_target": round(uv, 0),
            "implied_steady_customers_no_card": round(cust, 1),
            "implied_steady_mrr_no_card": round(cust * A.ARPU_USD, 0),
            "pass_threshold_uv": round(uv * 0.7, 0),   # 允许 30% 的下偏
            "action_if_missed": actions[m],
        })
    return out


def gap_analysis() -> dict:
    """诚实的缺口分析：计划的稳态流量与需求之间差多少。"""
    steady36 = float(steady_traffic_curve(36)[-1])
    need_no_card = A.visitors_needed_for_mrr(1000.0, False)
    need_card = A.visitors_needed_for_mrr(1000.0, True)
    return {
        "planned_steady_uv_month36": round(steady36, 0),
        "required_uv_for_1000_mrr_no_card": round(need_no_card, 0),
        "required_uv_for_1000_mrr_with_card": round(need_card, 0),
        "coverage_no_card": round(steady36 / need_no_card, 3),
        "coverage_with_card": round(steady36 / need_card, 3),
        "verdict_no_card": "不足" if steady36 < need_no_card else "足够",
        "verdict_with_card": "不足" if steady36 < need_card else "足够",
        "implied_mrr_at_month36_no_card": round(
            steady36 / 1000 * A.paid_per_1000_visitors(False) / A.MONTHLY_LOGO_CHURN * A.ARPU_USD, 0),
        "implied_mrr_at_month36_with_card": round(
            steady36 / 1000 * A.paid_per_1000_visitors(True) / A.MONTHLY_LOGO_CHURN * A.ARPU_USD, 0),
    }


def run() -> dict:
    return {
        "seo_base": asdict(seo_estimate()),
        "seo_sensitivity": seo_sensitivity(),
        "channels": [asdict(c) for c in CHANNELS],
        "compounding_uv_month36": round(float(steady_traffic_curve(36)[-1]), 1),
        "pulse_events": {str(k): v for k, v in PULSE_EVENTS.items()},
        "steady_curve": [round(float(x), 1) for x in steady_traffic_curve(36)],
        "full_curve": [round(float(x), 1) for x in full_traffic_curve(36)],
        "checkpoints": checkpoints(),
        "gap_analysis": gap_analysis(),
    }


def main() -> None:
    r = run()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "acquisition.json").write_text(
        json.dumps(r, ensure_ascii=False, indent=2, default=float), encoding="utf-8")

    print("=" * 78)
    print("获客模型（本项目的主要矛盾）")
    print("=" * 78)

    s = r["seo_base"]
    print(f"\n【程序化 SEO：唯一能用 A 级数据自下而上估算的渠道】")
    print(f"  {s['note']}")
    print(f"  → 稳态 {s['monthly_uv']:.0f} UV/月   "
          f"（排名概率 {s['top10_rate_grade']} 级；单页流量 {s['uv_grade']}）")
    print(f"\n  敏感性（页数 × 单页月流量）：")
    print(f"  {'页数':>6}" + "".join(f"{uv:>12}" for uv in (15, 40, 80)))
    for pages in (60, 120, 180, 300):
        vals = [x["monthly_uv"] for x in r["seo_sensitivity"] if x["pages"] == pages]
        print(f"  {pages:>6}" + "".join(f"{v:>12,.0f}" for v in vals))
    print("  → 区间从 55 到 1,467 UV/月，跨度 27 倍。**这说明 SEO 渠道的估算极不可靠。**")

    print(f"\n【渠道台账】")
    print(f"  {'渠道':<34}{'复利':>5}{'月12':>8}{'月24':>8}{'月36':>8}{'等级':>8}")
    for c in r["channels"]:
        print(f"  {c['name'][:32]:<34}{'是' if c['compounding'] else '否':>5}"
              f"{c['m12_uv']:>8,.0f}{c['m24_uv']:>8,.0f}{c['m36_uv']:>8,.0f}{c['grade'][:6]:>8}")
    print(f"  {'复利渠道合计（稳态）':<34}{'':<5}"
          f"{sum(c['m12_uv'] for c in r['channels'] if c['compounding']):>8,.0f}"
          f"{sum(c['m24_uv'] for c in r['channels'] if c['compounding']):>8,.0f}"
          f"{sum(c['m36_uv'] for c in r['channels'] if c['compounding']):>8,.0f}")
    print("  注：HN/社群脉冲按定义不计入稳态，仅作为一次性事件叠加。")

    print(f"\n【月度检查点】")
    print(f"  {'月':>4}{'稳态UV目标':>12}{'通过线(70%)':>13}{'隐含客户':>10}{'隐含MRR':>10}")
    for p in r["checkpoints"]:
        print(f"  {p['month']:>4}{p['steady_uv_target']:>12,.0f}{p['pass_threshold_uv']:>13,.0f}"
              f"{p['implied_steady_customers_no_card']:>10.1f}"
              f"{p['implied_steady_mrr_no_card']:>10,.0f}")

    g = r["gap_analysis"]
    print(f"\n【缺口分析（诚实结论）】")
    print(f"  计划的第 36 月稳态流量        : {g['planned_steady_uv_month36']:>8,.0f} UV/月")
    print(f"  $1,000 MRR 所需（不要信用卡）: {g['required_uv_for_1000_mrr_no_card']:>8,.0f} UV/月"
          f"  → 覆盖率 {g['coverage_no_card']:.0%}  【{g['verdict_no_card']}】")
    print(f"  $1,000 MRR 所需（要信用卡）  : {g['required_uv_for_1000_mrr_with_card']:>8,.0f} UV/月"
          f"  → 覆盖率 {g['coverage_with_card']:.0%}  【{g['verdict_with_card']}】")
    print(f"  按计划流量推算的第 36 月 MRR : 不要卡 ${g['implied_mrr_at_month36_no_card']:,.0f}"
          f"  |  要卡 ${g['implied_mrr_at_month36_with_card']:,.0f}")
    print(f"\n输出已写入 {OUT_DIR / 'acquisition.json'}")


if __name__ == "__main__":
    main()
