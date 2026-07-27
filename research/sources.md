# 事实底稿 · CursorFlow AI 商业计划书

**基准日：2026-07-27**
**用途：本文件是 BP 中每一个事实性陈述的唯一溯源入口。`model/assumptions.py` 中的每个常量都必须能在此找到对应条目。**

---

## 0. 证据分级制度

| 等级 | 含义 | 建模用法 |
|---|---|---|
| **A** | 一手权威：法规原文、SEC 备案、政府统计、厂商官方定价页/文档、有明确样本量的调研原文 | 可直接采用 |
| **B** | 有样本量但方法学有偏：自报告问卷、平台自有数据、单一供应商口径 | 采用，取区间下沿 |
| **C** | 个案 / 轶事 / 无法核实样本量的二手汇编 / AI 内容农场 | **禁止作为建模输入**，仅用于定性方向 |
| **D** | 无公开可靠数据 | 明示为类比推算，做敏感性分析 |

**污染警告：** 本轮检索中，获客渠道与独立开发者成功率两个主题的流通数字大量来自 AI 生成的 SEO 内容农场（trendix.tech、saasranger.com、hub.causo.ai、uprowshub.com、markaicode.com、jakeinsight.com、gitautoreview.com、weavai.app、aicodereview.cc、getoptimal.ai、basethread.ai、ccmd.dev、bestaiweb.ai 等）。它们互相引用、层层放大同一个未经核实的源头（多数追溯到 RockingWeb 2025）。**在别处再次遇到相同数字，不构成独立印证。**

**详细底稿分列于同目录三份文件：**
- `BENCHMARKS.md` — 九节基准数据册（漏斗、流失、获客、成功率、失败率、LLM 成本、基础设施、收款税务、局限）
- `competitive-brief-2026-07-27.md` — 29 个产品的定价核实与 8 项权威研究溯源
- `RISK_METHODOLOGY.md` — Kelly / 风险调整收益 / 蒙特卡洛的公式手册，34 条带 URL 出处

---

## 1. 平台事实：Cursor 生态（决定"能不能做 Cursor 插件生意"）

### 1.1 变现渠道被合同封死 [A]

Cursor Marketplace Publisher Terms 第 3.1 条原文：

> "Anysphere offers the Marketplace to publishers free of charge. By publishing your Plugin on the Marketplace, you agree that the Plugin will be made available to Users **at no cost**. Publisher agrees that it will **not charge Users any fees, whether directly or indirectly**, for access to or use of a Plugin through the Marketplace."

- 来源：https://cursor.com/marketplace-publisher-terms （2026-07-27 抓取）
- 配套约束 [A]：所有插件**必须开源**；每次更新需人工审核；目前为策展制非开放注册；提交渠道为 Slack 或直接邮件 Anysphere 员工。来源：https://cursor.com/help/security-and-privacy/marketplace-security
- 第 3.2 条：发布者须授予 Anysphere 免版税、可再许可、可转让的许可，且**该条优先于插件自身的开源许可证**。
- 第 8.1 条：发布者须就插件相关的一切索赔（含安全漏洞、数据泄露）为 Anysphere 抗辩并赔偿。

**推论：任何以"上架 Cursor 插件市场变现"为前提的商业模型，前提不成立。** 不是不方便，是合同禁止。

### 1.2 扩展分发只能走 Open VSX [A]

- Cursor 应用内扩展库使用 Open VSX，经自有代理 `marketplace.cursorapi.com` 路由，并做自动化恶意软件与供应链扫描。来源：https://cursor.com/help/customization/extensions
- 微软自 2020-09 的许可条款限定其闭源扩展仅用于微软自家产品，2025-04-03 的 C/C++ 扩展 v1.24.5 起在二进制层面实际执行。受影响：Remote Access、Pylance、C/C++、C#。来源：https://www.theregister.com/software/2025/04/24/microsoft-subtracts-c/c-extension-from-vs-code-forks/721912 [主流媒体]
- Open VSX 由 Eclipse 基金会管理，**无任何付费/订阅/分成基础设施** [A]。

### 1.3 平台方已自营两个直接竞品 [A]

**Bugbot**（AI code review）
- **2025-07-24/25 GA**，内测期已审查 100 万+ PR。来源：https://cursor.com/docs/bugbot.md
- 2026-05 从席位制改为**纯用量计费**，官方口径平均 **$1.00–1.50/次运行**（注意：是每次 run 而非每个 PR，默认每次 push 都触发）。来源：https://cursor.com/help/account-and-billing/bugbot-usage-based-billing
- 2026-06-10 由自研 Composer 2.5 驱动后**提速 3 倍、每次多找 10% bug、成本降约 22%**。来源：https://cursor.com/changelog/bugbot-updates-june-2026
- **支持 GitHub、GitLab（含自托管）、Bitbucket（含 Data Center）** —— 此点已用官方文档证伪所有"Bugbot 仅支持 GitHub"的二手说法。来源：https://cursor.com/docs/bugbot、https://cursor.com/docs/integrations/gitlab
- 不作为独立产品销售，须有 Cursor Individual 或 Teams 订阅。
- 残留缝隙 [A]：GitLab 集成要求 GitLab 付费版（Premium/Ultimate，依赖 Project Access Token），自托管另需 Cursor Teams/Enterprise。**GitLab Free 用户仍无 Bugbot** —— 但这是个很小且付费能力弱的细分。

**Cursor Security Review**（安全审计代理）
- **2026-04-30** 在 Teams 与 Enterprise 进入 beta。来源：https://cursor.com/changelog/04-30-26、https://cursor.com/docs/security-agents
- 覆盖漏洞、鉴权回归、隐私与数据处理风险、**agent 工具自动批准风险**、**提示词注入攻击**。
- 官方明说可挂接第三方 SAST / SCA / 密钥扫描器的 MCP server，并承认自身不能替代依赖与 CVE 覆盖。

### 1.4 模型成本的结构性差距 [A]

| 项 | 单价（USD / 百万 token） |
|---|---|
| Composer 2.5（Cursor 自研，驱动 Bugbot） | 输入 $0.5 / 输出 $2.5 |
| Claude Sonnet 5（引导价，至 2026-08-31） | 输入 $2 / 输出 $10 |
| Claude Sonnet 5（2026-09-01 起） | 输入 $3 / 输出 $15 |
| Cursor Token Rate（Teams/Enterprise 第三方模型附加） | 额外 $0.25 / 百万 token |

来源：https://cursor.com/docs/models-and-pricing.md、https://platform.claude.com/docs/en/about-claude/pricing

**推论：在"用前沿模型跑代码审查"这件事上，第三方对 Cursor 有约 4–6 倍的输入成本劣势，且无法靠工程优化弥补。** 但见 §4.1 —— 这个劣势的实际影响被我先前高估了。

### 1.5 团队效能分析已被以不可复制的方式占据 [A]

Cursor 的 AI 代码归因**完全在设备端完成**：对每一行 AI 建议做签名，与后续同一作者的 git commit 逐行比对，只上传行数统计。第三方无论如何做不到同等精度（只能靠启发式 diff）。
- 来源：https://cursor.com/docs/account/teams/ai-code-tracking-api
- 配套 API：Admin API、Analytics API、AI Code Tracking API（**均 Enterprise 限定**，后者仍为 Alpha）
- 官方自述的盲区：Background Agents 与 Cursor CLI 未实现归因；多根 workspace 不支持；commit 必须在写码的同一台机器完成；自动格式化会使 diff 签名失效。

### 1.6 唯一保留自主商业化能力的接入点：MCP [A]

- Cursor 支持 stdio / SSE / Streamable HTTP 三种传输，支持 OAuth，Marketplace 条目可一键安装。来源：https://cursor.com/docs/mcp
- **Publisher Terms 只约束"通过 Marketplace 收费"，你在自己托管的服务侧收费不受其限制。**
- 约束 [A]：Enterprise 管理员可在 Team Settings > MCP Configuration 按命令模式/URL 模式白名单，并做**工具级白名单**。**你的分发生死取决于对方 CISO。**

### 1.7 所有权变更 [A]

- SpaceX 于 **2026-06-16 签署收购 Anysphere 的合并协议**，隐含股权价值 **600 亿美元**，全股票，SpaceX 全资子公司 X67 Inc. 反向并入 Anysphere，预计 2026 Q3 交割。
- 来源：SEC 8-K 原文 https://www.sec.gov/Archives/edgar/data/1181412/000162828026043411/spaceexplorationtechnologi.htm ；路透 https://www.reuters.com/legal/transactional/spacex-buy-anysphere-60-billion-2026-06-16/
- 佐证：Cursor 官方定价文档已将 Grok 4.5 标注为"由 Cursor 与 **SpaceXAI** 联合训练"。
- **含义：Publisher Terms 是可单方修订的合同，新所有者无义务延续现有生态政策。**

### 1.8 Cursor 规模（仅列可信口径）

| 指标 | 数值 | 等级 |
|---|---|---|
| ARR（2025-06，Series C 官方博客） | $5 亿+ | A |
| ARR（2025-11，Series D 官方博客） | $10 亿+ | A |
| ARR（2026-02，媒体转引公司数字） | 约 $20 亿 | B |
| 估值（Series D，2025-11） | $293 亿 | A |
| 员工数（2025-11 官方） | 300+ | A |

来源：https://cursor.com/blog/series-c 、https://cursor.com/blog/series-d
**已判定不可靠：** Revelio Labs 称 2026-03 有 1,777 人，且称 2023 年即有 1,715 人 —— 与 Anysphere 2023 年尚为十几人初创的公开事实直接矛盾，判定为实体匹配错误。

---

## 2. 需求侧事实

### 2.1 采用率上升、信任度下降（对"验证类"产品最重要的单一信号）[A]

Stack Overflow Developer Survey 2025（**49,000+ 样本 / 177 国**，2025-05-29 至 06-23 field，2025-07-29 发布）
- 使用或计划使用 AI 工具：**84%**（2024 年 76%）
- 专业开发者每日使用：**51%**
- **信任 AI 输出准确性：仅 29%**（2024 年为 40%，**连续第二年下滑**）；**46% 明确不信任**
- 来源：https://survey.stackoverflow.co/2025/ai/

JetBrains State of Developer Ecosystem 2025（24,534 样本 / 194 国）
- 经常使用 AI 工具：85%；使用专门 AI 编码助手/agent/编辑器：62%
- 来源：https://blog.jetbrains.com/research/2025/10/state-of-developer-ecosystem-2025/

JetBrains AI Pulse Survey（10,000+ 样本，2026-01 field）
- 工作场景使用率：Copilot 29%、**Cursor 18%**、Claude Code 18%
- **这是 Cursor 份额最可靠的单一数字。** 各类"市场份额 X%"因分母定义（用户数/收入/企业渗透/使用时长）不同而互不可校验，不得入模。

### 2.2 审阅负担：本轮找到的最硬痛点证据 [A]

论文《"An Endless Stream of AI Slop": How Developers Discuss the Burden of AI-Assisted Software Development》
- 对 Reddit / HN 的 **15 个讨论串、1,154 条帖子**做定性编码分析
- 核心发现："公地悲剧"——作者的效率收益外部化为审阅者的成本。一个团队报告每天 30 个 PR、6 个审阅者。审阅者自述"是第一个看到这段代码的人类"、"被当成免费的提示工程师"
- 来源：https://arxiv.org/abs/2603.27249
- **不可辩驳的一手事件**：curl 项目因 AI 生成的漏洞报告消耗维护者时间却无有效发现，**关闭了 bug bounty 项目**（lists.haxx.se，2026-01）。Apache Log4j 2、Godot 报告类似问题。

### 2.3 AI 代码可维护性劣化 [A，但须注意利益冲突]

GitClear《The Maintainability Gap》（2026-06，与 GitKraken 合作，分析 2023–2026 的 **6.23 亿行**代码变更）
- 代码块重复 **+81%**（每百万变更行从 40.3 升至 73.0）
- commit 内 copy/paste **+41%**；错误屏蔽构造 **+47%**；两周 churn **+15%**
- moved code（重构）从 2022 年的 21% 跌至 2026 年的 **3.8%**；长期遗留代码维护 **−74%**
- 来源：https://www.gitclear.com/the_ai_code_quality_maintainability_gap
- **利益冲突警示：GitClear 自己就是卖这个度量产品的厂商。** 数据规模真实，但不可用它去打它自己的产品。

### 2.4 成本失控：真实用户正在流血 [A，但为轶事非统计]

Hacker News 一手帖：
- 用户被 Cursor 从订阅静默切到 On-Demand 按 token 计费，4 天烧掉 $20 不知情，2.5 周约 $60，退款被拒。https://news.ycombinator.com/item?id=46966879
- 取消 2 个 Cursor Ultra：月消耗从稳定 $60–100 涨到 $500+，预测 $1,600/月；真实用户输入约 4k token，**缓存读取约 2,100 万 token**，单次调用约 $12。核心抱怨："成本与你能观察到的任何东西解耦了"。https://news.ycombinator.com/item?id=46544838
- Ask HN: How are you keeping AI coding agents from burning money? —— **仅 8 分、32 条评论，弱信号**。https://news.ycombinator.com/item?id=47559293

### 2.5 CI 中 agent 的安全漏洞：四个独立权威源 [A]

- **微软威胁情报**（2026-06-05）：Claude Code GitHub Action 的 Read 工具绕过 Bubblewrap 沙箱，可读 `/proc/self/environ` 取得未脱敏的 `ANTHROPIC_API_KEY`；Anthropic 于 2026-05-05 在 Claude Code 2.1.128 修复。https://www.microsoft.com/en-us/security/blog/2026/06/05/securing-ci-cd-in-agentic-world-claude-code-github-action-case/
- **Aikido "PromptPwnd"**：GitHub Actions / GitLab CI 中结合 Gemini CLI、Claude Code、OpenAI Codex、GitHub AI Inference 的新型漏洞类别，首次真实演示 AI 提示注入攻陷 CI/CD。https://www.aikido.dev/blog/promptpwnd-github-actions-ai-agents
- **Noma Security "GitLost"**：未认证攻击者在公开仓库发一个 issue，即可让 GitHub Agentic Workflows 泄露同组织私有仓库内容。https://noma.security/blog/gitlost-how-we-tricked-githubs-ai-agent-into-leaking-private-repos/
- **CSA 研究简报**（2026-05-03，PDF）：系统梳理该攻击面，指出 `pull_request` / `issues` / `issue_comment` 事件自动触发、**无需维护者任何交互**。https://labs.cloudsecurityalliance.org/wp-content/uploads/2026/05/CSA_research_note_ai_github_actions_security_20260503-csa-styled.pdf

### 2.6 幻觉依赖包（slopsquatting）[A]

- USENIX Security 2025：**223 万份** LLM 生成代码样本中，约 **19.7%** 含至少一个幻觉包名；20 万+ 唯一幻觉包名，**58% 在 10 次以上重复出现**。经 Socket、CSA 多方转述：https://socket.dev/blog/slopsquatting-how-ai-hallucinations-are-fueling-a-new-class-of-supply-chain-attacks
- 已确认真实事件（Aikido，2026-02）：恶意 npm 包 `unused-imports`（对 `eslint-plugin-unused-imports` 的幻觉简写），即便已被 npm security-hold，2026-02 初仍有约 233 次周下载；`react-codeshift` 源自一次含 47 个 AI 生成 agent skill 文件的提交，扩散到 **237 个仓库**。https://www.aikido.dev/blog/slopsquatting-ai-package-hallucination-attacks

### 2.7 官方主动让出的位置 [A]

MCP 官方 Registry 文档原文：

> "The MCP Registry focuses on namespace authentication and metadata hosting, while relying on the broader ecosystem for security scanning of actual server code."

- 来源：https://github.com/modelcontextprotocol/registry/blob/main/docs/modelcontextprotocol-io/about.mdx
- Registry 于 2025-09-08 上线预览，至 2026-07 **仍在 preview**，无数据持久性保证。https://blog.modelcontextprotocol.io/posts/2025-09-08-mcp-registry-preview/
- **这是本轮调研中唯一一例平台方白纸黑字让出的位置。**

---

## 3. 监管事实：哪些是真的，哪些是营销话术

### 3.1 真实且紧迫：EU CRA [A]

法规 EU 2024/2847（Cyber Resilience Act）
- 2024-12-10 生效
- **2026-06-11**：合格评定机构通报框架（Chapter IV）适用
- **2026-09-11**：第 14 条报告义务适用 —— 主动被利用的漏洞需 **24 小时预警 / 72 小时通报 / 14 天最终报告**，经 ENISA 单一报送平台。**适用于已在欧盟市场上的存量产品**
- **2027-12-11**：全面适用，含 Annex I 基本要求、**机器可读 SBOM（至少覆盖顶层依赖）**、合格评定、CE 标志
- 来源：https://eur-lex.europa.eu/eli/reg/2024/2847/oj/eng 、https://digital-strategy.ec.europa.eu/en/policies/cra-summary

**但恐惧驱动比营销宣称的弱得多 [A]：**
- **Art. 64(10)：开源软件管理者（Art. 3(14) steward）完全不受行政罚款约束。自然人不构成 steward。** 来源：https://digital-strategy.ec.europa.eu/en/policies/cra-open-source
- 微型/小型企业制造商对 Art.14(2)(a)、14(4)(a) 的时限失误亦豁免罚款（Art. 64(10)(a)）
- **推论：€15M / 2.5% 营业额的罚款恐惧主要落在有规模的制造商身上，而这些客户走采购流程、不刷信用卡。**
- 另：GitHub 的 SBOM 导出（SPDX）对所有云仓库**免费**。https://github.blog/enterprise-software/governance-and-compliance/introducing-self-service-sboms/

### 3.2 明令禁用的三条叙事 [A]

**① "EU AI Act 要求审计 AI 生成的代码" —— 纯属营销话术。**
AI Act 监管的是 AI 系统**作为产品本身**（招聘、信贷、医疗器械等高风险用途），**完全不监管用 AI 编写普通商业软件**。且 Digital Omnibus 已于 **2026-07-27（本基准日）生效**，将高风险义务从 2026-08-02 推迟至 **2027-12-02**。Art.50 透明度义务管的是"你的产品是不是 AI、有没有告知用户"，与"你用 AI 写代码"无关。
→ **写进 BP 会被任何懂行的 CISO 当场戳穿。**

**② "美国 SSDF / EO 14028 构成强制要求" —— 联邦强制力已实质瓦解**，在 EO 14306（2025-06）与 OMB M-26-05（2026-02）之后。

**③ "AI 代码度量是新品类空隙" —— 它是 2026 年的入场券，不是空隙。**
LinearB、Swarmia、DX、Waydev、Faros **五家全部已上线**；DX 已做到行级归因（`AI additions ÷ (AI additions + human additions)`）并按 AI 占比分五档对比 revert rate；Waydev 把 AI 成本度量（Tokenmeter）做成**免费**获客层；Faros 官方 LinkedIn 公开发文称"我们的代码有多少是 AI 生成的"是个**错误的问题**。

---

## 4. 竞争与单位经济学

### 4.1 【重大更正】LLM 推理成本冲突的消解

**冲突：** 竞品调研称 Ellipsis 一次中等 PR 审查成本 **$0.74**，据此推得 Sourcery $12/席位毛利率仅 38%；基准调研自下而上推算 Sonnet 5 一次 10 文件 PR 审查仅 **$0.071**。相差约 10 倍。

**消解结论（已用一手来源确认）：$0.74 是售价，不是成本。竞品调研把价格误读成了成本。**

Ellipsis 官方定价页 [A] https://www.ellipsis.dev/pricing 的计费结构为：**token 按 Claude 原价透传（无加价）+ CPU $0.142/vCPU-hour + 内存 $0.024/GB-hour + 平台费 = token 用量的 100%**。故 $0.74 = token $0.37 + 平台费 $0.37。代码审查场景**不启动沙箱**，只付 token 与平台费。

Ellipsis 官方工程博客 [A] https://www.ellipsis.dev/blog/lessons-from-building-llm-agents （2026-05-01，作者 Nick Bradford）披露其真实 COGS：

```
# Cost per agent invocation (approximate)
# Before optimization: $0.80 - $2.50
# After tiered models:  $0.30 - $0.90
# After incremental:    $0.15 - $0.60
# After caching:        $0.08 - $0.35
#
# Production average:   $0.12 per code review
```

三项架构手段：**分层模型路由**（简单任务走便宜模型，降本 60–70%）、**增量处理**（只重审变更文件，降 token 40–50%）、**缓存去重**（仓库元数据、风格指南、常用文件跨调用缓存）。

**对账：** 基准调研的自下而上估算 $0.071 与 Ellipsis 生产均值 $0.12 属同一量级（差 1.7 倍），**互相印证，冲突消解**。$0.071 略偏乐观但量级正确。

**因此必须更正的结论：**

| 原结论（错误） | 更正后（正确） |
|---|---|
| $0.74 是所有人的 COGS 地板 | $0.74 是 Ellipsis 的**售价**；其 COGS 生产均值为 **$0.12** |
| Sourcery $12/席位毛利率约 38% | 按 20 次/月 × $0.12 = $2.40 COGS → **毛利率约 80%**；即便按最差档 $0.35 计，也有约 42% |
| "低价席位制 + 每次跑 LLM"结构上无毛利 | **成本是架构问题，不是结构性宿命。** 朴素实现（$0.80–2.50/次）确实亏损，做了分层路由+增量+缓存的实现（$0.12/次）毛利健康 |

**对硬过滤器第 6 条的修正：** 原条款"采用低价席位制 + 每次操作跑 LLM 的结构即淘汰"**收窄**为——"采用每次操作跑 LLM 的结构，且**未做分层路由 / 增量处理 / 缓存**三件套架构"才淘汰。一个称职的单人开发者有能力实现这三项。

**但真正的约束依然成立**，只是理由不同：AI 代码审查赛道的进入障碍不是单位经济学，而是 **(a) GitHub Copilot $10/月含 code review 构成的价格天花板；(b) 真实玩家 30+ 家；(c) 开源免费已是行业标配（CodeRabbit / Sourcery / Greptile / DeepSource / Socket / Codacy / Snyk / Semgrep 全部免费）；(d) 单人没有分发渠道。**

**遗留未消解项：** Ellipsis 官方定价页与博客 CTA 均显示 "No per-seat fees"（用量制），但两个二手来源（agentrank.tech、codereviewr.app）称其已改为 $20/开发者/月无限用。**以一手页面为准，$20/dev/mo 标注为未核实。**

### 4.2 价格天花板与开源免费 [A]

三个必须记住的数字：
1. **$10** —— GitHub Copilot Pro 含 AI code review 的价格，整个赛道的价格天花板
2. **$0.12** —— Ellipsis 公布的真实生产均值 COGS（更正前误为 $0.74）
3. **$0** —— 开源项目在 CodeRabbit / Sourcery / Greptile / DeepSource / Socket / Codacy / Snyk / Semgrep 处的价格，以及 Waydev Tokenmeter 的价格

其他锚点 [A]：CodeRabbit 用量计费 $1.00/credit（1 credit = 4 文件，即 **$0.25/文件**，https://docs.coderabbit.ai/management/usage-based-addon ）；CodeRabbit Pro $24/人/月（年付）；Greptile $30/席位含 50 次审查，超出 $1.00/次。

### 4.3 赛道已进入整合期 [A/B]

- Sonar 收购 Gitar
- **Snyk：ARR $326M 但同比仅增 7%**（前一年 27%），估值被 BlackRock 从 $7.4B 下调至 $3.7B，2026-02 换 CEO
- CodeRabbit：据 Sacra **估算** 2026-04 达 $40M ARR（同比 +700%），$60M B 轮（2025-09，$550M 估值），累计融资 $88M。https://sacra.com/c/coderabbit/ [B，为估算非公司披露]
- Greptile：Benchmark 领投 $25M A 轮。https://www.greptile.com/blog/series-a
- **Haystack 实质已死**：官网 footer 仍写 "Copyright © 2023"，页面残留 "Start jj trial" 占位文字，全站不提 AI

### 4.4 免费开源工具过剩：被低估的头号风险 [A]

几乎每个候选方向都已存在 4–12 个免费开源实现：
- **slopsquatting 检测（≥9 个）**：package-reality-check、slopgate、Phantom Guard、supply-scan、slop-scan、ghostimport、slopcheck、sentinel-ai、SlopScan
- **MCP 安全扫描（≥4 个 + NVIDIA）**：jsandov/mcp-audit、GaboITB/mcp-shield（17 个检测器）、glatinone/mcpscan、chaaiitanya/mcp-audit、**NVIDIA/SkillSpector**（68 个漏洞模式、17 个类别、自带 MCP server 形态）
- **AI 代码溯源（≥5 个）**：agentdiff、invariant-systems-ai/aiir、securestor/ai-footprint、om13rajpal/pedigree、agentmark
- **死代码检测**：**Knip**，11,752 stars、260 贡献者、603 个 release、ISC 免费、自带 `@knip/mcp`，Vercel 用它删掉约 30 万行。https://github.com/webpro-nl/knip

**这不是"没人做过"的空白市场，而是"做的人太多、但都不收钱"的市场。**

### 4.5 企业销售与"零人工"的硬冲突 [B]

- 该赛道 50 人规模的年合同额落在 **$10K–$50K**，中位约 $25K–35K
- **SOC 2 Type II 在 ACV 超过约 $50K 时是 gating（非有不可）**，审计周期 6–12 个月；企业销售周期 3–9 个月
- **$50K 以上的合同在 2026 年依然无法在零人类参与下成交** —— 安全问卷、MSA 红线谈判、DPA、供应商风险评估都需要能开会、能签字、能担责的自然人
- **这与"零人工"约束是硬冲突，必须正视**

---

## 5. 建模基准值（详见 `BENCHMARKS.md`）

### 5.1 漏斗 [A，ChartMogul 2026，200 个 B2B 软件产品]

| 指标 | 建模取值 | 等级 |
|---|---|---|
| 访客→注册（free trial，不要卡） | **4.5%** | A |
| 免费→付费（freemium，6 个月内） | **3.0%** | A |
| 免费→付费（trial，**要**卡） | **25%** | A |
| 每 1,000 访客产出付费客户（不要卡） | **1.35 人**（ChartMogul 原文 4.0） | 派生 |
| 每 1,000 访客产出付费客户（**要卡**） | **10.5 人** | A |

来源：https://chartmogul.com/reports/saas-conversion-report/
**注意：全样本 free-to-paid 中位数 8%，但分布是双峰的 —— 20% 低于 2.5%，23% 高于 25%，"几乎没人真的在 8%"。**

### 5.2 流失 [A/B]

| 指标 | 建模取值 | 等级 |
|---|---|---|
| 月度 logo churn（$10–50/月自助订阅） | **7.0%** | B |
| 隐含客户平均生命周期 | **14.3 个月** | 派生 |
| ARPA <$10/月的公司中 NRR>100% 的比例 | **仅 2.7%** | A |

来源：ChartMogul SaaS Retention Report（**2,100+ 家真实计费数据**）https://chartmogul.com/reports/saas-retention-report/
**不得在模型中假设 NRR > 100%。低客单价档的扩张收入循环基本不存在。**

### 5.3 获客 [A/B/C，本项目主要矛盾]

| 渠道 | 取值 | 等级 |
|---|---|---|
| 新页面 12 个月内进 Google 前 10 的概率 | **1.74%**（英文非空内容筛选后 6.11%） | A |
| 高搜索量词 12 个月内进前 10 的概率 | **0.3%** | A |
| HN 头版单次流量 | 10,000–30,000 UV / 24h | B |
| Product Hunt 7 日注册量 | 100–150（上限 450） | C |
| GitHub / VS Code Marketplace 安装→付费 | **无公开可靠数据** | D |

来源：Ahrefs **100 万个随机 URL** 追踪 12 个月 https://ahrefs.com/blog/how-long-does-it-take-to-rank-in-google-and-how-old-are-top-ranking-pages/

**串联推论（本项目最重要的一个数）：**
每 1,000 访客 → 45 注册 → **1.35 付费客户** → $25.65 新增 MRR。7% 月流失下稳态天花板 **19.3 个客户 / $366 MRR**。
**维持 $1,000 MRR 的稳态，需要每月持续 2,729 个精准访客。**

### 5.4 兼职惩罚 [B，本节最硬的可用信号]

MicroConf《State of Independent SaaS》2024（n=469，p.45）：**全职创始人的公司增速是兼职创始人的 2.2 倍**；开发者主导团队快 1.7 倍。
- 来源：https://microconf.com/state-of-indie-saas （PDF 需邮箱换取，本轮未获原文，引用官网带页码摘录，故降为 B）
- **推论：所有里程碑耗时应乘以 2.0–2.5。即便按乐观的全职 $1K MRR 中位耗时 12 个月，兼职情形应规划 24–30 个月。**

### 5.5 存活与失败 [A]

| 指标 | 取值 |
|---|---|
| 美国新设经营场所 1 年存活率 | 约 **79.6%** |
| 5 年存活率（全行业） | 约 **50%** |
| 10 年存活率（2013 队列） | **34.7%** |
| Show HN 项目年均死亡率 | 约 **9%**（n=10,000） |
| 首要失败原因 | **产品-市场不匹配 43%**（资金耗尽 70% 为终局症状而非根因） |

来源：BLS BED https://www.bls.gov/opub/ted/2024/34-7-percent-of-business-establishments-born-in-2013-were-still-operating-in-2023.htm ；CB Insights（n=431）https://www.cbinsights.com/research/report/startup-failure-reasons-top/ ；Anton Tarasenko https://antontarasenko.github.io/show-hn/

**口径差异必须明示：BLS 统计对象是有正雇员的经营场所，本项目零员工，严格说不在其统计总体内 —— 这是类比，不是直接适用。**
**对纯自有资金、零烧钱的项目，"资金耗尽"这个第一大终局原因基本不适用；真实风险几乎全部集中在 PMF 与时间机会成本上。**

### 5.6 基础设施 [A]

| 档位 | 月成本 |
|---|---|
| 极简（Cloudflare Workers + Neon + 域名） | **$10** |
| 标准（Vercel Pro + Supabase Pro + Workers + 杂项） | **$60**（建模基线） |

**在每月几千次调用量级，成本完全由固定订阅费主导，无需做复杂用量测算。**
Vercel Hobby 档**禁止商业用途**，一旦收费必须用 Pro（$20/月）。

### 5.7 收款 [A]

| 通道 | $9 | $19 | $29 | $49 |
|---|---|---|---|---|
| Stripe + Stripe Tax（自担 MoR） | 8.2% | 6.5% | 5.9% | 5.5% |
| Paddle | 10.6% | 7.6% | 6.7% | 6.0% |
| Lemon Squeezy | 12.6% | 9.6% | 8.7% | 8.0% |
| Polar Starter | 12.1% | 9.1% | 8.2% | 7.5% |
| Polar Pro（另 +$20/月） | 9.7% | 7.4% | 6.7% | 6.1% |

**建模按 8% 计提收款成本（MoR 方案，客单价 $19–$29）。客单价不应低于 $19 —— $9 档 MoR 有效费率高达 12%+。**
Polar Pro 在月流水约 $1,379 后比 Starter 划算。
GitHub Marketplace：抽 5%，GitHub 自任 MoR，但要求组织主体 + 域名验证 + 2FA + **月收入满 $500 才付款**。https://docs.github.com/en/site-policy/github-terms/github-marketplace-developer-agreement

### 5.8 无风险利率 [A]

- 美国 10 年期：**4.71%**（FRED DGS10，2026-07-23）
- 中国 10 年期：**1.73%**（中债国债收益率曲线，2026-07-24）

---

## 6. 风险量化方法论的三条禁令（详见 `RISK_METHODOLOGY.md`）

### 6.1 禁用 `g ≈ μ − σ²/2` 波动率拖累近似式 [A，已实测]

在创业级波动下**连符号都会算错**：

| μ | σ | 精确 g | 近似 μ−σ²/2 | 蒙特卡洛 g |
|---|---|---|---|---|
| 0.10 | 0.20 | 0.0790 | 0.0800 | 0.0791 |
| 0.30 | 0.60 | 0.1658 | 0.1200 | 0.1660 |
| **0.50** | **1.20** | **+0.1581** | **−0.2200** | **+0.1584** |

→ 一律使用精确式 + 蒙特卡洛交叉验证。

### 6.2 禁用"半 Kelly 保留 75% 增长率" [A，已实测]

该说法的严格来源是 Thorp 2006 eq.(7.7) 的**连续/对数正态近似** `c(2−c)`。用四档离散创业分布实测：

| 下注比例 | 实测保留的增长率 | 连续近似预测 |
|---|---|---|
| 0.25× Kelly | **54.1%** | 43.75% |
| 0.5× Kelly | **82.3%** | 75% |
| 2× Kelly | **52.9%** | **0%** |

→ 分数 Kelly 的折损比例**必须用本项目的离散分布实测**。

### 6.3 不把夏普 / 索提诺 / Omega 作为结论性指标 [A，已实测]

同一四档情景下：期望倍数 **2.05 倍**，但夏普 **−0.53**（rf=中国 10Y）/ **−0.57**（rf=美国 10Y）、索提诺 **−0.55**、Omega **0.29**。
这是 Jensen 不等式使然，不是矛盾。但把这组数字放进 BP 只会让读者得到相反印象。
→ **仅在方法论附录中作为"为何不适用于极度右偏分布"的说明材料出现。**

### 6.4 "年化收益率"的三种口径必须并列 [A，已实测]

同一分布产出三个互不相等的年化数字：

| 口径 | 数值 | 风险 |
|---|---|---|
| (a) 期望倍数先算再年化 `E[M]^(1/T)−1` | **+27.03%** | **最容易被误读为"预期收益"** |
| (b) 各档先年化再取期望 `E[M^(1/T)−1]` | **−41.57%** | 最悲观 |
| (c) 条件于未全损的几何均值 | **+35.99%** | **隐藏了 60% 的归零概率** |

→ BP 中任何"年化 XX%"必须紧跟口径说明，三种全部并列。

### 6.5 Kelly 在本情境的失效程度比通常认识更严重 [A]

- Samuelson 1971（PNAS）与 1979（JBF）两篇正式反对
- **Breiman 1961 的最优性证明全部是渐近结论**
- Thorp 自己给的量化例子：区分 1.0% 与 1.1% 优势的两个赌局，需要**两百万次试验**才有 84% 把握
- 单人创业一生的下注次数是个位数，**大数律完全不工作**
→ Kelly 仅作为"下注规模上限的参照"，绝不作为承诺。

### 6.6 一处文献错误的订正 [A]

Wiltbank & Boeker (2007) 天使投资研究中被广泛引用的"2.6 倍 / 3.5 年 ≈ 27% IRR"系**原报告计算错误**。
正确算法：2.6^(1/3.5) − 1 = **31.4%**（按平均值口径 31%，按逐笔现金流口径 30%）。
→ BP 引用该研究时须用订正值并注明。

---

## 7. 已知缺口清单（BP 中一律标注，不得当作事实）

### 7.1 阻断性未验证项（Gate 0）

**Paddle / Lemon Squeezy / Polar 是否接受中国大陆主体作为收款方（seller），三家官方渠道均无明确说明。**
- 已确认硬事实 [A]：**Stripe 不支持中国大陆主体开户**（https://stripe.com/global 支持地区列表不含中国大陆）
- 这是一个**二元的、前置的**风险：若三家全部不接受，整个"全球美元自助订阅"前提坍塌
- **可在一周内用几封邮件验证清楚，必须在投入任何开发工时之前完成**

### 7.2 无公开可靠数据（D 级，按类比推算处理）

1. 开发者工具类 SaaS 的年留存基准
2. GitHub / VS Code Marketplace 的安装→激活→付费转化
3. "多少比例的独立 SaaS 项目在 12 个月内仍有收入"（推算区间 50%–60%）
4. 单次 PR 审查的 token 消耗（本册为反推值，真实值可能有 2–3 倍偏差）
5. 本赛道的 PLG 自助转化率（搜到的数字全部来自无方法论的内容营销，不予采信）
6. 头号候选（agent CI 配置安全审计）的**直接付费意愿证据** —— 仅有 StepSecurity 的间接类比

### 7.3 原文未取得

- MicroConf《State of Independent SaaS》PDF（需邮箱换取）
- Baremetrics Open Benchmarks 实时数值（JS 动态渲染）
- OpenAI 官方定价页（两次抓取超时；GPT-5.6 定价未取得）
- Gartner 2026 Magic Quadrant 原文（仅有二手转述）

### 7.4 时效性陷阱（必须写入模型注释）

1. **Claude Sonnet 5 于 2026-09-01 涨价 50%**（$2/$10 → $3/$15）—— 任何跨越 9 月的测算不得使用现价
2. DeepSeek v4-pro 现价 $0.435/$0.87 为**促销价**，标准价 $1.74/$3.48（4 倍）
3. `deepseek-chat` 与 `deepseek-reasoner` 别名已于 **2026-07-24** 停用
4. Claude 4.7 及以后模型使用新分词器，**同样文本多产生约 30% token**

### 7.5 原始机会卡片中不可用的数据

`neeed.txt` 中的"机会价值分 50.2 / 综合评分 6.37 / 搜索量 50,000"来自本地启发式评分，**无外部可查证依据，不得作为任何决策输入**。

---

## 8. 本底稿的自我修正记录

诚实记录判断被推翻的过程，供 BP 正文引用：

1. **"Bugbot 仅支持 GitHub"** —— 错。官方文档确认支持 GitHub / GitLab / Bitbucket。据此提出的"去 GitLab 抢占 Bugbot 覆盖不到的地盘"路径**不存在**。
2. **"CRA 与 EU AI Act 共同驱动合规需求"** —— 错。AI Act 不监管用 AI 编写普通软件，且高风险义务已推迟至 2027-12-02。只有 CRA 是真的。
3. **"面向 Cursor Teams 客户做本地 AI 归因 + ISO 27001 证据包是最强候选"** —— 错。上游有 DX / LinearB / Jellyfish / Swarmia / Waydev 五家已建制平台，且找不到任何工程负责人抱怨"看不到这些数据"的一手帖子，需求证据为零。
4. **"$0.74 是 AI 代码审查的 COGS 地板，低价席位制结构上无毛利"** —— 错。$0.74 是售价（含 100% 平台费加价），Ellipsis 官方博客披露真实生产均值为 **$0.12/次**。成本是架构问题不是结构性宿命。该赛道的真实障碍是价格天花板与分发，不是单位经济学。
5. **计划初稿采用了 `g ≈ μ − σ²/2`** —— 错。在创业级波动下该近似式连符号都算错。
