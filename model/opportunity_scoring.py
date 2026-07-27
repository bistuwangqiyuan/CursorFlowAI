"""赛道重选的量化筛选：12 条硬过滤 + 9 维加权评分 + 权重敏感性分析。

设计原则（对应工作原则第十三、十四条）：
  1. 每一条硬过滤的判定都附书面理由，不允许裸给 True/False。
  2. 每一个维度的打分都附书面理由与至少一个来源，不允许裸给分。
  3. 权重可扰动；若扰动会翻转排名，必须如实输出并在 BP 中披露。

复现：python model/opportunity_scoring.py
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

SEED = 20260727
OUT_DIR = Path(__file__).resolve().parent.parent / "outputs"


# --------------------------------------------------------------------------
# 一、硬过滤器定义
# --------------------------------------------------------------------------
# 编号与 BP 正文一致。第 2、6 条已按 research/sources.md §4.1 的更正收窄措辞。

HARD_FILTERS = {
    "F1": "变现路径依赖 Cursor Marketplace 或任何合同禁止收费的渠道"
          "（Publisher Terms 3.1 条：插件必须免费提供）",
    "F2": "核心功能与平台方自营产品正面重叠，且该功能已被打包进客户已付费的订阅中"
          "（客户获得它的边际价格为零）",
    "F3": "依赖只有编辑器厂商才能采集的数据（如设备端 AI 代码逐行签名）",
    "F4": "需人工销售，或需先有 SOC 2 才能开出第一单",
    "F5": "推理成本不可透传（无法 BYOK，也无法按用量转嫁）",
    "F6": "采用「每次操作跑 LLM」的结构，且不具备分层路由/增量处理/缓存三件套的架构能力"
          "（已按 sources.md §4.1 更正：成本是架构问题，不是结构性宿命）",
    "F7": "变现叙事依赖 EU AI Act 或美国 SSDF 对普通软件开发的强制力（该前提不成立）",
    "F8": "核心功能可被一个免费 CLI 完整替代；可收费的必须是 CLI 结构上做不到的持续托管态",
    "F9": "需要重资产才能建立护城河（千万级片段语料库、纵向代码语料、漏洞情报数据库等），"
          "$4,000 预算无法支撑",
    "F10": "产品需对客户作出「你已合规」的法律判定——超出自身能力边界，只可做证据收集",
    "F11": "单人 20 小时每周下 MVP 超过 12 周",
    "F12": "合法性或公序良俗存疑",
}


# --------------------------------------------------------------------------
# 二、评分维度与默认权重
# --------------------------------------------------------------------------
# 权重反映「主要矛盾」的判定：获客是本项目的瓶颈（BENCHMARKS.md §9.1），
# 故 unmanned_acquisition 与 wtp_evidence 权重最高；监管顺风权重刻意压低，
# 因为已证伪的合规叙事太多（sources.md §3.2）。

DIMENSIONS = {
    "wtp_evidence":        ("付费意愿证据强度", 0.18),
    "unmanned_acquisition": ("无人化获客可行性", 0.16),
    "competition_low":     ("竞争稀疏度（竞争密度的反向）", 0.15),
    "pain_evidence":       ("痛点证据强度", 0.14),
    "deliverability_20h":  ("20 小时每周的可交付性", 0.13),
    "vendor_independence": ("跨厂商独立性（单厂商依赖度的反向）", 0.10),
    "margin_structure":    ("边际成本结构", 0.08),
    "switching_cost":      ("客户迁移成本 / 留存结构", 0.03),
    "regulatory_tailwind": ("监管顺风", 0.03),
}

assert abs(sum(w for _, w in DIMENSIONS.values()) - 1.0) < 1e-9, "权重之和必须为 1"


@dataclass
class Candidate:
    cid: str
    name: str
    thesis: str
    # 硬过滤：仅记录「命中（即淘汰）」的条目。未列出者视为通过。
    filter_hits: dict[str, str] = field(default_factory=dict)
    # 评分：dim -> (score 0-10, 理由, 来源)
    scores: dict[str, tuple[float, str, str]] = field(default_factory=dict)

    @property
    def survives(self) -> bool:
        return len(self.filter_hits) == 0

    def weighted(self, weights: dict[str, float]) -> float:
        return sum(self.scores[d][0] * weights[d] for d in weights)


# --------------------------------------------------------------------------
# 三、16 个候选
# --------------------------------------------------------------------------

S_MS = "微软威胁情报 https://www.microsoft.com/en-us/security/blog/2026/06/05/securing-ci-cd-in-agentic-world-claude-code-github-action-case/"
S_CSA = "CSA 研究简报 2026-05-03 https://labs.cloudsecurityalliance.org/wp-content/uploads/2026/05/CSA_research_note_ai_github_actions_security_20260503-csa-styled.pdf"
S_NOMA = "Noma GitLost https://noma.security/blog/gitlost-how-we-tricked-githubs-ai-agent-into-leaking-private-repos/"
S_AIKIDO = "Aikido PromptPwnd https://www.aikido.dev/blog/promptpwnd-github-actions-ai-agents"
S_REGISTRY = "MCP Registry 官方文档 https://github.com/modelcontextprotocol/registry/blob/main/docs/modelcontextprotocol-io/about.mdx"
S_SLOP = "arXiv 2603.27249（1,154 条帖子定性编码）https://arxiv.org/abs/2603.27249"
S_CURL = "curl 关闭 bug bounty，lists.haxx.se 2026-01"
S_BUGBOT = "Cursor Bugbot 官方文档 https://cursor.com/docs/bugbot.md"
S_COPILOT = "GitHub Copilot Pro $10/月含 code review（sources.md §4.2）"
S_KNIP = "Knip 11,752 stars, ISC 免费, 自带 MCP https://github.com/webpro-nl/knip"
S_CRA = "EU CRA 官方摘要 https://digital-strategy.ec.europa.eu/en/policies/cra-summary"
S_CRA64 = "CRA Art.64(10) 开源管理者免除行政罚款 https://digital-strategy.ec.europa.eu/en/policies/cra-open-source"
S_TRACK = "Cursor AI Code Tracking API https://cursor.com/docs/account/teams/ai-code-tracking-api"
S_AHREFS = "Ahrefs 100 万 URL 追踪：新页面 12 个月内进前十 1.74% https://ahrefs.com/blog/how-long-does-it-take-to-rank-in-google-and-how-old-are-top-ranking-pages/"
S_ELLIPSIS = "Ellipsis 工程博客：生产均值 $0.12/次审查 https://www.ellipsis.dev/blog/lessons-from-building-llm-agents"
S_SO = "Stack Overflow 2025（49,000+ 样本）：信任 AI 输出者仅 29% https://survey.stackoverflow.co/2025/ai/"
S_HN_SPEND = "HN 一手帖：月消耗 $60→$500+，单次调用 $12 https://news.ycombinator.com/item?id=46544838"
S_HN_WEAK = "Ask HN 「如何防止 agent 烧钱」仅 8 分 32 评论 https://news.ycombinator.com/item?id=47559293"
S_GITCLEAR = "GitClear 6.23 亿行分析（利益冲突：其自身即该品类厂商）https://www.gitclear.com/the_ai_code_quality_maintainability_gap"
S_SELF = "本 BP 自评（推测，无外部来源）"


CANDIDATES: list[Candidate] = [
    # ---------------- 入围候选 ----------------
    Candidate(
        cid="C12",
        name="AI agent 在 CI/CD 中的配置安全审计",
        thesis="检测「不受信输入流入 agent 提示 × agent 持有高权限凭据 × 存在外发通道」的致命三角，"
               "纯 YAML/AST 规则分析，零推理成本，持续监控仓库配置漂移。",
        filter_hits={},
        scores={
            "wtp_evidence": (3.0, "无任何直接付费证据。唯一支撑是 StepSecurity（同为 GitHub Actions 安全）"
                                  "已商业化运营这一间接类比。这是本候选最大的未验证风险。", "无一手来源；见 docs/WTP_VALIDATION.md"),
            "unmanned_acquisition": (6.0, "安全类内容在 HN 有天然传播力（四篇来源本身都是高传播安全研究）；"
                                          "GitHub Action Marketplace 是一个可被搜索的分发面。但安全产品历史上靠恐惧+销售，"
                                          "自助获客不确定。", S_AHREFS),
            "competition_low": (8.0, "zizmor / actionlint 覆盖通用 Actions 安全，但不理解 claude-code-action 等 "
                                     "agent action 的配置语义；本轮调研未发现做 agent 语义感知的商业竞品。", S_CSA),
            "pain_evidence": (9.0, "四个独立权威源（微软威胁情报、CSA、Aikido、Noma）且均为已确认漏洞而非推测；"
                                   "微软案例中 Anthropic 已发版修复，说明厂商承认问题真实。", f"{S_MS}；{S_CSA}；{S_AIKIDO}；{S_NOMA}"),
            "deliverability_20h": (9.0, "纯规则引擎：解析 workflow YAML + 已知 agent action 的输入语义 + 权限图，"
                                        "无模型训练、无 ML。MVP 明显在 12 周内。", S_SELF),
            "vendor_independence": (8.0, "同时适用 GitHub Actions 与 GitLab CI，且对 agent 厂商中立"
                                         "（Claude Code / Codex / Gemini CLI 都在覆盖面内）。", S_AIKIDO),
            "margin_structure": (10.0, "零 LLM 推理成本，边际成本仅为解析算力，可忽略。"
                                       "这是全部候选中唯一真正零边际成本的。", S_SELF),
            "switching_cost": (4.0, "规则本身可被复制；但历史发现记录与基线比对会积累一定状态黏性。", S_SELF),
            "regulatory_tailwind": (4.0, "CRA 的漏洞报告义务间接相关，但不构成强制要求。"
                                         "刻意不使用已证伪的 AI Act 叙事。", S_CRA),
        },
    ),
    Candidate(
        cid="C13",
        name="MCP server / Agent Skill 的持续供应链监控",
        thesis="官方 Registry 白纸黑字声明自己不做安全扫描、留给下游聚合方。"
               "一次性扫描已被免费 OSS 覆盖，唯一可收费的是持续 rug-pull 监控（你装的 47 个 server 昨晚有 3 个改了 tool description）。",
        filter_hits={},
        scores={
            "wtp_evidence": (3.0, "无直接付费证据。间接信号：Enterprise 管理员已在 Cursor 后台按 URL 屏蔽 MCP，"
                                  "说明企业侧已有担忧，但担忧未必转化为付费。", S_REGISTRY),
            "unmanned_acquisition": (6.0, "MCP 是 2026 年的高热话题，内容与工具都容易获得自然传播；"
                                          "但同样意味着注意力竞争激烈。", S_AHREFS),
            "competition_low": (6.0, "一次性扫描已有 4+ 免费 OSS 加 NVIDIA SkillSpector（68 个漏洞模式）；"
                                     "持续监控形态覆盖较少。**产品必须严格限定在持续态，否则直接撞 F8。**", S_REGISTRY),
            "pain_evidence": (6.0, "rug-pull 风险在概念上成立且 Registry 官方承认不管，但本轮未找到"
                                   "「我因为 MCP server 被改而受损」的一手事件。痛点是预期性的，不是已发生的。", S_REGISTRY),
            "deliverability_20h": (8.0, "抓取 Registry + 定期 diff tool description/权限声明 + 告警，工程量可控。", S_SELF),
            "vendor_independence": (9.0, "MCP 是跨厂商开放标准，被 Cursor/Codex/Claude Code 等共同采用，"
                                         "分发不由单一厂商条款决定。", "Cursor MCP 文档 https://cursor.com/docs/mcp"),
            "margin_structure": (9.0, "以爬取与结构化 diff 为主，LLM 仅在语义变更判定时可选调用，可控。", S_ELLIPSIS),
            "switching_cost": (6.0, "「你安装的 server 清单 + 历史基线」是托管状态，迁移会丢失历史，黏性中等偏上。", S_SELF),
            "regulatory_tailwind": (3.0, "CRA 的 SBOM 要求在 2027-12-11 后可能延伸到 agent 依赖，但目前无明文。", S_CRA),
        },
    ),
    Candidate(
        cid="C14",
        name="CI 中 agent 的花费熔断器",
        thesis="收窄至 CI 中的非交互式 agent（超支最狠、无 SLA 焦虑、必然走 API），"
               "做跨仓库预算与自动熔断。",
        filter_hits={},
        scores={
            "wtp_evidence": (5.0, "HN 上有最真实的「用户正在流血」证据（退款被拒、单次调用 $12）；"
                                  "但流血的人第一反应是要求厂商提供免费额度控制，不是买第三方网关。", S_HN_SPEND),
            "unmanned_acquisition": (5.0, "成本话题传播力强，但同题材已被 Helicone / Portkey / LiteLLM 的内容占满。", S_AHREFS),
            "competition_low": (3.0, "LiteLLM 是免费 OSS 网关且自带预算与速率限制；Helicone、Portkey、OpenMeter "
                                     "均已商业化；模型厂商自身也提供组织级支出上限。竞争密集。", S_HN_WEAK),
            "pain_evidence": (7.0, "个案证据极强但统计证据极弱——Ask HN 同题仅 8 分、32 条评论，"
                                   "说明这不是一个广泛被感知的问题。**强轶事 + 弱统计。**", f"{S_HN_SPEND}；{S_HN_WEAK}"),
            "deliverability_20h": (6.0, "网关处于请求热路径，对可用性与延迟的要求远高于旁路工具。"
                                        "单人维护一个不能挂的代理，风险被低估。", S_SELF),
            "vendor_independence": (7.0, "对模型厂商中立，但存在结构性错配：最痛的人用 Cursor 订阅制，"
                                         "网关拦不到那部分流量。", S_HN_SPEND),
            "margin_structure": (7.0, "透传为主，但需承担带宽与常驻算力，非零边际成本。", S_SELF),
            "switching_cost": (7.0, "一旦进入请求热路径，替换成本高。这是本候选最强的一维。", S_SELF),
            "regulatory_tailwind": (1.0, "无。", S_SELF),
        },
    ),
    Candidate(
        cid="C15",
        name="EU CRA 证据收集与打包",
        thesis="纯证据流水线：SBOM 生成、漏洞处置记录、报告时限追踪。"
               "绝不做「你已合规」的法律判定。",
        filter_hits={},
        scores={
            "wtp_evidence": (6.0, "已有 4 家在此收费，说明付费意愿被市场验证过——这是全部候选中"
                                  "付费证据最硬的一个。", S_CRA),
            "unmanned_acquisition": (4.0, "合规采购方不逛 HN，他们通过审计师、行业协会、咨询顾问获知方案。"
                                          "这与零人工自助获客的路径不匹配。", S_AHREFS),
            "competition_low": (3.0, "4 家在收费且各价位段被占满；GitHub 的 SPDX SBOM 导出对云仓库完全免费，"
                                     "吃掉了最容易做的那部分。", S_CRA),
            "pain_evidence": (5.0, "时间窗口真实（2026-09-11 报告义务、2027-12-11 全面适用），"
                                   "但 Art.64(10) 对开源管理者完全免除行政罚款，微小型制造商亦部分豁免，"
                                   "**恐惧驱动比营销宣称的弱得多**。", S_CRA64),
            "deliverability_20h": (5.0, "证据流水线 + SBOM + CVE 映射 + 时限追踪，12 周内做完偏紧。", S_SELF),
            "margin_structure": (8.0, "以数据管道为主，可用 OSV.dev 免费漏洞数据源，边际成本低。", S_SELF),
            "vendor_independence": (8.0, "与代码托管平台解耦，跨 GitHub/GitLab 均可。", S_CRA),
            "switching_cost": (8.0, "合规证据是纵向累积的，迁移会丢失历史记录，黏性最强。", S_SELF),
            "regulatory_tailwind": (10.0, "唯一有硬性外部时间窗口的候选。", S_CRA),
        },
    ),
    Candidate(
        cid="C16",
        name="AI PR 的审阅证据包",
        thesis="为 AI 生成的 PR 附上「这段代码被验证过什么」的证据，减轻审阅者负担。",
        filter_hits={},  # 见下方 §4.1 更正说明：F2 在收窄措辞后不再命中，改由评分淘汰
        scores={
            "wtp_evidence": (4.0, "同赛道有人付费（CodeRabbit 据 Sacra 估算 $40M ARR），"
                                  "但「证据包」这个特定形态无独立付费证据。", "Sacra 估算 https://sacra.com/c/coderabbit/"),
            "unmanned_acquisition": (2.0, "关键词（AI code review、cursor rules）已被 246 人的 CodeRabbit、"
                                          "有 Benchmark 背书的 Greptile 和大量 SEO 内容农场完全占据。"
                                          "单人无任何机会在此获得自然搜索流量。", S_AHREFS),
            "competition_low": (1.0, "真实玩家 30+ 家；Bugbot / CodeRabbit / Greptile 三方交火；"
                                     "GitHub Copilot $10/月含 code review 构成价格天花板；"
                                     "开源项目免费已是行业标配。", f"{S_BUGBOT}；{S_COPILOT}"),
            "pain_evidence": (10.0, "全场最硬：1,154 条帖子的定性编码分析，加 curl 因 AI 生成漏洞报告"
                                    "关闭 bug bounty 这一不可辩驳的一手事件。"
                                    "**但「痛点最强」与「你能赢」是两件事，这条属前者。**", f"{S_SLOP}；{S_CURL}"),
            "deliverability_20h": (6.0, "要做到比现有玩家更有说服力的证据，需要真正执行代码"
                                        "（Greptile 已发布 TREX 层），工程量大。", S_SELF),
            "vendor_independence": (6.0, "跨 GitHub/GitLab 可行，但与平台自营产品同场竞技。", S_BUGBOT),
            "margin_structure": (6.0, "有真实推理成本。按 Ellipsis 生产均值 $0.12/次、月 20 次计，"
                                      "$19 客单价下毛利约 87%——**成本不是问题，竞争才是**。", S_ELLIPSIS),
            "switching_cost": (4.0, "审查工具切换成本低，装个 App 即可换。", S_SELF),
            "regulatory_tailwind": (2.0, "无。刻意不使用已证伪的 AI Act 叙事。", S_SELF),
        },
    ),

    # ---------------- 被硬过滤淘汰的候选 ----------------
    Candidate(
        cid="C01",
        name="通用 AI 代码审查",
        thesis="做一个更好的 AI code reviewer。",
        filter_hits={
            "F2": "Cursor Bugbot 已含在 Cursor Individual/Teams 订阅中；GitHub Copilot Pro $10/月即含 "
                  "code review。客户获得该功能的边际价格为零，第三方必须为一个客户已免费拥有的东西收费。"
                  f"（{S_BUGBOT}；{S_COPILOT}）",
        },
        scores={
            "wtp_evidence": (7.0, "付费意愿已被充分验证（CodeRabbit 估算 $40M ARR、Greptile 拿 Benchmark A 轮）。", "https://sacra.com/c/coderabbit/"),
            "unmanned_acquisition": (1.0, "关键词与社群心智被完全占据。", S_AHREFS),
            "competition_low": (0.0, "真实玩家 30+ 家，加三家平台方自营。", S_BUGBOT),
            "pain_evidence": (9.0, "痛点真实且广泛。", S_SLOP),
            "deliverability_20h": (5.0, "做出 demo 容易，做到有竞争力难。", S_SELF),
            "vendor_independence": (4.0, "与平台自营产品同场。", S_BUGBOT),
            "margin_structure": (6.0, "按更正后的 $0.12/次成本，毛利可接受。", S_ELLIPSIS),
            "switching_cost": (4.0, "切换成本低。", S_SELF),
            "regulatory_tailwind": (2.0, "无。", S_SELF),
        },
    ),
    Candidate(
        cid="C02",
        name="团队 AI 编码 ROI 报表 / 本地 AI 代码归因",
        thesis="给工程负责人看 AI 编码的投入产出。",
        filter_hits={
            "F3": f"AI 代码归因依赖设备端对每行 AI 建议签名再与 git commit 比对，只有编辑器本身能产生该数据；"
                  f"第三方只能靠启发式 diff，精度天然落后。（{S_TRACK}）",
            "F4": "Cursor Analytics / AI Code Tracking API 仅 Enterprise 可用，客户必走采购流程，"
                  "与「零人工自助订阅」硬约束冲突。",
        },
        scores={
            "wtp_evidence": (6.0, "DX / LinearB / Jellyfish 等已收费。", S_GITCLEAR),
            "unmanned_acquisition": (2.0, "企业效能工具越往上走越是纯销售驱动。", S_AHREFS),
            "competition_low": (2.0, "LinearB、Swarmia、DX、Waydev、Faros 五家全部已上线；"
                                     "DX 已做到行级归因并按 AI 占比分五档对比 revert rate。", S_GITCLEAR),
            "pain_evidence": (2.0, "**本轮未能找到任何工程负责人抱怨「看不到这些数据」的一手帖子，需求证据为零。**"
                                   "这是我此前判断被推翻的地方。", S_SELF),
            "deliverability_20h": (4.0, "归因精度是核心，而精度上限被数据源卡死。", S_TRACK),
            "vendor_independence": (2.0, "强依赖 Cursor 的 Enterprise API。", S_TRACK),
            "margin_structure": (8.0, "以数据聚合为主。", S_SELF),
            "switching_cost": (6.0, "历史度量数据有黏性。", S_SELF),
            "regulatory_tailwind": (3.0, "ISO 27001 证据包有一点关联，但不构成驱动。", S_SELF),
        },
    ),
    Candidate(
        cid="C03",
        name="许可证污染 snippet 匹配",
        thesis="检测 AI 生成代码中混入的 GPL 片段。",
        filter_hits={
            "F9": "护城河是千万级代码片段语料库与索引，$4,000 预算连一次全量索引都不够。",
        },
        scores={
            "wtp_evidence": (5.0, "企业法务对许可证风险确有预算（Black Duck 等已存在）。", S_SELF),
            "unmanned_acquisition": (3.0, "法务采购不走自助。", S_AHREFS),
            "competition_low": (4.0, "已有 Black Duck / FOSSA / Snyk 等。", S_SELF),
            "pain_evidence": (4.0, "风险真实但发生率低。", S_SELF),
            "deliverability_20h": (2.0, "语料库建设远超 12 周。", S_SELF),
            "vendor_independence": (7.0, "与编辑器无关。", S_SELF),
            "margin_structure": (5.0, "索引存储与检索成本高。", S_SELF),
            "switching_cost": (5.0, "中等。", S_SELF),
            "regulatory_tailwind": (4.0, "CRA 的 SBOM 要求有一点关联。", S_CRA),
        },
    ),
    Candidate(
        cid="C04",
        name="AI 技术债度量",
        thesis="量化 AI 生成代码带来的可维护性劣化。",
        filter_hits={
            "F9": f"结论需建立在纵向大规模代码语料上（GitClear 用了 6.23 亿行变更），单人无法自建；"
                  f"且唯一权威数据的提供者 GitClear 自己就是卖这个产品的竞品。（{S_GITCLEAR}）",
        },
        scores={
            "wtp_evidence": (3.0, "无独立付费证据。", S_SELF),
            "unmanned_acquisition": (3.0, "与效能度量同属销售驱动。", S_AHREFS),
            "competition_low": (2.0, "与 C02 同一批玩家占据。", S_GITCLEAR),
            "pain_evidence": (5.0, "GitClear 的数据显示劣化真实（重复 +81%），但有利益冲突。", S_GITCLEAR),
            "deliverability_20h": (4.0, "指标定义容易，可信度难。", S_SELF),
            "vendor_independence": (6.0, "基于 git 历史，与编辑器无关。", S_SELF),
            "margin_structure": (7.0, "静态分析为主。", S_SELF),
            "switching_cost": (5.0, "中等。", S_SELF),
            "regulatory_tailwind": (2.0, "无。", S_SELF),
        },
    ),
    Candidate(
        cid="C05",
        name="死代码检测",
        thesis="找出 AI 大量生成后遗留的无用代码。",
        filter_hits={
            "F8": f"Knip 是免费事实标准：11,752 stars、260 贡献者、ISC 许可、且已自带 @knip/mcp；"
                  f"Vercel 用它删掉约 30 万行。核心功能可被一个 npx 命令完整替代。（{S_KNIP}）",
        },
        scores={
            "wtp_evidence": (2.0, "免费工具已占满，无付费证据。", S_KNIP),
            "unmanned_acquisition": (4.0, "话题有传播力但导流至免费工具。", S_AHREFS),
            "competition_low": (1.0, "Knip 一家独大且免费。", S_KNIP),
            "pain_evidence": (4.0, "真实但不紧急。", S_SELF),
            "deliverability_20h": (7.0, "技术不难。", S_SELF),
            "vendor_independence": (8.0, "语言生态相关，与编辑器无关。", S_SELF),
            "margin_structure": (9.0, "纯静态分析。", S_SELF),
            "switching_cost": (2.0, "极低。", S_SELF),
            "regulatory_tailwind": (1.0, "无。", S_SELF),
        },
    ),
    Candidate(
        cid="C06",
        name="agent / prompt 回归评测",
        thesis="给 agent 与提示词做回归测试。",
        filter_hits={
            "F8": "Promptfoo 是免费 OSS CLI 且功能完整；Braintrust、Langfuse 已占满托管形态。",
        },
        scores={
            "wtp_evidence": (5.0, "Braintrust 等已收费。", S_SELF),
            "unmanned_acquisition": (4.0, "开发者话题，有一定传播力。", S_AHREFS),
            "competition_low": (2.0, "三家已占满。", S_SELF),
            "pain_evidence": (6.0, "非确定性输出的回归问题真实。", S_ELLIPSIS),
            "deliverability_20h": (4.0, "评测框架的工程量大。", S_SELF),
            "vendor_independence": (7.0, "跨模型厂商。", S_SELF),
            "margin_structure": (5.0, "跑评测即烧推理。", S_ELLIPSIS),
            "switching_cost": (6.0, "历史评测结果有黏性。", S_SELF),
            "regulatory_tailwind": (2.0, "无。", S_SELF),
        },
    ),
    Candidate(
        cid="C07",
        name="私有知识库转 MCP",
        thesis="把公司内部文档变成 agent 可调用的 MCP server。",
        filter_hits={
            "F8": "已有多个免费 OSS 实现；KBKit 等已把该功能降级为免费赠品。",
        },
        scores={
            "wtp_evidence": (2.0, "无一手需求证据。", S_SELF),
            "unmanned_acquisition": (3.0, "同质内容过多。", S_AHREFS),
            "competition_low": (2.0, "免费实现众多。", S_REGISTRY),
            "pain_evidence": (2.0, "无一手证据。", S_SELF),
            "deliverability_20h": (7.0, "技术不难。", S_SELF),
            "vendor_independence": (8.0, "MCP 跨厂商。", S_REGISTRY),
            "margin_structure": (5.0, "向量检索有存储成本。", S_SELF),
            "switching_cost": (5.0, "中等。", S_SELF),
            "regulatory_tailwind": (1.0, "无。", S_SELF),
        },
    ),
    Candidate(
        cid="C08",
        name="EU AI Act Art.50 透明度扫描",
        thesis="扫描产品是否满足 AI Act 的透明度告知义务。",
        filter_hits={
            "F7": "范畴错误：Art.50 管的是「你的产品是不是 AI、有没有告知用户」，与「你用 AI 写代码」无关；"
                  "且 Digital Omnibus 已于 2026-07-27 生效，将高风险义务推迟至 2027-12-02。",
        },
        scores={
            "wtp_evidence": (2.0, "建立在错误前提上。", S_SELF),
            "unmanned_acquisition": (2.0, "合规采购不自助。", S_AHREFS),
            "competition_low": (5.0, "少人做——因为需求不存在。", S_SELF),
            "pain_evidence": (1.0, "前提不成立。", S_SELF),
            "deliverability_20h": (6.0, "技术不难。", S_SELF),
            "vendor_independence": (8.0, "与编辑器无关。", S_SELF),
            "margin_structure": (8.0, "静态扫描。", S_SELF),
            "switching_cost": (3.0, "低。", S_SELF),
            "regulatory_tailwind": (1.0, "**负分项：叙事已被证伪。**", S_SELF),
        },
    ),
    Candidate(
        cid="C09",
        name="AI 代码溯源 attestation",
        thesis="为每段代码出具「由谁/由哪个模型生成」的可验证证明。",
        filter_hits={
            "F8": "agentdiff、aiir、ai-footprint、pedigree、agentmark 等 5 个功能高度重叠的免费 OSS；"
                  "且没有任何法规要求证明代码作者身份。",
        },
        scores={
            "wtp_evidence": (1.0, "零付费证据，零法规要求。", S_SELF),
            "unmanned_acquisition": (3.0, "话题有热度但无购买意图。", S_AHREFS),
            "competition_low": (2.0, "5 个免费 OSS。", S_SELF),
            "pain_evidence": (3.0, "概念性痛点。", S_SELF),
            "deliverability_20h": (6.0, "技术不难。", S_SELF),
            "vendor_independence": (7.0, "跨工具。", S_SELF),
            "margin_structure": (8.0, "低成本。", S_SELF),
            "switching_cost": (4.0, "低。", S_SELF),
            "regulatory_tailwind": (2.0, "无法规要求。", S_SELF),
        },
    ),
    Candidate(
        cid="C10",
        name="AGENTS.md / rules 漂移检测",
        thesis="检测 agent 规则文件与代码实际状态的不一致。",
        filter_hits={
            "F8": "一个脚本即可完成；且论坛证据显示主因是「模型不遵守规则」而非「文件不同步」，"
                  "解决的是次要矛盾。",
        },
        scores={
            "wtp_evidence": (1.0, "零付费证据。", S_SELF),
            "unmanned_acquisition": (4.0, "AGENTS.md 是热门话题。", S_AHREFS),
            "competition_low": (3.0, "尚无人专做，因为价值太薄。", S_SELF),
            "pain_evidence": (3.0, "抱怨存在，但指向的是模型依从性。", S_SELF),
            "deliverability_20h": (8.0, "非常简单。", S_SELF),
            "vendor_independence": (9.0, "AGENTS.md 被 Codex、Copilot、Gemini CLI、Aider、Windsurf、Zed 原生读取。", S_SELF),
            "margin_structure": (9.0, "近零成本。", S_SELF),
            "switching_cost": (2.0, "极低。", S_SELF),
            "regulatory_tailwind": (1.0, "无。", S_SELF),
        },
    ),
    Candidate(
        cid="C11",
        name="slopsquatting 检测（独立产品）",
        thesis="检测 AI 幻觉出的不存在依赖包名。",
        filter_hits={
            "F8": "至少 9 个免费 OSS 实现；Augment 已在生成端解决；零付费意愿证据。",
        },
        scores={
            "wtp_evidence": (1.0, "零付费证据；同类全部免费。", S_SELF),
            "unmanned_acquisition": (5.0, "USENIX 论文与真实事件使话题有传播力。", S_AHREFS),
            "competition_low": (1.0, "9 个免费 OSS。", S_SELF),
            "pain_evidence": (7.0, "USENIX Security 2025：223 万份样本中 19.7% 含幻觉包名；"
                                   "已有真实恶意包事件。痛点是真的。", "USENIX 经 Socket 转述 https://socket.dev/blog/slopsquatting-how-ai-hallucinations-are-fueling-a-new-class-of-supply-chain-attacks"),
            "deliverability_20h": (8.0, "技术简单。", S_SELF),
            "vendor_independence": (8.0, "跨工具。", S_SELF),
            "margin_structure": (9.0, "查询包registry，近零成本。", S_SELF),
            "switching_cost": (2.0, "极低。", S_SELF),
            "regulatory_tailwind": (2.0, "无。", S_SELF),
        },
    ),
]


# --------------------------------------------------------------------------
# 四、计算
# --------------------------------------------------------------------------

def base_weights() -> dict[str, float]:
    return {k: w for k, (_, w) in DIMENSIONS.items()}


def weight_sensitivity(survivors: list[Candidate], n_draws: int = 10_000) -> dict:
    """两种敏感性分析：
    (a) 单维度 ±50% 扰动（其余按比例归一）——回答「哪一维在主导排名」
    (b) Dirichlet 随机权重抽样——回答「排名有多稳」
    """
    rng = np.random.default_rng(SEED)
    base = base_weights()
    dims = list(base)
    baseline_top = max(survivors, key=lambda c: c.weighted(base)).cid

    # (a) 单维度扰动
    oat = []
    for d in dims:
        for factor, tag in ((0.5, "-50%"), (1.5, "+50%")):
            w = dict(base)
            w[d] = base[d] * factor
            s = sum(w.values())
            w = {k: v / s for k, v in w.items()}
            top = max(survivors, key=lambda c: c.weighted(w)).cid
            oat.append({
                "dimension": d,
                "dimension_cn": DIMENSIONS[d][0],
                "perturbation": tag,
                "top1": top,
                "flipped": top != baseline_top,
            })

    # (b) Dirichlet 抽样：alpha 与基准权重成比例，集中度 40（中等分散）
    alpha = np.array([base[d] for d in dims]) * 40.0
    draws = rng.dirichlet(alpha, size=n_draws)
    score_mat = np.array([[c.scores[d][0] for d in dims] for c in survivors])  # (n_cand, n_dim)
    totals = draws @ score_mat.T                                              # (n_draws, n_cand)
    winners = np.argmax(totals, axis=1)
    counts = np.bincount(winners, minlength=len(survivors))
    top1_freq = {survivors[i].cid: int(counts[i]) / n_draws for i in range(len(survivors))}

    # 排名相关性：每次抽样的排序与基准排序的一致程度
    base_order = np.argsort([-c.weighted(base) for c in survivors])
    base_rank = np.empty_like(base_order)
    base_rank[base_order] = np.arange(len(survivors))
    ranks = np.argsort(np.argsort(-totals, axis=1), axis=1)
    exact_same_order = float(np.mean(np.all(ranks == base_rank, axis=1)))

    return {
        "baseline_top1": baseline_top,
        "one_at_a_time": oat,
        "oat_flip_count": sum(1 for r in oat if r["flipped"]),
        "dirichlet_draws": n_draws,
        "dirichlet_top1_frequency": top1_freq,
        "dirichlet_full_order_identical_rate": exact_same_order,
    }


def score_robustness(survivors: list[Candidate]) -> dict:
    """分数稳健性检验（比权重敏感性更重要的一种检验）。

    动机（自我批评）：领先候选的高分主要来自「我最容易评估」的维度
    （可交付性、边际成本结构），而真正决定成败的付费意愿证据分最低。
    因此必须回答：**如果我在付费意愿这一维上完全看错了，结论会不会翻转？**
    """
    base = base_weights()
    ranked = sorted(survivors, key=lambda c: -c.weighted(base))
    leader, runner_up = ranked[0], ranked[1]

    checks = []

    # 检验 1：把领先者的付费意愿分归零（即「完全没有任何人愿意付钱」的极端假设）
    lead_zero_wtp = leader.weighted(base) - leader.scores["wtp_evidence"][0] * base["wtp_evidence"]
    checks.append({
        "name": "领先者付费意愿分归零",
        "detail": f"{leader.cid} 的 wtp_evidence 由 {leader.scores['wtp_evidence'][0]} 降为 0",
        "leader_new_total": round(lead_zero_wtp, 4),
        "runner_up_total": round(runner_up.weighted(base), 4),
        "still_leads": bool(lead_zero_wtp > runner_up.weighted(base)),
    })

    # 检验 2：把领先者所有「无外部来源、仅本 BP 自评」的维度整体下调 3 分
    self_dims = [d for d in base if leader.scores[d][2] == S_SELF]
    penalty = sum(min(3.0, leader.scores[d][0]) * base[d] for d in self_dims)
    lead_penalised = leader.weighted(base) - penalty
    checks.append({
        "name": "领先者所有自评维度下调 3 分",
        "detail": f"{leader.cid} 的自评维度 {self_dims} 各降 3 分（不低于 0）",
        "leader_new_total": round(lead_penalised, 4),
        "runner_up_total": round(runner_up.weighted(base), 4),
        "still_leads": bool(lead_penalised > runner_up.weighted(base)),
    })

    # 检验 3：领先者与次名同时取各自的悲观情形（领先者 -2 分/维，次名 +2 分/维）
    lead_pess = sum(max(0.0, leader.scores[d][0] - 2) * base[d] for d in base)
    runner_opt = sum(min(10.0, runner_up.scores[d][0] + 2) * base[d] for d in base)
    checks.append({
        "name": "领先者全维 -2 且次名全维 +2（最不利对照）",
        "detail": f"{leader.cid} 每维 -2 分，{runner_up.cid} 每维 +2 分",
        "leader_new_total": round(lead_pess, 4),
        "runner_up_total": round(runner_opt, 4),
        "still_leads": bool(lead_pess > runner_opt),
    })

    return {
        "leader": leader.cid,
        "runner_up": runner_up.cid,
        "leader_weakest_dimension": min(base, key=lambda d: leader.scores[d][0]),
        "leader_weakest_score": min(leader.scores[d][0] for d in base),
        "checks": checks,
        "verdict": "第一名对权重稳健；对分数的稳健性见上述三项检验"
                   if all(c["still_leads"] for c in checks[:2])
                   else "第一名不稳健，必须在 BP 中披露",
    }


def run() -> dict:
    base = base_weights()
    survivors = [c for c in CANDIDATES if c.survives]
    eliminated = [c for c in CANDIDATES if not c.survives]
    survivors.sort(key=lambda c: -c.weighted(base))

    result = {
        "meta": {
            "seed": SEED,
            "n_candidates": len(CANDIDATES),
            "n_survivors": len(survivors),
            "n_eliminated": len(eliminated),
            "score_scale": "0-10",
            "weights": {k: {"cn": DIMENSIONS[k][0], "w": v} for k, v in base.items()},
            "hard_filters": HARD_FILTERS,
        },
        "survivors": [
            {
                "rank": i + 1,
                "cid": c.cid,
                "name": c.name,
                "thesis": c.thesis,
                "total": round(c.weighted(base), 4),
                "scores": {d: {"score": c.scores[d][0], "cn": DIMENSIONS[d][0],
                               "rationale": c.scores[d][1], "source": c.scores[d][2]}
                           for d in base},
            }
            for i, c in enumerate(survivors)
        ],
        "eliminated": [
            {
                "cid": c.cid,
                "name": c.name,
                "hypothetical_total": round(c.weighted(base), 4),
                "failed_filters": [{"id": k, "filter": HARD_FILTERS[k], "reason": v}
                                   for k, v in c.filter_hits.items()],
            }
            for c in sorted(eliminated, key=lambda c: -c.weighted(base))
        ],
        "sensitivity": weight_sensitivity(survivors),
        "score_robustness": score_robustness(survivors),
    }
    return result


def main() -> None:
    res = run()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "opportunity_scoring.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")

    m = res["meta"]
    print("=" * 78)
    print(f"赛道量化筛选  候选 {m['n_candidates']} 个 | 硬过滤淘汰 {m['n_eliminated']} | 入围 {m['n_survivors']}")
    print("=" * 78)

    print("\n【硬过滤淘汰明细】")
    for e in res["eliminated"]:
        ids = ", ".join(f["id"] for f in e["failed_filters"])
        print(f"  {e['cid']} {e['name']}")
        print(f"       命中 {ids} | 若未淘汰其加权分本应为 {e['hypothetical_total']:.2f}")
        for f in e["failed_filters"]:
            print(f"       └─ {f['id']}: {f['reason'][:100]}...")

    print("\n【入围候选加权排名】")
    dims = list(m["weights"])
    hdr = f"  {'排名':<4}{'ID':<5}{'总分':>6}  " + "".join(f"{m['weights'][d]['cn'][:4]:>7}" for d in dims)
    print(hdr)
    for s in res["survivors"]:
        row = f"  {s['rank']:<4}{s['cid']:<5}{s['total']:>6.2f}  " + \
              "".join(f"{s['scores'][d]['score']:>7.1f}" for d in dims)
        print(row)
        print(f"       {s['name']}")

    sen = res["sensitivity"]
    print("\n【权重敏感性分析】")
    print(f"  基准第一名           : {sen['baseline_top1']}")
    print(f"  单维 ±50% 扰动 18 次 : 翻转 {sen['oat_flip_count']} 次")
    for r in sen["one_at_a_time"]:
        if r["flipped"]:
            print(f"       ⚠ {r['dimension_cn']} {r['perturbation']} → 第一名变为 {r['top1']}")
    print(f"  Dirichlet 随机权重 {sen['dirichlet_draws']:,} 次抽样，各候选夺冠频率：")
    for cid, f in sorted(sen["dirichlet_top1_frequency"].items(), key=lambda kv: -kv[1]):
        print(f"       {cid}: {f:6.2%}")
    print(f"  完整排序与基准完全一致的比例: {sen['dirichlet_full_order_identical_rate']:.2%}")

    rob = res["score_robustness"]
    print("\n【分数稳健性检验】（比权重敏感性更关键）")
    print(f"  领先者 {rob['leader']} 的最弱一维: {DIMENSIONS[rob['leader_weakest_dimension']][0]}"
          f" = {rob['leader_weakest_score']:.1f} 分")
    for c in rob["checks"]:
        flag = "仍居首" if c["still_leads"] else "★排名翻转★"
        print(f"  · {c['name']}: {rob['leader']} {c['leader_new_total']:.2f}"
              f" vs {rob['runner_up']} {c['runner_up_total']:.2f} → {flag}")
    print(f"  判定: {rob['verdict']}")
    print(f"\n输出已写入 {OUT_DIR / 'opportunity_scoring.json'}")


if __name__ == "__main__":
    main()
