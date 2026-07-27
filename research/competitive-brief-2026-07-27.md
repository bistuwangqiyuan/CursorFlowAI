# AI 代码审查 / 代码安全审计 / 开发者效能度量 —— 竞争格局与真实定价尽职调查

**调研日期：2026-07-27（所有"抓取日期"如无特别说明均为此日）**
**调研对象：CursorFlow AI（零人工 AI 插件，为 Cursor 开发者提供自动代码审计、私有知识库集成与提示词优化）的赛道可行性**
**结论提要：不建议按原形态启动。理由与替代路径见第 9 节。**

---

## 0. 方法与证据等级说明

本报告对每个数字标注来源等级，请按等级采信：

- **[一级]** 我在 2026-07-27 直接抓取的厂商**官方定价页 / 官方文档 / 官方新闻稿**原文。可直接引用。
- **[二级]** 官方文件（PDF 白皮书、SEC/新闻稿）经媒体转述，或权威第三方数据库（Tracxn、CB Insights、Sacra）。可引用但建议复核。
- **[三级]** 定价聚合站（costbench.com、aicodereview.cc、stackpick.net、toolradar.com、codepulsehq.com、pandev-metrics.com 等）。**这类站点在 2025-2026 大量出现，本身带有导流/竞品替换动机，且不少疑似 AI 批量生成内容。凡本报告标 [三级] 的数字，在做财务模型前必须自行到官网复核。**

**未能核实的项目我明确写"未核实"，不做推测填充。**

一个方法论提醒：多家厂商的定价页用 JavaScript 动态渲染价格（Codacy、Swarmia、Qodo 席位价），抓取到的 HTML 里没有数字。这些我标注了"官网未渲染出价格"，并用二/三级来源补充。

---

## 1. A 组 · AI Code Review（13 个产品）

### CodeRabbit — 品类领跑者
- **定位**：PR 级 AI 代码审查平台，兼做 IDE/CLI 内审查。自称"AI code review 品类定义者"。
- **集成**：GitHub / GitLab / Bitbucket App、IDE、CLI、MCP 连接（Pro 5 个 / Pro+ 15 个）。
- **定价 [一级，https://www.coderabbit.ai/pricing]**：Free $0（无限公私仓，但只给 PR 摘要）；Pro $24/user/mo（年付）；Pro Plus $48/user/mo（年付）；Enterprise 询价（含自托管、EU SaaS 部署、RBAC/SSO/审计日志）。月付贵 20%。另有 Slack Agent 按 $0.50/agent-minute 计费，以及"无限 CLI + PR 审查"的用量包加购。
- **免费额度 / 开源**：公开仓库**永久免费**（用 GitHub/GitLab 注册后装到 public repo 即可）。付费方案 14 天试用不要信用卡。
- **席位计法**：只对**开 PR 的开发者**收费，可手工指派席位。
- **融资 / ARR [二级]**：累计融资 $88M。2025-09 B 轮 $60M，Scale Venture Partners 领投，NVIDIA NVentures 参投，投后估值 $550M（TechCrunch 2025-09-16；BusinessWire 2025-09-16）。B 轮时创始人自述 ARR >$15M、8,000+ 付费客户、10 万+ 开源项目。Sacra 估算 2026-04 ARR 达 $40M（同比 +700%）——**此为第三方估算，非公司披露**。
- **团队规模 [二级]**：246 人（Tracxn，截至 2026-06-30）。

### Greptile
- **定位**：全代码库上下文的 AI reviewer，2026 年推出 TREX（会实际运行你的代码来验证）。
- **集成**：GitHub Enterprise、自托管选项、外部应用连接。
- **定价 [一级，https://www.greptile.com/pricing]**：Starter 免费（50 credits/月，1 个活跃开发者，无限仓库）；Pro $30/seat/mo（每席位含 50 credits，超出 $1/credit；1 credit = 1 次标准审查，3 credits = 1 次 TREX 审查）；Enterprise 询价（自托管、SSO/SAML、专属 Slack）。
- **免费额度 / 开源**：MIT / Apache 许可的非商业开源项目**申请后免费**。Pre-Series A 且过去 12 个月收入 <$2M 的初创**打 5 折**。
- **融资 [二级]**：累计 $29.1–29.5M（2024-06 种子 $4.1M by Initialized；2025-08/09 A 轮 $25M by Benchmark），估值 $180M（Sacra；CB Insights；Georgia Tech 2026-01-05 报道称 2,000+ 客户，含 Brex、Whoop、Substack）。
- **团队规模**：未核实。

### Qodo（原 CodiumAI）
- **定位**："代码质量平台"，PR 审查 + 测试生成 + IDE。
- **集成**：Git（GitHub/GitLab/Bitbucket）+ IDE 插件 + CLI。
- **定价 [一级，https://www.qodo.ai/pricing/ + https://docs.qodo.ai/pricing-and-usage]**：官网现在主打**credit 制而非席位制**——$0.012/credit，工作区共享池，"Billing is usage-based (not seat-based)"，无自助年付选项。Credit 包示例：2,500 credits ≈ 18 次审查/月；5,000 ≈ 36 次；20,000 ≈ 144 次。Enterprise（30+ 用户）询价，含 SSO/SAML、BYOK、单租户或本地部署。
- **席位价 [三级]**：多家聚合站仍报 Teams $30/user/mo（年付）/ $38（月付），含 2,500 credits/user/mo。**注意：这与官网当前的 credit 模型口径不一致，官网页面本身也未渲染出席位价。做对比时以 $0.012/credit 为准，席位价存疑。**
- **免费额度 / 开源**：Developer 免费层存在（[三级] 称 30 次 PR 审查 + 250 credits/月）。官网 FAQ 有"Do you have a free plan for open source projects?"条目但内容未渲染，**未核实**。
- **融资 [二级]**：累计约 $40M（A 轮）。
- **团队规模**：未核实。

### Ellipsis — 唯一纯用量、零席位费的玩家
- **定位**：AI 代码审查 + 编码 agent（修 Sentry 告警、补测试、查 flaky test）。
- **集成**：GitHub PR、Sentry；支持 BYOK Bedrock 与自有 AWS 账号私有云部署。
- **定价 [一级，https://www.ellipsis.dev/pricing]**：**无席位费**。按会话计量：token 原价透传 + CPU $0.142/vCPU-hour + 内存 $0.024/GB-hour + **平台费 = token 用量的 100%**。官方公布单次成本：一次中等 PR 的代码审查 **$0.74**（token $0.37 + 平台费 $0.37）；小功能开发 $1.91；flaky test 排查 $1.48。官方示例：10 人团队、每人每周 1.5 个 PR、50% 用 AI，月账单约 **$111**。
- **免费额度 / 开源**：新组织一次性 $100 credit（个人账号 $10），约够 135 次代码审查。开源项目 case-by-case 免费（发邮件申请）。
- **战略价值**：这是全场**唯一公开真实单位经济学**的厂商。任何人要做这门生意，都应该拿它的 $0.74/审查 当 COGS 基准线——见第 9 节。
- **融资 / 团队规模**：未核实。

### Sourcery — 价格地板
- **定位**：以 Python 起家的 AI reviewer + 轻量安全扫描。
- **集成**：GitHub、GitLab、IDE。
- **定价 [一级，https://www.sourcery.ai/pricing]**：Open Source 免费；Pro **$12/seat**（私仓审查，10 个仓的双周安全扫描，自定义规则）；Team **$24/seat**（仓库分析、200+ 仓每日安全扫描、3 倍审查限速、BYO LLM）；Enterprise 询价（自托管）。年付省 20%（即 Pro ≈ $9.6）。
- **免费额度 / 开源**：开源项目**完全免费**，IDE / GitHub / GitLab 内直接可用。
- **融资 / 团队规模**：未核实。页面上"Talk to a founder"的 CTA 说明团队仍很小。

### Graphite（Diamond）
- **定位**：stacked PR 工作流平台，AI review 是其中一个能力，而非独立产品。
- **集成**：GitHub、CLI、VSCode、MCP、Slack。
- **定价 [一级，https://graphite.dev/pricing]**：Hobby 免费（个人仓、有限 AI Review）；Starter **$20/user/mo**（年付，全组织仓库，仍是有限 AI Review）；Team **$40/user/mo**（年付，**无限 AI Review** + 审查自定义 + Merge Queue + Automations）；Enterprise 询价（SAML、SIEM 审计日志、GHES）。
- **免费额度 / 开源**：Hobby 层免费但限个人账号仓库；无明确的开源专属方案。
- **融资 [二级]**：2025-03 B 轮 $52M。
- **团队规模**：未核实。

### Bito
- **定位**：双产品线——AI Code Reviews（按席位）+ AI Architect（按用量，代码库知识图谱）。
- **集成**：GitHub / GitLab / Bitbucket、VS Code / JetBrains / **Cursor / Windsurf**、CLI、CI/CD、MCP（面向 Cursor / Claude Code / Codex）。
- **定价 [一级，https://bito.ai/pricing/]**：Team **$12/seat/mo**（年付）/ $15（月付）；Professional **$20/seat/mo**（年付）/ $25（月付）。两档均含 **5K 行/席位/月**，超出 **$5 per 1K 行**。自托管是 Professional 的 $5/seat/mo 加购。Enterprise 询价。AI Architect 完全询价。
- **免费额度 / 开源**：14 天免费试用不要信用卡；**无公开的开源免费方案**。
- **合规**：SOC 2 Type II，不存代码、不训练。
- **融资 / 团队规模**：未核实。

### What The Diff — 事实上的僵尸产品
- **定位**：PR 描述自动生成 + 轻量重构建议。不是真正的"审查"。
- **集成**：GitHub / GitLab App。
- **定价 [三级，https://whatthediff.ai/pricing，本次未成功抓取官网原文，数字来自搜索结果引述]**：Free 25,000 tokens/月（约 10 个 PR）；Pro $19/mo（200K tokens，约 40 个 PR）；Unlimited $199/mo。平均 PR 约消耗 2,300 tokens，未用完的 token 不结转。
- **判读**：这是 2023 年代的产品形态（只写 PR 描述），在 2026 年已被 CodeRabbit 免费层完整覆盖。**它的存在本身就是这个赛道价格与功能通缩的证据。**

### Baz（baz.ai，注意不是 baz.co）
- **定位**："工程审查平台"，2026-06 推出 Planner，把审查左移到规划阶段。
- **集成**：GitHub / GitLab、Jira/Linear/Slack、VPC 部署。
- **定价 [二级，https://baz.ai/pricing 与 https://baz.ai/docs/account/billing 的搜索引述；baz.co 已 301 跳转]**：Pro **$30/active dev/mo**（含无限"标准"代码审查）；**自 2026-06-01 起**高模型 agent 工作单独按 Engineering Work Credits 计费，1 credit = $0.01：Fixer session $1.00–4.30、Advanced Security $1.75–2.20、Spec Reviewer $1.00–2.50、AI SRE $1.50–3.00。官方给出的规划口径是 **$20–50/active dev/mo 总花费**。Enterprise 询价。
- **免费额度 / 开源**：无免费层，14 天试用 [三级]。
- **融资 [一级，https://baz.ai/resources/news/baz-announces-planner-and-extended-seed-round + SiliconANGLE 2026-06-29]**：2026-06-29 宣布扩展种子轮 $9M（Battery Ventures + boldstart 共同领投，AFG Partners、Disruptive VC 加入），**累计 $17M**；自称 100+ 客户，AI Code Review 产品在 precision-weighted Code Review Bench 排名第一。
- **团队规模**：未核实。

### Cursor Bugbot — 定价模式在 2026-05 刚被改过
- **定位**：Cursor 第一方的 PR 审查 agent。
- **集成**：GitHub / GitLab / Bitbucket 及自托管 SCM，与 Cursor 账号体系打通。
- **定价 [一级，https://cursor.com/docs/bugbot + https://cursor.com/pricing + https://cursor.com/docs/bugbot/legacy-pricing]**：**2026-05 起改为纯用量计费**。个人版：Bugbot 先消耗套餐内含用量，超出走 on-demand spend；Teams 版：直接从 on-demand spend 扣。具体费率在 cursor.com/pricing#bugbot（该锚点内容未在本次抓取中渲染出来，**费率数字未核实**）。**旧方案（已废止）**：个人 $40/月封顶 200 PR；团队 **$40/user/mo**，只按当月真正被审 PR 的作者计席位，且席位每月重新分配。
- **打包关系 [一级]**：Cursor Teams **$40/user/mo** 已把 "Agentic code reviews with Bugbot" 列为套餐内含卖点；Individual **$20/mo** 列 "Bugbot on usage-based billing"。
- **战略含义**：**这是本报告对 CursorFlow AI 最致命的一条事实**。Cursor 自己已经在 Teams 套餐里捆绑了代码审查、团队内部 rules/skills/plugins 的 marketplace、用量分析；Enterprise 层还有 AI code tracking API、审计日志、MCP 访问控制、hooks。

### GitHub Copilot code review
- **定位**：Copilot 套件内的一个功能，不单卖。
- **定价 [一级，https://github.com/features/copilot/plans + https://docs.github.com/en/copilot/get-started/plans]**：Free $0（2,000 次补全/月，不含 code review）；**Pro $10/mo（"Access to Cloud agent and code review" 从这一档开始）**；Pro+ $39/mo；Max $100/mo；**Business $19/granted seat/mo（含 1,900 AI credits）**；**Enterprise $39/granted seat/mo（含 3,900 credits）**。超额 $0.01/credit，credits 组织内池化。
- **促销 [一级，github.blog 2025 公告]**：2026 年 6–8 月期间，存量 Business 客户每月得 $30 credits（而非 $19），Enterprise 得 $70（而非 $39）。**注意这个促销 8 月底就结束，届时市场上会出现一波"AI 预算突然变贵"的情绪，这是一个真实的时间窗口信号。**
- **判读**：$10/mo 就能拿到 AI code review，这是整个 A 组的**价格天花板压制线**。

### Google Gemini Code Assist code review
- **定位**：Gemini for Google Cloud 内的能力，同样不单卖。
- **定价 [一级，https://cloud.google.com/products/gemini/pricing]**：Google 按**许可小时**计价。Standard：$0.031232877/小时（月度承诺）或 $0.026027397/小时（12 个月承诺）。Enterprise：$0.073972603/小时（月度）或 $0.061643836/小时（年度）。
  - **换算（730 小时/月，可复现）**：Standard = **$22.80/mo（月度承诺）/ $19.00/mo（年度承诺）**；Enterprise = **$54.00/mo（月度）/ $45.00/mo（年度）**。（验算：19 ÷ 730 = 0.026027397 ✓；45 ÷ 730 = 0.061643836 ✓）
- **免费**：个人版 Gemini Code Assist 免费（codeassist.google），但 PR 审查主要走 GitHub App。

### Amazon Q Developer code review
- **定价 [一级，https://aws.amazon.com/q/developer/pricing/]**：Free 层每月 50 次 agentic requests + 1,000 行 Java 升级；**Pro $19/user/mo**，含更高额度、Identity Center 管理面板、**IP 赔偿（indemnity）**。Java 升级超额 $0.003/行，4,000 行/user/mo 在付款账户层面池化。
- **判读**：$19 的 Pro 里，代码审查只是 SDLC 全家桶里的一项。

### A 组小结（结论性判断）
- **玩家密度**：13 个点名产品之外，本次调研过程中还自然撞见了 CodeAnt AI、Gitar（已被 Sonar 收购）、Augment Code、PanDev、CodePulse、Typo、AnalyticsVerse 等。**这个赛道的真实玩家数量在 30+，而不是 13。**
- **价格带**：$12（Sourcery / Bito）→ $20（Graphite Starter）→ $24（CodeRabbit Pro）→ $30（Greptile / Baz / Qodo）→ $40（Graphite Team / Bugbot 旧价）→ $48（CodeRabbit Pro Plus）。
- **两条压制线**：(a) 巨头把审查打包进 $10–19 的 IDE 助手；(b) 开源项目免费已是**行业标配**（CodeRabbit、Sourcery、Greptile、DeepSource、Socket、Codacy 全都免费），意味着靠开源做增长的渠道已经被占满且不产生收入。
- **单位经济学已经公开**：Ellipsis 的 $0.74/次审查说明，一个 $12/月的席位如果一个月跑 30 次审查，COGS ≈ $11——**毛利趋近于零**。所以你会看到 CodeRabbit（5 次/开发者/小时）、Greptile（50 credits）、Bito（5K 行）、DeepSource（$10 credit/user/mo）全都在做用量封顶。**"低价无限用"在这个赛道是不可能的商业模式。**

---

## 2. B 组 · 代码安全 / SAST（9 个产品）

### Snyk
- **定价 [一级，https://snyk.io/plans/]**：Free $0/contributing developer（SCA/SAST/IaC/容器，5 个项目）；Team **起价 $25/contributing dev/mo**（100 项目）；**Ignite $1,260/contributing dev/年**（<50 开发者的组织，全平台能力、无限 code tests、自定义规则）；Enterprise 询价。
- **席位定义 [一级]**：过去 90 天向被 Snyk 监控的**私有**仓库提交过 commit 的开发者。公开仓贡献不计。
- **免费 / 开源**：开源维护者免费。
- **财务 [二级]**：Sacra 估 2026-02 ARR **$326M，同比仅 +7%**（前一年是 +27%），其中 Snyk Code 约占 40%。累计融资 $1.25B。**估值已从 2022 年峰值 $7.4B 被 BlackRock 下调至 $3.7B。** 2026-02 更换 CEO。团队规模 1,216 人（Revelio Labs，2026-03）或约 1,600（GetLatka）——两个来源冲突，未定。
- **判读**：**这是本报告里最重要的一个警示信号。** 一家在这个赛道做到 $326M ARR 的领头羊，增速掉到 7%，估值腰斩一半，CEO 换人。说明"开发者安全"这个大品类本身已经进入平台整合期（被 GitHub、Wiz、Palo Alto 的套件蚕食）。

### Semgrep
- **定价 [一级，https://semgrep.dev/pricing/]**：Free Edition $0（10 个私有仓、10 个 contributor 上限，含跨文件分析 Pro rules、60 AI credits）；Teams **按产品分别计价**——Code (SAST) $30/contributor/mo、Supply Chain (SCA) $30、Secrets $15；500 私有仓上限；20 AI credits/dev/mo。Enterprise 询价，50 AI credits/dev/mo。
- **Semgrep Assistant**：已并入"Semgrep Multimodal (AI)"，AI 检测/分诊/修复用 credit 计量，并支持自定义 AI 模型提供商。另有 "Guardian" —— 面向 AI 编码 agent 的插件，官方定位是"代码一写出来就扫 AI 生成代码"。
- **融资 / 团队 [二级]**：累计 $193M（Tracxn）/ $204M（另一来源），2025-02 D 轮 $100M；262 人（Tracxn，2026-05-31）。

### SonarQube / SonarCloud（Sonar）
- **定价 [一级，https://www.sonarsource.com/plans-and-pricing/]**：Cloud Team **起价 $34/月**（注意：**按代码行数计价，不是按席位**——$34 对应 10 万行，最高 190 万行；免费层 5 万行私有代码）；Enterprise 年付询价。Server 版按实例按年按 LOC 计价。SonarQube Advanced Security（SAST+SCA）与 Sonar Agent Essentials（Vortex）均为**加购、询价**。
- **2026 重大动作 [一级，同页 FAQ]**：**Sonar 已收购 Gitar。** 官网上 Gitar 定价并列展示：Core $20/user/mo（年付）/ $25（月付）、Pro $40（年付）/ $50（月付）、Enterprise 询价。FAQ 明确回答 "How does Gitar joining Sonar affect me?"。
- **合规卖点 [一级]**：功能对比表里 Enterprise 档明确列 **"Cyber Resilience Act (CRA) compliance"** 与 MISRA C++:2023、PCI DSS、STIG、CASA。**这是全场唯一把 CRA 直接写进功能表的厂商——说明合规确实能卖钱，但也说明这个位置已被占。**
- **AI 相关**：AI Code Assurance（针对 AI 生成代码的 quality gate）、SonarQube MCP Server（开源免费）、面向 Claude Code / Gemini / Kiro 的 agent 插件、明确支持 Cursor。

### Codacy
- **定价**：官网 [一级，https://www.codacy.com/pricing] 抓取到的 HTML **未渲染出价格数字**，只有 FAQ 说明分档逻辑：Open Source 免费；Pro 面向 ≤30 contributors / ≤100 私有项目；Business 面向 >30 contributors 或 >100 项目。年付支持电汇/ACH。
- **[三级]**：多个聚合站称 2026 年改版为 Team **$18/dev/mo（年付）/ $21（月付）**，此前是 $15/user/mo 的 Pro。**未在官网证实，请自行复核。**
- **开源**：Free forever for open-source projects（官网 [一级] 确认）。
- **AI 相关 [一级]**：官网首屏卖点是"Auto-fix AI code before it reaches the editor"、"Scan-as-you-type"、"Agent Handoff for Auto-Fixing Issues"、**明确列出 VSCode / JetBrains / Cursor 集成**。

### DeepSource
- **定价 [一级，https://deepsource.com/pricing]**：Team **$24/user/mo（年付）**，无限仓库、无限 PR 审查。AI Review 另按量：**每 user 每月含 $10 credit（年付 $100/user）**，Standard $8/10K 处理行、Advanced $15/10K 行。OSS 依赖扫描含 3 个 target，额外 $8/target/mo。Enterprise 询价（自托管、BYOK Anthropic/OpenAI/Gemini）。
- **免费 / 开源 [一级]**：开源永久免费（公开仓无限、1,000 PR 审查/月、1,000 次格式化/月）。
- **注意**：DeepSource 自称 "82% accuracy on real vulnerabilities"（结构化数据里的自述，无第三方验证）。

### Aikido Security
- **定价 [一级，https://www.aikido.dev/pricing]**：Developer $0（含 2 users、10 repos、2 容器镜像、1 域名、1 云账号、10 次 AI AutoFix/月）；**Basic $300/月（含 10 users）**；**Pro $600/月（含 10 users）**；Advanced $600/月（含 10 users）；Enterprise 询价。年付省 10%。另有独立的 Pentest 产品：典型 $4,000/次，按范围 $500–$30,000+。
- **判读**：**Aikido 是全场唯一采用"平台费 + 打包席位"而非纯人头的定价**。$300/月起（10 人）≈ $30/人，但边际用户便宜。这对小团队是友好的，对做对标的人是价格锚点。
- **合规集成 [一级]**：直接同步到 Drata、Vanta。

### Corgea
- **定价 [一级，https://corgea.com/pricing]**：Free $0（2 人、10 仓、10 次 PR 扫描/月、10 次 SAST autofix）；**Growth $39/dev/mo**（最少 5 席，100 仓，无限 PR 扫描）；**Scale $49/dev/mo**（最少 20 席，200 仓，自定义规则、阻断规则、报表）；Enterprise 询价（SSO/SCIM、单租户、审计日志）。
- **席位定义**：过去 90 天的 contributing developer。
- **集成**：GitHub App、GitLab、Azure DevOps、Bitbucket、IDE 扩展、**MCP Server**。
- **合规**：SOC 2 Type II。

### ZeroPath — 全场最贵的定价结构
- **定价 [一级，https://zeropath.com/pricing]**：**Team 起价 $1,000/月 + $60/dev/月**（无限仓库/扫描、AI-native SAST 含业务逻辑与鉴权缺陷检测、SCA 可达性分析、DAST、runtime validation、autofix）；Enterprise 询价（本地部署、BYOK、SCIM、策略引擎、自定义合规报表）。Credits 按扫描付费的方案"Coming soon"。
- **优惠**：初创最高 5 折；安全研究者免费；MSP/白标合作。
- **判读**：**$1,000/月的平台底价 + $60/人，是全报告的价格上限。** 它证明了一件事：如果你能把产品定位成"取代人工安全审计"而非"帮开发者写好点代码"，客单价能高一个数量级。这是第 9 节讨论差异化空隙的重要输入。

### Socket.dev
- **定价 [一级，https://socket.dev/pricing]**：Free $0/dev/mo（无限开发者与仓库，1,000 次扫描/月，3 members，70+ 风险类型检测，恶意依赖自动拦截）；**Team $25/dev/mo**（5,000 扫描、预计算可达性分析，官方称可自动消除 60% 的 CVE 误报）；**Business $50/dev/mo**（无限成员/扫描、Vanta 等合规集成、SBOM 导入导出、SSO/SAML、扫 GitHub Actions 与 AI 模型）；Enterprise 询价（函数级全应用可达性，官方称可消除高达 90% 的无关 CVE）。年付省 20%。
- **开源**：**开源永久免费**，可申请免费 Team 账号。
- **AI 相关 [一级]**：功能表里列了 "AI code agents"、"MCP server"、"Socket ExtensionGuard（扫浏览器与 IDE 扩展）"。

### B 组小结
- 价格带比 A 组更宽：$18–24（Codacy/DeepSource）→ $25–30（Snyk/Semgrep/Socket）→ $39–49（Corgea）→ $50（Socket Business）→ $60 + $1,000 底价（ZeroPath）。
- **开源免费同样是标配**（Snyk、Semgrep、DeepSource、Socket、Codacy 全都有）。
- **合规是 B 组的定价杠杆**：Sonar 把 CRA 写进功能表，Socket/Aikido 卖 Vanta/Drata 同步，ZeroPath 卖"自定义合规报表"，这些都在 Enterprise 档收费。**"合规能卖钱"这一点成立；但"AI 代码合规"这个具体角度，位置已经被 Snyk（Evo Agent Security）、Semgrep（Guardian）、Sonar（AI Code Assurance）、Socket（扫 AI 模型与 IDE 扩展）四家同时占了。**

---

## 3. C 组 · 开发者效能度量（DORA/SPACE）+ AI code metrics

**直接回答你的关键问题：是的，"AI 生成代码的占比与质量"已经不是新品类的空隙，而是 2026 年 C 组每一家的标配 SKU，并且已经有厂商把它做到了行级归因。**

### LinearB
- **定价 [一级，https://linearb.io/pricing]**：Essentials **$29/user/mo**（仅支持 GitHub Cloud，含 1,000 credits/月，超出 $0.015/credit）；Enterprise **$59/user/mo**（含 1,500 credits）。**全部年付，不提供月付。** 最小计费用户数：Essentials 30 人 / Enterprise 50 人。45 天免费试用。
- **AI code metrics [一级]**：Essentials 档就明确列出 **"AI Impact Measurement"、"AI code reviews"、"AI PR enrichment"、"AI retros"、"MCP Server"**。
- **公开基准数据 [二级，LinearB 2026 Benchmarks 播客]**：人工 PR 的 30 天内合并率约 **84.5%**，AI 辅助 PR 只有 **32.7%**（不到一半）；P75 的 AI 辅助 PR 约 **400+ 行**，人工约 194 行。
- **ARR [二级]**：Sacra 记 2024 年 $16M ARR，同比 +45%。

### Swarmia
- **定价**：官网 [一级，https://www.swarmia.com/pricing/] 抓取到的 HTML **未渲染出价格**。官方文档 [一级，https://help.swarmia.com/resources/pricing-and-plans] 确认：**免费层面向开发者 <10 人的公司**，含 Standard 档的大部分功能；年付比月付便宜。
- **[三级，来源互相冲突，务必自行复核]**：codepulsehq（2026-07）称四个模块分别计价（€/dev/mo，年付）：Productivity & AI impact €22、Software capitalization €16、Developer surveys €8、**AI adoption & cost €4**；Standard 打包 €42（月付 €49），Enterprise €52。而 rywalker.com 称 Lite ≈€20 / Standard ≈€39；TrustRadius 称 Lite $25 / Standard $45。**三个来源三个数字。**
- **AI code metrics [二级]**：AI Impact 产品可识别由 GitHub Copilot、**Cursor**、Claude Code 辅助或创建的 PR，含独立的 cloud-agents 视图；但是 **PR 级别，没有代码行级的 AI/人工拆分**。

### Jellyfish
- **定价**：**不公开**。[三级] Vendr 记录 91 笔采购的**年合同中位数 $35,920**，实际成交最低约 $16,500（2026-07）；PriceLevel 数据约 $588/contributor/年（≈$49/月）；买家报告区间 $20–40/dev/月；另一来源称合同区间 $50K–250K/年、**最低约 50 席起售、不卖给 25 人以下团队**。
- **判读**：这是典型的销售驱动型企业软件，与"零人力、无人化"的模式**根本不兼容**。

### Waydev
- **定价 [一级，https://waydev.co/pricing/]**：**Tokenmeter $0**（免费看 AI token 效率、每活跃用户 AI 成本、每合并 PR 的 AI 成本、每 1K tokens 混合成本、缓存命中率、AI 重度用户比例；50 仓、3 个月数据）；**Pro $29/active contributor/mo**（50 人 = $17,400/年）；**Premium $49/active contributor/mo**（50 人 = $29,400/年）；Enterprise 询价。**全部年付。** 90 天退款保证，前 90 天可解约。
- **AI code metrics [一级]**：Premium 档明确含 **AI Adoption、AI Impact（"Track AI-generated code from commit to production"）、AI ROI（每个 AI 工具的 token、成本、产出）、Waydev Agent（Premium 含 200 次查询/月）**。FAQ 明确："AI coding agents are tracked alongside your team… 不额外按 agent 收费。"
- **判读**：**Waydev 的免费 Tokenmeter 层是一个必须重视的信号。** 它把"AI 成本与效率度量"这件事做成了免费获客钩子。任何人想以此为核心卖点收费，起点就是负的。

### DX (getdx.com)
- **定价 [一级，https://getdx.com/pricing/]**：**不公布任何数字。** 官方 FAQ 只说：模块化定价、按开发者 license 计费、MCP server 另有用量分档、**最短 1 年合同**、提供免费 PoC。
- **AI code metrics [一级，https://docs.getdx.com/reports/ai-code-overview/]**：**这是 C 组做得最深的一家，也是最应该让你警惕的一家。** DX 的 "AI pull request overview" 报表把每个 PR 按 AI 代码占比分成 5 档（0% / <33% / 33–66% / >66% / Unknown），计算公式是 **AI additions ÷ (AI additions + human additions) × 100**，然后把 cycle time、PR size、review comment density、**PR revert rate** 全部按这 5 档拆开对比。这已经是**代码行级归因**，不是元数据推测。
- **公开研究数据 [一级/二级]**：DX 每季度发布 500+ 组织的数据。2026 Q1，开发者自报的"已合并代码中 AI 编写的比例"从上季度 22% 升到 **27.4%**；每日使用者从 24.1% 升到 **30.8%**。DX 明确说明当前这个指标是**开发者自报**，并预告将补充遥测口径。另有 Q4 报告（13.5 万开发者）称 AI 工具平均每周节省 **3.6 小时**。
- **客户**：Adyen、Dropbox、Vanguard、Booking.com（官网列名）。

### Haystack (usehaystack.io)
- **定价 [一级，https://www.usehaystack.io/pricing]**：Growth **$20/member/mo**（年付承诺，建议 <100 工程师）；Enterprise 询价（本地部署）。14 天试用不要信用卡。
- **AI code metrics**：定价页与 FAQ 中**完全没有提到 AI**。页面 footer 是 **"Copyright © 2023"**，且页面里有 "## Start jj trial" 这样的未清理占位文字。
- **判读**：**高度疑似停止维护的产品。** 在一个所有竞品都在 2026 年重写 AI 叙事的品类里，一个连版权年份都停在 2023 的产品，不应该被当作活跃竞品，但**它是"这个赛道会死人"的直接证据**。

### Faros AI
- **定价**：**不公开**，企业级。[三级] 估计 $30–60/dev/月；50 人规模年费估 $80K–150K。有免费开源 Community Edition 可自托管。
- **AI code metrics [一级，https://www.faros.ai/platform/ai-transformation]**：产品页明确列 **"% of AI-generated code by repo and PR"、"AI-generated code tagging"、"Policy orchestration for risk mitigation"、"Audit trails for AI regulatory compliance"**，并声称"distinguishes between human and machine-generated code"。
- **重要的立场矛盾 [二级，Faros 官方 LinkedIn，2026-01-09]**：Faros 公开发文说 **"'我们的代码有多少是 AI 生成的?' —— 这是个显而易见的问题，也是个错误的问题"**，理由是 LOC 作为生产力代理指标早已被证伪，且"技术上准确测量几乎不可能"。**一家自己卖这个功能的厂商公开唱衰这个指标，这对"AI 代码占比度量"作为独立产品的可售性是一个强烈的负面信号。**
- **研究数据 [二级，Faros《AI Engineering Report 2026: The Acceleration Whiplash》，22,000 开发者 / 4,000+ 团队 / 两年遥测]**：AI 生成代码的接受率从 20% 升到 **60%**；人均任务完成 +34%、人均 epic 完成 +66%、人均 PR 合并率 +16.2%；同时 **人均 bug +54%、每 PR bug +28%、incident-to-PR 比率翻三倍、PR 体积 +51%、中位审查时间 5 倍、代码 churn 10 倍、31% 更多的 PR 在完全无人审查的情况下合并**。Faros 明确说其数据**与 DORA 2025 关于"高绩效组织有免疫力"的结论相矛盾**。
- **公司规模 [三级，LinkedIn 数据]**：50–60 人，年收入区间 $1M–$10M，累计融资 $36M。

### C 组小结
- **AI code metrics 不是空隙，是 2026 年的入场券。** LinearB（Essentials 档就含）、Swarmia（独立 AI adoption & cost 模块）、DX（行级 AI 占比分档报表）、Waydev（免费 Tokenmeter + Premium 全套 AI ROI）、Faros（按 repo/PR 的 AI 占比 + 合规审计轨迹）五家全部已上线。
- **技术门槛的真相**：能做到**行级**归因的只有 DX、Faros，以及 **Cursor 自己**（见下节）。其余（LinearB、Swarmia）停留在 PR/元数据级。**行级归因的门槛不在算法，在数据源** —— 你必须能拿到 IDE 侧的 AI 建议签名，而这个数据只有 IDE 厂商（Cursor / GitHub）和装了 agent 的平台（DX、Faros）能拿到。**一个第三方插件拿不到，除非用户自己装你的 IDE 扩展。**

---

## 4. D 组 · 与 Cursor 直接相关的第三方商业产品

**直接回答你的问题："付费的 Cursor prompt 优化工具"这个市场确实存在，但它是一个"信息产品 / 模板包"市场，不是 SaaS 市场，客单价在 $27 一次性到 $99/月之间，且正在被 Cursor 官方功能直接消灭。**

### 4.1 Cursor 官方已经自己做了什么（这是最重要的一节）

| 能力 | Cursor 官方现状 | 来源 |
|---|---|---|
| AI 代码审查 | Bugbot，Teams $40/user/mo 套餐内含，Individual 按量 | [一级] cursor.com/pricing, /docs/bugbot |
| 团队规则 / skills / plugins 分发 | Teams 档 **"Team marketplace for internal rules, skills, and plugins"**；Enterprise 可"recommend or require rules from the cloud dashboard" | [一级] cursor.com/pricing, cursor.com/blog/enterprise |
| AI 代码归因（行级） | **AI Code Tracking API，Enterprise Only，alpha 状态**。端点 `/analytics/ai-code/commits`、`/analytics/ai-code/changes`、`/analytics/ai-code/commits/:commitHash`，把每一行归因到 TAB / COMPOSER / 非 AI，支持 CSV 流式导出。检测在**本地设备**完成，不上传代码。 | [一级] cursor.com/docs/account/teams/ai-code-tracking-api, /analytics.md |
| 仪表盘 | Teams + Enterprise 都有 Usage Analytics；Enterprise 新版可"View percentage of AI lines of code on the commit level"，按 AD 组过滤，数据每 2 分钟更新 | [一级] cursor.com/blog/enterprise |
| 安全 / 治理 | Enterprise：审计日志（19 类事件）、SCIM、仓库/模型/MCP 访问控制、auto-run/browser/network 控制、hooks（可强制合规策略、拦截未批准命令、实时清洗密钥） | [一级] cursor.com/pricing, cursor.com/blog/enterprise |
| MCP | 全档支持，Enterprise 可做访问控制 | [一级] |

**CursorFlow AI 提案里的三个功能（自动代码审计、私有知识库集成、提示词优化），Cursor 官方分别对应 Bugbot、MCP + Enterprise 上下文、Team rules marketplace。三个全部已被第一方覆盖。**

一个可能的缝隙（第 9 节会展开）：**AI Code Tracking API 是 Enterprise 独占的 alpha 功能**。$40/user/mo 的 Teams 客户拿不到行级 AI 归因。

### 4.2 付费 Cursor rules / prompt 优化产品（真实存在，但形态不是 SaaS）

- **aiprompt.co [三级，https://aiprompt.co/pricing]**：Starter $14/月（200 次生成）、Pro $49/月（1,000 次）、Premium $99/月（3,000 次）。核心功能"Export as Cursor Rules"。**这是最接近"付费 Cursor prompt 优化 SaaS"的真实存在物。**
- **Brainfile Pro [三级，https://brainfile.io/cursorrules-templates]**：**$99/月**，12+ 角色的 .cursorrules 模板，卖点是"每月随 Cursor 演进更新"。本质是订阅制信息产品。
- **BuyCoded Cursor Rules Mega-Pack [三级]**：**$27 一次性**，100+ 规则覆盖 20 个技术栈，含商业授权与免费更新。
- **WOWHOW Cursor AI Rules Pack [三级]**：**₹1,615（约 $19）一次性**，12 个配置文件 + 40+ prompt 模板。

**判读**：
1. 这个市场真实存在且有人付费，但**是 Gumroad/Lemon Squeezy 级别的数字商品市场，不是企业 SaaS**。$27–99 的客单价、无网络效应、无数据护城河。
2. **Cursor 的 Team marketplace 是这个市场的死刑判决书**。当团队可以在 Cursor 内部免费分发和强制规则时，外部卖模板包的生意会迅速萎缩到个人开发者长尾。
3. 这些产品的定价页大量出现在聚合站而非独立媒体报道中，**说明它们缺乏真实的市场声量**。

### 4.3 私有知识库 / RAG 接入 Cursor

- **Context7（Upstash 出品）[一级/三级]**：MCP server **MIT 开源、可自托管**。免费层 1,000 次 API 调用/月 + OAuth；**Pro $10/seat/mo**（私有仓、每成员 5,000 次调用、超出 $10/1,000 次）；Enterprise 询价（SOC 2 Type II、SSO SAML/OAuth/OIDC、私有 GitHub/GitLab/Bitbucket 仓库摄取、本地部署、可禁用查询存储、可用自有 LLM）。ISO 27001 认证进行中。
- **DeepWiki**：公开仓库免费，无需认证。
- **Ref Tools**：$19/月（Basic，2K credits）、$50/月（Pro）、$200/月（Max）。
- **Docsie MCP Server**：面向治理型私有文档，OAuth 2.0 + 企业 SSO + RBAC + 审计轨迹 + 工作区隔离；定价未核实。
- **Bito AI Architect [一级]**：代码库知识图谱 + Jira/Confluence/Google Docs 图谱索引，通过 MCP 接入 Cursor / Claude Code / Codex。按用量计价，需询价。

**判读**："给 Cursor 接私有知识库"这件事的核心组件（MCP server）**是 MIT 开源的，$10/席位就有商业托管版**。这是彻底的商品化（commoditized）领域，没有定价权。

---

## 5. 定价对比清单（纯文本对齐，非表格）

```
=== A 组 · AI CODE REVIEW =====================================================
- CodeRabbit ......... 免费(仅摘要) | Pro $24  | Pro+ $48 | 企业询价 ... 开源永久免费
- Greptile ........... 免费(50cr)   | Pro $30  | 企业询价            ... 开源申请免费 / 初创5折
- Qodo ............... 免费层       | $0.012/credit 用量制 | 企业询价 ... 席位价$30[三级,存疑]
- Ellipsis ........... $100 试用金  | 无席位费, $0.74/次审查          ... 开源逐案免费
- Sourcery ........... 开源免费     | Pro $12  | Team $24 | 企业询价 ... 年付再省20%
- Graphite ........... Hobby 免费   | Start $20| Team $40 | 企业询价 ... 年付价, AI审查仅Team无限
- Bito ............... 无免费层     | Team $12 | Pro  $20 | 企业询价 ... 年付价, 含5K行/席位/月
- What The Diff ...... 免费25K token| Pro $19  | 无限 $199           ... [三级] 产品已陈旧
- Baz ................ 无免费层     | Pro $30 + credits($20-50实付) ... 100+客户, 累计融资$17M
- Cursor Bugbot ...... Teams套餐内含 | 纯用量制(费率未核实)          ... 旧价$40/user封顶200PR
- GitHub Copilot ..... 免费(无审查) | Pro $10  | Biz $19 | Ent $39  ... $10档起即含 code review
- Gemini Code Assist . 个人版免费   | Std $19-22.8 | Ent $45-54     ... 按许可小时计, 730h/月换算
- Amazon Q Developer . 免费50次/月  | Pro $19                        ... 含 IP 赔偿

=== B 组 · 代码安全 / SAST =====================================================
- Snyk ............... 免费(5项目)  | Team $25 | Ignite $105/月等价 | 企业询价
- Semgrep ............ 免费(10仓)   | Code $30 + SCA $30 + Secrets $15 分产品计价 | 企业询价
- SonarQube Cloud .... 免费5万行    | Team $34/月起(按10万行, 非席位) | 企业询价 + CRA合规
- Gitar (已被Sonar收购) 无免费层     | Core $20 | Pro $40 | 企业询价 ... 年付价
- Codacy ............. 开源免费     | Team $18[三级] | Business 询价 ... 官网未渲染价格
- DeepSource ......... 开源免费     | Team $24 + AI审查$8-15/万行   ... 每席位含$10 AI credit
- Aikido ............. 免费(2用户)  | Basic $300/月 | Pro $600/月   ... 均含10用户, 非纯人头
- Corgea ............. 免费(2用户)  | Growth $39(≥5席) | Scale $49(≥20席) | 企业询价
- ZeroPath ........... 无免费层     | Team $1,000/月 + $60/dev      ... 全场最高, 卖"替代人工审计"
- Socket.dev ......... 免费(1000扫描)| Team $25 | Business $50 | 企业询价 ... 开源永久免费

=== C 组 · 效能度量 + AI CODE METRICS =========================================
- LinearB ............ 无免费层     | Essent $29(≥30席) | Ent $59(≥50席) ... 仅年付, 含AI Impact
- Swarmia ............ <10开发者免费| Standard €39-45[三级,来源冲突] | 企业询价
- Jellyfish .......... 无免费层     | 不公开, 中位年合同$35,920[三级] ... ≥50席起售, 纯销售驱动
- Waydev ............. Tokenmeter免费| Pro $29 | Premium $49 | 企业询价 ... 仅年付, 免费层含AI成本度量
- DX (getdx.com) ..... 无免费层     | 完全不公开, 最短1年合同        ... 提供免费PoC
- Haystack ........... 无免费层     | Growth $20 | 企业询价          ... 疑似停止维护(footer仍写2023)
- Faros AI ........... 开源社区版   | 完全不公开, 估$30-60/dev[三级]  ... 有免费自托管CE

=== D 组 · CURSOR 周边 =========================================================
- Cursor 本体 ........ Hobby 免费   | Individual $20 | Teams $40 | 企业询价
- aiprompt.co ........ 无免费层     | $14 / $49 / $99 每月按生成次数
- Brainfile Pro ...... 有免费样例   | $99/月 订阅制 .cursorrules 模板
- BuyCoded 规则包 .... 无           | $27 一次性买断
- Context7 ........... 免费1000次/月| Pro $10/seat | 企业询价 ... MCP server MIT开源可自托管
- Ref Tools .......... 200 credits  | $19 / $50 / $200 每月
- DeepWiki ........... 公开仓免费   | (走 Devin 商业化)
```

**读这张表最该记住的三个数字：**
1. **$10** —— GitHub Copilot Pro 包含 AI code review 的价格。这是整个 A 组的价格天花板。
2. **$0.74** —— Ellipsis 公布的单次 PR 审查真实成本。这是所有人的 COGS 地板。
3. **$0** —— 开源项目在 CodeRabbit / Sourcery / Greptile / DeepSource / Socket / Codacy / Snyk / Semgrep 处的价格，以及 Waydev Tokenmeter 的 AI 成本度量价格。

---

## 6. 问题存在性：AI 生成代码质量与安全的权威量化研究

这一节是你 BP 里"问题真实存在"论证的证据基础。我按证据强度从高到低排列，并明确标注每项研究的**局限**——因为投资人会问，你必须先自己知道。

### 6.1 METR RCT（证据强度：最高，唯一的随机对照试验）
- **出处**：Becker et al., *Measuring the Impact of Early-2025 AI on Experienced Open-Source Developer Productivity*, METR, 2025-07-10。
  - 博客：https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/
  - 论文 PDF：https://metr.org/Early_2025_AI_Experienced_OS_Devs_Study-paper.pdf
  - arXiv：https://arxiv.org/abs/2507.09089（DOI: 10.48550/arxiv.2507.09089）
- **样本量**：**16 名开发者，246 个真实任务**。开发者来自 22k+ stars、1M+ 行代码的成熟开源仓库，在该项目上平均有 5 年经验。任务平均 2 小时。参与者报酬 $150/小时。工具主要是 **Cursor Pro + Claude 3.5/3.7 Sonnet**。
- **核心数字**：
  - 允许使用 AI 时，完成任务耗时 **增加 19%**（AI 让人变慢）。
  - 事前开发者预测 AI 会**加快 24%**；**事后（亲身经历了变慢之后）仍然认为 AI 加快了 20%**。
  - 经济学专家预测加快 39%，ML 专家预测加快 38%。全部反向。
  - 研究者检验了 20–21 个可能的混杂因素，结论稳健。
- **局限（你必须主动披露）**：n=16 极小；只覆盖成熟开源仓库的资深维护者（对新代码库/初级开发者不适用）；93% 用过 LLM 但**只有 44% 之前用过 Cursor**（学习曲线未剔除）；模型是 2025 年 2–6 月的 Claude 3.5/3.7，**已经过时两代**。
- **对 BP 的用法**：这是"感知与现实存在系统性偏差"的最硬证据 —— 20 个百分点的自我评估偏差。**这恰恰是"需要客观度量工具"的最佳论据，但也同时是"客观度量结论可能让客户不高兴"的风险警示。**

### 6.2 GitClear 代码质量纵向研究（证据强度：高，样本最大）
- **出处**：*AI Copilot Code Quality: 2025 Look Back at 12 Months of Data*, GitClear。https://www.gitclear.com/ai_assistant_code_quality_2025_research/
- **样本量**：**2.11 亿行变更代码**（2020-01 至 2024-12），来自 Google、Microsoft、Meta 及企业 C-Corp 的仓库。约 2/3 来自选择匿名共享数据的私有企业客户，1/3 来自 25 个大型开源项目。
- **核心数字**：
  - "moved"（重构信号）行占比从 2021 年的 **24.1%/25% 跌到 2024 年的 9.5%**（降幅 39.9%）。
  - "copy/paste"（克隆）行占比从 2020 年 **8.3% 升到 2024 年 12.3%**（相对增幅 48%）。
  - **2024 年是史上第一次"复制粘贴行数"超过"移动行数"。**
  - 含 5 行以上重复的代码块出现频率 **2024 年增长 8 倍**，比两年前高 10 倍。
  - 两周内被修订的新代码（churn）占比从 2020 年 3.1% 升到 2024 年 5.7%（另一处口径为 5.5%→7.9%）。
  - 新增代码行占比从 2020 年 39% 升到 2024 年 46%。
- **局限**：**相关性非因果** —— GitClear 无法证明这些变化由 AI 造成，只能证明时间上重合。数据集有自选择偏差（愿意共享数据的 GitClear 客户）。GitClear 自己卖代码质量分析工具，**有商业动机**。
- **对 BP 的用法**：这是"AI 代码引入长期可维护性债务"最常被引用的数据。用它时必须同时说明它是相关性研究。

### 6.3 Veracode GenAI 代码安全基准（证据强度：高，可复现的基准测试）
- **出处**：*2025 GenAI Code Security Report*, Veracode, 2025-07-30。
  - PDF：https://www.veracode.com/wp-content/uploads/2025_GenAI_Code_Security_Report_Final.pdf
  - 2025-10 更新版：https://www.veracode.com/wp-content/uploads/October-2025-GenAI-Code-Security-Report-Update.pdf
  - 新闻稿：https://www.businesswire.com/news/home/20250730694951/en/
- **样本量**：**80 个代码补全任务 × 100+ 个 LLM**。任务设计：4 种语言（Java、JavaScript、C#、Python）× 4 类 CWE（SQL 注入 CWE-89、XSS CWE-80、日志注入 CWE-117、不安全加密算法 CWE-327）× 每组 5 个实例。用 Veracode Static Analysis 判定。
- **核心数字**：
  - 全体模型全体任务中，**只有 55% 生成安全代码；45% 的情况引入了 OWASP Top 10 级别的已知漏洞**。
  - **Java 最危险，失败率 >70%**；Python / C# / JavaScript 在 38–45%。
  - **XSS 失败率 86%，日志注入失败率 88%。**
  - **关键结论：模型在语法正确性上大幅进步，但安全性能"largely flat across model sizes and over time"—— 更新更大的模型并不生成更安全的代码。**
- **局限**：只测 4 类 CWE、4 种语言，是窄范围的合成基准；测的是"补全"场景，不是完整的 agentic 开发流程；Veracode 卖 SAST，有商业动机。
- **对 BP 的用法**：**"安全性不随模型能力提升"是这份报告最有价值的一句话** —— 它意味着这个问题不会被 GPT-6 自动解决，这是唯一能支撑"长期需求"的论据。

### 6.4 Georgetown CSET（证据强度：中高，政策级权威）
- **出处**：*Cybersecurity Risks of AI-Generated Code*, Center for Security and Emerging Technology, Georgetown University, 2024-11。
  - https://cset.georgetown.edu/publication/cybersecurity-risks-of-ai-generated-code/
  - PDF：https://cset.georgetown.edu/wp-content/uploads/CSET-Cybersecurity-Risks-of-AI-Generated-Code.pdf
- **样本量**：**5 个 LLM**，同一组 prompt，用 ESBMC（Efficient SMT-based Context-Bounded Model Checker）形式化验证。
- **核心数字**：
  - **约 48% 的生成代码片段可编译但含被 ESBMC 标记的 bug**（CSET 定义为"不安全"）。
  - 约 30% 编译通过且验证通过（定义为"安全"）。其余编译失败或验证管线出错。
  - **所有 5 个模型在至少 40% 的 prompt 上产出含 bug 的代码。**
  - 有趣的反直觉发现：**GPT-3.5 的表现优于 GPT-4**。
  - 报告把这个结果定性为"最小干预条件下的粗略上界"。
- **局限**：CSET 自己声明"limited in scope and specifically intended to test systems' propensity to generate bugs"—— 即 prompt 是**刻意设计来诱发 bug 的**，不代表真实使用分布。
- **对 BP 的用法**：政策圈引用度高，适合放在"监管者已经在关注"的论证里；不适合当作真实漏洞率。

### 6.5 Stanford / Perry et al.（证据强度：中，但是唯一的人机交互用户研究）
- **出处**：Perry, Srivastava, Kumar, Boneh, *Do Users Write More Insecure Code with AI Assistants?*, ACM CCS 2023。
  - DOI: 10.1145/3576915.3623157 | arXiv: 2211.03622 | 数据与 UI 开源：https://github.com/neilaperry/do-users-write-more-insecure-code-with-ai-assistants
- **样本量**：**47 名参与者**，5 个安全相关编程任务，3 种语言（Python、JavaScript、C）。AI 助手基于 OpenAI `codex-davinci-002`。
- **核心数字**：
  - 有 AI 助手的参与者在 **5 个任务中的 4 个** 上写出的代码**显著更不安全**。
  - 有 AI 助手的参与者**更倾向于相信自己写的代码是安全的**（过度自信）。
  - **越不信任 AI、越多调整 prompt（改写措辞、调温度）的参与者，代码漏洞越少。**
- **局限**：**模型是 codex-davinci-002，即 2022 年的技术，已彻底过时**。这是它最大的问题。引用时必须注明年份，否则会被内行当场戳穿。
- **对 BP 的用法**：只用它的"过度自信"发现（这一点与 METR 2025 的 20 个百分点偏差互相印证，跨越 3 年仍成立），不要用它的漏洞率。

### 6.6 Google DORA 2024 / 2025（证据强度：中高，样本大但是自报调查）
- **出处**：*DORA 2025 State of AI-assisted Software Development Report*, DORA/Google, 2025-09。
  - https://research.google/pubs/dora-2025-state-of-ai-assisted-software-development-report/
  - 官方博客：https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report
- **样本量**：**近 5,000 名技术专业人士**的问卷 + 100+ 小时定性数据。**注意：这是自报调查，不是遥测。**
- **核心数字（2025）**：
  - **90% 的受访者在工作中使用 AI**（较去年 +14%）；80%+ 认为提升了生产力。
  - **30% 的人对 AI 生成的代码"几乎不信任或完全不信任"**（比去年略降）。
  - **AI 采纳与交付吞吐量（throughput）的关系在 2025 年转正**（2024 年是负的），但 **AI 采纳与交付稳定性（stability）的关系持续为负**。
  - 中心论点："AI 是放大器（amplifier）"——放大高绩效组织的优势，也放大失能组织的问题。
  - 90% 的组织已采用至少一个内部平台，76% 有专职平台团队；高质量内部平台是释放 AI 价值的关键前提。
- **2024 年的对应数字（承前）**：DORA 2024 报告 AI 采纳与交付吞吐量、稳定性**双双负相关**；每增加 25% 的 AI 采纳，交付稳定性下降约 7.2%（此数字广为引用，本次未直接抓取 2024 原文，**标记为待复核**）。
- **重要冲突 [必须在 BP 中披露]**：**Faros AI 的 2026 报告明确说其遥测数据"directly contradicts DORA's 2025 findings"**，特别是关于"工程成熟度能否形成保护"这一点。DORA 是自报调查，Faros 是遥测。**两个方法论给出不同结论，任何只引用一方的 BP 都不诚实。**
- **DORA 2026**：截至 2026-07-27 尚未发布（DORA 通常 9–10 月发布）。**不要在 BP 里假装有 2026 数据。**

### 6.7 Faros AI《The Acceleration Whiplash》（证据强度：高，遥测；但厂商自研）
- **出处**：*AI Engineering Report 2026: The Acceleration Whiplash*, Faros AI。https://www.faros.ai/research/ai-acceleration-whiplash
- **样本量**：**22,000 名开发者、4,000+ 团队、两年遥测数据**，方法是在**同一组织内部**比较其 AI 采纳最低期与最高期的指标变化。
- **核心数字**：吞吐面 —— AI 代码接受率 20%→60%，人均任务完成 +34%，人均 epic 完成 +66%，人均 PR 合并率 +16.2%，团队级代码相关任务 +210%。质量面 —— **人均 bug +54%，每 PR bug +28%，incident-to-PR 比率翻 3 倍，PR 体积 +51%，中位审查时间 5 倍，代码 churn 10 倍，31% 更多的 PR 完全无人审查就合并**。80% 的团队已超过"50% 周活跃 AI 用户"阈值。
- **局限**：Faros 卖的就是解决这个问题的产品，**利益冲突明显**；"同组织高低采纳期对比"的设计无法排除时间趋势混杂。
- **对 BP 的用法**：这是目前**最新、样本最大的遥测证据**，且它的"31% 更多 PR 无人审查合并"直接支撑"需要自动审查"的论点。但必须标注厂商自研。

### 6.8 DX 的 AI 代码占比纵向数据（证据强度：中，自报但连续）
- **出处**：https://getdx.com/blog/ai-generated-merged-code-holds-steady-at-30/ 及 https://docs.getdx.com/reports/ai-code-overview/
- **样本**：500+ 组织，每季度调研。
- **核心数字**：已合并代码中 AI 编写的比例，2025 Q4 = **22%** → 2026 Q1 = **27.4%**；每日 AI 使用者从 24.1% → **30.8%**。DX 自己明确说明**这是开发者自报，不是遥测**，并预告将补遥测口径。另有 Q4 报告（13.5 万开发者）称 AI 工具平均每周省 **3.6 小时**。
- **交叉验证**：Stack Overflow 2025 开发者调查称 **45.2% 的开发者认为调试 AI 生成代码更费时**（https://survey.stackoverflow.co/2025/ai）。

### 6.9 证据基础的诚实总结

**成立的部分（可以放心写进 BP）：**
1. AI 生成代码的安全缺陷率在 45–48% 量级，且**不随模型能力提升而改善**（Veracode 是这一点的最强证据）。
2. AI 加速了代码产出，同时**下游质量指标全面恶化**（Faros 遥测 + GitClear 纵向 + DORA 自报，三种方法论指向同一方向）。
3. 开发者**系统性高估**了 AI 对自己的帮助（METR 20 个百分点 + Stanford 过度自信，跨 3 年一致）。
4. 采纳率已接近饱和（DORA 90%、Faros 80% 团队超阈值），**这意味着"AI 采纳"不再是问题，"AI 治理"才是**。

**不成立 / 被夸大的部分（不要写）：**
1. 没有任何研究证明"AI 生成代码导致了实际的生产安全事故增加"。所有研究都是基准测试或代理指标。
2. GitClear 是相关性，不是因果。
3. Stanford 研究用的是 2022 年的模型。
4. DORA 与 Faros 结论互相矛盾，不能同时全信。
5. **最关键的**：以上所有研究，**没有一个证明"买一个第三方工具能解决这个问题"**。它们只证明问题存在。这是"问题存在性"和"解决方案可售性"之间的鸿沟。

---

## 7. 合规与审计需求：真实监管驱动 vs 营销话术

我按"确有强制要求"和"营销话术"两栏明确区分。

### 7.1 ✅ 确有强制要求

**EU CRA（Cyber Resilience Act，Regulation (EU) 2024/2847）—— 这是唯一一个时间紧迫、真实强制、且与代码直接相关的法规**
- 来源 [一级]：欧盟委员会官方摘要 https://digital-strategy.ec.europa.eu/en/policies/cra-summary
- 时间表：2024-12-10 生效 → **2026-06-11** 第四章（合格评定机构通知）适用 → **2026-09-11 第 14 条报告义务适用** → **2027-12-11 全面适用**。
- **2026-09-11 起（距今 46 天）的硬性义务**：制造商知悉被主动利用的漏洞或严重事件后，须向所在成员国 CSIRT 和 ENISA 报告 —— **24 小时内预警、72 小时内正式通报、修复措施可用后 14 天内最终报告**（严重事件为 72 小时后 1 个月内）。**这项义务适用于所有已在欧盟市场上的产品，包括 2027-12-11 之前投放的存量产品。**
- **SBOM 要求**：附件 I 要求制造商识别并记录组件与漏洞，"including by drawing up a software bill of materials in a commonly used and machine-readable format covering at the very least the top-level dependencies"。SBOM **不必公开，但必须存在并应主管机关要求提供**。这项属于 2027-12-11 的全面适用范围。
- **判读**：这是真金白银的强制要求，且 2026-09-11 的 24 小时时钟在运营上极难满足（你必须能在 24 小时内说清哪些产品受影响）。**但请注意：CRA 管的是"产品中的漏洞"，不是"代码是不是 AI 写的"。CRA 不会因为你用 AI 写代码而增加任何义务。** 这个需求的受益者是 SCA/SBOM 厂商（Snyk、Socket、Aikido、Sonar），不是 AI 代码审计厂商。

**ISO/IEC 27001:2022 Annex A 8.28（安全编码）—— 真实的认证控制项**
- 控制原文："Secure coding principles shall be applied to software development."
- **审计员实际要的证据**（多个独立来源一致）：正式的安全编码政策（引用 OWASP 等标准）、开发者安全编码培训记录（12 个月内）、**CI 流水线中 SAST/secret scanning/SCA 的配置且带阻断阈值**、**PR 记录中带有安全导向的评审意见与签核**、依赖清单/SBOM 及其漏洞状态、漏洞分诊与 SLA 闭环记录。
- 关联控制：A.8.25（安全开发生命周期，定义流程与关卡）、A.8.29（安全测试，验证结果）。
- **审计员的关键判据**："工具许可证本身什么都不证明"（a tool license proves nothing on its own）—— 他们要看**能否真的阻断构建**、**PR 是否真的被独立评审**（会检查开发者能否用第二个 admin 账号自我批准）。
- **判读**：这是真实的、每年重复的、有付费意愿的需求。**但它已经被现有工具链完全满足** —— GitHub 的 PR 记录 + 任意一个 SAST 就能产出全部证据，且 Aikido / Codacy / Socket 已经把结果同步到 Vanta / Drata。

**SOC 2**
- Trust Services Criteria 中与代码相关的主要是变更管理与逻辑访问控制。**SOC 2 本身不强制要求"AI 代码审查"，也不强制要求任何特定工具。**
- **真正的硬约束在商业侧而非监管侧**：多个独立来源一致指出，**SOC 2 Type II 报告在 ACV 超过约 $50,000 时是"gating"（非有不可）**，审计周期 6–12 个月。**这是对你自己的约束，不是你的卖点。**

### 7.2 ⚠️ 部分成立但被严重曲解

**EU AI Act —— 时间表刚刚被推迟，且基本不适用于普通软件开发**
- **2026-07-24 在《欧盟官方公报》公布、2026-07-27（就是今天）生效的 Digital Omnibus on AI**，正式修改了 Regulation (EU) 2024/1689：
  - 独立高风险系统（Annex III）义务：**从 2026-08-02 推迟到 2027-12-02**（推迟约 16 个月）。
  - 嵌入受监管产品的高风险 AI（Annex I）：**从 2027-08-02 推迟到 2028-08-02**。
  - 第 50 条透明度义务：**仍为 2026-08-02**（未推迟）；对已上市系统的机器可读内容标记有宽限至 2026-12-02。
  - 第 5 条禁止性实践、第 4 条 AI 素养、GPAI 义务：均维持原状，已生效。
  - 新增对 AI nudifier / CSAM 生成工具的禁令（2026-12 生效）。
  - 成员国建立国家 AI 监管沙盒的期限推迟至 2027-08-02。
- 来源：Gibson Dunn、Freshfields（EU AI Act unpacked #34）、欧洲议会 2026-06-16 通过、欧盟理事会 2026-06-29 最终通过。
- **对普通软件开发的适用性 —— 请务必看清楚**：AI Act 监管的是**"AI 系统"作为产品/服务本身**（招聘、信贷评分、执法、教育、边境管控等 Annex III 场景，以及医疗器械、机械、玩具等 Annex I 场景）。**它完全不监管"你用 AI 工具写普通商业软件"这件事。** 一家用 Cursor 写 CRM 的公司，不会因为 AI Act 产生任何新的代码审计义务。
- **判读**：**"EU AI Act 要求企业审计 AI 生成的代码"是彻头彻尾的营销话术。** 如果你的 BP 里出现这句话，任何懂行的投资人或客户 CISO 都会立刻降低对你的信任。而且时间表刚推迟了 16 个月，紧迫感也不存在了。

**美国 EO 14028 / SSDF (NIST SP 800-218) —— 强制力已被显著削弱**
- 时间线：2021-05 EO 14028 → NIST 发布 SSDF v1.1 (SP 800-218) → OMB M-22-18 / M-23-16 要求联邦采购方获取供应商自证 → CISA 2024-03 发布 Secure Software Development Attestation Form（"Common Form"）。
- **2025-06-06 EO 14306**（"Sustaining Select Efforts to Strengthen the Nation's Cybersecurity"）修改了 EO 14144，**删除了要求 CISA 集中验证供应商自证完整性的指令**，并**取消了配套的 FAR 条款制定方向**（FAR Case 2023-0021 前景不明）。随附的 fact sheet 批评前令"微观管理本应由部门层面处理的技术性网络安全决策"。
- **2026-02 OMB M-26-05**：联邦机构**"被允许但不被要求"**获取安全开发自证；可继续使用 CISA Common Form 与 NIST SSDF，但改为**各机构自行基于风险决定**。
- EO 14306 仍保留的部分：要求 NIST 于 2025-08-01 前在 NCCoE 设立产业联盟、2025-12-01 前发布 SSDF 初步更新、其后 120 天内发布最终版。
- **判读**：**SSDF 作为技术框架仍然有效且被广泛引用，但"联邦强制"这个销售抓手在 2025-06 之后已经实质性瓦解。** 如果你的目标客户不是美国联邦承包商，这条根本用不上；即使是联邦承包商，现在也变成"看各机构心情"。

### 7.3 ❌ 纯营销话术（切勿使用）
- "EU AI Act 要求你审计 AI 生成的代码" —— **假**。见上。
- "CRA 要求你标注哪些代码是 AI 写的" —— **假**。CRA 全文没有 AI 代码归因要求。
- "SOC 2 要求 AI 代码审查" —— **假**。SOC 2 不指定任何工具或技术。
- "监管机构正在要求 AI 代码审计轨迹" —— **目前为止没有任何生效法规有此要求**。Faros 在产品页写 "Audit trails for AI regulatory compliance" 是在**预售一个尚不存在的监管要求**。

### 7.4 合规角度的净结论

**真实可售的合规需求只有一个半：**
- **一个**：CRA 的 SBOM + 24 小时漏洞报告（2026-09-11 硬期限）。**但这个位置已被 Snyk / Socket / Aikido / Sonar 占据，且需要漏洞情报数据库这种重资产。单人开发者进不去。**
- **半个**：ISO 27001 A.8.28 / SOC 2 的代码审查证据留痕。**真实但已被现有工具链免费满足。**

**"AI 代码合规审计"作为一个独立品类，在 2026-07 没有监管支撑。它只有"企业内部治理焦虑"这一个驱动力 —— 焦虑是真的（Faros 数据支持），但焦虑不等于预算，更不等于合规预算。**

---

## 8. 买家画像与采购路径

### 8.1 谁签字（多来源一致的结论，均为 [三级] 行业分析，非硬数据）

按 ACV 分层：
- **$0 – $5K/年**：个人开发者或小团队负责人自己刷信用卡。真正的 PLG。
- **$5K – $50K/年**：**工程 VP / 工程总监**签字，采购走公司卡或简易 PO。需要通过基础的安全审查（问卷 + SOC 2 报告）。
- **$50K+/年**：买方委员会形成。技术冠军（开发者/技术主管）→ **VP Eng / CTO**（预算与架构契合）→ **安全/CISO**（数据隐私、SSO/SAML、风险）→ **采购/法务**（合同条款、MSA/DPA 谈判）→ **CFO**（ROI 与 license 利用率）。
- **代码安全类（B 组）的买家重心明显上移到 CISO / AppSec 负责人**，而效能度量类（C 组）的买家是 **VP Eng / CTO / 有时是 CFO**（因为涉及 R&D 资本化，LinearB 和 Swarmia 都单独卖这个模块）。

### 8.2 典型合同额（可查证的实数）
- **Jellyfish [三级，Vendr 交易数据]**：91 笔采购的**年合同中位数 $35,920**，实际成交下限约 $16,500（2026-07）；另有分析称区间 $50K–250K/年。
- **Waydev [一级，官网]**：50 人团队 Pro = $17,400/年，Premium = $29,400/年。
- **LinearB [一级，官网]**：Essentials 最低 30 席 × $29 × 12 = **$10,440/年起**；Enterprise 最低 50 席 × $59 × 12 = **$35,400/年起**。
- **Swarmia [三级]**：50 人 Standard 年付 ≈ €25,200/年（约 $27,500）。
- **CodeRabbit [一级换算]**：50 人 Pro 年付 = 50 × $24 × 12 = **$14,400/年**。
- **ZeroPath [一级]**：50 人 Team = ($1,000 + 50×$60) × 12 = **$48,000/年**。
- **归纳**：**这个赛道 50 人规模的年合同额落在 $10K – $50K 区间，中位数约 $25K–35K。** 这是一个"太大不能纯自助、太小养不起销售团队"的尴尬区间 —— 这也是为什么这么多厂商在 30–50 席设最低门槛。

### 8.3 PLG 自助率有多高（诚实回答：数据很弱）
- 我**没有找到**这个细分赛道的公开、可信的 PLG 自助转化率基准数据。所有搜到的数字都来自内容营销博客，**没有一个附带方法论或样本量**，我不予采信。
- **可以确认的结构性事实**：
  - **完全自助**的厂商（发布价格 + 信用卡即可用）：CodeRabbit、Greptile、Sourcery、Bito、Graphite、DeepSource、Socket、Corgea、Aikido、Semgrep、Snyk Team、Waydev Pro、Haystack、Ellipsis。
  - **强制询价**的厂商：Jellyfish、DX、Faros、ZeroPath（Team 档都要 Book a Demo）、Baz（Enterprise）、Qodo（30+ 用户）。
  - **规律很清晰：A 组（代码审查）高度自助化；B 组混合；C 组（效能度量）越往企业走越是纯销售驱动。**
- **一条硬约束 [三级但多来源一致]**：**SOC 2 Type II 在 ACV 超过约 $50K 时是 gating（非有不可）**，审计周期 6–12 个月。企业销售周期从首次接触到签约 **3–9 个月**，受监管行业更长。
- **对"零人工"模式的直接含义**：**$50K 以上的合同，在 2026 年依然无法在零人类参与的情况下成交。** 安全问卷、MSA 红线谈判、DPA、供应商风险评估、季度采购批次 —— 这些环节都需要一个能开会、能签字、能承担责任的自然人。这与你的**第〇之一条（无人化）**存在硬冲突，必须正视。

---

## 9. 红海判断与差异化空隙

### 9.1 这个赛道是否已经过度拥挤 —— 是，而且已经进入整合期

不是"竞争激烈"这么温和的说法。以下是六条独立的、可验证的结构性证据：

**证据一：玩家密度远超点名清单。** 你列了 29 个产品，我在调研过程中**顺带撞见**的额外玩家包括：CodeAnt AI、Gitar、Augment Code、Endor Labs、Veracode、Checkmarx、Pluralsight Flow、Code Climate Velocity、Plandek、PanDev Metrics、CodePulse、Typo、AnalyticsVerse、Docsie、Ref Tools、Docfork、DeepWiki。Tracxn 记录 CodeRabbit 有 **231 个活跃竞争对手**，Semgrep 有 **620 个**。

**证据二：并购整合已经开始。** **Sonar 收购了 Gitar**（Sonar 定价页上并列展示两个产品线，FAQ 专门解释"Gitar 加入 Sonar 对我有什么影响"）。Snyk 收购 Invariant Labs（2025-06）。整合期的到来意味着风投窗口正在关闭。

**证据三：领头羊增速崩塌。** Snyk —— 这个品类的定义者 —— ARR $326M 但**同比只增长 7%**（前一年 27%），估值从 $7.4B 被 BlackRock 下调到 $3.7B，2026-02 换 CEO。Sacra 的分析直白："the developer security category Snyk pioneered has grown crowded with competition from platform bundles like GitHub & Wiz and AI-native startups"。

**证据四：已经有产品在无声死亡。** Haystack 的定价页 footer 仍写 "Copyright © 2023"，页面里有未清理的 "Start jj trial" 占位文字，整个站点不提 AI 一个字。What The Diff 的产品形态（只写 PR 描述）已被 CodeRabbit 免费层完整覆盖。**这两个曾经有真实用户的产品已经是僵尸。**

**证据五：巨头把核心功能打包成边际免费。** GitHub Copilot **$10/月**就含 code review；Amazon Q **$19/月**；Gemini Code Assist **$19/月**；Cursor Teams **$40/月**已含 Bugbot；Sonar 的 MCP server 完全开源免费；Context7 的 MCP server 是 MIT 许可。**当 $10 能买到 80% 的价值时，一个新玩家没有定价空间。**

**证据六 —— 这条最致命：单位经济学已经被公开处刑。** Ellipsis 公布：一次中等 PR 的代码审查真实成本 **$0.74**（token $0.37 + 平台费 $0.37）。反推：Sourcery 的 $12/席位，如果一个开发者一月跑 20 次审查，COGS ≈ $7.4（假设与 Ellipsis 同量级模型），**毛利率 38%** —— 而 SaaS 的健康线是 75%+。这就是为什么**所有人都在做用量封顶**：CodeRabbit 5 次/开发者/小时、Greptile 50 credits、Bito 5K 行、DeepSource $10 credit、Qodo 直接改成纯 credit 制、Cursor Bugbot 在 2026-05 从席位制改成用量制。**这个赛道的商业模式正在集体从"SaaS"退化成"带加价的 API 转售"。** 一个没有议价能力的单人开发者，拿不到任何模型折扣，COGS 会比这些人更高。

### 9.2 CursorFlow AI 原方案的三个功能，逐条判死刑

| 提案功能 | 现状 | 判断 |
|---|---|---|
| **自动代码审计** | Cursor Bugbot（Teams 套餐内含）+ 13 个独立 AI reviewer + GitHub Copilot $10/月 + 10 个 SAST 厂商 | **完全红海。** 无进入空间。 |
| **私有知识库集成** | MCP 协议是开放标准；Context7 的 MCP server **MIT 开源可自托管**，商业托管版 $10/席位；Bito AI Architect、Docsie、Ref Tools 已在做 | **彻底商品化。** 无定价权。 |
| **提示词优化 / Cursor rules** | Cursor Teams 自带 "Team marketplace for internal rules, skills, and plugins"，Enterprise 可强制下发规则；外部市场是 $27 一次性模板包到 $99/月订阅的**信息产品**，非 SaaS | **市场存在但性质错了**，且正被官方功能吞掉。 |

**"零人工、全自动、企业级 SaaS"这个组合本身内部矛盾。** 第 8 节的数据显示：企业级（$50K+ ACV）在 2026 年依然需要 SOC 2 Type II（6–12 个月审计）、安全问卷、MSA 谈判、DPA —— 这些**无法无人化**。而能无人化的部分（$0–5K 自助），单位经济学被 LLM COGS 吃掉，且要和 $10 的 GitHub Copilot 正面竞争。

### 9.3 单人 / 每周 20 小时 / 零员工 / 纯自有资金的现实胜算

**按原方案：我的估计是成功概率低于 5%，且这个数字是我的主观判断，不是可复现的计算 —— 但支撑它的每一条事实都在上文标了来源。**

具体的失败机制，按发生顺序：
1. **前 3 个月**：能做出 demo。LLM API + GitHub App 的技术门槛在 2026 年已经很低（这既是好消息也是坏消息 —— 它对所有人都低）。
2. **第 4–6 个月**：获客撞墙。开源免费是标配（你也得做，不然没流量），但开源用户不付费；付费流量的关键词（"AI code review"、"cursor rules"）已被 246 人的 CodeRabbit、有 Benchmark 背书的 Greptile 和一堆 SEO 农场（本次调研中撞见的 costbench / aicodereview.cc / stackpick / toolradar / codepulsehq 全都是）完全占据。
3. **第 7–12 个月**：即使拿到几十个付费用户，COGS 吃掉毛利。你没有模型折扣，Ellipsis 的 $0.74 是你的地板而不是天花板。
4. **任何时候**：企业客户问"你们有 SOC 2 吗"、"能自托管吗"、"能签 DPA 吗"、"数据在欧盟吗"。CodeRabbit 有（EU SaaS 部署、自托管、审计日志、供应商安全审查与合同红线谈判都在 Enterprise 档明确列出）。你没有，且**每周 20 小时也拿不到**。
5. **随时可能发生**：Cursor 把 AI Code Tracking API 从 Enterprise 下放到 Teams，或者在 marketplace 里内置 rules 生成 —— 一次产品更新就归零。

### 9.4 如果一定要在这个赛道找空隙，具体在哪

我找到三个**真实存在的、具体到人群和功能**的缝隙。我按"单人可执行度"排序，并对每个给出证伪条件。**注意：我认为其中两个是真机会，一个是陷阱。**

---

#### 空隙 A（推荐度最高）：给"Cursor Teams 档"客户做 AI 代码归因与合规证据包

**空隙的精确位置**：Cursor 的 **AI Code Tracking API 是 Enterprise 独占，且仍是 alpha 状态**（官方文档明确标注 "Availability: Enterprise only"、"Status: Alpha"）。Cursor Teams 档（$40/user/mo）的客户拿不到 commit 级的 AI 归因数据。Teams 档覆盖的正是**10–200 人规模的公司**，而这恰好是：
- 数量最多的 Cursor 付费群体；
- 正在准备**第一次 SOC 2 Type II 或 ISO 27001 认证**的公司；
- 买不起 DX（不公开定价、最短 1 年合同）、Jellyfish（≥50 席、中位 $35,920/年）、Faros（估 $80K–150K/年）的公司。

**具体人群**：30–80 人规模的 B2B SaaS 公司里，那个**同时兼任 DevOps、平台工程和合规负责人的一个人**。他的实际任务是：明年 Q1 拿 SOC 2 Type II，审计员会要 A.8.28 / 变更管理的证据，而他团队里 60% 的代码现在是 Cursor 写的，他答不上来"你们怎么保证 AI 生成的代码经过了审查"。

**具体功能（不是"做得更好"，是做别人没做的）**：
1. 一个装在开发者本地的轻量 Cursor 扩展 + Git hook，在**本地**做 AI 行签名与 commit 匹配（Cursor 自己就是这么做的，官方文档说 "All the AI detection is done on device"）—— 这条路径对 Teams 客户是开放的，因为你不依赖 Cursor 的 Enterprise API。
2. 输出**不是仪表盘**（仪表盘是 C 组五家的红海），而是**审计证据包**：每个 release 周期生成一份 PDF/CSV，内容是"本周期 X 个 PR，其中 Y 个含 >50% AI 生成代码，这 Y 个中 Z 个经过了至少一名非作者的人工评审 + SAST 通过"，直接对应 ISO 27001 A.8.28 审计员要的"PR 记录 + 独立评审 + 流水线阻断"三件套。
3. 一键推送到 **Vanta / Drata**（Aikido 和 Codacy 已经证明这个集成路径有人买单）。
4. 定价按**组织**而不是按席位：$199–499/月固定价。这绕开了席位制的 COGS 陷阱（你不跑 LLM，你只做本地签名匹配 + 报告生成，**边际成本接近零**）。

**为什么单人可做**：核心技术是 diff 签名匹配和报告生成，**不需要 LLM 推理**，所以没有 COGS 问题；不需要索引客户代码，所以安全审查压力小得多（"我们不接触你的源码"是 Waydev 和 Haystack 都在用的话术）；ACV 在 $2.4K–6K/年，**低于 SOC 2 的 $50K gating 线**，可以纯自助。

**证伪条件（必须先验证，不要先写代码）**：
1. 找 10 家 30–80 人、重度用 Cursor Teams、正在做或刚做完 SOC 2 的公司，问他们的合规负责人：**审计员有没有问过 AI 生成代码的问题？** 如果 10 家里少于 3 家说"问过"或"我担心会被问"，**这个空隙不存在，立刻停止**。
2. 查 Cursor 的公开路线图和论坛，判断 AI Code Tracking API 下放到 Teams 的可能性。如果 Cursor 官方明确表示要下放，**这个空隙的生命周期不足 12 个月**。
3. 验证本地 diff 签名匹配的准确率能否达到可用于审计的水平。Cursor 官方文档自己就承认了局限："Diff signatures may be invalidated if automated code formatting is modifying lines"、"AI Code Tracking has not been implemented for Background Agents, or the Cursor CLI yet"。**如果你的准确率低于 85%，审计场景就不成立**（审计要的是可辩护，不是大概）。

---

#### 空隙 B（推荐度中等）：垂直行业的 AI 编码规则集，作为内容产品卖给现有平台的用户

**空隙的精确位置**：本次调研发现，**几乎所有主流平台都开放了第三方规则**：Semgrep 有 rule registry（Teams/Enterprise 可发布私有规则）、CodeRabbit 有 custom pre-merge checks（Pro Plus 20 个）、Cursor 有 Team marketplace for rules、Sourcery 有 custom review rules、Corgea/ZeroPath 有 custom rules/policy engine。**但没有任何一家提供垂直行业的深度规则集。**

**具体人群**：医疗（HL7 / FHIR / HIPAA 的 PHI 处理规范）、金融（PCI DSS 的持卡人数据边界）、汽车/嵌入式（MISRA —— 注意 Sonar 已经在 Enterprise 档卖 MISRA C++:2023，说明这个方向确实有人付费）、以及**中国出海企业的数据出境合规**代码规范。这些团队的痛点是：通用 AI reviewer 完全不懂他们的行业规则，AI 生成的代码会把 PHI 写进日志、把卡号存进明文字段。

**具体功能**：不做平台，做**规则内容 + 持续维护订阅**。跨平台交付：同一套规则同时导出为 Semgrep rules、Cursor .mdc rules、CodeRabbit custom checks、CLAUDE.md。定价 $99–299/月/组织，或按行业包一次性 + 年度更新订阅。

**为什么单人可做**：这是**知识密集而非工程密集**的工作，边际成本为零，不与平台竞争而是寄生于平台（"卖铲子给淘金者"），每周 20 小时可持续维护。**已经有人在做类似的事并收到钱**（BuyCoded $27 一次性、Brainfile $99/月），只是他们做的是通用技术栈的浅规则。垂直深度是真差异。

**风险**：(a) 你必须真的懂那个行业，否则规则没有价值 —— **这是最大的门槛，如果你没有医疗/金融的代码合规背景，不要做这个**；(b) 天花板低（这是一个几十万美元/年的生意，不是几千万）；(c) 平台方可能自己做（Sonar 已经在做 MISRA）。

---

#### 空隙 C（我认为这是陷阱，写出来是为了让你避开）：更便宜的 AI code review

看起来 Sourcery $12、Bito $12 之下还有空间，实际上没有。原因见 9.1 证据六：$0.74/次审查的 COGS 地板 + 巨头 $10 的打包价 + 开源免费的获客标配 = **价格战的终局是所有人毛利归零**。Cursor Bugbot 在 2026-05 主动从席位制改成用量制，就是这个赛道最聪明的玩家承认"席位制卖 AI 审查不赚钱"的公开信号。**不要进。**

---

### 9.5 最终建议

**对 CursorFlow AI 原方案：不建议做。** 三个核心功能全部被 Cursor 第一方覆盖，商业模式与"零人工"约束存在内在矛盾，单位经济学被公开的 COGS 数据证伪。

**如果你决定继续，按这个顺序执行（每阶段有可证伪的验收标准）：**

- **阶段 0（第 1–2 周，0 行代码）**：执行空隙 A 的证伪条件 1。**验收标准：10 次真实对话，≥3 家确认审计员问过或担心被问 AI 代码问题。不达标则整个方向终止。**
- **阶段 1（第 3–6 周）**：如果阶段 0 通过，做本地 diff 签名匹配的技术验证。**验收标准：在你自己的 3 个真实仓库上，AI 归因准确率 ≥85%（人工抽样 100 个 commit 核对）。不达标则终止。**
- **阶段 2（第 7–12 周）**：做出只有"生成审计证据包 PDF"这一个功能的最小版本，找阶段 0 里那 3 家做免费试点。**验收标准：至少 1 家愿意把这份 PDF 真的交给审计员。**
- **阶段 3（第 13–20 周）**：只有阶段 2 通过才开始收费。**验收标准：3 个月内 ≥5 个付费组织，MRR ≥$1,000。不达标则终止，止损。**

**明确的止损线：如果 6 个月内没有 5 个付费客户，关掉它。** 这个赛道 2026 年的现实是，一个 246 人的公司做到 $40M ARR 用了 3 年并烧掉 $88M —— 每周 20 小时的单人开发者没有理由在同一个正面战场上赢。

---

## 10. 待验证事项清单（本报告中我未能核实的部分，请勿在 BP 中当作事实使用）

1. **Cursor Bugbot 的当前费率**（cursor.com/pricing#bugbot 锚点内容未渲染）。
2. **Codacy 的实际价格**（官网 JS 渲染，$18/dev/mo 仅来自三级来源）。
3. **Swarmia 的实际价格**（官网 JS 渲染，三个三级来源给出三个不同数字：€42 / €39 / $45）。
4. **Qodo 的席位价是否仍存在**（官网已转为 credit 制，$30/user 仅来自三级来源）。
5. **Qodo 是否有开源免费方案**（FAQ 有此条目但内容未渲染）。
6. **What The Diff 官方定价页原文**（本次仅得搜索引述）。
7. **Baz 官方定价页原文**（baz.co 已 301，baz.ai/pricing 仅得搜索引述）。
8. **DORA 2024 报告"AI 采纳每 +25% 交付稳定性 -7.2%"的原文出处**（广为引用但本次未抓到原始报告页）。
9. **Sourcery、Bito、Graphite、Qodo、Corgea、ZeroPath、DeepSource、Aikido、Socket 的团队规模与 ARR**（均未找到可信来源）。
10. **本赛道 PLG 自助转化率的真实基准数据**（未找到任何带方法论的公开数据；所有搜到的数字均为无来源的内容营销，不予采信）。
11. **Faros AI 的员工数与收入区间**（仅来自 LinkedIn 公司信息面板，可靠性低）。

---

*报告完成于 2026-07-27。所有一级来源均于当日直接抓取。本报告的判断部分（第 9 节）是分析意见，不是事实陈述；其依据的每一项事实都在上文标注了来源与等级。*
