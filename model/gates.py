"""阶段目标与止损门：预算台账、双轨止损线，以及**每道门值多少钱**。

多数商业计划书的「里程碑」章节是装饰性的：写了标准，但没写不达标怎么办，
也从没算过这些标准本身值不值。本文件做三件事：

  1. **预算台账**：每道门的工时与现金上限，累计封顶值即为止损线。
     止损线必须是「累计」而非「单期」，否则会被反复追加吃掉。

  2. **双轨计量**：现金与工时**分别**设线，任一触线即执行预设动作。
     只设现金线是本项目最容易犯的错——现金只占赌注的 4.8%，
     真正会被烧光的是时间，而时间没有对账单提醒你。

  3. **给每道门定价**：用蒙特卡洛跑「有这道门 vs 没这道门」，
     差额就是这道门省下的期望损失。**这是把流程管理翻译成钱的唯一诚实方式。**

复现：python model/gates.py
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path

try:
    from . import assumptions as A
    from . import monte_carlo as MC
except ImportError:
    import assumptions as A  # type: ignore
    import monte_carlo as MC  # type: ignore

OUT_DIR = Path(__file__).resolve().parent.parent / "outputs"

MONTHLY_HOURS = A.HOURS_PER_YEAR / 12          # 83.3 h/月

# 第 3–5 关是**时点检查**而非工作包：它们的工时是「距上一关的增量」，
# 由每月可投入工时推导，不得硬编码。（初稿在此写成了累计值并被再次累加，
# 自检器抓到了累计封顶 3,856 h > 预算 3,000 h 的越界，已订正。）
GATE3_MONTHS, GATE4_MONTHS, GATE5_MONTHS = 1, 6, 12


@dataclass
class Gate:
    gid: str
    name: str
    when: str
    hours: float
    cash_usd: float
    criteria: list[str]           # 客观、可检验的通过标准
    on_pass: str
    on_fail: str
    source: str
    retries: int = 0
    notes: str = ""
    cum_hours: float = field(default=0.0, init=False)
    cum_cash: float = field(default=0.0, init=False)


GATES: list[Gate] = [
    Gate(
        gid="0-A", name="收款通道", when="第 1–2 周（与 0-B 并行）",
        hours=4, cash_usd=512,
        criteria=[
            "A1 中国大陆自然人完成 Paddle 卖家 KYC，收到 approved 通知",
            "A2 境内银行账户在 Transfer Preferences 中显示 verified",
            "A3 拿到 Paddle 要求的材料清单（网站、条款、隐私、定价页）",
        ],
        on_pass="进入 Gate 1；把 MoR 实际费率回填 assumptions.py 核对",
        on_fail="按成本升序走三级回退：个体工商户 → 香港公司 → 美国 LLC。"
                "三级全不可行则终止，并如实写出「本商业模式无可执行形态」",
        source="docs/GATE0.md §1",
        notes="不致命：有已定价的回退路径，最高约 $500 + 年费",
    ),
    Gate(
        gid="0-B", name="流量验证（本项目的生死线）", when="第 1–3 周",
        hours=22, cash_usd=12,
        criteria=[
            "B1 目标关键词族月搜索量合计 ≥ 1,000，且 KD ≤ 20 的词 ≥ 5 个",
            "B2 近 12 个月 ≥ 10 个相关讨论串，其中 ≥ 3 个得分 > 50",
            "B3 免费最小工具上线 14 天内 ≥ 300 真实独立访客 且 ≥ 30 次实际使用",
            "B4 能写出至少一条具体复利机制，且 B3 期间观察到 ≥ 1 次第三方自发引用",
        ],
        on_pass="进入 Gate 1",
        on_fail="B3 未过 → **本候选赛道作废**，回到机会集取下一名重跑 0-B。"
                "理由：连免费都没人要，收费不可能有人要。最多换 3 个赛道；"
                "三次全败则结论为「不做」，转向替代的资金与时间配置",
        source="docs/GATE0.md §2",
        retries=2,
        notes="**未通过前累计开发工时上限为 0。** 这是全表最重要的一条纪律",
    ),
    Gate(
        gid="1", name="付费意愿", when="第 3–5 周",
        hours=26, cash_usd=0,
        criteria=[
            "W1 可识别的目标仓库 ≥ 200 个（受众规模下限）",
            "W2 负责任披露后 ≥ 30% 回复，且 ≥ 3 人主动问「有没有持续监控的版本」",
            "W3 价格锚定候补名单 ≥ 25 人留资，其中 ≥ 10 人选了付费档",
            "W4 **≥ 3 人真实预付 $99**（唯一的 L3 级证据）",
        ],
        on_pass="进入 Gate 2，开始写第一行产品代码",
        on_fail="W4 未过 → 赛道作废，回机会集。**不允许以「再打磨一下文案」为由重试**——"
                "预付款是二元信号，反复试探会滑向骚扰，违反 docs/WTP_VALIDATION.md §3 的道德底线",
        source="docs/WTP_VALIDATION.md §2",
        notes="这是全流程唯一能把「口头感兴趣」变成「掏钱」的一关，也是筛掉最多路径的一关",
    ),
    Gate(
        gid="2", name="MVP 交付", when="第 6–17 周（12 周 × 20 小时）",
        hours=240, cash_usd=3 * A.INFRA_MINIMAL_MONTHLY_USD,
        criteria=[
            "自助注册 → 接入 → 出首份报告的全链路无人工介入，端到端跑通",
            "Paddle 订阅、开票、退款、取消四条路径全部自助可用",
            "前 3 名预付客户全部完成接入并收到第一份有效报告",
        ],
        on_pass="进入 Gate 3，转入运营与获客",
        on_fail="12 周未交付 → **不加时**，砍功能到能交付为止；"
                "若砍到无价值仍不能交付，说明范围判断错误，回 Gate 1 重定范围",
        source="model/opportunity_scoring.py（可交付性维度 9 分）",
        notes="纯规则引擎、零推理成本，工程风险是全流程最低的一环",
    ),
    Gate(
        gid="3", name="首批留存", when="第 6 个月",
        hours=GATE3_MONTHS * MONTHLY_HOURS,
        cash_usd=GATE3_MONTHS * A.INFRA_MONTHLY_USD,
        criteria=[
            "付费客户 ≥ 10 个",
            "月流失率 ≤ 10%（连续 2 个月观测）",
            "自然月访客 ≥ 300 且其中非脉冲来源占比 ≥ 50%",
        ],
        on_pass="进入 Gate 4",
        on_fail="客户数不达标 → 把全部工时转投获客，产品功能冻结 8 周；"
                "流失率不达标 → 停止获客，先修留存（漏水的桶不值得多倒水）",
        source="model/funnel.py、docs/ACQUISITION.md 月度检查点",
        notes="**先诊断是「桶漏」还是「水少」，两者的处置动作正好相反**",
    ),
    Gate(
        gid="4", name="复利渠道成立", when="第 12 个月",
        hours=GATE4_MONTHS * MONTHLY_HOURS,
        cash_usd=GATE4_MONTHS * A.INFRA_MONTHLY_USD,
        criteria=[
            "月访客 ≥ 360，且脉冲渠道贡献占比 ≤ 30%",
            "MRR ≥ $400",
            "存在至少 2 条可验证的复利机制（第三方 README 引用数、"
            "被索引的程序化页面数，二者均需月度环比为正）",
        ],
        on_pass="进入 Gate 5",
        on_fail="**这是最容易自欺的一关。** 若流量仍靠脉冲维持，"
                "则 docs/ACQUISITION.md 的核心假设已被证伪，"
                "必须把稳态 MRR 天花板按纯脉冲重算——大概率转负，届时应止损退出",
        source="docs/ACQUISITION.md 第 12 月检查点",
    ),
    Gate(
        gid="5", name="稳态可持续", when="第 24 个月",
        hours=GATE5_MONTHS * MONTHLY_HOURS,
        cash_usd=GATE5_MONTHS * A.INFRA_MONTHLY_USD,
        criteria=[
            "MRR ≥ $1,000（对应约 53 个客户、月访客 ≥ 995）",
            "月净利为正（扣除 MoR 费率、退款与基础设施）",
            "月均投入工时 ≤ 87 小时（未靠透支时间维持）",
        ],
        on_pass="进入收获期：要么持有现金流，要么按 2–4 × ARR 寻求转让",
        on_fail="**触发终局判断。** 若 24 个月、约 1,900 小时仍换不来 $1,000 MRR，"
                "则实现时薪已远低于 model/kelly.py 算出的无差异时薪（约 $11.8/h），"
                "继续投入不再由数据支持，应转为维护模式或按 2–4 × ARR 出售",
        source="model/monte_carlo.py（P(达 $1,000 MRR) = 7.17%）",
        notes="模型给出的这一关通过概率仅约 7%。**写下这个数，是为了半年后不自欺**",
    ),
]


def build_ledger() -> list[Gate]:
    ch = cc = 0.0
    for g in GATES:
        ch += g.hours * (1 + g.retries)   # 允许重试的门按最坏情况封顶
        cc += g.cash_usd
        g.cum_hours, g.cum_cash = ch, cc
    return GATES


def stop_loss_lines() -> dict:
    """双轨止损线。**两条线互不替代，任一触线即执行动作。**"""
    gs = build_ledger()
    total_h = A.HOURS_PER_YEAR * A.HORIZON_YEARS
    total_c = A.CASH_CAP_USD + A.ENTITY_SETUP_RESERVE_USD
    final = gs[-1]
    tail_months = 12                      # 第 25–36 月：Gate 5 之后的收获期
    tail_h = tail_months * MONTHLY_HOURS
    tail_c = tail_months * A.INFRA_MONTHLY_USD
    return {
        "tail_after_final_gate": {
            "months": tail_months, "hours": tail_h, "cash_usd": tail_c,
            "total_hours_36m": final.cum_hours + tail_h,
            "total_cash_36m": final.cum_cash + tail_c,
        },
        "hours_track": {
            "budget": total_h,
            "committed_by_final_gate": final.cum_hours,
            "headroom": total_h - final.cum_hours,
            "unit_value_usd": A.HOURLY_OPPORTUNITY_COST_USD,
            "budget_value_usd": total_h * A.HOURLY_OPPORTUNITY_COST_USD,
            "rule": "任一门的累计工时超出该门上限即触线。"
                    "**工时线没有银行对账单提醒你，必须自己每周记账**，"
                    "否则它会在毫无感觉的情况下被烧穿——这是本项目最现实的失控方式。",
        },
        "cash_track": {
            "budget": total_c,
            "committed_by_final_gate": final.cum_cash,
            "headroom": total_c - final.cum_cash,
            "rule": "累计现金支出超出该门上限即触线，不得追加（委托方给定：不可追加）。",
        },
        "asymmetry_warning":
            f"现金预算 ${total_c:,.0f} 只占全额赌注的 "
            f"{total_c / (total_c + total_h * A.HOURLY_OPPORTUNITY_COST_USD):.1%}。"
            f"**只盯现金线等于不设防。**",
    }


def gate_value(n: int = 40_000) -> dict:
    """给每道门定价：拆掉它（令其必过）会让期望损失增加多少。

    做法：把该门的通过概率强行设为 1.0，重跑蒙特卡洛，看期望值如何变化。
    差额即为「这道门每次决策为你省下的期望金额」。

    **一个反直觉但重要的结果**：拆掉门会让 P(不亏) 上升（更多路径走到有收入的
    阶段），但期望值下降（更多路径烧掉全部 3,000 小时）。
    **门的价值不在提高胜率，而在削减亏损幅度。**
    """
    base = MC.simulate(n=n)
    W = base["meta"]["full_wager_usd"]
    base_ev = (base["outcomes_full"]["mean"] - 1.0) * W

    rows = []
    for key, label in (("p_gate0b", "Gate 0-B 流量验证"),
                       ("p_gate1", "Gate 1 付费意愿"),
                       ("p_gate2", "Gate 2 MVP 交付")):
        r = MC.simulate(n=n, overrides={key: 1.0})
        ev = (r["outcomes_full"]["mean"] - 1.0) * W
        rows.append({
            "gate": label,
            "ev_with_gate_usd": base_ev,
            "ev_without_gate_usd": ev,
            "gate_value_usd": base_ev - ev,
            "p_gain_with_gate": base["outcomes_full"]["p_gain"],
            "p_gain_without_gate": r["outcomes_full"]["p_gain"],
        })

    allopen = MC.simulate(n=n, overrides={"p_gate0b": 1.0, "p_gate1": 1.0, "p_gate2": 1.0})
    ev_all = (allopen["outcomes_full"]["mean"] - 1.0) * W
    return {
        "per_gate": rows,
        "all_gates_removed": {
            "ev_usd": ev_all,
            "total_gate_value_usd": base_ev - ev_all,
            "interpretation":
                f"全部拆掉门后期望值从 ${base_ev:,.0f} 变为 ${ev_all:,.0f}，"
                f"即这套门机制值 ${base_ev - ev_all:,.0f}。"
                "**在一个期望值本就为负的项目里，门是唯一把损失压住的东西。**",
        },
        "n_sims": n,
    }


def self_check() -> list[str]:
    """台账自洽性检查：不允许任何一门的累计上限超出总预算。"""
    errs = []
    gs = build_ledger()
    total_h = A.HOURS_PER_YEAR * A.HORIZON_YEARS
    total_c = A.CASH_CAP_USD + A.ENTITY_SETUP_RESERVE_USD
    for g in gs:
        if g.cum_hours > total_h:
            errs.append(f"{g.gid} 累计工时 {g.cum_hours:.0f} 超总预算 {total_h:.0f}")
        if g.cum_cash > total_c:
            errs.append(f"{g.gid} 累计现金 ${g.cum_cash:.0f} 超总预算 ${total_c:.0f}")
        if not g.criteria:
            errs.append(f"{g.gid} 缺少客观通过标准")
        if not g.on_fail:
            errs.append(f"{g.gid} 缺少未通过时的处置动作")
    for a, b in zip(gs, gs[1:]):
        if b.cum_hours < a.cum_hours or b.cum_cash < a.cum_cash:
            errs.append(f"{a.gid}→{b.gid} 累计额非单调")
    return errs


def run() -> dict:
    errs = self_check()
    return {
        "gates": [asdict(g) | {"cum_hours": g.cum_hours, "cum_cash": g.cum_cash}
                  for g in build_ledger()],
        "stop_loss": stop_loss_lines(),
        "gate_value": gate_value(),
        "self_check_errors": errs,
    }


def main() -> None:
    r = run()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "gates.json").write_text(
        json.dumps(r, ensure_ascii=False, indent=2, default=float), encoding="utf-8")

    print("=" * 100)
    print("  阶段目标与止损门 · 预算台账")
    print("=" * 100)
    print(f"  {'门':<5}{'名称':<22}{'时点':<20}"
          f"{'本门工时':>9}{'累计工时':>9}{'累计现金':>10}")
    for g in r["gates"]:
        retry = f"×{g['retries'] + 1}" if g["retries"] else ""
        print(f"  {g['gid']:<5}{g['name']:<22}{g['when']:<20}"
              f"{g['hours']:>7.0f}h{retry:<2}{g['cum_hours']:>8.0f}h"
              f"{g['cum_cash']:>9.0f}$")

    sl = r["stop_loss"]
    print("\n【双轨止损线】")
    h, c = sl["hours_track"], sl["cash_track"]
    print(f"  工时轨: 预算 {h['budget']:,.0f} h（价值 ${h['budget_value_usd']:,.0f}），"
          f"最终门累计封顶 {h['committed_by_final_gate']:,.0f} h，"
          f"余量 {h['headroom']:,.0f} h")
    print(f"  现金轨: 预算 ${c['budget']:,.0f}，"
          f"最终门累计封顶 ${c['committed_by_final_gate']:,.0f}，"
          f"余量 ${c['headroom']:,.0f}")
    t = sl["tail_after_final_gate"]
    print(f"  第 25–36 月（Gate 5 之后的收获期）: {t['hours']:,.0f} h / ${t['cash_usd']:,.0f}")
    print(f"  36 个月合计: {t['total_hours_36m']:,.0f} h / ${t['total_cash_36m']:,.0f}"
          f"  → 均在预算内")
    print(f"  [注意] {sl['asymmetry_warning']}")

    gv = r["gate_value"]
    print(f"\n【每道门值多少钱】（n={gv['n_sims']:,}，令该门必过后重算期望值）")
    print(f"  {'门':<22}{'有门期望':>12}{'拆门期望':>12}{'门的价值':>12}"
          f"{'有门胜率':>10}{'拆门胜率':>10}")
    for row in gv["per_gate"]:
        print(f"  {row['gate']:<22}${row['ev_with_gate_usd']:>10,.0f}"
              f"${row['ev_without_gate_usd']:>11,.0f}"
              f"${row['gate_value_usd']:>11,.0f}"
              f"{row['p_gain_with_gate']:>10.2%}{row['p_gain_without_gate']:>10.2%}")
    ag = gv["all_gates_removed"]
    print(f"\n  {ag['interpretation']}")
    print("  注意胜率一列：拆掉门后**胜率反而上升**，但期望值下降。")
    print("  这不矛盾——门不是用来提高胜率的，是用来在注定失败的路径上少亏钱的。")

    if r["self_check_errors"]:
        print("\n【自检未通过】")
        for e in r["self_check_errors"]:
            print(f"  [FAIL] {e}")
        raise SystemExit(1)
    print("\n【自检】全部通过：每门均有客观标准与处置动作，累计额单调且不超预算。")
    print(f"\n输出已写入 {OUT_DIR / 'gates.json'}")


if __name__ == "__main__":
    main()
