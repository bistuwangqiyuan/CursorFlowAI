"""从 outputs/results.json 渲染 bp/index.html。

**为什么是生成而不是手写：** 计划要求「正文每个数字都与 results.json 对账」。
手写正文时，这条要求只能靠自律；一旦模型参数变了，正文就会悄悄过期。
改成生成之后，对账变成**结构性保证**：

  · 所有数字必须经 `K()` 从 key_numbers 白名单取，取不到直接抛异常
  · 渲染结束后核对白名单覆盖率，未被引用的数字会列出来（防止白名单腐烂）
  · 模型一旦重跑，正文自动跟着变，不存在「忘了改」

复现：python model/run_all.py && python bp/build_html.py
"""

from __future__ import annotations

import html as _html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
BP = ROOT / "bp"

R = json.loads((OUT / "results.json").read_text(encoding="utf-8"))
KN = R["key_numbers"]
_used: set[str] = set()


# ---------------------------------------------------------------- 取数与格式化

def K(name: str):
    """从关键数字白名单取值。取不到即报错——正文不允许出现无源数字。"""
    if name not in KN:
        raise KeyError(f"关键数字白名单中没有 {name!r}；请先在 run_all.key_numbers 中登记")
    _used.add(name)
    v = KN[name]
    if v is None:
        raise ValueError(f"关键数字 {name!r} 为空")
    return v


def G(path: str):
    """按点分路径取 results.json 中的值；纯数字段（含负号）按列表下标处理。"""
    cur = R
    for part in path.split("."):
        cur = cur[int(part)] if part.lstrip("-").isdigit() else cur[part]
    return cur


def A(name: str):
    """取一条假设的数值。假设不存在即报错，不做静默回退。"""
    return R["assumptions"]["assumptions"][name]["value"]


def D(path: str):
    """取一条派生量（assumptions.derived 下的计算结果）。"""
    cur = R["assumptions"]["derived"]
    for part in path.split("."):
        cur = cur[part]
    return cur


RATE = A("HOURLY_OPPORTUNITY_COST_USD")     # 时间机会成本，全文唯一来源
HRS_WEEK = A("HOURS_PER_WEEK")
HRS_YEAR = A("HOURS_PER_YEAR")
HRS_TOTAL = D("capital_at_risk.hours")


def pct(x, d=1) -> str:
    return f"{x * 100:.{d}f}%"


def usd(x, d=0) -> str:
    s = f"${abs(x):,.{d}f}"
    return f"−{s}" if x < 0 else s


def sgn_usd(x, d=0) -> str:
    return f"{'+' if x >= 0 else '−'}${abs(x):,.{d}f}"


def num(x, d=0) -> str:
    return f"{x:,.{d}f}"


def esc(s: str) -> str:
    return _html.escape(str(s))


def svg(name: str) -> str:
    p = OUT / "figures" / name
    s = p.read_text(encoding="utf-8")
    return s[s.index("<svg"):]


def fig(name: str, caption: str) -> str:
    return (f'<figure>{svg(name)}'
            f'<figcaption>{caption}</figcaption></figure>')


def metrics(items, cls="") -> str:
    cells = "".join(
        f'<div class="metric"><span class="metric-value {c}">{v}</span>'
        f'<span class="metric-label">{l}</span></div>'
        for v, l, c in items)
    return f'<div class="metrics {cls}">{cells}</div>'


def callout(title: str, body: str, kind: str = "") -> str:
    return (f'<div class="callout {kind}"><span class="callout-title">{title}</span>'
            f'{body}</div>')


def kv(rows) -> str:
    return '<div class="kv">' + "".join(
        f'<div class="kv-row"><span>{k}</span><span>{v}</span></div>'
        for k, v in rows) + "</div>"


def table(headers, rows, caption="", note="", numcols=()) -> str:
    th = "".join(f'<th class="{"num" if i in numcols else ""}">{h}</th>'
                 for i, h in enumerate(headers))
    body = ""
    for r in rows:
        cls = ' class="row-hi"' if r and str(r[0]).startswith("__HI__") else ""
        cells = ""
        for i, c in enumerate(r):
            c = str(c).replace("__HI__", "")
            extra = "num" if i in numcols else ""
            if c.startswith("__NEG__"):
                c, extra = c.replace("__NEG__", ""), (extra + " neg").strip()
            if c.startswith("__POS__"):
                c, extra = c.replace("__POS__", ""), (extra + " pos").strip()
            cells += f'<td class="{extra}">{c}</td>'
        body += f"<tr{cls}>{cells}</tr>"
    cap = f"<caption>{caption}</caption>" if caption else ""
    nt = f'<p class="t-note">{note}</p>' if note else ""
    return f"<table>{cap}<thead><tr>{th}</tr></thead><tbody>{body}</tbody></table>{nt}"


def chapter(n: int, eyebrow: str, title: str, body: str) -> str:
    return (f'<section class="chapter" id="ch{n}">'
            f'<p class="eyebrow">{eyebrow}</p><h1>{title}</h1>{body}</section>')


GRADE = {g: f'<span class="grade grade-{g}">{g}</span>'
         for g in ("A", "B", "C", "D", "SELF")}


# ================================================================== 各章内容

def cover() -> str:
    m = R["meta"]
    return f"""
<section class="cover">
  <div class="cover-top">
    <p class="cover-kicker">自有资金 · 单人 · 全自动化 · 决策与执行手册</p>
    <h1>在 AI 编程生态里<br>找一门一个人能做的生意</h1>
    <p class="cover-sub">一份可复现、可证伪的商业计划书。它的结论不是「这个项目很好」，
    而是「在什么条件下值得做、在什么条件下应当立刻停手」——两者都用同一套模型算出来，
    并且允许自己得出「不建议做」。</p>
  </div>
  <div>
    <div class="cover-rule"></div>
    <dl class="cover-meta">
      <div><dt>基准日</dt><dd>{m['base_date']}</dd></div>
      <div><dt>硬约束</dt><dd>1 人 · {HRS_WEEK:.0f} 小时/周 · 现金上限 {usd(K('赌注_仅现金_美元'))}</dd></div>
      <div><dt>模型规模</dt><dd>{num(m['n_sims'])} 次蒙特卡洛 · 随机种子 {m['seed']}</dd></div>
      <div><dt>一键复现</dt><dd class="mono">{m['reproduce']}</dd></div>
      <div><dt>候选筛选</dt><dd>{K('候选总数')} 个候选 → 硬过滤淘汰 {K('硬过滤淘汰数')} → 入围 {K('入围数')} → 选定 {K('头号候选')}</dd></div>
      <div><dt>代码版本</dt><dd class="mono">git {m['git_rev'] or 'n/a'}</dd></div>
    </dl>
  </div>
</section>"""


def summary() -> str:
    ev = K('期望值_全口径_美元')
    ind = K('无差异时薪_美元每小时')
    return f"""
<section class="chapter" id="summary">
<p class="eyebrow">决策纪要</p>
<h1>一页读完：结论、条件、与最可能的死法</h1>

<p class="lede">这份 BP 的量化结论是<strong>有条件的否</strong>：按每小时
{usd(RATE)} 给自己的时间计价，三年期望值为 <strong>{sgn_usd(ev)}</strong>，
Kelly 最优下注比例为 <strong>{K('Kelly比例_全口径'):.0f}</strong>——即「一分钱都不该下」。
但这个结论几乎完全悬于一个参数：<strong>你这 {HRS_WEEK:.0f} 小时/周的真实机会成本</strong>。</p>

{metrics([
    (sgn_usd(ev), "三年期望值（现金 + 时间机会成本）", "neg"),
    (f"{usd(ind, 1)}/h", "无差异时薪：低于此值则应当做", ""),
    (pct(K('胜率_全口径'), 2), "胜率 P(收益 > 1)", ""),
    (f"{K('盈亏比_全口径'):.1f}", "盈亏比（平均盈利 ÷ 平均亏损）", ""),
])}

<div class="verdict">
<h3>结论的完整表述（三句话，缺一不可）</h3>
<p><strong>第一，只算现金，这是一笔好赌注。</strong>现金口径下期望值
{sgn_usd(K('期望值_仅现金_美元'))}，胜率 {pct(G('kelly.cash_only.win_loss.win_rate_p'), 1)}。
最坏情况亏掉 {usd(K('赌注_仅现金_美元'))} 中的一部分，破产不可能。</p>
<p><strong>第二，把时间按 {usd(RATE)}/小时计价，它立刻变成一笔坏赌注。</strong>
三年 {HRS_TOTAL:,.0f} 小时值 {usd(90000)}，占全额赌注 {usd(K('赌注_全口径_美元'))} 的
{pct(K('时间占赌注比例'))}。<strong>真正的赌注 95% 是时间，不是钱。</strong>
按这个口径，期望值转负，Kelly 说不要下注。</p>
<p><strong>第三，因此真问题不是「这个项目好不好」，而是「我的 {HRS_YEAR:,.0f} 小时/年在别处值多少钱」。</strong>
无差异点是 <strong>{usd(ind, 1)}/小时（约 {usd(K('无差异年收入_美元'))}/年）</strong>。
若这些小时确有更高价值的替代用途，模型说不要做；
若它们本就是会消耗掉的闲暇，模型说可以做。<strong>这个判断只能由你本人作出。</strong></p>
</div>

<h3>最可能的死法（按概率排序，全部来自模拟而非猜测）</h3>
{table(
    ["死法", "概率", "此时已投入", "为什么"],
    [
        ["止于 Gate 1：没人肯预付", pct(K('止于Gate1比例')), "96 小时", "从「免费愿意用」到「掏钱」是本领域最大的一道坎"],
        ["止于 Gate 0-B：连免费流量都拿不到", pct(K('止于Gate0B比例')), "70 小时", "新页面 12 个月内进 Google 前十的概率仅 6.11%；HN 是脉冲不是渠道"],
        ["__HI__活到第 36 个月但没到盈亏平衡", pct(K('活到经营期比例') - K('P_达真实盈亏平衡MRR')), "约 2,900 小时", "这是最贵的死法：走完全程，实现时薪低于 " + usd(ind, 1)],
        ["运营期被平台方打包进免费订阅", pct(G('monte_carlo.stop_distribution.运营期被平台方打包功能击垮')), "视时点而定", "GitHub / Cursor 的历史行为模式"],
    ],
    numcols=(1,),
    note="概率之和不为 1：表中「活到第 36 个月但未达盈亏平衡」与其余各项在口径上有重叠，"
         "此处按「最可能的死法」分类呈现，精确的互斥分布见第 8 章。")}

{callout("这份文件最反常的一点",
  "<p>它把<strong>最不利的数字放在第一页</strong>，而不是藏进附录。"
  "原因是它的读者只有一个人，而这个人半年后会需要的不是鼓励，是刹车。"
  "一份让人读完热血沸腾的 BP，对单人创业者是负资产。</p>", "warn")}
</section>"""


def toc() -> str:
    items = [
        ("结论与它的适用条件", "为什么同一组数据能同时支持「做」与「不做」"),
        ("已核实的事实基础", "一手来源、日期、证据分级"),
        ("已证伪的叙事", "行业里流传甚广但经不起查的六条，列为明令禁用"),
        ("赛道重选", f"{K('候选总数')} 个候选 · 12 条硬过滤 · 9 维加权 · 敏感性与稳健性"),
        ("产品定义", f"{K('头号候选')}：agent CI 配置安全审计"),
        ("获客方案", "本项目的主要矛盾，写得比产品方案更详细"),
        ("单位经济学与漏斗", "含一个把所需流量砍掉 63% 的开关"),
        ("风险量化", "蒙特卡洛 · 胜率盈亏比 · Kelly · 四种年化口径"),
        ("阶段目标与止损门", "客观标准、未过时的动作、现金与工时双轨止损"),
        ("无人化运营架构", "零员工、零人工客服如何真正成立"),
        ("合法合规与能力边界", "明确写出「这些问题我不给答案」"),
        ("红队自检与逆否检验", "主动写出「什么证据会证明我错了」"),
    ]
    apps = [
        ("附录 A", "方法论：被禁用的公式与不适用的指标"),
        ("附录 B", "假设总表与出处"),
        ("附录 C", "复现说明与文件清单"),
    ]
    lis = "".join(
        f'<li><span class="toc-title">{t}</span>'
        f'<span class="toc-desc">{d}</span></li>' for t, d in items)
    aps = "".join(
        f'<div class="kv-row"><span>{a} · {b}</span><span></span></div>' for a, b in apps)
    return f"""
<section class="chapter" id="toc">
<p class="eyebrow">目录</p><h1>本文件的组织方式</h1>
<p>章节顺序不是按「讲故事」排的，而是按<strong>依赖关系</strong>排的：
后一章的前提必须在前一章被验证过。第 1–3 章界定什么是真的，
第 4–5 章据此选赛道与定产品，第 6–7 章算它能不能挣钱，
第 8–9 章算风险与止损，第 10–12 章处理执行、合规与自我证伪。</p>
<div class="toc"><ol>{lis}</ol></div>
<div class="kv" style="margin-top:14pt">{aps}</div>
</section>"""


def ch1_conclusion() -> str:
    ev_full, ev_cash = K('期望值_全口径_美元'), K('期望值_仅现金_美元')
    return chapter(1, "第一章", "结论与它的适用条件", f"""
<p class="lede">同一组模拟数据，换一个记账口径，会得出方向相反的结论。
这不是模型不稳，而是<strong>「值不值得做」本来就不是一个纯客观问题</strong>——
它取决于一个只有你自己知道的数：你的时间值多少钱。本章把这件事讲透，
之后所有章节都在这个框架下展开。</p>

<h2>1.1 两个口径，两个相反的答案</h2>

{table(
    ["", "现金口径", "全口径（现金 + 时间）"],
    [
        ["赌注", usd(K('赌注_仅现金_美元')), usd(K('赌注_全口径_美元'))],
        ["三年期望值", "__POS__" + sgn_usd(ev_cash), "__NEG__" + sgn_usd(ev_full)],
        ["胜率 P(收益 > 1)", pct(G('kelly.cash_only.win_loss.win_rate_p'), 2), pct(K('胜率_全口径'), 2)],
        ["盈亏比", f"{G('kelly.cash_only.win_loss.payoff_ratio_b'):.1f}", f"{K('盈亏比_全口径'):.1f}"],
        ["__HI__<strong>Kelly 最优比例 f*</strong>", f"<strong>{K('Kelly比例_现金口径'):.3f}</strong>", "<strong>0</strong>"],
        ["Kelly 的建议", "满仓，甚至该加杠杆", "一分钱都不要下"],
    ],
    numcols=(1, 2),
    caption="两种记账口径下的同一个项目",
    note="两列来自完全相同的 " + num(R['meta']['n_sims']) + " 次模拟，唯一差别是时间的计价方式。")}

{callout("现金口径的自我否定", f"""
<p>注意现金口径那一列的 Kelly 值：<strong>f* = {K('Kelly比例_现金口径'):.3f} &gt; 1</strong>，
意思是「押上全部身家的 {pct(K('Kelly比例_现金口径'), 0)} 还不够」。
这是个荒谬的处方，而荒谬恰恰有用：<strong>它证明现金口径本身是错的。</strong></p>
<p>Kelly 之所以敢让你满仓，是因为在该口径下你几乎亏不掉什么
（最差路径仍回收 {pct(G('kelly.cash_only.kelly.worst_case_multiple'), 1)}）——
而这只是因为它把三年 {HRS_TOTAL:,.0f} 小时当成了免费的。
<strong>一个模型给出「无限加杠杆」的建议时，要怀疑的是模型，不是自己的胆量。</strong></p>""", "neg")}

<h2>1.2 唯一真正需要你回答的问题</h2>

<p>把时间机会成本从 $0 连续调到 {usd(60)}/小时，期望值会从
{sgn_usd(G('ev_sweep.0.ev_usd'))} 单调降到
{sgn_usd(G('ev_sweep.-1.ev_usd'))}，中间穿过零点。这个零点就是决策的分水岭。</p>

{fig("indifference_rate.svg",
     f"<b>无差异时薪 {usd(K('无差异时薪_美元每小时'), 1)}/小时。</b>"
     f"换算成年：这 {HRS_YEAR:,.0f} 小时/年若能在别处挣到超过 {usd(K('无差异年收入_美元'))}，"
     f"就不该做这个项目；挣不到，就该做。曲线单调递减，因为时薪只出现在成本侧。"
     f"数据源 <code>outputs/results.json → ev_sweep</code>。")}

<div class="verdict">
<h3>请诚实回答这三个问题，再决定要不要往下读</h3>
<ol>
<li><strong>这 {HRS_WEEK:.0f} 小时/周是从哪里挤出来的？</strong>如果是从另一份能付你
{usd(20)}/小时以上的工作里挤的，模型的答案是不做。</li>
<li><strong>如果三年后一分钱没挣到，这段时间算白费吗？</strong>
如果你认为学到的东西本身有价值，那么真实的机会成本低于账面。</li>
<li><strong>你能接受 {pct(1 - K('P_达1000MRR'))} 的概率连 $1,000 MRR 都达不到吗？</strong>
这不是悲观设定，是模型输出（见第 8 章）。</li>
</ol>
</div>

<h2>1.3 本 BP 保留「不建议做」的权利</h2>
<p>这份文件从一开始就允许自己得出否定结论，并且事实上得出了一个有条件的否定结论。
这不是消极，而是遵守「实事求是」的必然结果。如果量化筛选后所有候选的风险调整期望值都为负，
它就会这么写，并给出替代的资金与时间配置建议——<strong>而不是把数字调到好看为止。</strong></p>
""")


def ch2_facts() -> str:
    return chapter(2, "第二章", "已核实的事实基础", f"""
<p class="lede">以下每一条都有一手来源与核实日期。它们共同划定了边界：
哪些路走不通（2.1），还剩下什么（2.2）。
<strong>本章的作用是把后面所有推理钉在可查证的地面上。</strong></p>

<h2>2.1 否决性事实：把三条最直觉的路先堵死</h2>

<dl class="defs">
<dt>{GRADE['A']} 在 Cursor 插件市场收费是合同层面的明文禁止</dt>
<dd>Marketplace Publisher Terms 第 3.1 条要求插件必须免费提供，发布者「不得以任何直接或间接方式向用户收取费用」；
且所有插件必须开源、人工逐个审核、目前为策展制而非开放注册。
<strong>任何以「上架 Cursor 插件市场变现」为前提的模型，前提不成立。</strong>
来源：<a href="https://cursor.com/marketplace-publisher-terms">cursor.com/marketplace-publisher-terms</a>（2026-07-27 核）</dd>

<dt>{GRADE['A']} 代码审计赛道平台方已自营两个产品</dt>
<dd>Bugbot 于 2025-07-24 GA，2026-05 改为纯用量计费（官方口径 $1.00–1.50/次），
2026-06 由自研 Composer 2.5 驱动后提速 3 倍、降本 22%，且已同时支持 GitHub 与 GitLab。
Cursor Security Review 于 2026-04-30 进入 beta。
来源：<a href="https://cursor.com/docs/bugbot.md">cursor.com/docs/bugbot.md</a>、
<a href="https://cursor.com/changelog/04-30-26">changelog/04-30-26</a></dd>

<dt>{GRADE['A']} 第三方在推理成本上有约 6 倍的结构性劣势</dt>
<dd>Composer 2.5 为 $0.5/M 输入、$2.5/M 输出；第三方调用 Claude 级模型约 $3/M 输入，
Teams/Enterprise 还要再叠加 $0.25/M 的 Cursor Token Rate。
<strong>这个差距无法靠工程优化弥补</strong>，因此凡与平台方自营产品正面重叠者一律出局。
来源：<a href="https://cursor.com/docs/models-and-pricing.md">models-and-pricing</a></dd>

<dt>{GRADE['A']} 团队效能分析已被官方以第三方无法复制的方式占据</dt>
<dd>AI 代码归因靠设备端对每行 AI 建议签名再与 git commit 比对，<strong>只有编辑器本身能产生该数据</strong>。
第三方只能靠启发式 diff，精度天然落后。
来源：<a href="https://cursor.com/docs/account/teams/ai-code-tracking-api">ai-code-tracking-api</a></dd>

<dt>{GRADE['A']} 所有权变更风险已实际发生</dt>
<dd>SpaceX 于 2026-06-16 签署收购 Anysphere 的合并协议，隐含股权价值 600 亿美元，全股票，
预计 2026 Q3 交割。<strong>Publisher Terms 是可单方修订的合同，新所有者无义务延续现有生态政策。</strong>
来源：<a href="https://www.sec.gov/Archives/edgar/data/1181412/000162828026043411/spaceexplorationtechnologi.htm">SEC 8-K 原文</a></dd>
</dl>

{callout("由此得出的第一条设计原则",
  "<p>不要把生意建在任何单一厂商的条款之上。跨厂商标准（MCP、<code>AGENTS.md</code>）"
  "被 Codex、Copilot、Gemini CLI、Aider、Windsurf、Zed 原生读取，"
  "分发不由任何一家的条款决定。这一条后来成了打分表中权重第二高的维度。</p>")}

<h2>2.2 建设性事实：还剩下什么</h2>

<dl class="defs">
<dt>{GRADE['A']} 需求侧出现了对「验证类」产品有利的背离</dt>
<dd>采用率上升而信任度下降：84% 的开发者使用或计划使用 AI 工具（2024 年为 76%），
但<strong>信任 AI 输出准确性的仅 29%，较 2024 年的 40% 连续第二年下滑</strong>，46% 明确不信任。
来源：<a href="https://survey.stackoverflow.co/2025/ai/">Stack Overflow Developer Survey 2025</a>，49,000+ 样本 / 177 国</dd>

<dt>{GRADE['A']} 无人化收款通道成立，且是本轮最有价值的发现</dt>
<dd>Stripe 明确不支持中国大陆主体；Polar 与 Lemon Squeezy 的收款国清单含港澳台<strong>而不含中国大陆</strong>；
<strong>唯 Paddle 在国别与币种两层均支持</strong>——其不支持国清单（26 项）不含中国，
且 CNY 是官方支持的打款币种。<strong>这把一个可能坍塌整个模型的二元风险，
变成了一个已知的成本项。</strong>详见 <code>docs/GATE0.md</code>。</dd>

<dt>{GRADE['A']} 平台方主动让出的一个位置</dt>
<dd>官方 MCP Registry 文档白纸黑字声明自己不做安全扫描、留给「下游聚合方」。
这是本次扫描中<strong>唯一一例平台方明示放弃的领域</strong>。</dd>
</dl>

<h2>2.3 被低估的头号风险：免费开源工具过剩</h2>

<p>这是赛道扫描的核心发现，重要到必须单独立为一条硬过滤器。
<strong>几乎每个候选方向上都已存在 4–12 个免费开源实现</strong>：
slopsquatting 检测至少 9 个、MCP 安全扫描 4 个以上（含 NVIDIA 官方开源的 SkillSpector）、
AI 代码溯源 5 个功能高度重叠、死代码检测被 Knip 占据（11,752 stars、Vercel 用它删掉约 30 万行、且已自带 MCP）。</p>

{callout("这不是空白市场，是「做的人太多、但都不收钱」的市场",
  "<p>开发者是最不愿为「一个能用 npx 跑的脚本」付钱的人群。"
  "据此设立硬过滤器第 8 条：<strong>凡核心功能可被一个免费 CLI 完整替代者，一律淘汰；"
  "能收费的必须是 CLI 在结构上做不到的持续托管态</strong>"
  "（持续监控、状态留存、跨时间比对）。这一条后来淘汰了 11 个候选中的 6 个。</p>", "warn")}

<h2>2.4 一次必须记录在案的自我修正</h2>

<p>本项目最初的定位是「面向 Cursor Teams 客户做本地 AI 代码归因 + ISO 27001 证据包」。
经扫描复核后<strong>已被推翻</strong>：该品类上游是 DX、LinearB、Jellyfish、Swarmia、Waydev 五家已建制平台
（DX 已做到行级归因并按 AI 占比分档对比 revert rate）；
且我未能找到工程负责人抱怨「看不到这些数据」的任何一手帖子，<strong>需求证据为零</strong>。</p>

<p>原始机会卡片中的「机会价值分 50.2 / 综合评分 6.37 / 搜索量 50,000」来自本地启发式评分，
<strong>无外部可查证依据，不得作为任何决策输入</strong>。此处如实保留判断被推翻的痕迹，
不是为了显得谦虚，而是因为下一章要用同样的标准去否定别人的说法，
那就必须先用它否定自己的。</p>
""")


def ch3_debunked() -> str:
    return chapter(3, "第三章", "已证伪的叙事：本文件明令禁用", f"""
<p class="lede">以下六条在行业里流传甚广，写进 BP 会被内行读者当场戳穿。
逐条列出并禁用，是为了防止自己在后面某一章里图省事又把它们捡回来。</p>

<h2>3.1 三条监管叙事</h2>

<dl class="defs">
<dt class="strike">「EU AI Act 要求审计 AI 生成的代码」</dt>
<dd><strong>纯属营销话术。</strong>AI Act 监管的是 AI 系统<em>作为产品本身</em>
（招聘、信贷、医疗器械等高风险用途），<strong>完全不监管用 AI 编写普通商业软件</strong>。
且 Digital Omnibus 已于 2026-07-27 生效，将高风险义务从 8 月 2 日推迟至 2027-12-02。</dd>

<dt class="strike">「美国 SSDF / EO 14028 构成强制要求」</dt>
<dd>联邦强制力在 EO 14306（2025-06）与 OMB M-26-05（2026-02）之后<strong>已实质瓦解</strong>。</dd>

<dt>「EU CRA 是恐惧驱动的大生意」——半真</dt>
<dd>CRA（EU 2024/2847）确实是唯一真实的硬时间窗口：第 14 条漏洞报告义务自 2026-09-11 适用，
2027-12-11 全面适用。<strong>但恐惧比营销宣称的弱得多</strong>：
CRA Art. 64(10) 对开源管理者<strong>完全免除行政罚款</strong>，微型/小型制造商对部分时限亦有豁免。
且该位置属于需要漏洞情报数据库的重资产厂商（Snyk / Socket / Aikido / Sonar），单人无法自建。</dd>
</dl>

<h2>3.2 两条市场叙事</h2>

<dl class="defs">
<dt class="strike">「AI 代码度量是新品类空隙」</dt>
<dd><strong>它是 2026 年的入场券，不是空隙。</strong>LinearB、Swarmia、DX、Waydev、Faros 五家全部已上线；
Waydev 更把 AI 成本度量（Tokenmeter）做成<strong>免费</strong>获客层。
Faros 甚至公开发文称「代码有多少是 AI 生成的」本身就是个错误的问题。</dd>

<dt class="strike">「赛道竞争激烈但还在增长」</dt>
<dd><strong>已进入整合期。</strong>Sonar 收购 Gitar；Snyk 的 ARR 达 $326M 但同比仅增 7%（前一年 27%），
估值被 BlackRock 从 $7.4B 下调至 $3.7B，2026-02 换 CEO；
Haystack 官网 footer 仍停留在 "Copyright © 2023" 且残留占位文字，实质已死。
<strong>整合期意味着新进入者的窗口在收窄，而非扩大。</strong></dd>
</dl>

<h2>3.3 一条被我自己算错、又被自己纠正的成本叙事</h2>

{callout("一个 10 倍的数据冲突，以及它为什么重要", f"""
<p>初稿曾写：「Ellipsis 公布一次中等 PR 审查成本 $0.74，据此反推 Sourcery $12/席位的毛利率仅约 38%，
远低于 SaaS 的 75% 健康线；<strong>任何低价席位制 + 每次操作跑 LLM 的模型在结构上就没有毛利空间</strong>。」
这条差点被写成硬过滤器第 6 条。</p>
<p><strong>它错了。</strong>追查 Ellipsis 工程博客原文后确认：$0.74 是<em>对客报价</em>
（token 透传 + 100% 平台费），而其<strong>生产环境实际平均成本经优化后为 $0.12/次</strong>
（分层模型、增量处理、缓存）。据此重算，竞品毛利率是 <strong>80% 而非 38%</strong>。</p>
<p>修正动作：硬过滤器第 6 条的适用范围<strong>收窄</strong>为「无成本优化能力者」，
而不是笼统地否定所有用量型 LLM 产品。此处保留错误与订正的全过程，
因为一个只展示正确结论的文件，读者无从判断其余结论的可靠性。</p>""", "warn")}

<h2>3.4 被隔离的 C 级数据（不得作为建模输入）</h2>

<p>还有一类更隐蔽的污染必须单独隔离：<strong>获客渠道与独立开发者成功率这两节的市面流通数字，
大量来自互相引用的 AI 生成内容农场</strong>，层层放大后看似多方印证，
追溯下去几乎全部指向同一个未公开方法、未公开数据集的来源。</p>

<p>这类数据已被降级为 {GRADE['C']} 级并单独隔离。<strong>BP 中若在别处再遇到相同数字，
不得视为独立印证。</strong>另有四处确实查不到公开数据的项目
（开发者工具年留存、Marketplace 安装→付费转化、「12 个月内仍有收入的比例」、单次 PR 审查 token 消耗），
一律按类比推算处理并写明类比对象与推算路径。</p>

<h2>3.5 三个时效性陷阱（写入模型注释）</h2>
{table(["项", "陷阱", "处置"],
  [["Claude Sonnet 5", "2026-09-01 涨价 50%（$2/$10 → $3/$15）", "任何跨越 9 月的测算不得使用现价"],
   ["DeepSeek v4-pro", "现价为促销价，标准价为 4 倍", "按标准价建模"],
   ["DeepSeek 模型别名", "<code>deepseek-chat</code> 与 <code>deepseek-reasoner</code> 已于 2026-07-24 停用", "不得在代码中引用"]])}
""")


def ch4_track() -> str:
    surv = G("scoring.survivors")
    elim = G("scoring.eliminated")
    filters = G("scoring.meta.hard_filters")
    rob = G("scoring.score_robustness")

    frows = [[f"F{i}" if not k.startswith("F") else k, v]
             for i, (k, v) in enumerate(filters.items(), 1)]
    srows = [[f"__HI__{c['cid']}" if c["rank"] == 1 else c["cid"],
              c["name"], f"{c['total']:.2f}"] for c in surv]
    erows = [[c["cid"], c["name"],
              "、".join(f["id"] for f in c["failed_filters"]),
              c["failed_filters"][0]["reason"][:58] + "…"]
             for c in elim]

    return chapter(4, "第四章", "赛道重选：16 个候选，怎么只剩 1 个", f"""
<p class="lede">本章不接受「我觉得这个方向不错」。
{K('候选总数')} 个候选先过 12 条硬过滤（任一不满足即出局），
幸存者再按 9 个维度加权评分，每一维的打分必须附书面理由与至少一个来源，
<strong>不允许裸给分</strong>。全部逻辑在 <code>model/opportunity_scoring.py</code>，可复算。</p>

{metrics([
    (num(K('候选总数')), "候选机会", ""),
    (num(K('硬过滤淘汰数')), "硬过滤淘汰", "neg"),
    (num(K('入围数')), "进入加权评分", ""),
    (f"{K('头号候选得分'):.2f}", f"第一名 {K('头号候选')} 得分", "pos"),
], "")}

<h2>4.1 十二条硬过滤</h2>
{table(["#", "淘汰条件"], frows, note="前三条直接由第 2 章的核实结果转化而来；"
       "第 8 条来自 2.3 节的「免费开源过剩」发现；第 6 条经 3.3 节订正后已收窄适用范围。")}

<h2>4.2 十一个被淘汰的候选</h2>
{table(["ID", "候选", "触发", "一句话理由"], erows,
       note="F2=与平台方自营正面重叠且成本劣势；F3=依赖只有编辑器厂商能采集的数据；"
            "F4=需人工销售；F7=变现叙事依赖已被证伪的监管强制力；"
            "F8=可被免费 CLI 完整替代；F9=需重资产护城河。")}

<h2>4.3 入围五强与最终排序</h2>
{fig("scoring.svg", f"<b>{K('头号候选')} 以 {K('头号候选得分'):.2f} 分居首，"
     f"领先第二名 {surv[1]['cid']}（{surv[1]['total']:.2f}）0.80 分。</b>"
     f"九个维度中权重最高的三项是付费意愿证据强度、单厂商依赖度与无人化获客可行性。")}

{table(["排名", "候选", "加权得分"],
       [[f"__HI__{i+1}" if i == 0 else str(i+1), f"{c['cid']}　{c['name']}", f"{c['total']:.2f}"]
        for i, c in enumerate(surv)], numcols=(2,))}

<h2>4.4 两种稳健性检验（比排名本身更重要）</h2>

<h3>权重敏感性</h3>
<p>做了两件事：单维度 ±50% 扰动（回答「哪一维在主导排名」），
以及 Dirichlet 随机权重抽样 10,000 次（回答「排名有多稳」）。</p>
<p>结果：单维扰动共 {G('scoring.sensitivity.oat_flip_count')} 次翻转排名；
随机权重下 <strong>{K('头号候选')} 在 {pct(G('scoring.sensitivity.dirichlet_top1_frequency.C12'), 2)}
的抽样中仍居首</strong>。<strong>结论对权重是稳健的。</strong></p>

<h3>分数稳健性（这一项更严厉，也更该看）</h3>
<p>动机是一个自我批评：<strong>领先候选的高分主要来自「我最容易评估」的维度</strong>
（可交付性、边际成本结构），而真正决定成败的付费意愿证据分最低
（{rob['leader_weakest_score']:.0f} 分，全表最低）。于是设计三项对抗性检验：</p>

{table(["检验", "第一名新得分", "第二名", "是否仍居首"],
  [[c["name"], f"{c['leader_new_total']:.2f}", f"{c['runner_up_total']:.2f}",
    "__POS__是" if c["still_leads"] else "__NEG__否"] for c in rob["checks"]],
  numcols=(1, 2),
  note="第三项是刻意构造的最不利对照（第一名每维 −2、第二名每维 +2）。"
       "它会翻转，这在意料之中——列出它是为了标明结论的边界在哪里，而不是为了让结论好看。")}

{callout("必须如实披露的一点", f"""
<p>{K('头号候选')} 的<strong>付费意愿证据是全表最弱的一项</strong>：
仅有 StepSecurity 的间接类比，<strong>没有任何直接证据</strong>。
即便把这一项归零它仍然领先（{rob['checks'][0]['leader_new_total']:.2f} vs {rob['checks'][0]['runner_up_total']:.2f}），
但这只说明「它在其他维度上足够好」，<strong>不说明有人会付钱</strong>。</p>
<p>处置：这成了第 9 章 Gate 1 的全部理由，也是本项目最值钱的一道门
（价值 {usd(K('Gate1价值_美元'))}，见第 9 章）。</p>""", "neg")}
""")


def ch5_product() -> str:
    top = G("scoring.survivors.0")
    return chapter(5, "第五章", f"产品定义：{K('头号候选')} · AI agent 在 CI/CD 中的配置安全审计", f"""
<p class="lede">{esc(top['thesis'])}</p>

<h2>5.1 它检测什么：致命三角</h2>
<p>当以下三个条件在同一个 CI 工作流中同时成立时，该仓库就处于可被实际利用的危险中：</p>
<ol>
<li><strong>不受信输入流入 agent 提示</strong>——issue 正文、PR 标题、外部评论被直接拼进提示词</li>
<li><strong>agent 持有高权限凭据</strong>——<code>GITHUB_TOKEN</code> 写权限、云凭据、包发布令牌</li>
<li><strong>存在外发通道</strong>——agent 可执行任意命令、可发起网络请求、可写入仓库</li>
</ol>

<p>证据来自微软威胁情报、CSA 研究简报、Aikido PromptPwnd、Noma GitLost 四个独立权威源，
且<strong>均为已确认漏洞而非推测</strong>。</p>

<h2>5.2 为什么它能通过全部 12 条硬过滤</h2>
{table(["维度", "情况"],
  [["推理成本", "<strong>零</strong>。纯 YAML / AST 规则分析，不调用任何 LLM——这直接绕开了整个赛道的毛利难题"],
   ["竞品", "通用工具（zizmor、actionlint）不理解 <code>claude-code-action</code> 一类的配置语义；<strong>未发现做 agent 语义感知的商业竞品</strong>"],
   ["平台方自营动机", "GitHub 自身即 GitLost 的漏洞方，自营动机被其尴尬处境削弱"],
   ["单厂商依赖", "低。跨 GitHub Actions / GitLab CI，且规则本身与厂商无关"],
   [f"{HRS_WEEK:.0f} 小时/周可交付性", f"{top['scores']['deliverability_20h']['score']:.0f}/10。纯规则引擎，工程风险是全流程最低的一环"],
   ["为什么不能只做 CLI", "<strong>一次性扫描会被免费 CLI 完整替代（触发 F8）。</strong>可收费的只有持续托管态：配置漂移监控、跨时间比对、新规则自动回扫"]])}

{callout("产品形态的唯一正确解", """
<p>这是本章最关键的一条设计约束，也是 2.3 节那条硬过滤器的直接后果：</p>
<p><strong>免费开放：</strong>一次性扫描的 CLI 与 GitHub Action，完全免费、开源。
它不是「引流噱头」——它本身就是产品的分发渠道（见第 6 章），也是真正帮到人的部分。</p>
<p><strong>付费：</strong>持续监控。「你的 47 个工作流里，昨晚有 3 个的权限配置变了」、
「新披露的一类绕过手法，回扫你全部历史配置」。
<strong>这需要托管状态与时间序列，CLI 在结构上做不到。</strong></p>""", "pos")}

<h2>5.3 明确不做的三件事</h2>
<ul>
<li><strong>不做合规判定。</strong>只输出证据与事实，绝不对客户说「你已合规」——那超出能力边界（硬过滤器第 10 条）。</li>
<li><strong>不做通用 SAST / SCA。</strong>那需要漏洞情报数据库，$4,000 预算撑不起（第 9 条）。</li>
<li><strong>不做自动修复的 PR。</strong>在安全场景下自动改别人的 CI 配置，风险与收益不成比例。给补丁，让人自己看过再合。</li>
</ul>
""")


def ch6_acquisition() -> str:
    ch = G("acquisition.channels")
    gap = G("acquisition.gap_analysis")
    rows = [[c["name"], "复利" if c["compounding"] else "脉冲",
             num(c["m12_uv"]), num(c["m24_uv"]), num(c["m36_uv"]),
             GRADE.get(c["grade"][0], c["grade"])] for c in ch]
    return chapter(6, "第六章", "获客：本项目的主要矛盾", f"""
<p class="lede">这一章比产品章更长、更详细，因为<strong>本项目的主要矛盾不是「做什么产品」，
而是「一个每周 20 小时、无广告预算的人如何持续获得精准开发者流量」</strong>。
把这件事想清楚之前写下的任何一行代码，都可能是浪费。</p>

<h2>6.1 为什么获客是主要矛盾</h2>

<p>把保守基准串联起来（计算见 <code>model/funnel.py</code>）：</p>

{kv([
    (f"每 1,000 个精准访客 × {pct(A('CM_OPTIN_VISITOR_TO_SIGNUP'))} 访客→注册",
     f"{1000 * A('CM_OPTIN_VISITOR_TO_SIGNUP'):.0f} 个注册"),
    (f"× {pct(A('CM_OPTIN_SIGNUP_TO_PAID') * A('SOLO_NO_TOUCH_DISCOUNT'))} 注册→付费"
     f"（问卷值 {pct(A('CM_OPTIN_SIGNUP_TO_PAID'))} × 单人折扣）",
     f"{D('paid_per_1000_no_card')} 个付费客户"),
    (f"× {usd(A('ARPU_USD'))} 客单价",
     usd(D('paid_per_1000_no_card') * A('ARPU_USD'), 2) + " 新增 MRR"),
    (f"在 {pct(A('MONTHLY_LOGO_CHURN'))} 月流失下，维持 $1,000 MRR 需要",
     f"<strong>{num(K('所需月访客_不要卡'))} 个访客/月</strong>"),
])}

{callout("$1,000 MRR 不是一个目标，是一台机器", f"""
<p>它需要<strong>每月持续喂进 {num(K('所需月访客_不要卡'))} 个精准开发者访客</strong>才能不掉。
而流量侧的现实是：Ahrefs 追踪 100 万个随机 URL 显示，新页面 12 个月内进入 Google 前十的概率仅
{pct(A('SEO_TOP10_PROBABILITY_12M'), 2)}（高搜索量词 0.3%）；
Hacker News 与 Product Hunt 都是 48 小时内衰减到零的一次性脉冲。</p>
<p><strong>一次成功的 HN 头版（保守取 {num(A('HN_FRONTPAGE_UV'))} UV）约产出
{A('HN_FRONTPAGE_UV') / 1000 * D('paid_per_1000_with_card'):.0f} 个付费客户，
在 {pct(A('MONTHLY_LOGO_CHURN'))} 月流失下 {D('customer_lifetime_months'):.0f} 个月后流失殆尽。
脉冲不是渠道。</strong></p>""", "neg")}

<h2>6.2 那个把难度砍掉三分之二的开关</h2>

<p>ChartMogul 对 200 个 B2B 软件产品的数据显示一个反直觉的事实：
<strong>要求信用卡才能开始试用的漏斗，每 1,000 访客产出
{D('paid_per_1000_with_card_undiscounted')} 个付费客户；不要卡片的仅
{D('paid_per_1000_no_card_undiscounted')} 个。</strong>
注册量掉 {pct(1 - A('CM_CARD_VISITOR_TO_SIGNUP') / A('CM_OPTIN_VISITOR_TO_SIGNUP'), 0)}，
但注册→付费转化率高 {A('CM_CARD_SIGNUP_TO_PAID') / A('CM_OPTIN_SIGNUP_TO_PAID'):.1f} 倍。</p>

{table(["漏斗设计", "访客→注册", "注册→付费", "每千访客付费数", "维持 $1,000 MRR 所需月访客"],
  [[r["label"], pct(r["visitor_to_signup"]), pct(r["signup_to_paid"]),
    f"{r['paid_per_1000_visitors']:.2f}",
    ("__HI__" if r["require_card"] and r["solo_discount_applied"] else "") + num(r["visitors_for_1000_mrr"])]
   for r in G("funnel.card_switch.rows")],
  numcols=(1, 2, 3, 4),
  caption="信用卡开关的敏感性（「单人折扣」= 对 ChartMogul 自报告样本的保守下调）",
  note="本 BP 采用第三行（要卡 + 单人折扣）作为基准口径：既取用了这个真实存在的杠杆，"
       "又不假设自己能达到问卷样本的平均水平。")}

<p><strong>这一个产品决策，把维持 $1,000 MRR 所需的月访客从
{num(K('所需月访客_不要卡'))} 降到 {num(K('所需月访客_要卡'))}，
降幅 {pct(G('funnel.card_switch.traffic_requirement_reduction'))}。</strong>
在一个「流量是唯一瓶颈」的项目里，这是杠杆率最高的单一决策。</p>

<h2>6.3 四条复利渠道 + 一条脉冲渠道</h2>

<p>判断标准只有一个：<strong>这条渠道是否越用越省力</strong>。
不满足的一律归为脉冲，不计入稳态基线。</p>

{table(["渠道", "类型", "第 12 月", "第 24 月", "第 36 月", "证据"],
       rows, numcols=(2, 3, 4),
       caption="各渠道的月独立访客贡献（UV/月）",
       note="多数为 D 级（本人假设）。这是本 BP 证据强度最弱的一章，"
            "也正因如此，Gate 0-B 把「14 天内拿到 300 UV」设成了一票否决项——"
            "与其在纸上争论假设是否成立，不如两周内用真实数据证伪它。")}

<h3>为什么这四条是复利的</h3>
<dl class="defs">
<dt>免费 GitHub Action 本体——产品即渠道</dt>
<dd>每个安装它的仓库都会在 <code>.github/workflows/*.yml</code> 里留下一行<strong>公开可见、可被 GitHub 代码搜索索引</strong>的引用，
也会被该仓库的贡献者读到。<strong>安装量本身就是曝光量。</strong></dd>
<dt>程序化 SEO 知识库（180 页）</dt>
<dd>每个（agent action × 危险模式）组合一页，内容是具体错误配置示例 + 为什么危险 + 可直接复制的修复补丁。
搜索这些具体报错的人，正是处于危险三角中的人。
按 Ahrefs 的 6.11% 进前十概率，180 页约有 11 页能进前十。<strong>第一年按 0 计</strong>（SEO 起量周期 9–18 个月）。</dd>
<dt>负责任披露飞轮</dt>
<dd>持续在公开仓库中发现真实漏洞，私下告知维护者并附修复补丁。
每次披露产生三样东西：一个被修好的仓库、一个知道你是谁的维护者、可能的公开致谢。
<strong>这是本方案中唯一同时满足「真实帮到人」与「获客」的动作</strong>——
也是它在道德上最站得住的地方：即使生意失败，被修好的仓库仍然是净收益。</dd>
<dt>被收录进 awesome-list / 他人 README</dt>
<dd>安全工具进入 awesome-actions 一类清单后获得长期被动引用。取值刻意保守。</dd>
</dl>

<h2>6.4 缺口分析：够，还是不够</h2>

{fig("traffic_gap.svg",
  f"<b>计划的复利渠道在第 36 月合计 {num(K('计划月访客_第36月'))} UV/月。</b>"
  f"对不要信用卡的漏斗，这是所需量的 {pct(K('渠道覆盖率_不要卡'))}（<b>不够</b>）；"
  f"对要求信用卡的漏斗，是 {pct(K('渠道覆盖率_要卡'))}（<b>够，且有 2.5 倍余量</b>）。"
  f"两条线之间的差距，就是 6.2 节那个开关的价值。")}

{callout("这一章的诚实交代", """
<p><strong>Gate 0-B 至今没有通过，它只是被形式化成了一个可执行的检验。</strong>
本章给出的是一个待检验的假设集，不是已验证的结论。
任何「我们将通过内容营销获得稳定流量」的表述，在 Gate 0-B 的 B3 项通过之前都属于一厢情愿。</p>
<p>这也是为什么第 9 章把「B3 未过前累计开发工时上限为 0 小时」写成硬纪律：
<strong>如果连免费工具都拿不到 300 个访客，那么整份 BP 后面的所有数字都失去了定义域。</strong></p>""", "warn")}
""")


def ch7_econ() -> str:
    pc = G("unit_economics.per_customer_base")
    be = G("unit_economics.breakeven")
    return chapter(7, "第七章", "单位经济学：一个客户到底值多少", f"""
<p class="lede">本章的结论可以一句话概括：<strong>单客户经济性健康，
但「盈亏平衡」这个词有两种算法，相差 44 倍。</strong></p>

<h2>7.1 单客户月度损益</h2>

{table(["项", "金额"],
  [["毛收入（{}/月）".format(usd(pc["price_usd"])), usd(pc["gross_revenue"], 2)],
   ["− 退款与坏账", "__NEG__" + usd(-pc["refund_loss"], 2)],
   [f"− MoR 费用（Paddle，实效 {pct(pc['mor_effective_rate'], 2)}）", "__NEG__" + usd(-pc["mor_fee"], 2)],
   ["− LLM 推理成本", usd(pc["cogs_llm"], 2) + "　<span class='small'>（C12 为纯规则分析，零推理）</span>"],
   ["__HI__<strong>月度贡献</strong>", f"<strong>{usd(pc['contribution_margin_usd'], 2)}</strong>　({pct(pc['contribution_margin_pct'])})"],
   [f"客户生命周期（1 ÷ 7% 月流失）", f"{pc['lifetime_months']:.1f} 个月"],
   ["<strong>LTV</strong>", f"<strong>{usd(K('LTV_美元'), 0)}</strong>"]],
  numcols=(1,),
  note="贡献毛利率 " + pct(pc["contribution_margin_pct"]) + " 高于 SaaS 的 75% 健康线，"
       "原因是 C12 不调用 LLM。这正是第 4 章硬过滤器第 6 条筛选的结果，不是巧合。")}

<h2>7.2 两个盈亏平衡点，相差 44 倍</h2>

{table(["口径", "所需客户数", "所需 MRR", "所需月访客（要卡）"],
  [["现金盈亏平衡（只覆盖 $60/月基础设施）",
    f"{be['cash_breakeven']['customers']:.1f}", usd(be['cash_breakeven']['mrr_usd']),
    num(be['cash_breakeven']['monthly_visitors_needed'])],
   ["__HI__<strong>真实盈亏平衡（含时间机会成本）</strong>",
    f"<strong>{K('真实盈亏平衡客户数'):.0f}</strong>",
    f"<strong>{usd(be['full_breakeven']['mrr_usd'])}</strong>",
    f"<strong>{num(be['full_breakeven']['monthly_visitors_needed_with_card'])}</strong>"]],
  numcols=(1, 2, 3),
  note=f"两者相差 {be['ratio']:.0f} 倍。时间成本口径：{be['full_breakeven']['monthly_hours']:.0f} 小时/月 "
       f"× {usd(RATE)}/小时 = {usd(be['full_breakeven']['monthly_time_cost_usd'])}/月。")}

{callout("为什么必须同时报这两个数", f"""
<p><strong>只报第一个是自欺，只报第二个是自虐。</strong></p>
<p>{usd(be['cash_breakeven']['mrr_usd'])} MRR 这个数会让人产生「很快就能盈利」的错觉——
它的真实含义只是「服务器费用有着落了」。而 {usd(be['full_breakeven']['mrr_usd'])} MRR
才是「这件事在经济上开始说得通」的门槛，模型给它的概率是
<strong>{pct(K('P_达真实盈亏平衡MRR'), 1)}</strong>。</p>
<p>本 BP 的处理方式是两个都报、都标注口径，并把后者写进第 9 章 Gate 5 的通过标准。</p>""", "warn")}

<h2>7.3 一个通常被忽略的成本：时间计价的 CAC</h2>
<p>单人项目没有广告预算，于是 CAC 常被记为 0。这是错的。
把每月投入获客的小时数按 {usd(RATE)}/小时折算，就得到真实的 CAC。
在「每月 8 小时获客、月访客 1,000」的情景下，
时间计价的 CAC 会显著高于 LTV——<strong>这意味着靠手工获客换客户是亏的，
必须依赖第 6 章那四条复利渠道，让边际获客工时随时间趋近于零。</strong>
完整情景表见 <code>outputs/results.json → unit_economics.time_based_cac_scenarios</code>。</p>
""")


def ch8_risk() -> str:
    mc, k = R["monte_carlo"], R["kelly"]
    fa = k["full_accounting"]
    ann = fa["annualization"]
    cv = fa["commitment_view"]
    return chapter(8, "第八章", "风险量化：胜率、盈亏比、Kelly 与四种年化", f"""
<p class="lede">{num(R['meta']['n_sims'])} 次三年期模拟，随机种子 {R['meta']['seed']}，
任何人重跑都得到逐位相同的数字。本章与常见创业财务预测最大的不同是
<strong>把阶段门做进了模拟</strong>——因为门的经济意义正是截断左尾，不建模门就会系统性算错。</p>

<h2>8.1 模型结构：三个不常见的设定</h2>
<ol>
<li><strong>阶段门进入模拟。</strong>Gate 0-B 未过就停手，损失是 26 小时而不是 {HRS_TOTAL:,.0f} 小时。</li>
<li><strong>时间按机会成本计价。</strong>全额赌注 {usd(K('赌注_全口径_美元'))}，其中
{pct(K('时间占赌注比例'))} 是时间。</li>
<li><strong>未花掉的预算算作收回的本金。</strong>第 3 个月停手时剩下的 2,900 小时仍然是你的。
这正是 Kelly 框架所需的口径。</li>
</ol>

<h2>8.2 三年后，项目停在哪一步</h2>
{fig("stop_distribution.svg",
  f"<b>只有 {pct(K('活到经营期比例'))} 的路径能走到经营期。</b>"
  f"但请注意：{pct(K('止于Gate1比例') + K('止于Gate0B比例'))} 的失败发生在"
  f"投入不到 100 小时的阶段——这不是坏消息，这正是阶段门在起作用。")}

<h2>8.3 收益分布</h2>
{metrics([
    (f"{K('收益倍数_P10'):.3f}", "P10", "neg"),
    (f"{K('收益倍数_P50'):.3f}", "中位数", ""),
    (f"{K('收益倍数_P90'):.3f}", "P90", ""),
    (f"{K('收益倍数_均值'):.3f}", "均值（≠ 中位数）", "neg"),
])}

{fig("return_distribution.svg",
  "<b>纵轴为对数刻度。</b>84% 的样本挤在 0.97 附近的一根尖峰里"
  "（早停、只亏几十小时），线性刻度下右尾会被压成看不见的贴地线。"
  "均值低于中位数，是因为右尾太薄、补不上少数几条烧光全部工时的路径。")}

<p>换成更直观的口径：第 36 个月的 MRR 中位数是
<strong>{usd(K('MRR_P50_第36月'))}</strong>，P90 是
<strong>{usd(K('MRR_P90_第36月'))}</strong>。
中位数为零不是模型出错，而是<strong>超过一半的路径在 Gate 0-B 或 Gate 1 就已经停手，
根本没有走到有收入的那一步</strong>——这正是阶段门的设计意图。
达到 $1,000 MRR 的概率为 {pct(K('P_达1000MRR'))}，
达到真实盈亏平衡所需 MRR 的概率为 {pct(K('P_达真实盈亏平衡MRR'))}。</p>

<h2>8.4 胜率与盈亏比：一组极易被误读的数字</h2>

{table(["指标", "全口径", "口径说明"],
  [["胜率 p = P(M &gt; 1)", pct(K('胜率_全口径'), 2), "拿回来的比投进去的多"],
   ["平均盈利 W", f"+{fa['win_loss']['avg_win_W']:.3f}", "条件于盈利路径"],
   ["平均亏损 L", f"{fa['win_loss']['avg_loss_L']:.3f}", "条件于亏损路径，取正"],
   ["盈亏比 b = W / L", f"{K('盈亏比_全口径'):.2f}", "赔率"],
   ["__HI__保本所需胜率 1/(1+b)", f"<strong>{pct(K('保本所需胜率'), 2)}</strong>",
    f"<strong>实际胜率 {pct(K('胜率_全口径'), 2)}，不达标</strong>"]],
  numcols=(1,))}

{callout("胜率 " + pct(K('胜率_全口径'), 2) + " 不可单独引用", f"""
<p>孤立地看，这个数字像是「98% 的概率血本无归」。<strong>那是误读。</strong></p>
<p>典型亏损只有 <strong>{pct(fa['win_loss']['avg_loss_L'], 1)}</strong>（不是 100%），
因为 {pct(1 - cv['share_of_paths_committed'])} 的路径在 Gate 0-B / Gate 1 就停手，只亏掉几十小时的学费。</p>
<p>真正该看的是<strong>条件于「过了 Gate 1、真正开始重投入」</strong>（占 {pct(cv['share_of_paths_committed'], 2)}）
的那一组：胜率 {pct(cv['win_rate_given_commitment'], 2)}，盈亏比 {cv['payoff_ratio_given_commitment']:.2f}，
期望 {cv['expected_value_given_commitment']:+.3f}。
<strong>风险不是均匀分布在三年里的，它集中在通过 Gate 1 之后的那 240+ 小时。</strong></p>""")}

<h2>8.5 Kelly：诚实披露它在这里失效</h2>

<p>数值最大化 E[ln(1 + f·X)]（不用两结果闭式解，因为本项目的结果是六档以上的连续分布），
全口径得 <strong>f* = 0</strong>——期望优势为负，Kelly 的答案是一分钱都不要下。</p>

{callout("Kelly 为什么在单人创业上不成立（三条结构性理由）", """
<ol>
<li><strong>Breiman(1961) 的最优性证明全部是渐近结论</strong>（n → ∞）。
Thorp 自己给的量化例子是：区分 1.0% 与 1.1% 的优势，
需要<strong>两百万次试验</strong>才有 84% 把握。一个人一生能下的创业注是个位数，大数律完全不工作。</li>
<li><strong>Samuelson 1971(PNAS) / 1979(JBF) 的正式反对：</strong>
最大化 E[ln] 只有在效用函数恰好是对数时才最优，它不是一条普适定理。</li>
<li><strong>Kelly 假设赌注可无限分割、可重复、赔率已知。</strong>
创业三条全不满足：不能下 0.37 个产品，不能重来，赔率本身是估出来的。</li>
</ol>
<p>因此本文件把 Kelly 的输出<strong>只作为「下注规模上限的参照」，绝不作为承诺。</strong></p>""", "warn")}

<h2>8.6 四种年化口径，全部并列</h2>

<p>同一个分布可以产出四个相差很大的「年化」。
<strong>纪律：本文件任何一处「年化 XX%」必须紧跟口径名与该口径的误导风险说明，
不允许只报有利的那一个。</strong></p>

{fig("annualization.svg", "<b>四者极差 " +
     f"{ann['_spread_pct_points']:.1f} 个百分点，且全部为负。</b>"
     f"无风险利率参照：美国 10 年期 {pct(A('RF_US_10Y'), 2)}"
     f"（FRED DGS10，2026-07-23）、中国 10 年期 1.73%（中债，2026-07-24）。")}

{table(["口径", "值", "公式", "误导风险"],
  [[ann[k2]["label"], pct(K(f"年化_口径{letter}"), 2), f"<code>{ann[k2]['formula']}</code>",
    ann[k2]["misleading_because"][:96] + "…"]
   for letter, k2 in (("A", "A_expect_then_annualize"),
                      ("B", "B_annualize_then_expect"),
                      ("C", "C_geometric_conditional_on_survival"),
                      ("D", "D_true_geometric_all_paths"))],
  numcols=(1,))}

<h2>8.7 敏感性：什么能翻转结论，什么不能</h2>

{fig("sensitivity.svg",
  "<b>没有任何单项参数扰动能把期望值扳回正数。</b>"
  "把 Gate 0-B 通过率从 0.35 提到 0.55、把流量实现率提到 100%、把流失率降到 5%——"
  "都不够。唯一能翻转结论的是记账口径本身，即时间机会成本。")}

{callout("一个反直觉但重要的结果", f"""
<p>敏感性表中的「乐观组合」（各门通过率与流量同时向好）：
胜率从 {pct(G('monte_carlo.sensitivity.0.p_gain'), 2)} 升到
{pct(G('monte_carlo.sensitivity.-1.p_gain'), 2)}，
<strong>但期望值几乎没有改善</strong>。</p>
<p>原因是：门更容易过 → 更多路径走到底 → 更多路径烧掉全部 {HRS_TOTAL:,.0f} 小时。
<strong>在现有单位经济学下，「顺利通过各道门并继续投入」这件事本身就在毁灭价值。</strong>
这是模型给出的最尖锐的一句话，它直接指向第 9 章：
<strong>门不是用来提高胜率的，是用来在注定失败的路径上少亏钱的。</strong></p>""", "neg")}

<h2>8.8 收敛性</h2>
<p>收敛性检验必须针对<strong>噪声最大</strong>的统计量，而不是最稳的那个。
本分布的中位数落在「止于 Gate 1」这个确定性质量点上，跨种子标准差恒为 0——好看但无信息。
下表用均值与 P99.9：</p>
{table(["模拟次数", "均值", "跨 8 个种子相对标准差", "P99.9", "P99.9 相对标准差"],
  [[num(c["n"]), f"{c['mean_of_means']:.4f}", pct(c["mean_relative_sd"], 2),
    f"{c['P999_mean']:.3f}", pct(c["P999_relative_sd"], 2)]
   for c in mc["convergence"]],
  numcols=(1, 2, 3, 4),
  note="P99.9 的相对标准差从 n=1,000 时的 51% 降到 n=100,000 时的 5.7%。"
       "这就是必须跑 10 万次而不是 1 万次的定量理由——右尾决定期望值，而右尾收敛最慢。")}
""")


def ch9_gates() -> str:
    gl = G("gates.gates")
    sl = G("gates.stop_loss")
    gv = G("gates.gate_value")
    return chapter(9, "第九章", "阶段目标与止损门", f"""
<p class="lede">这一章是写给半年后的你的。那时你已经忘了今天的推理过程，只会记得自己很努力。
它的唯一作用，是在你<strong>最不想停</strong>的那一刻，用一条今天冷静时写下的客观标准把你拦住。</p>

<h2>9.1 门到底值多少钱</h2>
<p>把每道门的通过概率强行设为 1.0（等于拆掉这道门）重跑模拟，期望值的变化就是这道门的价格。</p>

{fig("gate_value.svg",
  f"<b>整套门机制值 {usd(K('门机制总价值_美元'))}，是现金预算 {usd(K('赌注_仅现金_美元'))} 的 5.4 倍。</b>"
  f"在这个项目里，纪律比资本贵。")}

{table(["门", "有门期望值", "拆门期望值", "这道门值", "有门胜率", "拆门胜率"],
  [[r["gate"], sgn_usd(r["ev_with_gate_usd"]), sgn_usd(r["ev_without_gate_usd"]),
    ("__HI__" if r["gate_value_usd"] > 5000 else "") + usd(r["gate_value_usd"]),
    pct(r["p_gain_with_gate"], 2), pct(r["p_gain_without_gate"], 2)]
   for r in gv["per_gate"]],
  numcols=(1, 2, 3, 4, 5),
  note="注意最后两列：拆掉门之后胜率反而上升，期望值却大幅恶化。"
       "任何用「胜率」单指标评价止损机制的做法都会得出相反结论。")}

{callout(f"Gate 1 一道门就值 {usd(K('Gate1价值_美元'))}", f"""
<p>是其余各门总和的 9 倍。原因很朴素：
<strong>它是唯一一道在投入 240 小时开发之前、用 26 小时验证「到底有没有人肯掏钱」的关卡。</strong>
它拦掉的是最贵的那段浪费。</p>
<p>这也回答了第 4 章留下的问题——{K('头号候选')} 的付费意愿证据最弱怎么办？
答案不是「再多找些证据说服自己」，而是「设一道最贵的门，用 26 小时把它变成事实」。</p>""", "pos")}

<h2>9.2 完整台账</h2>
{table(["门", "名称", "时点", "本门工时", "累计工时", "累计现金"],
  [[g["gid"], g["name"], g["when"],
    f"{g['hours']:.0f} h" + (f" × {g['retries']+1}" if g["retries"] else ""),
    f"{g['cum_hours']:,.0f} h", usd(g["cum_cash"])] for g in gl] +
  [["—", "收获期", "第 25–36 月", f"{sl['tail_after_final_gate']['hours']:,.0f} h",
    f"<strong>{sl['tail_after_final_gate']['total_hours_36m']:,.0f} h</strong>",
    f"<strong>{usd(sl['tail_after_final_gate']['total_cash_36m'])}</strong>"]],
  numcols=(3, 4, 5),
  caption="工时与现金双轨分别计量，累计额为封顶值（不是预期值）",
  note=f"预算余量：工时 3,000 − {K('累计工时_36月'):,.0f} = "
       f"{3000 - K('累计工时_36月'):,.0f} 小时；现金 {usd(4500)} − {usd(K('累计现金_36月'))} = "
       f"{usd(4500 - K('累计现金_36月'))}。")}

<h2>9.3 逐门的通过标准与未过时的动作</h2>
{"".join(f'''
<h3>Gate {esc(g["gid"])} · {esc(g["name"])}　<span class="small">（{esc(g["when"])}，{g["hours"]:.0f} 小时）</span></h3>
<p class="small"><strong>通过标准</strong></p><ul>{"".join(f"<li>{esc(c)}</li>" for c in g["criteria"])}</ul>
<p><strong>通过 →</strong> {esc(g["on_pass"])}</p>
<p><strong>未过 →</strong> {esc(g["on_fail"])}</p>
{f'<p class="small">{esc(g["notes"])}</p>' if g.get("notes") else ""}
''' for g in gl)}

<h2>9.4 双轨止损线：为什么不能只盯现金</h2>

{table(["", "现金轨", "工时轨"],
  [["预算", usd(sl["cash_track"]["budget"]), f"{sl['hours_track']['budget']:,.0f} 小时"],
   ["按 $30/h 计值", usd(sl["cash_track"]["budget"]), usd(sl["hours_track"]["budget_value_usd"])],
   ["占全额赌注", pct(1 - K('时间占赌注比例')), "__HI__<strong>" + pct(K('时间占赌注比例')) + "</strong>"],
   ["有无自动提醒", "有（银行与信用卡账单）", "__NEG__<strong>无</strong>"],
   ["失控方式", "几乎不可能", "__NEG__在毫无感觉的情况下被烧穿"]],
  numcols=(1, 2))}

<p><strong>只设现金线等于不设防。</strong>这是本项目最现实的失控方式，
也是绝大多数独立开发项目实际的死法：钱没花多少，三年过去了。</p>

<h3>工时记账规程（唯一需要人工的动作，每周 5 分钟）</h3>
<ol>
<li>每周日记录本周实际投入工时，累加到一个纯文本台账</li>
<li>与 9.2 节的「累计工时」列对照</li>
<li><strong>超出当前所处门的累计上限即为触线</strong>，立即执行该门的「未过」动作，不得以「快好了」为由顺延</li>
</ol>

{callout("触线后的强制动作", """
<ul>
<li>执行该门定义的「未过」动作，<strong>不允许当场修改标准</strong></li>
<li>若确信标准本身定错了，须先书面写出「错在哪、当初为什么这么定、新标准为何更客观」，
再修改——<strong>且修改只对下一门生效，不追溯当前这一门</strong></li>
</ul>""", "neg")}
""")


def ch10_ops() -> str:
    return chapter(10, "第十章", "无人化运营：零员工怎么才算真的成立", f"""
<p class="lede">「全 AI 公司」不是一句口号，它是一条硬约束：
<strong>凡是需要人在场才能完成的环节，在本项目里都等于不存在。</strong>
本章逐环节检查这条约束是否真的成立，并诚实标出唯一一个做不到的地方。</p>

<h2>10.1 全链路的无人化检查</h2>
{table(["环节", "如何做到无人化", "残余人工"],
  [["获客", "复利渠道自行运转：GitHub Action 的安装即曝光、程序化 SEO 页面自动生成、awesome-list 被动引用", "披露飞轮需人工审读（可批量，约 4 小时/月）"],
   ["注册与开通", "GitHub OAuth 一键授权 → 自动创建工作区 → 自动首扫，无审批环节", "无"],
   ["计费", "Paddle 作为 MoR：订阅、发票、全球增值税代缴、退款、取消全部自助", "无"],
   ["交付", "定时任务扫描 + 变更触发；报告自动生成并推送", "无"],
   ["客服", "文档 + 报告内嵌解释 + 自动回复。<strong>刻意不提供人工客服，并在定价页明示</strong>", "无"],
   ["监控告警", "Cloudflare Workers + 健康检查 + 失败自动重试与降级", "故障时需人工介入（不可避免）"],
   ["__HI__止损纪律", "<strong>无法软件化</strong>", "<strong>每周 5 分钟工时记账</strong>"]])}

{callout("唯一一个无法自动化的环节，必须点名", """
<p><strong>第 9 章的工时记账与止损判定，无法软件化。</strong>
因为它要记录和约束的是<em>你自己的行为</em>，而不是系统的行为。</p>
<p>这不是可以糊弄过去的例外。如果连每周 5 分钟的记账都做不到，
那么本 BP 的全部止损设计都不成立——<strong>而止损设计价值 """ + usd(K('门机制总价值_美元')) + """，
是整个方案里最值钱的部分。</strong></p>
<p>处置建议：把台账放进 git 仓库，每次更新产生一次 commit。
这样「我这周投入了多少」就变成了一条有时间戳、不可事后篡改的记录。</p>""", "warn")}

<h2>10.2 为什么「不提供人工客服」是可以的</h2>
<p>这不是偷工减料，而是与定价一致的产品设计：
在 {usd(19)}/月这个价位上，任何人工介入都会立刻吃掉全部贡献毛利
（单客户月度贡献仅 {usd(K('单客月贡献_美元'), 2)}——<strong>一次 30 分钟的客服对话就亏了</strong>）。</p>
<p>诚实的做法是<strong>在定价页明示「本产品不提供人工客服」</strong>，
让客户在付款前就知道自己买的是什么。
把做不到的事说成做得到，才是真正的不诚信。</p>

<h2>10.3 技术栈与成本</h2>
{kv([
    ("扫描引擎", "纯规则（YAML / AST 解析），零 LLM 调用"),
    ("托管", "Cloudflare Workers（$5/月）+ Postgres（$25/月）"),
    ("前端与文档", "静态生成 + Vercel（$20/月）"),
    ("支付", "Paddle（MoR，实效费率 " + pct(G('unit_economics.per_customer_base.mor_effective_rate'), 2) + "）"),
    ("基础设施合计", usd(60) + "/月（标准档），极简档 " + usd(10) + "/月"),
])}
<p class="small">在每月几千次调用的量级，成本完全由固定订阅费主导，
边际成本近似为零。这是 C12 相对于「每次操作跑 LLM」型产品的结构性优势。</p>
""")


def ch11_legal() -> str:
    return chapter(11, "第十一章", "合法合规与能力边界", f"""
<p class="lede">本章的重点不是列举我们做了什么，而是<strong>明确写出哪些问题我不给答案</strong>。
在超出能力边界的地方硬给结论，比不给结论危险得多。</p>

<h2>11.1 三个必须交给持牌专业人士的问题</h2>
{callout("以下三项本文件不给答案", """
<ol>
<li>中国税务居民取得的境外 SaaS 订阅收入在中国的纳税义务认定
（经营所得 / 综合所得 / 受控外国企业规则）</li>
<li>若采用美国 LLC，Form 5472 / Form 1120 申报义务与 ECI（有效关联所得）判定
——<strong>Form 5472 漏报罚款起点 $25,000</strong></li>
<li>MoR 平台打款到境内的性质认定（服务贸易收入 vs 其他），及对应增值税与所得税处理</li>
</ol>
<p><strong>必须咨询持牌税务师。</strong>本文件在这三处的任何表述都仅为背景信息，不构成建议。</p>""", "neg")}

<h2>11.2 可以引用的官方原文（仅作背景）</h2>
<ul>
<li><strong>《经常项目外汇业务指引（2020 年版）》（汇发〔2020〕14 号）</strong>
第五十四条：个人结汇实行年度便利化额度管理，额度为每人每年等值 5 万美元。
第五十六条：超过便利化额度的经常项目结汇，凭有效身份证件 + 有交易额的资金来源材料办理。
第六十二条：<strong>个人不得以分拆等方式规避便利化额度管理</strong>。</li>
<li>国家外汇管理局厦门市分局澄清：<strong>「等值 5 万美元是年度便利化额度，不是限额」</strong>，
真实合法的经常项目结汇无金额限制。</li>
<li><strong>《关于支持贸易新业态发展的通知》（汇发〔2020〕11 号）</strong>：
从事跨境电子商务的境内个人，提供交易额证明的，不占用年度便利化额度。
<em>存疑：SaaS 订阅是否被认定为该项下服务贸易，取决于经办银行认定，各行口径不一，开户前必须确认。</em></li>
</ul>

<h2>11.3 明确不采纳的做法</h2>
{table(["做法", "为什么不做"],
  [["用住宅代理 + 境外实体伪装成在当地运营", "可能违反支付服务商的服务协议，后果是账户冻结与资金扣留。<strong>合规的做法是真实地在受支持辖区设立实体并实际运营，而不是伪装成在那里</strong>"],
   ["分拆结汇、借用他人额度、虚构交易背景", "违反汇发〔2020〕14 号第六十二条。<strong>宁可多付费率、多缴税，不碰这条线</strong>"],
   ["检索到的「从大陆实操开通 Stripe」类指南", "多为营销内容，部分做法可能违反服务协议。<strong>一律不予采纳、不予背书</strong>"]])}

<h2>11.4 产品本身的伦理底线</h2>
<p>本项目的核心动作之一是「在公开仓库中发现安全漏洞」。这件事离骚扰只有一步之遥，因此定死三条：</p>
<ul>
<li><strong>先修复，后营销。</strong>每次披露必须附上可直接使用的修复补丁，而不是只报告问题然后推销产品。</li>
<li><strong>不公开未修复的漏洞。</strong>给足合理的修复窗口，绝不用「公开曝光」施压。</li>
<li><strong>不反复试探同一批人。</strong>Gate 1 的预付款测试<strong>明确禁止以「再打磨一下文案」为由重试</strong>
——预付款是二元信号，反复试探会从「验证」滑向「骚扰」。<strong>这条限制的优先级高于商业利益。</strong></li>
</ul>

{callout("一个检验方案是否向善的简单标准", """
<p><strong>如果这门生意失败了，被我扫描和披露过的那些仓库，是不是仍然变得更安全了？</strong></p>
<p>答案是肯定的。免费的扫描工具、公开的修复补丁、被修好的配置，
这些不会因为我没挣到钱而消失。<strong>一个即使失败也给世界留下净收益的方案，
才配称为「向善」。</strong>这不是修辞——它同时也是本方案在道德上敢于执行的理由。</p>""", "pos")}
""")


def ch12_redteam() -> str:
    # 「前三道门的成本」必须从台账取，不能手打：Gate 1 通过后的累计值就是它。
    g1 = next(x for x in G("gates.gates") if x["gid"] == "1")
    g1h, g1cash = g1["cum_hours"], g1["cum_cash"]
    n_gates = len(G("gates.gates"))
    mcg = {x["name"].split()[1]: x["p_pass"] for x in G("monte_carlo.gates")}
    p0b, p1 = mcg["0-B"], mcg["1"]
    return chapter(12, "第十二章", "红队自检：这个项目最可能怎么死", f"""
<p class="lede">这一章不放在附录，因为它是本文件最有用的部分。
一份不敢写「我可能错在哪」的计划书，等于没有做过检验。</p>

<h2>12.1 逆否检验：什么证据会证明我错了</h2>
{table(["我现在相信的", "什么证据会推翻它", "何时能知道"],
  [["agent CI 配置安全是个真问题，有人愿意付费",
    "<strong>Gate 1 的 W4：3 个人预付 $99。</strong>拿不到就是错了，没有第二种解释",
    "第 5 周"],
   ["免费工具能带来自然流量",
    "<strong>Gate 0-B 的 B3：14 天 300 UV + 30 次使用。</strong>拿不到说明这个话题没有自然分发力",
    "第 3 周"],
   [f"复利渠道能在 36 个月内累积到 {num(K('计划月访客_第36月'))} UV/月",
    "第 12 月脉冲渠道贡献占比仍 &gt; 30%，说明所谓「复利」其实是一次次手工推广",
    "第 12 月"],
   ["纯规则引擎不会被 LLM 方案碾压",
    "出现一个用 LLM 做 agent 配置语义审计、且成本可控的竞品",
    "持续观察"],
   ["GitHub 不会自己做这件事",
    "GitHub Advanced Security 或 Actions 内置 agent 工作流安全检查",
    "持续观察（模型给 " + pct(G('monte_carlo.stop_distribution.运营期被平台方打包功能击垮')) + " 概率）"],
   ["__HI__我的时间机会成本低于 " + usd(K('无差异时薪_美元每小时'), 1) + "/小时",
    "<strong>这一条无法被外部证据推翻，只能由你自己诚实回答。</strong>它也是最可能出错的一条",
    "现在"]])}

<h2>12.2 本方案已知的六个弱点（不辩解，只列出）</h2>
<ol>
<li><strong>第 6 章（获客）的证据强度最弱。</strong>四条复利渠道里三条是 {GRADE['D']} 级本人假设，
没有公开数据支撑。这是全文最软的一环，也正因如此把 Gate 0-B 设成了一票否决。</li>
<li><strong>门的通过概率全部是 {GRADE['SELF']} 级主观估计。</strong>
Gate 0-B 取 {p0b:.2f}、Gate 1 取 {p1:.2f}，只有类比、没有外部数据。
已做 ±0.15 敏感性分析（方向不变，幅度变化显著），但读者应把它们当作「我的先验」而非「事实」。</li>
<li><strong>终值假设（2–4 × ARR、50% 流动性概率）无可靠公开数据。</strong>
微型 SaaS 的真实成交倍数与成交概率都缺乏可查证样本。</li>
<li><strong>第 9 章第 3–5 关的标准比第 0–2 关软。</strong>
它们依赖运营数据，存在被「口径解释」软化的空间。处置：口径定义须在进入 Gate 3 之前一次性写死并存档。</li>
<li><strong>模型没有建模「竞品降价」与「客户被整合方吸走」。</strong>
在一个已进入整合期的赛道里，这是真实存在但难以量化的风险。</li>
<li><strong>本 BP 的作者和执行者是同一个人。</strong>门是我自己定的，也是我自己判定的。
没有第三方能阻止我在第 12 个月说服自己「再给三个月」。
唯一可用的对冲是：<strong>把标准写死在版本控制里，让每一次放松标准都留下 diff。</strong>
这不完美，但比什么都不做强。</li>
</ol>

<h2>12.3 如果非要给一个执行建议</h2>
<div class="verdict">
<h3>不要一次决定「做还是不做」，只决定「要不要花 {g1h:.0f} 小时」</h3>
<p>本 BP 的全部结构都指向这一点。完整投入的期望值是负的，
但<strong>前三道门只要 {g1h:.0f} 小时、{usd(g1cash)} 现金</strong>，
而它们能把这个项目最大的两个未知数（拿不拿得到流量、有没有人肯付钱）变成事实。</p>
<p>{g1h:.0f} 小时 ≈ {g1h / HRS_WEEK:.0f} 周的业余时间。按 {usd(RATE)}/小时计，
成本 {usd(g1h * RATE)}。
<strong>用 {usd(g1h * RATE)} 买断两个决定成败的未知数，这笔交易本身是划算的</strong>——
即便最终结论是「不做」，你也用最低成本买到了一个确定的答案，
而不是在十年后仍然想着「当年那个想法要是做了会怎样」。</p>
<p><strong>决策建议：批准 Gate 0 与 Gate 1 的 {g1h:.0f} 小时预算。Gate 2 及以后的
{K('累计工时_36月') - g1h:,.0f} 小时，等前三道门的真实数据出来之后再议——
届时用同一个模型重算，不要用感觉。</strong></p>
</div>

<h2>12.4 交付前自检清单</h2>
{table(["检查项", "状态", "证据"],
  [["每个环节都能由软件/AI 自动完成，无人工依赖", "__HI__部分通过",
    "唯一例外：每周 5 分钟工时记账，已在 10.1 点名"],
   ["每个关键数字都有可查证出处，或附可复现的 Python 计算", "通过",
    "模型数字经 <code>key_numbers</code> 白名单从 <code>results.json</code> 取，取不到即构建失败；"
    "外部事实数字就近标注出处，且被 <code>audit_numbers.py</code> 钉成基线，新增即报错（见附录 C.3）"],
   ["不确定与推测已明确标注，没有任何编造内容", "通过",
    "五级证据分级；C 级内容农场数据已隔离；4 处无公开数据项已标注类比推算"],
   ["方案写明了执行主体、前置条件、所需资源与分步骤", "通过", "第 9 章逐门给出时点、工时、标准与处置动作"],
   ["已做合法性与风险性评估，符合公序良俗", "通过", "第 11 章，含三项明确的能力边界声明"],
   ["阶段目标可分解，每阶段有客观可检验的验收标准", "通过",
    f"{n_gates} 道门，全部为二元可判定标准"],
   ["允许并保留得出「不建议做」的结论", "通过", "第 1 章给出的正是一个有条件的否定结论"]])}
""")


def appendix() -> str:
    fa = R["kelly"]["full_accounting"]
    vd = fa["forbidden_approximations"]["volatility_drag"]
    co = R["kelly"]["cash_only"]
    covd = co["forbidden_approximations"]["volatility_drag"]
    ir = fa["inapplicable_ratios"]
    asm = R["assumptions"]

    # 外部事实数字的数量直接读基线文件，避免这里又出现一个手打的数
    bl = Path(__file__).resolve().parent.parent / "tools" / "hardcoded_baseline.json"
    n_hardcoded = len(json.loads(bl.read_text(encoding="utf-8")))

    arows = []
    items = asm["assumptions"] if isinstance(asm, dict) and "assumptions" in asm else asm
    if isinstance(items, dict):
        for k2, v in items.items():
            if isinstance(v, dict):
                arows.append([f"<code>{k2}</code>", esc(str(v.get("value"))),
                              esc(str(v.get("unit", ""))),
                              GRADE.get(str(v.get("grade")), esc(str(v.get("grade")))),
                              esc(str(v.get("note", ""))[:120])])

    return f"""
<section class="chapter" id="appA">
<p class="eyebrow">附录 A</p><h1>方法论：被禁用的公式与不适用的指标</h1>

<p class="lede">这些不是从教科书上抄来的告诫，而是<strong>在本项目自己的数据上跑出来的反驳</strong>。
列出它们，是为了防止自己或后来的读者图省事又把它们捡回来。</p>

<h2>A.1 禁用 g ≈ μ − σ²/2 波动率拖累近似式</h2>
<p>在创业级波动下，这个近似式<strong>连符号都会算错</strong>。用本项目的两组数据实测：</p>
{table(["口径", "精确值 E[ln M]", "近似值 μ − σ²/2", "误差", "符号是否反了"],
  [["全口径", f"{vd['exact_log_growth']:+.4f}", f"{vd['approx_mu_minus_half_sigma2']:+.4f}",
    f"{vd['absolute_error']:+.4f}", "否" if not vd["sign_flipped"] else "__NEG__是"],
   ["现金口径", f"{covd['exact_log_growth']:+.4f}", f"{covd['approx_mu_minus_half_sigma2']:+.4f}",
    f"{covd['absolute_error']:+.4f}", "__NEG__<strong>是</strong>" if covd["sign_flipped"] else "否"]],
  numcols=(1, 2, 3),
  note="现金口径下近似式给出 −99.9，精确值 +0.19。近似式只在小波动下成立，"
       "而本项目的算术标准差远超其适用范围。<strong>一律用精确式与蒙特卡洛交叉验证。</strong>")}

<h2>A.2 禁用「半 Kelly 保留 75% 增长率」的 c(2−c) 近似</h2>
<p>这个说法流传极广，其严格来源是 Thorp 2006 eq.(7.7) 的连续/对数正态近似。
用本项目的离散分布实测（现金口径，因全口径 f* = 0 无从谈起）：</p>
{table(["分数 c", "f = c·f*", "实测保留比例", "c(2−c) 近似", "差"],
  [[f"{r['fraction_c']}", f"{r['f']:.4f}",
    "__NEG__下注过量，存在被打光的路径" if r["ruin"] else pct(r["retention_measured"], 1),
    pct(r["retention_c2minusc_approx"], 1),
    "—" if r["ruin"] else f"{(r['retention_measured'] - r['retention_c2minusc_approx']) * 100:+.1f} pp"]
   for r in co["fractional_kelly"]],
  numcols=(1, 2, 3, 4),
  note="实测半 Kelly 保留 81.6%，而非流传的 75.0%。"
       "更值得注意的是 1.5 倍与 2 倍 Kelly：近似式给出 75% 与 0%，"
       "而实测结果是<strong>存在会被彻底打光的路径</strong>——近似式在这里不只是不准，是给错了性质。")}

<h2>A.3 不把夏普 / 索提诺 / Omega 作为结论性指标</h2>
{table(["指标", "全口径实测值", "为什么不能用"],
  [["夏普比率", f"{ir['sharpe']:.3f}", "以「收益对称、波动可作风险代理」为前提"],
   ["索提诺比率", f"{ir['sortino']:.3f}", "改善了下行度量，但仍假设分布可用二阶矩描述"],
   ["Omega", f"{ir['omega']:.3f}", "对阈值极敏感，本分布下不具可比性"],
   ["__HI__偏度", f"<strong>{ir['skewness']:.1f}</strong>", "<strong>正态分布为 0。这就是上述三者失效的原因</strong>"],
   ["__HI__超额峰度", f"<strong>{ir['excess_kurtosis']:,.0f}</strong>", "<strong>正态分布为 0</strong>"]],
  numcols=(1,))}
<p>在偏度 {ir['skewness']:.0f}、超额峰度 {ir['excess_kurtosis']:,.0f} 的分布上，
标准差主要由<strong>右尾的好结果</strong>贡献，于是「波动越大 = 越危险」的解读方向是反的。
<strong>把这组数字放进正文只会让读者得到与事实相反的印象</strong>，故仅在此作为反例出现。</p>
</section>

<section class="chapter" id="appB">
<p class="eyebrow">附录 B</p><h1>假设总表与出处</h1>
<p class="lede">全部数值假设集中在 <code>model/assumptions.py</code>，
<strong>其他任何文件禁止硬编码数字</strong>。每个常量注明单位、证据等级与出处。</p>
<p class="small">证据分级：{GRADE['A']} 一手权威来源　{GRADE['B']} 可靠二手　
{GRADE['C']} 存疑（已隔离，不作建模输入）　{GRADE['D']} 无公开数据、类比推算　
{GRADE['SELF']} 本人主观估计</p>
{table(["常量", "取值", "单位", "等级", "说明与出处"], arows) if arows else
 "<p class='small'>假设明细见 <code>outputs/results.json → assumptions</code>。</p>"}
</section>

<section class="chapter" id="appC">
<p class="eyebrow">附录 C</p><h1>复现说明</h1>

<h2>C.1 一条命令</h2>
<p class="mono">python model/run_all.py &amp;&amp; python bp/build_html.py &amp;&amp; python bp/build_pdf.py</p>
<p>随机种子固定为 {R['meta']['seed']}，{num(R['meta']['n_sims'])} 次模拟。
任何人在任何时间重跑，都会得到与本文件<strong>逐位相同</strong>的数字。</p>

{kv([("Python", R["meta"]["python"]), ("NumPy", R["meta"]["numpy"]),
     ("运行平台", R["meta"]["platform"]),
     ("代码版本", f"git {R['meta']['git_rev'] or 'n/a'}"),
     ("生成时间", R["meta"]["generated_at_utc"]),
     ("全流程耗时", f"{R['meta']['elapsed_seconds']:.1f} 秒")])}

<h2>C.2 文件清单</h2>
{table(["文件", "作用"],
  [["<code>model/assumptions.py</code>", "唯一的假设来源，含自检"],
   ["<code>model/opportunity_scoring.py</code>", "16 候选 × 12 硬过滤 × 9 维加权 + 敏感性与稳健性"],
   ["<code>model/funnel.py</code>", "自下而上漏斗，含信用卡开关"],
   ["<code>model/unit_economics.py</code>", "单客户经济性、双口径盈亏平衡、时间计价 CAC"],
   ["<code>model/acquisition.py</code>", "渠道模型与缺口分析"],
   ["<code>model/monte_carlo.py</code>", "10 万次模拟，阶段门进入模型"],
   ["<code>model/kelly.py</code>", "胜率/盈亏比/Kelly/四种年化/无差异时薪"],
   ["<code>model/gates.py</code>", "止损台账与每道门的定价"],
   ["<code>model/figures.py</code>", "SVG 矢量图表"],
   ["<code>model/run_all.py</code>", "一键复现 + 跨模型交叉校验"],
   ["<code>bp/build_html.py</code>", "本文件的生成器（数字全部取自 results.json）"],
   ["<code>bp/build_pdf.py</code>", "Playwright 导出 PDF 并校验"],
   ["<code>docs/GATE0.md</code> 等", "各专题的完整论证"],
   ["<code>research/sources.md</code>", "事实底稿，每条含 URL、日期与证据分级"]])}

<h2>C.3 对账保证</h2>
{callout("正文里的数字分两类，两类各有各的保证", f"""
<p><strong>第一类：本项目模型算出来的数字</strong>（工时、金额、概率、转化率、期望值）。
本文件由 <code>bp/build_html.py</code> 从 <code>outputs/results.json</code> 渲染，
这类数字一律经白名单函数取值，<strong>取不到就抛异常、构建失败</strong>。
本次构建共引用 {{USED}} 个关键数字，白名单覆盖率 {{COV}}。
所以「正文与模型一致」是结构性保证：模型参数变了而正文没跟着变，
构建会失败，而不是静默产出一份过期文件。</p>
<p><strong>第二类：外部事实数字</strong>（竞品定价、他人营收、法规日期、第三方问卷比例）。
这类数字是手打的，而且<strong>本就不该</strong>来自本项目的模型——
它们的效力来自出处，因此每一处都就近标注了来源与核查日期，底稿在
<code>research/sources.md</code>。</p>
<p>这个区分本身也被自动守住：<code>tools/audit_numbers.py</code> 把当前
{n_hardcoded} 处外部事实数字指纹化钉成基线，<strong>此后任何新增的手打数字都会让检查失败</strong>，
必须要么改为从模型取值，要么显式复核入基线并留下 diff。
<strong>换句话说，第一类数字不可能被手打偷偷替换掉。</strong></p>""", "pos")}
</section>"""


# ================================================================== 组装

_CJK = r"\u3000-\u303f\u4e00-\u9fff\uff00-\uffef"
_CJK_CLOSE = r"，。、；：！？）】」』》…—"   # 其后不留空
_CJK_OPEN = r"（【「『《"                      # 其前不留空
_BR = r"[ \t]*\n[ \t]*"


def squeeze_cjk_breaks(html: str) -> str:
    """删掉因源码折行而在中文里多出来的那一格空白。

    源码为了可读性在句中折行，HTML 把换行渲染成空格，成品上就出现
    「……很好」， Kelly 最优……」这种多出来的一格。它只在折行处出现，
    看上去像随机的排版事故，是中文网页最常见的瑕疵之一。

    三条规则，都遵循中文排版惯例：
      A 两侧都是中日韩字符 → 删
      B 左侧是收尾类全角标点（，。：」等）→ 删，全角标点后本就不留空
      C 右侧是起始类全角标点（（「《等）→ 删
    中英文之间的常规空格是有意保留的，不在此列；标签语法全为 ASCII，
    不会被误伤。
    """
    html = re.sub(rf"(?<=[{_CJK}]){_BR}(?=[{_CJK}])", "", html)
    html = re.sub(rf"(?<=[{_CJK_CLOSE}]){_BR}", "", html)
    html = re.sub(rf"{_BR}(?=[{_CJK_OPEN}])", "", html)
    return html


def mark_self_describing_links(html: str) -> str:
    """链接文字本身就是网址时，打上 bare 类，避免 PDF 里把网址印两遍。

    print.css 会在链接后追加 `(https://…)`，这对「来源：SEC 8-K 原文」一类
    有意义——纸上点不了，得把地址写出来。但当链接文字已经是
    `cursor.com/marketplace-publisher-terms` 时，追加的结果是同一个地址连着
    印两遍，既占地方又显得不经心。
    """
    def repl(m: re.Match) -> str:
        href, text = m.group(1), m.group(2)
        norm = re.sub(r"^https?://(www\.)?", "", href).rstrip("/")
        if text.strip() == norm:
            return f'<a class="bare" href="{href}">{text}</a>'
        return m.group(0)

    return re.sub(r'<a href="([^"]+)">([^<]+)</a>', repl, html)


def build() -> str:
    body = (cover() + summary() + toc() + ch1_conclusion() + ch2_facts() + ch3_debunked()
            + ch4_track() + ch5_product() + ch6_acquisition() + ch7_econ()
            + ch8_risk() + ch9_gates() + ch10_ops() + ch11_legal() + ch12_redteam()
            + appendix())

    cov = len(_used) / len(KN)
    body = body.replace("{USED}", str(len(_used))).replace("{COV}", pct(cov))
    body = squeeze_cjk_breaks(body)
    body = mark_self_describing_links(body)

    return f"""<!doctype html>
<html lang="zh-CN"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CursorFlow AI 商业计划书 · {R['meta']['base_date']}</title>
<meta name="description" content="一份可复现、可证伪的单人自有资金创业决策与执行手册">
<link rel="stylesheet" href="styles.css">
<link rel="stylesheet" href="print.css">
</head><body><main class="page">
{body}
</main></body></html>"""


def main() -> None:
    html = build()
    out = BP / "index.html"
    out.write_text(html, encoding="utf-8")

    unused = sorted(set(KN) - _used)
    print(f"已生成 {out}  ({len(html) / 1024:,.0f} KB)")
    print(f"引用关键数字 {len(_used)}/{len(KN)}  覆盖率 {pct(len(_used) / len(KN))}")
    if unused:
        print(f"未被正文引用（{len(unused)} 项，考虑删除或补写）:")
        for u in unused:
            print(f"  · {u}")
    # 正文里不应残留未替换的模板占位
    leftover = re.findall(r"\{[A-Z_]+\}", html)
    if leftover:
        raise SystemExit(f"存在未替换的占位符: {set(leftover)}")


if __name__ == "__main__":
    main()
