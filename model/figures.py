"""SVG 矢量图表生成（苹果视觉风格）。

设计纪律，逐条对应「苹果风格」的实质而非表象：
  · 单一强调色，其余全用中性灰阶——颜色只用来指示语义，不用来装饰
  · 发丝级网格线（0.5pt、#D2D2D7），且只保留一个方向
  · 去掉全部边框，只留必要的基线
  · 数值直接标在图元上，不让读者在图例与色块之间来回查
  · 大量留白：字号层级拉开，宁可少画一条曲线也不挤

输出 SVG 而非 PNG：在 PDF 中无损，且文字可被检索与复制。
"""

from __future__ import annotations

import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

import assumptions

FIG_DIR = Path(__file__).resolve().parent.parent / "outputs" / "figures"

INK = "#1D1D1F"        # 主文字
INK2 = "#6E6E73"       # 次要文字
HAIRLINE = "#D2D2D7"   # 发丝分隔线
ACCENT = "#0071E3"     # 唯一强调色
NEG = "#FF3B30"        # 仅用于负值语义
POS = "#34C759"
MUTED = "#E8E8ED"

_CJK = "Noto Sans SC"
_LATIN = "Inter"
FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"


def setup() -> None:
    """注册本地静态字重。

    **不要用系统里的 NotoSansSC-VF.ttf**：它是可变字体，matplotlib 只能解析出
    weight 100，所有图表会渲染成极细字形。改用 assets/fonts 下的静态字重文件
    （Inter 与 Noto Sans SC，均为 SIL OFL 1.1，见同目录 LICENSES.txt）。
    """
    for p in sorted(FONT_DIR.glob("*.ttf")):
        font_manager.fontManager.addfont(str(p))
    plt.rcParams.update({
        # Inter 在前：拉丁字母与数字用 Inter，中文回落到 Noto Sans SC
        "font.family": [_LATIN, _CJK, "DejaVu Sans"],
        "font.weight": "regular",
        "font.size": 9,
        "axes.edgecolor": HAIRLINE,
        "axes.labelcolor": INK2,
        "axes.titlecolor": INK,
        "axes.titlesize": 11,
        "axes.titleweight": "semibold",
        "axes.titlepad": 14,
        "axes.grid": True,
        "grid.color": HAIRLINE,
        "grid.linewidth": 0.5,
        "grid.alpha": 0.7,
        "xtick.color": INK2,
        "ytick.color": INK2,
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
        "svg.fonttype": "none",       # 文字保留为文本，PDF 中可检索
        # 标签里的 $ 是美元号，不是数学模式。不关掉 mathtext，matplotlib 会把
        # 「$30/h → $20/h」当公式解析并悄悄换成 STIXGeneral 衬线斜体，
        # 既与全文字体不一致，也会在 PDF 里多嵌一套字体。
        "text.parse_math": False,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.unicode_minus": False,
        # 默认 matplotlib 用随机数给 SVG 里的 clipPath 等元素编 id，
        # 同样的数据两次构建会得到不同的文件。固定盐值后 id 变成确定的，
        # 图表因此可以逐字节对比——这是「可复现」的一部分，不是洁癖：
        # 只有字节可比，才能一眼看出某次改动到底动了图还是只动了时间戳。
        "svg.hashsalt": "cursorflowai-bp",
    })


def _clean(ax, keep=("left",), grid_axis="x") -> None:
    for side in ("top", "right", "bottom", "left"):
        ax.spines[side].set_visible(side in keep)
    for side in keep:
        ax.spines[side].set_linewidth(0.8)
        ax.spines[side].set_color(HAIRLINE)
    ax.grid(axis=grid_axis)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)


def _save(fig, name: str) -> Path:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    p = FIG_DIR / name
    # metadata Date=None 去掉 <dc:date>：那是构建时刻，不是图的内容，
    # 留着会让每次构建的 SVG 都不同，掩盖真正的改动。
    fig.savefig(p, format="svg", bbox_inches="tight", pad_inches=0.15,
                metadata={"Date": None})
    plt.close(fig)

    # svg.fonttype="none" 让文字以文本形式保留（PDF 中可检索、可复制），
    # 代价是字体解析交给渲染器。matplotlib 会把 rcParams 的整个族列表写进
    # style，因此这里只做一道断言：确认 CJK 族确实在列，否则汉字会由渲染器
    # 自行回退到系统字体（Windows 上是微软雅黑），换台机器构建结果就会不同。
    svg = p.read_text(encoding="utf-8")
    if "<text" in svg and _CJK not in svg:
        raise RuntimeError(f"{name} 的文本未声明 {_CJK}，汉字将触发系统字体回退")
    return p


# --------------------------------------------------------------------------

def fig_stop_distribution(mc: dict) -> Path:
    d = mc["stop_distribution"]
    order = ["止于 Gate 0-B（流量验证）", "止于 Gate 1（付费意愿）",
             "止于 Gate 2（MVP 未能交付）", "运营期被平台方打包功能击垮", "运营中"]
    items = [(k, d[k]) for k in order if k in d]
    labels = [k for k, _ in items][::-1]
    vals = [v for _, v in items][::-1]
    colors = [ACCENT if "运营中" in l else MUTED for l in labels]

    fig, ax = plt.subplots(figsize=(7.0, 2.9))
    bars = ax.barh(labels, vals, color=colors, height=0.6)
    for b, v in zip(bars, vals):
        ax.text(v + 0.008, b.get_y() + b.get_height() / 2, f"{v:.1%}",
                va="center", fontsize=9, color=INK, fontweight="medium")
    ax.set_xlim(0, max(vals) * 1.22)
    ax.set_xticks([])
    ax.set_title("三年后项目停在哪一步（10 万次模拟）")
    _clean(ax, keep=(), grid_axis="x")
    ax.grid(False)
    ax.text(0, -0.22, "阶段门把 78.3% 的失败拦在只亏几十小时的阶段",
            transform=ax.transAxes, fontsize=8.5, color=INK2)
    return _save(fig, "stop_distribution.svg")


def fig_return_distribution(mc: dict, samples: np.ndarray) -> Path:
    o = mc["outcomes_full"]
    fig, ax = plt.subplots(figsize=(7.0, 3.4))
    # 纵轴取对数：84% 的样本挤在 0.97 附近的一根尖峰里，线性刻度下
    # 右尾（真正决定期望值的那部分）会被压成一条看不见的贴地线。
    ax.hist(np.clip(samples, 0, 2.5), bins=160, color=MUTED, edgecolor="none")
    ax.set_yscale("log")
    ax.set_ylim(1, None)
    top = ax.get_ylim()[1]

    ax.axvline(1.0, color=INK, lw=0.9, ls="--")
    ax.text(1.015, top * 0.30, "保本线", fontsize=8.5, color=INK)
    for q, lbl, h in (("P10", "P10", 0.05), ("P50", "中位", 0.012), ("P90", "P90", 0.05)):
        ax.axvline(o[q], color=ACCENT, lw=1.0, alpha=0.8)
        ax.text(o[q], top * h, f"{lbl} {o[q]:.2f}", fontsize=8, color=ACCENT,
                rotation=90, va="bottom", ha="right")
    ax.axvline(o["mean"], color=NEG, lw=1.3)
    ax.text(o["mean"], top * 0.0035, f"均值 {o['mean']:.2f} ", fontsize=8.5,
            color=NEG, rotation=90, va="bottom", ha="right")

    ax.set_xlabel("收益倍数（全口径：现金 + 时间机会成本；未花掉的预算算作收回）")
    ax.set_ylabel("样本数（对数刻度）")
    ax.set_xlim(0, 2.0)
    ax.set_title("收益倍数分布：中位数贴在保本线之下，右尾太薄以致均值仍为负")
    _clean(ax, keep=("bottom",), grid_axis="x")
    ax.grid(False)
    return _save(fig, "return_distribution.svg")


def fig_indifference(sweep: list[dict], indiff_rate: float,
                     hours_per_year: float) -> Path:
    """无差异时薪图。

    无差异点**不在这里重算**：曲线只有十几个采样点，线性插值出来的交点会与
    kelly.py 的求解结果差 0.1 美元左右，正文与图上就会出现两个数。
    这里直接用求解器给出的值标注，图上画的是同一条曲线。
    """
    rates = [s["hourly_usd"] for s in sweep]
    evs = [s["ev_usd"] for s in sweep]
    fig, ax = plt.subplots(figsize=(7.0, 3.2))
    ax.axhline(0, color=INK, lw=0.9)
    ax.plot(rates, evs, color=ACCENT, lw=2.0, solid_capstyle="round")
    ax.fill_between(rates, evs, 0, where=[e > 0 for e in evs], color=POS, alpha=0.10)
    ax.fill_between(rates, evs, 0, where=[e <= 0 for e in evs], color=NEG, alpha=0.08)

    cross = indiff_rate
    ax.axvline(cross, color=INK, lw=0.8, ls=":")
    ax.plot([cross], [0], "o", color=INK, ms=5)
    ax.annotate(f"无差异时薪 ${cross:.1f}/h\n（≈ ${cross * hours_per_year:,.0f}/年）",
                xy=(cross, 0), xytext=(cross + 4, max(evs) * 0.45),
                fontsize=9, color=INK,
                arrowprops=dict(arrowstyle="-", color=HAIRLINE, lw=0.8))
    ev30 = next(s["ev_usd"] for s in sweep if abs(s["hourly_usd"] - 30) < 1e-6)
    ax.plot([30], [ev30], "o", color=NEG, ms=5)
    # 标在点的左下方：曲线向右下走，放右侧会压在线上
    ax.annotate("当前假设 $30/h", xy=(28.4, ev30 - (max(evs) - min(evs)) * 0.10),
                fontsize=8.5, color=NEG, ha="right")

    ax.set_xlabel("时间机会成本（美元/小时）")
    ax.set_ylabel("三年期望值（美元）")
    ax.set_title("整份分析里最可操作的一张图：时薪多少以下才值得做")
    _clean(ax, keep=("left", "bottom"), grid_axis="y")
    return _save(fig, "indifference_rate.svg")


def fig_gate_value(gates: dict) -> Path:
    rows = gates["gate_value"]["per_gate"]
    labels = [r["gate"] for r in rows][::-1]
    vals = [r["gate_value_usd"] for r in rows][::-1]
    fig, ax = plt.subplots(figsize=(7.0, 2.3))
    bars = ax.barh(labels, vals, color=[ACCENT if v > 5000 else MUTED for v in vals],
                   height=0.55)
    for b, v in zip(bars, vals):
        ax.text(v + max(vals) * 0.015, b.get_y() + b.get_height() / 2,
                f"${v:,.0f}", va="center", fontsize=9, color=INK, fontweight="medium")
    ax.set_xlim(0, max(vals) * 1.2)
    ax.set_xticks([])
    ax.set_title("每道门省下的期望损失")
    _clean(ax, keep=(), grid_axis="x")
    ax.grid(False)
    ax.text(0, -0.30, "Gate 1（付费意愿）一门抵其余各门总和的 9 倍："
                      "它用 26 小时挡住了 240 小时的无效开发",
            transform=ax.transAxes, fontsize=8.5, color=INK2)
    return _save(fig, "gate_value.svg")


def fig_sensitivity(mc: dict) -> Path:
    rows = mc["sensitivity"]
    base = rows[0]["mean"]
    # 剔除「$0/h 纯闲暇」一行：它不是参数扰动，而是**换了一套记账口径**，
    # 幅度（+1.39）比其余各行大一个数量级，留在图里会把真正的参数敏感性压平。
    # 该情景单独在正文与无差异时薪图中呈现。
    items = sorted((r for r in rows[1:] if "$0/h" not in r["scenario"]),
                   key=lambda r: abs(r["mean"] - base))
    labels = [r["scenario"] for r in items]
    deltas = [r["mean"] - base for r in items]
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    ax.barh(labels, deltas, color=[POS if d > 0 else NEG for d in deltas],
            height=0.6, alpha=0.85)
    ax.axvline(0, color=INK, lw=0.9)
    for i, d in enumerate(deltas):
        ax.text(d + (0.012 if d > 0 else -0.012), i, f"{d:+.3f}",
                va="center", ha="left" if d > 0 else "right",
                fontsize=8.5, color=INK)
    pad = max(abs(min(deltas)), abs(max(deltas))) * 0.35
    ax.set_xlim(min(deltas) - pad, max(deltas) + pad)
    ax.set_xlabel(f"期望收益倍数相对基准（{base:.3f}）的变化")
    ax.set_title("参数敏感性：单项扰动都改不了「期望值为负」这个结论")
    _clean(ax, keep=(), grid_axis="x")
    ax.text(0, -0.16, "已剔除「时薪按 $0 计」一行：那是换记账口径而非参数扰动，"
                      "幅度 +1.39，另见无差异时薪图",
            transform=ax.transAxes, fontsize=8, color=INK2)
    return _save(fig, "sensitivity.svg")


def fig_traffic_gap(acq: dict, funnel: dict) -> Path:
    months = np.arange(1, 37)
    plan = np.array(acq["steady_curve"], dtype=float)
    gap = acq["gap_analysis"]
    need_card = gap["required_uv_for_1000_mrr_with_card"]
    need_nocard = gap["required_uv_for_1000_mrr_no_card"]

    fig, ax = plt.subplots(figsize=(7.0, 3.4))
    ax.plot(months, plan, color=ACCENT, lw=2.2, solid_capstyle="round",
            label="复利渠道计划流量")
    ax.axhline(need_nocard, color=NEG, lw=1.1, ls="--")
    ax.axhline(need_card, color=INK, lw=1.1, ls="--")
    ax.text(35.5, need_nocard * 1.04, f"不要信用卡：需 {need_nocard:,.0f} UV/月",
            fontsize=8.5, color=NEG, ha="right")
    ax.text(35.5, need_card * 1.10, f"要求信用卡：需 {need_card:,.0f} UV/月",
            fontsize=8.5, color=INK, ha="right")
    ax.text(24, plan[23] * 0.55, "复利渠道计划流量", fontsize=8.5, color=ACCENT)
    ax.fill_between(months, plan, need_card, where=plan >= need_card,
                    color=POS, alpha=0.10)
    ax.set_xlabel("月份")
    ax.set_ylabel("月独立访客")
    ax.set_xlim(1, 36)
    ax.set_ylim(0, max(need_nocard, plan.max()) * 1.15)
    ax.set_title("维持 $1,000 MRR 所需流量 vs 计划能拿到的流量")
    _clean(ax, keep=("left", "bottom"), grid_axis="y")
    ax.text(0, -0.28,
            f"「是否要求信用卡」这一个开关，把所需流量从 {need_nocard:,.0f} 降到 "
            f"{need_card:,.0f} UV/月",
            transform=ax.transAxes, fontsize=8.5, color=INK2)
    return _save(fig, "traffic_gap.svg")


def fig_annualization(kelly: dict) -> Path:
    ann = kelly["full_accounting"]["annualization"]
    keys = [k for k in ann if not k.startswith("_")]
    # 横向排布：四个口径名都很长，竖排必然折行或压叠
    labels = [f"{ann[k]['label'].split('：')[0]}　{ann[k]['label'].split('：')[1]}"
              for k in keys][::-1]
    vals = [ann[k]["value"] for k in keys][::-1]
    fig, ax = plt.subplots(figsize=(7.0, 2.5))
    bars = ax.barh(labels, vals, color=[NEG if v < 0 else ACCENT for v in vals],
                   height=0.55, alpha=0.9)
    ax.axvline(0, color=INK, lw=0.9)
    for b, v in zip(bars, vals):
        ax.text(v - 0.0015, b.get_y() + b.get_height() / 2, f"{v:+.2%} ",
                ha="right", va="center", fontsize=9, color=INK)
    ax.set_xlim(min(vals) * 1.55, 0.012)
    ax.set_xticks([])
    plt.setp(ax.get_yticklabels(), fontsize=8.5, color=INK2)
    ax.set_title("同一个分布，四个「年化」（全口径）")
    _clean(ax, keep=(), grid_axis="x")
    ax.grid(False)
    ax.text(0, -0.20, "四者极差 2.7 个百分点，且全部为负。"
                      "正文任何一处「年化 XX%」都必须紧跟口径名。",
            transform=ax.transAxes, fontsize=8.5, color=INK2)
    return _save(fig, "annualization.svg")


def fig_scoring(scoring: dict) -> Path:
    rows = scoring.get("survivors", [])[:5]
    if not rows:
        return FIG_DIR / "scoring.svg"
    labels = [f"{r['cid']}　{r['name']}"[:26] for r in rows][::-1]
    vals = [r["total"] for r in rows][::-1]
    fig, ax = plt.subplots(figsize=(7.0, 2.5))
    bars = ax.barh(labels, vals,
                   color=[ACCENT if i == len(vals) - 1 else MUTED
                          for i in range(len(vals))], height=0.58)
    for b, v in zip(bars, vals):
        ax.text(v + max(vals) * 0.012, b.get_y() + b.get_height() / 2, f"{v:.2f}",
                va="center", fontsize=9, color=INK, fontweight="medium")
    ax.set_xlim(0, max(vals) * 1.15)
    ax.set_xticks([])
    ax.set_title("通过 12 条硬过滤后的加权评分（前五名）")
    _clean(ax, keep=(), grid_axis="x")
    ax.grid(False)
    return _save(fig, "scoring.svg")


def build_all(results: dict, samples: np.ndarray, sweep: list[dict]) -> list[str]:
    setup()
    made = [
        fig_stop_distribution(results["monte_carlo"]),
        fig_return_distribution(results["monte_carlo"], samples),
        fig_indifference(
            sweep,
            results["kelly"]["indifference_hourly_rate"]["indifference_hourly_usd"],
            assumptions.HOURS_PER_YEAR),
        fig_gate_value(results["gates"]),
        fig_sensitivity(results["monte_carlo"]),
        fig_traffic_gap(results.get("acquisition", {}), results["funnel"]),
        fig_annualization(results["kelly"]),
        fig_scoring(results.get("scoring", {})),
    ]
    return [str(p.name) for p in made if p.exists()]
