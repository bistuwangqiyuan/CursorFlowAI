# 早期创业项目风险量化：方法论与公式手册

**适用对象**：单人、纯自有资金、单次不可重复、不可流动的早期创业投入
**编制日期**：2026-07-27
**配套可复现计算**：`risk_methodology_calcs.py`（Python 3.12.10 + numpy 2.5.1，固定随机种子 20260727），输出见 `risk_methodology_output.txt`
**编制原则**：每条公式给出变量定义、适用前提、已知局限与权威出处；凡属假设或推测一律显式标注；凡引用数字，或有可查证 URL，或有可运行代码复现。

---

## 0. 阅读须知：本手册的适用边界

本手册整理的是**为可重复、可流动、可连续再投资的赌局设计的数学工具**。把它们用在"一个人、一次性、投进去就拿不出来"的创业项目上，属于**跨适用域使用**。手册的态度是：

1. 这些工具依然有用，但用途是**约束思维、暴露内在矛盾、划定行动边界**，而不是产出可承诺的收益数字。
2. 每一节都单列"已知局限"。第 6 节汇总说明在本项目中哪些指标只能作为参考、必须如何向读者披露。
3. 手册中出现的一切概率（如"全损 60%"）都是**主观估计**，不是观测频率。任何基于它们的输出，其精度上限由这些主观输入决定，不由计算的小数位数决定。

---

## 1. Kelly 准则

### 1.1 原始出处

| 项目 | 内容 |
|---|---|
| 论文 | Kelly, J. L., Jr. (1956). *A New Interpretation of Information Rate*. **Bell System Technical Journal**, 35(4), 917–926 |
| DOI | [10.1002/j.1538-7305.1956.tb03809.x](https://doi.org/10.1002/j.1538-7305.1956.tb03809.x) |
| 全文（免费） | [Internet Archive: BSTJ 35:4 (1956) pp.917–926](https://archive.org/details/bstj35-4-917) |
| 目次佐证 | [BSTJ vol.35 issue 4 目录](https://vtda.org/pubs/BSTJ/vol35-1956/bstj-vol35-issue04.html) |
| IEEE 重刊 | [10.1109/TIT.1956.1056803](https://doi.org/10.1109/tit.1956.1056803)（IRE Trans. Inf. Theory, 1956-09） |

Kelly 原文的问题设定是**通信信道**：赌徒通过一条有噪信道接收关于随机事件结果的私有信息，在给定赔率下下注。原文结论是"赌徒资本的最大指数增长率等于信道的信息传输率"。**"最优下注比例"是这一信息论结论的副产品，不是 Kelly 论文的主题。** 这一点在引用时应如实说明，避免把 Kelly 说成"投资理论"。

**理论基础的严格化**由 Breiman 完成：

> Breiman, L. (1961). *Optimal Gambling Systems for Favorable Games*. **Proc. 4th Berkeley Symposium on Mathematical Statistics and Probability**, Vol. 1, 65–78.
> 全文：<https://digitalassets.lib.berkeley.edu/math/ucb/text/math_s4_v1_article-05.pdf>

Breiman 证明了最大化 `E[log S_n]` 的策略 A\* 在两个意义上渐近最优：（i）渐近最大化财富增长率；（ii）渐近最小化达到给定目标财富所需的期望时间。**注意 Breiman 的结论全部是"渐近"（asymptotic）的**，其前提是**独立同分布的、可无限重复的赌局**。这是后文所有质疑的根源。

---

### 1.2 离散两结果情形：`f* = (bp − q)/b`

#### 公式与变量定义

```text
f*  =  (b·p − q) / b  =  p − q/b

f*  最优下注比例（占当前总资本的比例）
p   获胜概率
q   失败概率，q = 1 − p
b   净赔率（net odds）：赢时每投入 1 单位净赚 b 单位；输时损失全部投入的 1 单位
```

#### 推导

设当前资本 `W`，下注比例 `f`，一期后：

```text
赢（概率 p）：W → W(1 + f·b)
输（概率 q）：W → W(1 − f)

每期对数增长率的期望：
g(f) = E[ln(W_1/W_0)] = p·ln(1 + f·b) + q·ln(1 − f)

一阶条件：
g'(f) = p·b/(1 + f·b) − q/(1 − f) = 0
  ⇒  p·b·(1 − f) = q·(1 + f·b)
  ⇒  p·b − p·b·f = q + q·b·f
  ⇒  p·b − q = b·f·(p + q) = b·f          （因 p + q = 1）
  ⇒  f* = (p·b − q)/b

二阶条件（保证是最大值）：
g''(f) = −p·b²/(1 + f·b)² − q/(1 − f)² < 0   对一切可行 f 严格成立
故 g 严格凹，一阶条件的根唯一且为全局最大。
```

#### 适用前提（缺一不可）

1. **两个结果，且输时全损**（`−100%`）。若输时只损失部分本金，公式形式改变，须用 §1.3 的一般形式。
2. `p` 与 `b` **已知且精确**。
3. 赌局**可无限重复**，且每期结果**独立同分布**。
4. 资本**可连续分割**、**可即时再投资**、**无交易成本、无税、无最小下注额**。
5. 目标函数是**长期几何增长率最大化**（等价于对数效用），而非其他任何效用函数。
6. `f* > 0` 要求 `b·p > q`，即**期望为正**。期望非正时 Kelly 的答案是"一分钱都不下"。

#### 数值校验（`risk_methodology_output.txt` 第 [1] 节）

| p | b | 闭式 f\* | 数值解 f\* | 偏差 | g(f\*) |
|---|---|---|---|---|---|
| 0.60 | 1.0 | 0.200000 | 0.200000 | 3.6e−13 | 0.020136 |
| 0.51 | 1.0 | 0.020000 | 0.020000 | 9.3e−15 | 0.000200 |
| 0.10 | 20.0 | 0.055000 | 0.055000 | 3.2e−13 | 0.023280 |
| 0.05 | 30.0 | 0.018333 | 0.018333 | 4.1e−13 | 0.004334 |

（"数值解"由 §1.3 的通用二分法求解器独立算出，用于交叉验证闭式解。）

**值得注意的一行**：`p = 0.05, b = 30`——即"5% 的概率赚 30 倍，95% 的概率全损"，期望倍数 `0.05×31 = 1.55`，看起来极其诱人。Kelly 给出的答案是**只押 1.83% 的资本**。这个反差是本手册最重要的直觉之一。

---

### 1.3 多结果 / 连续分布的一般形式

#### 一般形式

```text
最大化   g(f) = E[ ln(1 + f·X) ]

X   每单位下注的净收益率随机变量（赢为正、亏为负；X = M − 1，M 为回报倍数）
f   投入比例
可行域： f ∈ [0, 1/|x_min|)，其中 x_min = min(X) < 0
        （必须保证 1 + f·X > 0 对所有可能结果成立，否则有正概率触及零或负资本，
          此时 E[ln(·)] = −∞，数学上等价于"确定性破产"）
```

#### 离散多档情形

```text
设结果有 n 档：概率 p_1..p_n，净收益率 x_1..x_n，Σp_i = 1

g(f)  = Σ_i  p_i · ln(1 + f·x_i)
g'(f) = Σ_i  p_i · x_i / (1 + f·x_i)
g''(f)= − Σ_i p_i · x_i² / (1 + f·x_i)²  ≤ 0    （严格 < 0，只要存在 x_i ≠ 0）
```

**g 在可行域上严格凹**，因此：

- 若 `g'(0) = E[X] ≤ 0` ⇒ `f* = 0`（不下注）；
- 若 `g'(0) > 0` ⇒ 存在唯一 `f* ∈ (0, 1/|x_min|)` 使 `g'(f*) = 0`，可用**二分法**在 `[0, 1/|x_min| − ε]` 上求根，收敛有保证且无需梯度库。

本手册实现见 `risk_methodology_calcs.py` 中的 `kelly_multi_outcome()`，容差 1e−12，与两结果闭式解交叉验证偏差 < 1e−12（见上表）。

#### 连续分布情形

```text
g(f) = ∫ ln(1 + f·x) dF(x)
```

一阶条件 `E[X/(1+fX)] = 0`。除对数正态等特例外一般无闭式解，实践中用蒙特卡洛积分 + 一维求根。

**对数正态/连续时间近似**（Thorp 2006, eq. 7.7，见 §1.5）：

```text
f* = (m − r) / s²

m  资产（连续复利口径）期望收益率
r  无风险利率
s  波动率
```

#### 已知局限

- **对分布尾部极度敏感**。`ln(1 + f·x)` 在 `f·x → −1` 处发散，因此"全损档"的概率估计误差会不成比例地影响 `f*`。
- 存在全损档（`M = 0`）时，可行域上界严格小于 1，即 **Kelly 永远不允许 all-in**。
- 多档模型要求给出"档内代表倍数"，这一步通常是纯假设，必须显式标注。

#### 算例（`risk_methodology_output.txt` 第 [2]、[3] 节）

**算例 A：以 VC 融资级别结果分布为参照系**

档位概率取自 Correlation Ventures 数据（见 §2.2），各档代表倍数为**本手册的假设值**：

| 档位 | 概率 | 代表倍数（假设） |
|---|---|---|
| <1× | 0.6507 | 0.2 |
| 1–5× | 0.2503 | 2.0 |
| 5–10× | 0.0601 | 7.0 |
| 10–20× | 0.0250 | 14.0 |
| 20–50× | 0.0100 | 30.0 |
| >50× | 0.0040 | 70.0 |

结果：胜率 34.93%，`E[M] = 1.982`，盈亏比 5.38，Profit Factor 2.89，
**Kelly `f* = 15.21%`**，`g(f*) = 0.0439`。

解读：即便期望倍数接近 2 倍，对数最优的单笔仓位也只有净资产的约 15%。若 `f = 1`（把全部身家投进去），`E[ln] = −0.64`，即**长期几何增长率为负**——注意此处最差档被假设为 0.2×（而非归零），`f = 1` 仍在可行域内；若最差档为真正的归零，则 `f = 1` 时 `E[ln] = −∞`。

**算例 B：四档创业情景（占位假设，必须替换为项目自有估计）**

| 情景 | 全损 | 回本 | 小成 | 大成 | E[M] | Kelly f\* |
|---|---|---|---|---|---|---|
| A（悲观） | 0.70 @ 0× | 0.15 @ 1× | 0.12 @ 3× | 0.03 @ 15× | 0.96 | **0**（不下注） |
| B（中性） | 0.60 @ 0× | 0.20 @ 1× | 0.15 @ 4× | 0.05 @ 25× | 2.05 | **10.83%** |

情景 A 的 `E[M] = 0.96 < 1`，Kelly 的答案是"一分钱都不要下"。**这不是模型故障，而是模型在给定输入下的正确输出。** 若在这组概率估计下仍决定创业，理由必须来自 Kelly 框架之外（如非货币回报、期权价值、学习价值），并且必须在文档中明说。

情景 B 下：半 Kelly 保留 `82.3%` 的增长率，四分之一 Kelly 保留 `54.1%`，两倍 Kelly 保留 `52.9%`。**注意这些比例与 §1.5 中"半 Kelly 保留 75%"的经典结论不同**——后者是连续/对数正态近似下的结果，离散重尾分布下不成立。这是一个必须诚实说明的差异。

---

### 1.4 ★ 核心质疑：Kelly 用于不可流动、不可重复、单次下注的创业投资

这一节是本手册最重要的部分。以下每一条批评都有明确出处。

#### 质疑一：Kelly 的最优性是"渐近"的，单次下注不适用

Breiman (1961) 的两个最优性定理都是 `n → ∞` 的极限结论（原文："In this work, we are especially interested in the asymptotic point of view."）。**在 N = 1 时，Kelly 没有任何最优性可言。**

Thorp 自己给出的量化例子（Thorp 2006，转引于 MacLean-Thorp-Ziemba 综述）：

> 掷硬币，A 游戏优势 1.0%，B 游戏优势 1.1%。需要**两百万次**试验，才有 84% 的把握让 A 的表现被 B 超过。
> 连续时间下，若 μ_A = 20%、μ_B = 10%、σ_A = σ_B = 10%，5 年即可以 95% 置信度区分；但若 σ_A = 20%、σ_B = 10%，则需要 **157 年**。

出处：MacLean, L. C., Thorp, E. O., & Ziemba, W. T., *Good and Bad Properties of the Kelly Criterion*（收入 *The Kelly Capital Growth Investment Criterion*, World Scientific, 2011）
全文：<https://www.stat.berkeley.edu/~aldous/157/Papers/Good_Bad_Kelly.pdf>

**推论**：创业者一生能"下注"的次数是个位数。Kelly 所依赖的大数律在这个样本量下完全不起作用。

#### 质疑二：Samuelson 的正式反对（两篇，必须都引）

**（1）Samuelson, P. A. (1971).** *The "Fallacy" of Maximizing the Geometric Mean in Long Sequences of Investing or Gambling*. **PNAS**, 68(10), 2493–2496.
DOI: [10.1073/pnas.68.10.2493](https://doi.org/10.1073/pnas.68.10.2493) ｜ 全文 PDF: <https://finance.martinsewell.com/money-management/Samuelson1971.pdf>

原文摘要的核心论断（直接引用）：

> "…this does not imply the false corollary that the geometric-mean strategy is optimal for any finite number of periods, however long, or that it becomes asymptotically a good approximation. As a trivial counter-example, it is shown that for utility proportional to x^γ/γ, whenever γ ≠ 0, the geometric strategy is suboptimal for all T and never a good approximation."

即：**对任何不是对数效用的幂效用函数，几何均值最大化在任何有限期数下都不是最优的，而且不会渐近变好。**

**（2）Samuelson, P. A. (1979).** *Why we should not make mean log of wealth big though years to act are long*. **Journal of Banking & Finance**, 3(4), 305–307.
全文 PDF（Wharton 课程页）: <http://stat.wharton.upenn.edu/~steele/Courses/434/434Context/Kelly%20Resources/Samuelson1979.pdf>

这篇著名的"全单音节词"论文的核心句（直接引用）：

> "A win of ten is not the same as a win of two. Nor is a loss of two the same as a loss of three. How much you win by counts. How much you lose by counts. … Why then do some still think they should want to make mean log of wealth big? They nod. They feel 'That way I must end up with more. More sure beats less'. But they err. What they do not see is this: **When you lose — and you sure can lose — with N large, you can lose real big.**"

Samuelson 的论证不是"Kelly 的数学错了"，而是"**Kelly 隐含地把一个特定效用函数（对数）伪装成一条普适的理性法则**"。对本项目而言：如果创业者的真实风险偏好不是对数效用（几乎可以肯定不是——单人创业者对"归零"的厌恶远超对数效用所刻画的程度），Kelly 给出的比例就不是他应该采用的比例。

#### 质疑三：破产风险与效用函数的错位

- 对数效用的 Arrow–Pratt 绝对风险厌恶系数 `R_A(w) = 1/w`，对非破产的投资者接近零。MacLean-Thorp-Ziemba 明确指出："**Since log has R_A(w) = 1/w, which is close to zero, the Kelly bets may be exceedingly large and risky for favorable bets.**"
- Kelly 数学上"永不破产"（`f < 1` 保证 `1 + fX > 0`），但这个保证依赖**资本可无限分割**。现实中存在最小可行投入（一个人的生活成本、一台服务器的月费），跌破该门槛即等价于出局。**Kelly 模型里不存在"出局"这个吸收态，现实中存在。**
- 同一份综述的"Bad"清单还包括：任何固定比例策略，在试验次数足够多时，都会有相当概率经历极大回撤。

#### 质疑四：不可流动 = Kelly 的核心假设被直接删除

Kelly / Breiman / Thorp 框架的机制是"**下注 → 立即结算 → 用新的资本基数再下注**"。创业投资：

- 结算周期以年计，且不确定；
- 期间资本不可赎回，无法按新信息调整仓位；
- "资本基数"在结算前不可观测（未上市股权无可靠市价）。

实务界对此有直接论述（非学术文献，作为实务佐证引用）：

> "the Kelly Criterion was built on a scenario where all bets pay off immediately… you may find the Kelly Criterion suggesting you up a bet when all of your cash is already in other companies."
> — Jerry Neumann, *Venture Follow-on and the Kelly Criterion*, <https://reactionwheel.net/2017/06/venture-follow-on-and-the-kelly-criterion.html>

#### 质疑五：遍历性（ergodicity）——反而支持"不要用期望值"，但也否定"单次下注"

- Peters, O., & Gell-Mann, M. (2016). *Evaluating gambles using dynamics*. **Chaos: An Interdisciplinary Journal of Nonlinear Science**, 26(2), 023103. DOI [10.1063/1.4940236](https://doi.org/10.1063/1.4940236) ｜ arXiv 预印本: <https://arxiv.org/abs/1405.0585>
- Peters, O. (2019). *The ergodicity problem in economics*. **Nature Physics**, 15, 1216–1221.（本手册未直接核验该篇原文，系转引自 Peters 团队后续论文的参考文献列表，引用时宜标注为二手来源。）

遍历性经济学的论点是：乘性财富过程**非遍历**，个体经历的**时间平均增长率**不等于跨个体的**系综平均（期望值）**。经典反例（Peters 抛硬币）：赢则 +50%，输则 −40%，期望值每轮增长 5%，但单条轨迹的时间平均每轮**衰减约 5%**。

**这一框架对本项目是双刃的**：

- 支持面：它论证了"用 `E[收益]` 来评价一个乘性、不可分散的赌局是错误的"，从而**支持不要用期望倍数作为创业回报的宣传口径**。
- 否定面：时间平均增长率同样定义在 `T → ∞` 的极限上。**单次、不可重复的创业投入，既没有系综也没有时间序列**，两种平均都不适用。

**诚实的结论**：在 N = 1 的情形下，能被严格辩护的只有"完整的结果分布"本身，任何把分布压缩成单一数字（期望值、几何均值、Kelly 比例）的做法都要付出信息损失，且这种损失在重尾分布下极大。

---

### 1.5 Fractional Kelly（半 Kelly / 四分之一 Kelly）

#### 理论依据与量化结论

在**连续时间 / 对数正态**近似下，Thorp (2006) 给出（eq. 7.7）：

```text
f*        = (m − r)/s²
g(c·f*)   = (m − r)²·(c − c²/2)/s²  +  r
Sdev(G)   = c·(m − r)/s

c   Kelly 分数（c = 1 为满 Kelly）
m   期望收益率；r 无风险利率；s 波动率
```

由此立即得到**超额几何增长率的保留比例**：

```text
[g(c·f*) − r] / [g(f*) − r]  =  (c − c²/2) / (1/2)  =  c·(2 − c)
```

| c | 保留的超额增长率 `c(2−c)` | 波动率（相对满 Kelly） |
|---|---|---|
| 0.25 | 43.75% | 25% |
| **0.50** | **75.00%** | **50%** |
| 0.75 | 93.75% | 75% |
| 1.00 | 100% | 100% |
| 1.50 | 75.00% | 150% |
| 2.00 | **0%** | 200% |

**"半 Kelly 保留约 75% 的增长率、波动率减半"这一广为流传的结论，其严格来源就是上式在 c = 0.5 处的取值**，而不是某个经验观察。同理，`c = 2`（两倍 Kelly）时超额增长率归零——这与 MacLean-Thorp-Ziemba 的表述一致：

> "for processes which are well approximated by continuous time, the growth rate becomes zero plus the risk free rate when one bets exactly twice the Kelly wager."

#### 权威出处

| 结论 | 出处 |
|---|---|
| `g(cf*)` 公式与 fractional Kelly 论证 | Thorp, E. O. (2006). *The Kelly Criterion in Blackjack, Sports Betting, and the Stock Market*. **Handbook of Asset and Liability Management**, Vol. 1, 385–428. DOI [10.1016/S1872-0978(06)01009-X](https://doi.org/10.1016/S1872-0978(06)01009-X)。全文 PDF: <https://gwern.net/doc/statistics/decision/2006-thorp.pdf> |
| 增长 vs 安全的完整权衡框架、fractional Kelly 有效前沿 | MacLean, L. C., Ziemba, W. T., & Blazenko, G. (1992). *Growth Versus Security in Dynamic Investment Analysis*. **Management Science**, 38(11), 1562–1585. DOI [10.1287/mnsc.38.11.1562](https://doi.org/10.1287/mnsc.38.11.1562) |
| fractional Kelly ≡ Kelly 与现金的混合；半 Kelly ⟺ 负幂效用 δ = −1，四分之一 Kelly ⟺ δ = −3（对数正态下精确） | MacLean, Thorp & Ziemba, *Good and Bad Properties of the Kelly Criterion*（前引） |

#### Thorp 本人的原话（论证"为什么要打折"）

> "My experience has been that most cautious gamblers or investors who use Kelly find the frequency of substantial bankroll reduction to be uncomfortably large. … To reduce this, they tend to prefer somewhat less than the full betting fraction f\*. **This also offers a margin of safety in case the betting situations are less favorable than believed.** The penalty in reduced growth rate is not severe for moderate underbetting."

#### 已知局限（必须与上表同时呈现）

1. **`c(2−c)` 是连续/对数正态近似的结果**。本手册算例 B（四档离散、含全损档）实测：半 Kelly 保留 82.3%、四分之一 Kelly 保留 54.1%、两倍 Kelly 保留 52.9%——**与 75% / 43.75% / 0% 均不相符**。重尾离散分布下必须直接数值计算，不能套用 75%。
2. "波动率减半"指的是对数财富增长率的标准差，**不是最大回撤减半**。网上流传的"回撤从 40% 降到 15–20%"一类说法未见于上述原始文献，本手册不予采用。
3. fractional Kelly 降低的是**增长率的方差**，不是**估计误差**本身。它是对未知的保险，不是对未知的消除。

---

### 1.6 参数估计误差与过度下注的危害

#### 定量结论一：估计误差 × 下注比例的联合效应

在 `r = 0` 的连续近似下，令 `k = m_true / m_est`（真实边际相对估计边际的比值）、`c = f / f*_est`：

```text
g(c·f*_est) = (m_est² / 2s²) · (2ck − c²)
```

**推导**：`g(f) = f·m_true − f²s²/2`，代入 `f = c·f*_est = c·m_est/s²`、`m_true = k·m_est` 即得。

下表单位为 `m_est²/(2s²)`（`risk_methodology_output.txt` 第 [4b] 节，与 Thorp 2006 图 5 的文字描述逐项吻合）：

| k \ c | 0.50（半 Kelly） | 1.00（满 Kelly） | 1.50（超额下注） |
|---|---|---|---|
| **k = 0.5**（真实只有估计的一半） | **+0.25** | **0.00** | **−0.75（必然破产）** |
| k = 1.0（估计准确） | +0.75 | +1.00 | +0.75 |
| k = 1.5（低估了自己） | +1.25 | +2.00 | +2.25 |

**读法**：
- 高估边际一倍时，满 Kelly 的增长率**归零**，1.5 倍 Kelly 变为 **−0.75（确定性毁灭）**；
- 而半 Kelly 在这一情形下反而取得该行的最大值 +0.25；
- 代价的**不对称性**：低估自己（k = 1.5）时半 Kelly 只损失 0.75（相对 2.00 的最优），而高估自己时超额下注直接归零以下。

Thorp 的结论（原文）：

> "To the extent m_e is an uncertain estimate of m_t, it is wise to assume m_t < m_e and to choose f < f\*_e by enough to prevent g ≤ 0."
> "…**overbetting is much more severely penalized than underbetting**."

#### 定量结论二：均值的估计误差最致命

> Chopra, V. K., & Ziemba, W. T. (1993). *The Effect of Errors in Means, Variances, and Covariances on Optimal Portfolio Choice*. **Journal of Portfolio Management**, 19(2), 6–11. DOI [10.3905/jpm.1993.409440](https://doi.org/10.3905/jpm.1993.409440)
> 全文 PDF（Duke 课程页）: <https://people.duke.edu/~charvey/Teaching/BA453_2006/Chopra_The_effect_of_1993.pdf>

核心结论：**均值的估计误差，其危害约为方差估计误差的 11 倍、协方差估计误差的 21 倍以上。**
（该表述的独立佐证：<https://eprints.whiterose.ac.uk/id/eprint/79158/1/weights_final.pdf>，其中直接引用了 Chopra–Ziemba 原句。需注意：后续研究如 *Quantitative Finance* 22(10) 对该结论的普适性提出了修正意见，认为在全分布视角下相关系数的影响可能占主导，引用时宜标注这一学术争议。）

#### 对本项目的直接含义

Kelly 的输入里，`p`（各档概率）在数学地位上等价于"均值估计"。单人创业项目的 `p` **没有任何历史频率支撑**，纯属主观先验。按 Chopra–Ziemba 的敏感度排序，这正好是最致命的那个参数。**因此本项目使用 Kelly 时，必须（a）打折至 1/4–1/2，（b）同时报告概率的敏感性分析，(c) 明说 f\* 的小数位不代表精度。**

---

## 2. 胜率、盈亏比与结果分布

### 2.1 标准定义

```text
p    胜率      = P(结果为盈利)
q    败率      = 1 − p
W    平均盈利  = E[盈利额 | 盈利]        （正数）
L    平均亏损  = E[|亏损额| | 亏损]      （正数）

期望值（每笔）：
    E = p·W − q·L

盈亏比（payoff ratio / win-loss ratio）：
    R = W / L

盈亏平衡胜率：
    E = 0  ⇒  p_BE = L/(W + L) = 1/(1 + R)

Profit Factor（总盈利 / 总亏损，概率加权口径）：
    PF = (p·W) / (q·L) = (p/q)·R
    注意恒等式：E > 0 ⟺ PF > 1
```

**变量口径必须写明**：`W` 与 `L` 是"绝对金额"还是"相对本金的倍数"，两种口径下 `R` 的数值不同。本手册统一采用**相对本金的净收益率**口径：回报倍数 `M`，净收益率 `X = M − 1`。

**与 Kelly 的关系**：两结果全损情形下 `L = 1`、`W = b`，于是 `f* = p − q/b = (E)/b`，即 **Kelly 比例 = 期望值 / 净赔率**。

#### 已知局限

- `p`、`W`、`L` 三个数字只能刻画分布的前两阶信息中的一部分。**在幂律型重尾分布下，`W` 由极少数极端值决定，其样本估计极不稳定**（见 §2.2 关于 α < 2 的讨论）。
- Profit Factor 是交易实务指标，**未见于同行评议文献的规范定义**；本手册按上式定义并自证其与 `E > 0` 的等价性，引用时应说明这是操作性定义而非学术标准。

### 2.2 风险投资行业的真实结果分布（现实锚点）

这是为创业项目设定"结果分档概率"时唯一可查证的外部参照系。**必须注意：以下都是"拿到机构融资的公司"的分布，与"单人自筹的项目"不是同一总体。** 用作锚点时须显式说明这一偏差方向（机构筛选后的样本，成功率应高于未筛选样本）。

#### （1）Correlation Ventures：约 21,000 笔美国 VC 融资

原始来源：Correlation Ventures 官方博客（David Coats），
- *Venture Capital — No, We're Not Normal*：<https://medium.com/correlation-ventures/venture-capital-no-were-not-normal-32a26edea7c7>
- *Venture Capital — We're Still Not Normal*（更新版）：<https://medium.com/correlation-ventures/venture-capital-were-still-not-normal-9d07d354db88>

原文关键句（第一篇）：

> "About half (51%) of all of the capital invested into venture-funded companies exiting over the last decade lost money, while **less than 4% generated a 10X or greater multiple**. When calculated as a percent of financings, rather than by dollars, the distribution is even more skewed: **almost two thirds of financings lost money for investors**."

按融资笔数的分档（由 Seth Levine 依 Correlation 数据整理，2004–2013，约 21,000 笔）：

| 结果 | 占融资笔数 |
|---|---|
| 亏损 / 未收回 1× | ~65% |
| 1×–5× | ~25% |
| 5×–10× | ~6% |
| 10×–20× | ~2.5% |
| 20×–50× | ~1% |
| >50× | ~0.4% |

出处：Seth Levine, *Venture Outcomes are Even More Skewed Than You Think*（2014-08）：<https://sethlevine.com/archives/2014/08/venture-outcomes-are-even-more-skewed-than-you-think.html>
交叉佐证：Collaborative Fund, *Tails, You Win*：<https://collabfund.com/blog/tails-you-win/>

**方法论提醒（重要）**：这两个来源对 65% 的口径描述略有差别（"lost money" vs "fail to return 1x capital"），且 Correlation 的更新版数据（"37% generated a less than 1X return"，按投入资金口径；"nearly half of financings lost money"）与旧版不同。**引用时必须写明是哪一版、哪个口径、哪个年份区间。** 本手册在算例中采用 Levine 整理的笔数口径分档，并已标注为"参照系"而非"本项目的概率"。

#### （2）Horsley Bridge：7,000+ 笔投资，1985–2014

出处：Chris Dixon (a16z), *Performance Data and the 'Babe Ruth' Effect in Venture Capital*：<https://a16z.com/performance-data-and-the-babe-ruth-effect-in-venture-capital/>

原文关键句：

> "about **~6% of investments representing 4.5% of dollars invested generated ~60% of the total returns**."

#### （3）AngelList：早期投资服从 α < 2 的幂律

出处：
- Othman, A., *Startup Growth and Venture Returns*（AngelList 研究报告）：<https://angel.co/pdf/growth.pdf>
- AngelList 向 SEC 提交的补充数据（S7-08-19）：<https://www.sec.gov/comments/s7-08-19/s70819-7773213-223398.pdf>
- *How Portfolio Size Affects Early-Stage Venture Returns*：<https://angel.co/pdf/lp-performance.pdf>

SEC 文件中的原文：

> "The returns draw from a probability distribution p(x) ∝ x^(−α)… Using the log-likelihood maximization technique from the work of Clauset et al. (2009), we derived a fit of **α = 2.42** based on AngelList data."

研究报告进一步论证：seed 阶段投资在 5 年后其回报倍数分布趋向 **α < 2 的幂律，即期望值无界（unbounded mean）**。

> "our results suggest that after five years a winning seed-stage investment begins to draw its return multiple distribution from an α < 2 (i.e., unbounded mean) power law."

**这一条对本项目至关重要**：若回报分布确实是 α < 2 的幂律，则**样本均值不收敛**——"期望回报倍数"这个数字在数学上没有稳定含义，样本量越大均值越高。这直接否定了在 BP 中写"预期回报 X 倍"的做法。同时也要诚实指出：这一结论存在学术争议，有分析指出这些经验分布更接近对数正态或混合分布，未必严格服从单参数幂律（见 <https://www.openalmanac.org/w/venture-capital/power-law> 中"the precise mathematical form is contested"一段）。

#### （4）天使投资（更接近个人投资者的参照系）

出处：Wiltbank, R., & Boeker, W. (2007). *Returns to Angel Investors in Groups*（Kauffman Foundation / ACEF 资助）
SSRN: <https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1028592>
全文 PDF: <http://www.angelcapitalassociation.org/data/Documents/Resources/AngelGroupResarch/1d%20-%20Resources%20-%20Research/6%20RSCH_-_ACEF_-_Returns_to_Angel_Investor_in_Groups.pdf>

样本：539 名天使投资人、3,097 笔投资、1,137 次退出。原文关键结论：

> - "The average return of angel investments in this study is **2.6 times the investment in 3.5 years**—approximately 27 percent Internal Rate of Return (IRR)."
> - "**Fifty-two percent** of all of the exits returned less than the capital the angel had invested."
> - "**Seven percent** of the exits achieved returns of more than ten times the money invested, **accounting for 75 percent of the total investment dollar returns**."

**IRR 数字的勘误（必须一并披露）**：`2.6^(1/3.5) − 1 = 31.4%`（本手册计算，见 `risk_methodology_output.txt` 第 [8] 节），而非原报告写的 27%。Right Side Capital 的分析指出：按平均值口径的正确算法应为 31%，而按逐笔现金流的正确口径计算，该数据集的 IRR 为 **30%**。
出处：<https://rightsidecapital.com/assets/documents/HistoricalAngelReturn.pdf>

#### （5）基础存活率（非 VC 口径的下界参照）

美国劳工统计局 Business Employment Dynamics，Table 7 *Survival of private sector establishments by opening year*：<https://www.bls.gov/bdm/bdmage.htm>

该表为一手数据源。广为引用的派生结论是"约 20% 的新建机构在第 1 年内退出、约 50% 在第 5 年内退出"。**本手册未直接从 BLS 原表中读取具体百分比，故将该派生结论标注为"二手转引，使用前应自行下载 Table 7 核对当期数值"。**

---

## 3. 风险调整收益指标

### 3.1 夏普比率（Sharpe Ratio）

#### 出处

- 原始（1966）：Sharpe, W. F. *Mutual Fund Performance*. **Journal of Business**, 39(1, Part 2), 119–138. DOI [10.1086/294846](https://doi.org/10.1086/294846)（原文称之为 "reward-to-variability ratio"）
- 修订与规范化（1994）：Sharpe, W. F. *The Sharpe Ratio*. **Journal of Portfolio Management**, 21(1), 49–58. DOI [10.3905/jpm.1994.409501](https://doi.org/10.3905/jpm.1994.409501)
- **作者本人提供的全文**：<http://web.stanford.edu/~wfsharpe/art/sr/sr.htm>

#### 公式与变量定义

```text
事前（ex ante）：
    S = E[R − R_b] / σ(R − R_b)

事后（ex post）：
    Sh = mean(d_t) / sd(d_t),   d_t = R_t − R_b,t

R    组合收益率
R_b  基准收益率（常取无风险利率 R_f；Sharpe 1994 强调基准应随时间变化而调整）
σ    差额收益率的标准差
```

Sharpe 1994 原文的重要限定（直接引用）：

> "The Sharpe Ratio is designed to measure the expected return per unit of risk for a **zero investment strategy**. The difference between the returns on two investment assets represents the results of such a strategy. **The Sharpe Ratio does not cover cases in which only one investment return is involved.**"

#### 在极度右偏、非正态的创业回报上为何失效

1. **只用前两阶矩**。夏普比率把"上行波动"与"下行波动"等同惩罚。创业回报的价值几乎全部来自右尾，而右尾在分母里被当作风险扣掉。
2. **可被非线性payoff系统性操纵**。
   > Goetzmann, W., Ingersoll, J., Spiegel, M., & Welch, I. (2007). *Portfolio Performance Manipulation and Manipulation-proof Performance Measures*. **Review of Financial Studies**, 20(5), 1503–1546. DOI [10.1093/rfs/hhm025](https://doi.org/10.1093/rfs/hhm025)
   > 工作论文全文：<https://repec.som.yale.edu/icfpub/publications/2471.pdf> ／ NBER w9116：<https://www.nber.org/system/files/working_papers/w9116/w9116.pdf>

   原文结论："the best static manipulated strategy has a **truncated right tail and a fat left tail**"——即卖出价外期权式的收益结构可以人为拉高夏普比率。**创业项目的收益结构恰好相反（截断左尾、肥右尾），因此其夏普比率会被系统性低估。**
3. **估计误差与序列相关**。
   > Lo, A. W. (2002). *The Statistics of Sharpe Ratios*. **Financial Analysts Journal**, 58(4), 36–52. DOI [10.2469/faj.v58.n4.2453](https://doi.org/10.2469/faj.v58.n4.2453)

   Lo 证明：`√12` 年化法只在特殊情形下成立；序列相关可使年化夏普比率被高估达 **65%**。（另注：Wolf 的评论指出 Lo 的 IID 情形推导还依赖正态假设，肥尾下置信区间会偏窄，见 <https://quantresearch.org/Wolf_Lo_2002.pdf>。）
4. **对本项目的致命问题：没有时间序列**。单个未上市项目没有可观测的周期性收益率序列，`σ` 无法被估计，只能由假设的情景分布倒推。此时夏普比率不是"测量结果"，而是"假设的再表述"。

#### 本项目的实测（`risk_methodology_output.txt` 第 [7] 节，情景 B，3 年退出）

| 指标 | 数值 |
|---|---|
| 各档年化收益率 | −100%, 0%, +58.74%, +192.40% |
| E[年化] | **−41.57%** |
| sd(年化) | 81.49% |
| Sharpe（r_f = 中国 10Y 1.73%） | **−0.53** |
| Sharpe（r_f = 美国 10Y 4.71%） | −0.57 |
| Sortino（MAR = 1.73%） | −0.55 |
| Omega（阈值 1.73%） | 0.29 |

**这些数字全部为负 / 小于 1，而同一情景下 `E[M] = 2.05`（期望倍数超过 2 倍）。** 这不是矛盾，而是 Jensen 不等式（见 §3.3）：一个 60% 概率归零的赌局，其"各档年化收益率的期望"必然是大负数。**结论：夏普/索提诺/Omega 在本项目上不具备解释力，本手册建议在 BP 中不使用这三个指标，或仅作为"为何不使用"的说明性材料出现。**

### 3.2 索提诺比率（Sortino）与 Omega 比率

#### Sortino

> Sortino, F. A., & Price, L. N. (1994). *Performance Measurement in a Downside Risk Framework*. **The Journal of Investing**, 3(3), 59–64. DOI [10.3905/joi.3.3.59](https://doi.org/10.3905/joi.3.3.59)
> CFA Institute 的规范说明（Deborah Kidd, 2012）：<https://rpc.cfainstitute.org/sites/default/files/-/media/documents/code/gips/the-sortino-ratio.pdf>

```text
Sortino = (R_p − MAR) / DD

DD  下行偏差（downside deviation）:
    DD = sqrt( E[ min(R − MAR, 0)² ] )

MAR 最低可接受收益率（Minimum Acceptable Return），需显式声明取值
```

**已知局限**：CFA Institute 的说明明确警告——"caution [is warranted] in applying the Sortino ratio to strategies with **known asymmetric return distributions**"。创业回报正是已知的极度非对称分布。此外 MAR 的选择是主观的，不同 MAR 会改变排序结论。

#### Omega

> Keating, C., & Shadwick, W. F. (2002). *A Universal Performance Measure*. **The Journal of Performance Measurement**, 6(3).
> 全文 PDF: <http://www.performance-measurement.org/KeatingShadwick2002a.pdf>
> 配套导读 *An Introduction to Omega*: <http://www.performance-measurement.org/KeatingShadwick2002.pdf>

```text
        ∫_r^b [1 − F(x)] dx
Ω(r) = ──────────────────────
        ∫_a^r F(x) dx

F    收益率的累积分布函数
r    阈值收益率（threshold）
[a,b] 收益率的取值区间
直观：阈值以上的概率加权收益 / 阈值以下的概率加权损失
```

**优点**：使用完整分布，捕捉所有高阶矩，无需正态假设——在原理上比夏普更适合重尾分布。
**已知局限**：（i）对椭圆分布族，Omega 最优组合与夏普最优组合重合，此时并无增量信息（<https://arxiv.org/pdf/1911.10254>）；（ii）Ω 是阈值 `r` 的函数，报告单一数值等于隐藏了选择 `r` 的自由度；（iii）在本项目中，`F` 本身是由 4 个主观概率点构成的，Omega 的"使用完整分布"优势无从发挥。

### 3.3 几何期望 vs 算术期望：波动率拖累

#### 公式

```text
精确关系（对数正态）：
    设 1 + R 服从对数正态，E[R] = μ，sd(R) = σ，则
    g ≡ E[ln(1+R)] = ln(1+μ) − ½·ln(1 + σ²/(1+μ)²)

常用近似（小收益、低波动）：
    g ≈ μ − σ²/2

CAGR（复合年增长率，事后口径）：
    CAGR = (W_T / W_0)^(1/T) − 1
```

#### 出处与适用条件

- 几何布朗运动下 `d ln S = (μ − σ²/2)dt + σ dB` 由伊藤引理直接得出，是标准随机分析结果（教科书级；推导示例：<http://leonardorocchi.info/topics-pages/qfin/log-normal-stock-prices/log-normal-stock-price.html>）。
- 离散样本下的二阶泰勒展开推导（不需要任何分布假设）：<https://quant.stackexchange.com/questions/49008/mathematical-proof-of-g-mu-frac-sigma22-relationship-between-cagr-a>
- "波动率税 / volatility tax"术语与形式化：<https://en.wikipedia.org/wiki/Volatility_Tax>（该词条明确指出："**Though this formula is under the assumption of log-normality**… The precise formula is a function of the central moments of the return distribution."）
- 实证校核示例（S&P 500：算术 8.75%、σ 18.86% ⇒ 近似几何 6.97%，实际 6.94%）：<https://www.kitces.com/blog/volatility-drag-variance-drain-mean-arithmetic-vs-geometric-average-investment-returns/>

#### 已知局限：近似式在高波动下彻底失效

本手册数值校验（`risk_methodology_output.txt` 第 [5] 节，蒙特卡洛 n = 1,000,000）：

| μ | σ | 精确 g | 近似 μ−σ²/2 | 蒙特卡洛 g | 近似式误差 |
|---|---|---|---|---|---|
| 0.10 | 0.20 | 0.079049 | 0.080000 | 0.079112 | +0.001 |
| 0.30 | 0.60 | 0.165809 | 0.120000 | 0.165963 | −0.046 |
| 0.50 | 1.20 | **0.158117** | **−0.220000** | 0.158365 | **−0.378（符号都错了）** |

**结论：创业项目的 σ 远大于 1，`μ − σ²/2` 在此完全不可用。** BP 中若要给出几何口径的增长率，必须用精确式或直接蒙特卡洛，并注明所用方法。

#### Jensen 不等式：三种"年化收益率"互不相等（`risk_methodology_output.txt` 第 [7b] 节）

同一情景 B（3 年退出）下：

| 口径 | 公式 | 数值 |
|---|---|---|
| (a) 期望倍数先算再年化 | `E[M]^(1/T) − 1` | **+27.03%** |
| (b) 各档先年化再取期望 | `E[M^(1/T) − 1]` | **−41.57%** |
| (c) 条件于未全损的几何均值 | `exp(E[ln M ｜ M>0])^(1/T) − 1` | **+35.99%**（存活概率 40%） |

**同一个分布，三个"年化收益率"，从 −41.57% 到 +35.99%。** 商业计划书中出现"年化 XX%"时，若不写明是哪一种口径，该数字不具备可验证性。其中 (a) 最容易被误读为"预期收益"，(c) 则隐藏了 60% 的归零概率——**这两个都是本项目在披露时必须主动避免的表述方式**。

### 3.4 无风险利率的当前取值（截至 2026 年年中）

| 基准 | 数值 | 日期 | 官方来源 |
|---|---|---|---|
| 美国 10 年期国债（Constant Maturity） | **4.71%** | 2026-07-23 | FRED 系列 **DGS10**，源数据 Board of Governors of the Federal Reserve System, H.15 Selected Interest Rates。<https://fred.stlouisfed.org/series/DGS10>（该页显示 Updated: Jul 24, 2026） |
| 中国 10 年期国债 | **1.73%** | 2026-07-24 | 中债国债收益率曲线（中央国债登记结算有限责任公司编制），财政部官方展示页：<https://yield.chinabond.com.cn/cbweb-czb-web/czb/moreInfo?locale=cn_ZH&nameType=1> |

FRED DGS10 近 5 个交易日：2026-07-17 = 4.55、07-20 = 4.60、07-21 = 4.63、07-22 = 4.67、07-23 = 4.71（呈上行）。
中债曲线同日其他关键期限：3M 1.10、1Y 1.14、5Y 1.44、30Y 2.19。

**FRED 建议引用格式**（照抄该页 Suggested Citation）：
> Board of Governors of the Federal Reserve System (US), Market Yield on U.S. Treasury Securities at 10-Year Constant Maturity, Quoted on an Investment Basis [DGS10], retrieved from FRED, Federal Reserve Bank of St. Louis; https://fred.stlouisfed.org/series/DGS10

**使用注意**：
1. 二者币种不同，**不可混用**。若项目现金流以人民币计价，基准应为中债 1.73%；若以美元计价则为 4.71%。混用会凭空制造 ~3 个百分点的"超额收益"。
2. 国债收益率**每日变动**。BP 中引用必须写明取数日期，并说明"截至编制日"。
3. 期限应与项目期限匹配。若项目规划期为 3 年，用 3 年期（中债 1.28%）比用 10 年期更恰当。

### 3.5 早期创业 / 天使投资的要求回报率（hurdle rate）

#### （1）VC Method 的目标折现率：30%–70%

> Sahlman, W. A., & Scherlis, D. R. (1987, rev. 2009). *A Method For Valuing High-Risk, Long-Term Investments: The "Venture Capital Method"*. **Harvard Business School Background Note 288-006**.
> <https://www.hbs.edu/faculty/Pages/item.aspx?num=6515>

HBS 摘要原文："forecasting a future value (e.g., five years from the present) and discounting that terminal value back to the present by applying a **high discount rate (e.g., 50%)**"。

学术综述中对该区间的记载："Scherlis & Sahlman (1989) note that venture capitalists use high discount rates—**from 40 to over 60 percent**"（<https://digitalcommons.pepperdine.edu/cgi/viewcontent.cgi?article=1186&context=jef>）。

**必须同时披露的关键限定**：这个 30–70% **不是投资人的预期收益率**。它同时补偿了四件事：（i）货币时间价值；（ii）风险；（iii）**只用"成功情景"做预测所隐含的乐观偏差**；（iv）后续轮次的稀释。把它当作"预期回报"引用是常见误用。

#### （2）天使投资的已实现回报：约 2.6×/3.5 年，IRR ≈ 30%

Wiltbank & Boeker (2007)，见 §2.2（4）。注意 IRR 数字的勘误：原报告 27%，正确值 30–31%。

倍数与 IRR 的换算（`risk_methodology_output.txt` 第 [8] 节，本手册计算）：

| 目标 IRR | 3 年 | 5 年 | 7 年 |
|---|---|---|---|
| 20% | 1.73× | 2.49× | 3.58× |
| 30% | 2.20× | 3.71× | 6.27× |
| 40% | 2.74× | 5.38× | 10.54× |
| 50% | 3.38× | 7.59× | 17.09× |
| 60% | 4.10× | 10.49× | 26.84× |
| 70% | 4.91× | 14.20× | 41.03× |

#### （3）作为对照的行业实际净回报（防止 hurdle rate 被误读为可实现回报）

> Cambridge Associates LLC, **US Venture Capital Index®**，2025 Q4 Benchmark Book（基于 1981–2025 年成立的 2,816 只美国 VC 基金，pooled horizon return，**已扣除费用、开支与 carried interest，净给 LP**）
> <https://www.cambridgeassociates.com/wp-content/uploads/2026/06/2025-Q4-USVC-Benchmark-Book.pdf>

| 期限 | 1 年 | 3 年 | 5 年 | 10 年 | 15 年 | 20 年 | 25 年 |
|---|---|---|---|---|---|---|---|
| CA US VC Index（净） | 21.14% | 8.74% | 10.24% | 14.86% | 15.53% | 12.85% | **8.10%** |

**这组数字与 30–70% 的 hurdle rate 之间的巨大落差，是 BP 中必须诚实呈现的事实**：hurdle rate 是施加在"单一成功情景"上的折现率，而 8–15% 才是整个行业分散化之后、扣费之后、长周期的实际净回报。**单一项目的合理要求回报率应显著高于 15%，但不能因此宣称"预期回报 = 50%"。**

---

## 4. 蒙特卡洛模拟在创业财务预测中的规范做法

### 4.1 为什么必须做（Flaw of Averages）

> Savage, S. L. (2009/2012). *The Flaw of Averages: Why We Underestimate Risk in the Face of Uncertainty*. Wiley. ISBN 978-1-118-37358-3
> 出版社页：<https://www.wiley.com/en-us/The+Flaw+of+Averages%3A+Why+We+Underestimate+Risk+in+the+Face+of+Uncertainty-p-9781118373583>
> Savage & Van Allen 的方法论章节（含 Jensen 不等式的正式表述）：<https://www.jenner.com/a/web/mw6mse15uBFYG3Xr2krRr4/4HRMZQ/Chapter_2010.pdf>

数学基础是 **Jensen 不等式**：

```text
若 F 为凸函数：  F(E[X]) ≤ E[F(X)]
若 F 为凹函数：  F(E[X]) ≥ E[F(X)]

⇒ 「把平均值代入模型」得到的结果 ≠ 「模型输出的平均值」
```

本手册算例的直接体现（`risk_methodology_output.txt` 第 [6] 节）：年毛利润的**均值 379,484 ≠ 中位数（P50）326,225**，相差 16%。若在电子表格中用"最可能值"填入每个格子，得到的是 P50 附近的某个点，而**不是**期望值。

### 4.2 变量分布的选择

| 变量类型 | 推荐分布 | 理由与出处 |
|---|---|---|
| 由三点专家估计给出（乐观/最可能/悲观），且希望权重集中于最可能值 | **PERT（Beta-PERT）** | 均值 `(a + 4m + b)/6`，标准差约为极差的 1/6，形状连续平滑。Vose, D. (2008). *Risk Analysis: A Quantitative Guide*, 3rd ed., Wiley。参数化说明：<https://search.r-project.org/CRAN/refmans/prevalence/html/betaPERT.html> |
| 三点估计，但不愿对"最可能值"赋予额外权重；或数据极少 | **三角分布 / 双三角分布** | AACE International RP 41R-08 原版建议："a reasonable approximation is to use one of two distributions: the triangular distribution, the double triangular distribution"。原文 PDF：<https://www.wsdot.wa.gov/publications/fulltext/cevp/RangeEstimating.pdf> |
| 本质为**乘性**、非负、右偏的量（销售额、用户数、单位成本、项目工期） | **对数正态** | 乘性过程的自然极限分布（中心极限定理作用于对数）；SPE PRMS 即将可采储量建模为对数正态 |
| 二值事件（是否通过合规审查、是否拿到某客户） | **伯努利**，与后续量相乘 | 离散风险事件应与连续不确定性分开建模（AACE PGD-02 对 "uncertainties versus risk events" 的区分） |

**关键警告（AACE 原文）**："A common error is to assign the triangular distribution **without verifying that it actually applies**. As with any PDF, the range implies a probability in a triangular distribution."——三角分布的左右两块面积隐含地规定了"低于/高于最可能值"的概率，这个隐含概率往往与估计者的真实信念不符。

**PERT 参数化**：

```text
mean  = (a + λ·m + b) / (λ + 2)          λ = 4 时即 (a + 4m + b)/6
α     = 1 + λ·(m − a)/(b − a)
β     = 1 + λ·(b − m)/(b − a)
X     = a + (b − a)·Beta(α, β)

a 最小值(悲观)、m 众数(最可能)、b 最大值(乐观)
```

（`(a+4m+b)/6` 这一均值假设最早见于 Clark, C. E. (1962), *The PERT model for the distribution of an activity time*, **Operations Research** 10(3), 405–406——**本手册未直接查阅该原文，系转引自 PERT distribution 的公开条目，引用时应标注为二手来源。**）

### 4.3 相关性处理

**不做相关性处理是蒙特卡洛最常见的严重错误**：独立采样会系统性低估极端情景的概率（例如"用户数低"和"成本高"在现实中往往同时发生）。

标准方法：

> Iman, R. L., & Conover, W. J. (1982). *A distribution-free approach to inducing rank correlation among input variables*. **Communications in Statistics — Simulation and Computation**, 11(3), 311–334. DOI [10.1080/03610918208812265](https://doi.org/10.1080/03610918208812265)

方法特点（原文摘要）："This method is simple to use, is **distribution free**, **preserves the exact form of the marginal distributions** on the input variables"。它通过对各列样本**重排序**来诱导目标秩相关，不改变任何变量的边际分布。该算法是 @RISK、Crystal Ball 等商业软件的标准实现。

本手册的实现与验证（`risk_methodology_output.txt` 第 [6] 节，n = 100,000）：

```text
目标相关矩阵            施加 Iman-Conover 后的实测相关矩阵
[ 1.00 -0.35  0.00  0.45]   [ 1.0000 -0.3372 -0.0001  0.4395]
[-0.35  1.00  0.20  0.00]   [-0.3372  1.0000  0.1969  0.0005]
[ 0.00  0.20  1.00 -0.15]   [-0.0001  0.1969  1.0000 -0.1483]
[ 0.45  0.00 -0.15  1.00]   [ 0.4395  0.0005 -0.1483  1.0000]
```

（最大偏差 0.013，属该方法的正常偏差范围；Iman–Conover 诱导的是秩相关，Pearson 相关会略有偏离。）

### 4.4 迭代次数

AACE RP 41R-08（原版）的建议：

> "Typically, between **300 and 800 iterations** are necessary in order to obtain statistically significant results using these software packages. It is recommended that **1000 iterations** be used as this will, with rare exceptions, be a large enough sample for reliable results."

**本手册的立场：1,000 次对现代硬件而言毫无必要地少，且对重尾分布不够。** 应以**收敛性检验**代替固定次数——重复运行 N 次，观察目标统计量（尤其是 P90 和均值）的跨次标准差是否降到可接受水平。

本手册实测（`risk_methodology_output.txt` 第 [6b] 节，每档重复 30 次独立运行，报告 P50 的跨次标准差）：

| 迭代次数 | P50 均值 | 跨次标准差 | 相对波动 |
|---|---|---|---|
| 1,000 | 331,397 | 13,108 | 3.96% |
| 5,000 | 331,138 | 4,744 | 1.43% |
| 10,000 | 331,687 | 4,029 | 1.21% |
| 50,000 | 330,534 | 1,999 | 0.60% |
| 100,000 | 330,786 | 1,556 | 0.47% |

**建议：本项目采用 ≥ 50,000 次迭代，并固定随机种子以保证可复现。** 注意 P90/P99 的收敛比 P50 慢得多，若要报告尾部分位数需进一步增加迭代次数。

### 4.5 结果的报告方式：P10 / P50 / P90

最规范、最有强制力的定义来自石油行业储量披露标准：

> **SPE Petroleum Resources Management System (PRMS)**, §2.2.1.2
> <https://www.spe.org/media/filer_public/0c/83/0c835db9-501f-4ce7-97f1-a1d6bb4e3331/prmgmtsystem_v103.pdf>

原文（**超越概率**口径，务必注意方向）：

> A. There should be at least a **90% probability (P90)** that the quantities actually recovered will **equal or exceed the low estimate**.
> B. There should be at least a **50% probability (P50)** … equal or exceed the best estimate.
> C. There should be at least a **10% probability (P10)** … equal or exceed the high estimate.

**即 P10 = 高情景、P90 = 低情景**（与统计学中"第 10 百分位 = 低值"的习惯**相反**）。BP 中必须写明采用的是哪一种约定，否则会造成方向性误读。本手册在算例中采用统计学百分位约定（P10 = 第 10 百分位 = 低值）并已在表格中注明。

**报告要求（本手册规定）**：
1. 同时给出 P10 / P50 / P90 **和均值**，并明确指出均值 ≠ P50；
2. 给出 **P(亏损)** 或 P(现金流断裂) 这类"是否出局"的概率，而不只是分位数；
3. 给出**敏感性分析**（哪个输入变量对输出方差贡献最大）；
4. 附上模型代码与随机种子。

本手册算例的完整报告格式（情景为占位假设）：

| 指标 | 年毛利润 |
|---|---|
| P10（第 10 百分位，低情景） | 96,677 |
| P50（中位数） | 326,225 |
| P90（第 90 百分位，高情景） | 735,575 |
| 均值 | 379,484 |
| P(亏损) | 0.84% |

---

## 5. 实物期权与分阶段投资（stage-gating）

### 5.1 理论基础

> Dixit, A. K., & Pindyck, R. S. (1994). *Investment under Uncertainty*. Princeton University Press. ISBN 0-691-03410-9
> 出版社页：<https://press.princeton.edu/books/hardcover/9780691034102/investment-under-uncertainty>
> 导论章节 PDF：<https://msuweb.montclair.edu/~lebelp/DixitPindyck1994.pdf>

核心论点（导论原文）：绝大多数投资决策同时具备三个特征——**(i) 不可逆（沉没成本）、(ii) 未来回报不确定、(iii) 在时点上有一定的自由度**。传统 NPV 法隐含假设"要么可逆、要么 now-or-never"，因而**系统性低估了等待的价值**。企业进行不可逆投资时等于"行权"，放弃了等待新信息的期权。

```text
决策规则的修正：
    传统：NPV > 0 即投资
    实物期权：NPV > 期权价值(等待的价值) 才投资
    ⇒ 投资门槛被抬高，且不确定性越大，门槛越高
```

### 5.2 VC 为何普遍采用分阶段注资：实证证据

> Gompers, P. A. (1995). *Optimal Investment, Monitoring, and the Staging of Venture Capital*. **The Journal of Finance**, 50(5), 1461–1489. DOI [10.1111/j.1540-6261.1995.tb05185.x](https://doi.org/10.1111/j.1540-6261.1995.tb05185.x)

样本：794 家 VC 支持的公司（随机抽样）。原文摘要关键句：

> "Venture capitalists periodically gather information and **maintain the option to discontinue funding projects with little probability of going public**."
> "Expected agency costs increase as assets become less tangible, growth options increase, and asset specificity rises."
> "Decreases in industry ratios of tangible assets to total assets, higher market-to-book ratios, and greater R&D intensities lead to **more frequent monitoring**."

**对本项目的直接映射**：纯软件 SaaS 项目 = 无形资产占比极高 + 成长期权占比极高 + 资产专用性高，正是 Gompers 模型中**监控频率应当最高、单轮注资额应当最小**的那一类。

### 5.3 创业情境下的实物期权推理

> McGrath, R. G. (1999). *Falling Forward: Real Options Reasoning and Entrepreneurial Failure*. **Academy of Management Review**, 24(1), 13–30. DOI [10.5465/amr.1999.1580438](https://doi.org/10.5465/amr.1999.1580438)

原文摘要核心："emphasizes managing uncertainty by **pursuing high-variance outcomes but investing only if conditions are favorable**. This can increase profit potential **while containing costs**."

### 5.4 为什么这能降低"有效风险敞口"（形式化）

```text
一次投满：
    最大损失 = I（全部投入）
    结果分布 = 原始分布

分 K 阶段，每阶段投入 I_k，阶段 k 通过门槛的概率为 s_k：
    期望总投入 = I_1 + s_1·I_2 + s_1·s_2·I_3 + … 
               = Σ_k [ I_k · Π_{j<k} s_j ]

由于 s_j < 1，期望总投入 < Σ I_k = I

同时上行不受损：只有在通过所有门槛（即项目确实有效）时才付出全部 I，
而此时正是回报分布最好的那一支。
⇒ 分阶段 = 截断左尾、保留右尾 = 买入了一个"放弃期权"（abandonment option）
```

**数值示意**（占位假设，非本项目实际数据）：总预算 60 万元分 3 阶段（20/20/20 万），若各阶段通过率为 60%、50%，则期望总投入 = 20 + 0.6×20 + 0.6×0.5×20 = **38 万元**，比一次投满少 37%，而"项目真正跑通"情形下的投入不变。

**已知局限（必须诚实说明）**：
1. 分阶段有**代价**：可能错失时间窗口、单位成本更高、每次门槛评审本身消耗资源。Dixit–Pindyck 框架中这体现为"等待期间竞争者先行"的机会成本。
2. 期权价值的**定价**需要标的资产的波动率与无套利环境，而未上市项目**不存在可交易的标的**，因此 Black–Scholes 式的实物期权定价在本项目中只能作为**定性论证**，其数值结果不可信。本手册**不建议**在 BP 中给出实物期权的具体估值数字。
3. 分阶段要求**门槛（gate）事先可客观检验**。若门槛标准可以事后调整，期权价值就被创业者自己的乐观偏差消解了。**门槛必须在投入之前以书面、可量化、可自动检验的形式写死。**

---

## 6. ★ 在本项目中如何正确、诚实地使用这些工具

**本项目的客观特征**：单人执行；纯自有资金；单次投入、不可重复；股权不可流动；无历史频率数据可用于估计概率；失败即全损且无法通过组合分散。

### 6.1 逐项裁定：每个工具能用到什么程度

| 工具 | 在本项目中的地位 | 允许的用途 | 禁止的用途 |
|---|---|---|---|
| **Kelly f\*** | 参考，非结论 | ①给出"单笔投入占净资产比例"的**数量级上界**；②通过 `f* = 0` 的输出暴露"我的概率估计其实不支持创业"这一内在矛盾 | ❌ 不得作为出资额的决定依据；❌ 不得声称"按 Kelly 最优配置"；❌ 不得报告到小数点后两位 |
| **Fractional Kelly** | 参考，方向性有效 | 论证"应当按 1/4–1/2 打折"这一**定性方向** | ❌ 不得引用"半 Kelly 保留 75% 增长率"作为本项目的结论（该结论仅对连续/对数正态成立，本项目实测为 82.3%） |
| **胜率 / 盈亏比 / Profit Factor** | 参考 | 作为**内部一致性检查**：若声称的胜率与盈亏比隐含的期望值不成立，说明假设自相矛盾 | ❌ 不得作为业绩承诺；❌ 在 α<2 幂律下不得引用"平均盈利"这一统计量 |
| **VC / 天使的结果分布** | **可引用的外部事实** | 作为设定档位概率时的**参照系与上界**（机构筛选后的样本，成功率高于未筛选样本） | ❌ 不得直接把 Correlation/Horsley Bridge 的百分比当作本项目的概率；❌ 不得省略"这是机构融资项目"的口径说明 |
| **夏普比率** | **不建议使用** | 仅可作为"为何本项目不适用夏普比率"的说明材料 | ❌ 不得报告夏普比率数值。本项目实测为 **−0.53**，同时 E[M] = 2.05——这个组合只会误导读者 |
| **索提诺 / Omega** | 弱参考 | 同上；Omega 在原理上更适合重尾，但输入是 4 个主观概率点，无实质增量信息 | ❌ 不得单独报告某一个阈值下的 Ω 值 |
| **几何期望 / CAGR** | **必须使用** | 所有"年化"表述都必须写明口径，并同时给出 (a)(b)(c) 三种口径的差异（见 §3.3） | ❌ 不得使用 `μ − σ²/2` 近似（本项目 σ ≫ 1，该式符号都会算错）；❌ 不得只报告条件于成功的几何均值 |
| **无风险利率** | **必须使用** | 作为机会成本基准；币种与期限须与项目匹配，并注明取数日期 | ❌ 不得混用中美利率制造虚假超额收益 |
| **Hurdle rate 30–70%** | 参考，且必须加注 | 作为"该行业对单一成功情景所要求的折现率"的行业惯例引用 | ❌ 不得表述为"预期回报率"。必须同时给出 CA US VC Index 的净回报（25 年期 8.10%）作为对照 |
| **蒙特卡洛** | **核心工具，必须使用** | 输出完整分布：P10/P50/P90 + 均值 + P(出局) + 敏感性分析 + 代码 + 种子 | ❌ 不得只报告 P50 或均值；❌ 不得省略输入分布的选择理由与相关性设定 |
| **分阶段投入 / 实物期权** | **核心决策框架，必须使用** | 定性论证 + 期望总投入的算术计算（见 §5.4） | ❌ 不得给出实物期权的定价数值（无可交易标的，波动率不可观测） |

### 6.2 必须写进 BP 的披露段落（建议文本）

以下文字建议以"风险量化方法的局限性说明"为标题，**紧邻**任何量化结论出现，而非放在文末附录：

> **关于本报告中量化结果的性质与局限**
>
> 一、本报告所有概率取值均为编制者的**主观估计**，不是观测频率。本项目为单人、自有资金、单次不可重复的投入，不存在可供统计的历史样本。任何以这些概率为输入的计算结果，其可靠性上限由这些主观估计决定，与计算过程的精度无关。报告中数字的小数位数**不代表精度**。
>
> 二、本报告引用的 Kelly 准则（Kelly 1956; Breiman 1961）在数学上要求赌局**可无限重复、结果独立同分布、资本可连续分割并可即时再投资**。本项目**同时违反上述全部前提**。Samuelson (1971, 1979) 已正式论证：几何均值最大化在任何有限期数下都不是最优的，且它隐含地假定投资者具有对数效用。本报告使用 Kelly 仅为给出仓位量级的参考上界，**不构成任何形式的最优性主张**。
>
> 三、本报告引用的 Correlation Ventures、Horsley Bridge、AngelList、Wiltbank & Boeker 等结果分布数据，其总体为**已获得机构投资的公司**，与本项目所处的总体不同，且经过了机构的事前筛选。以其作为概率参照系会**系统性高估**本项目的成功概率。
>
> 四、AngelList 的研究（Othman）提示早期投资回报可能服从 α < 2 的幂律分布，此类分布的**期望值在数学上不收敛**（样本均值随样本量增大而增大）。因此本报告**不提供"预期回报倍数"作为投资承诺**，仅提供完整的结果分布及其分位数。
>
> 五、夏普比率等基于均值—方差的风险调整指标，在本项目的极度右偏、含全损档的分布上不具解释力（Goetzmann et al. 2007; Lo 2002）。本报告据此**不采用**这些指标。
>
> 六、本报告的蒙特卡洛模拟结果为**给定输入假设下的条件分布**，不是预测。全部模型代码、输入分布参数、相关性矩阵与随机种子均已随本报告提供，任何第三方可完整复现并替换假设。
>
> 七、本报告**不构成投资建议**。项目失败并损失全部投入是本分布中概率最高的单一结果。

### 6.3 应当采用的决策流程（可自动化，无人工依赖）

```text
第 0 步  写死"最大可承受损失" L_max（绝对金额，与净资产、生活储备、法定义务挂钩）
         规则：L_max ≤ min( 净资产 × f_Kelly × 0.5 ,  可承受归零而不影响基本生活的金额 )
         其中 f_Kelly 由 kelly_multi_outcome() 在自有概率估计下算出

第 1 步  把项目切成 K 个阶段，每阶段预算 I_k，且 Σ I_k ≤ L_max
         每个阶段设一个**事先写死、可由脚本自动检验**的门槛 G_k
         例：G_1 = "60 天内 ≥ N 个付费用户 且 月留存 ≥ X%"

第 2 步  每阶段结束时由脚本读取埋点数据自动判定 G_k 是否达成
         未达成 → 自动进入终止流程（不再追加投入）
         达成   → 用新数据更新各档概率的贝叶斯后验，重算 f_Kelly，重新校准 I_{k+1}

第 3 步  每次重算后重跑蒙特卡洛（≥50,000 次，固定种子），
         更新 P10/P50/P90、P(出局) 与敏感性排序，写入版本化的决策日志

第 4 步  终止条件（任一触发即停）：
         (a) 累计投入达到 L_max
         (b) 连续两个阶段门槛未达成
         (c) 重估后 E[X] ≤ 0 且 f_Kelly = 0
```

**这个流程的价值不在于它能提高成功率，而在于它把"什么时候停"这个最难的决定，在情绪介入之前就用可自动检验的规则固定下来。** 这正是 §5 中"放弃期权"的可执行形式，也是 Gompers (1995) 所描述的机构做法在单人项目上的映射。

### 6.4 一句话总结

在单人、自有资金、单次不可重复的创业情境下：
**这些工具唯一诚实的用途，是回答"我最多能输多少、以多大概率输掉、什么时候必须停"，而不是回答"我能赚多少"。**

---

## 7. 参考文献总表

### Kelly 准则与资本增长理论

1. Kelly, J. L., Jr. (1956). A New Interpretation of Information Rate. *Bell System Technical Journal*, 35(4), 917–926. [DOI](https://doi.org/10.1002/j.1538-7305.1956.tb03809.x) ｜ [全文](https://archive.org/details/bstj35-4-917)
2. Breiman, L. (1961). Optimal Gambling Systems for Favorable Games. *Proc. 4th Berkeley Symp.*, 1, 65–78. [全文](https://digitalassets.lib.berkeley.edu/math/ucb/text/math_s4_v1_article-05.pdf)
3. Samuelson, P. A. (1971). The "Fallacy" of Maximizing the Geometric Mean… *PNAS*, 68(10), 2493–2496. [DOI](https://doi.org/10.1073/pnas.68.10.2493) ｜ [全文](https://finance.martinsewell.com/money-management/Samuelson1971.pdf)
4. Samuelson, P. A. (1979). Why we should not make mean log of wealth big though years to act are long. *J. Banking & Finance*, 3(4), 305–307. [全文](http://stat.wharton.upenn.edu/~steele/Courses/434/434Context/Kelly%20Resources/Samuelson1979.pdf)
5. MacLean, L. C., Ziemba, W. T., & Blazenko, G. (1992). Growth Versus Security in Dynamic Investment Analysis. *Management Science*, 38(11), 1562–1585. [DOI](https://doi.org/10.1287/mnsc.38.11.1562)
6. Thorp, E. O. (2006). The Kelly Criterion in Blackjack, Sports Betting, and the Stock Market. *Handbook of Asset and Liability Management*, 1, 385–428. [DOI](https://doi.org/10.1016/S1872-0978(06)01009-X) ｜ [全文](https://gwern.net/doc/statistics/decision/2006-thorp.pdf)
7. MacLean, Thorp & Ziemba. Good and Bad Properties of the Kelly Criterion. [全文](https://www.stat.berkeley.edu/~aldous/157/Papers/Good_Bad_Kelly.pdf)
8. Chopra, V. K., & Ziemba, W. T. (1993). The Effect of Errors in Means, Variances, and Covariances on Optimal Portfolio Choice. *JPM*, 19(2), 6–11. [DOI](https://doi.org/10.3905/jpm.1993.409440) ｜ [全文](https://people.duke.edu/~charvey/Teaching/BA453_2006/Chopra_The_effect_of_1993.pdf)
9. Peters, O., & Gell-Mann, M. (2016). Evaluating gambles using dynamics. *Chaos*, 26(2), 023103. [DOI](https://doi.org/10.1063/1.4940236) ｜ [arXiv](https://arxiv.org/abs/1405.0585)
10. Peters, O. (2019). The ergodicity problem in economics. *Nature Physics*, 15, 1216–1221.（二手转引）

### 风险投资结果分布

11. Coats, D. / Correlation Ventures. Venture Capital — No, We're Not Normal. [链接](https://medium.com/correlation-ventures/venture-capital-no-were-not-normal-32a26edea7c7) ｜ [更新版](https://medium.com/correlation-ventures/venture-capital-were-still-not-normal-9d07d354db88)
12. Levine, S. (2014). Venture Outcomes are Even More Skewed Than You Think. [链接](https://sethlevine.com/archives/2014/08/venture-outcomes-are-even-more-skewed-than-you-think.html)
13. Dixon, C. / a16z (2015). Performance Data and the 'Babe Ruth' Effect in Venture Capital（Horsley Bridge 数据）. [链接](https://a16z.com/performance-data-and-the-babe-ruth-effect-in-venture-capital/)
14. Othman, A. / AngelList. Startup Growth and Venture Returns. [PDF](https://angel.co/pdf/growth.pdf) ｜ [SEC 提交件](https://www.sec.gov/comments/s7-08-19/s70819-7773213-223398.pdf) ｜ [组合规模研究](https://angel.co/pdf/lp-performance.pdf)
15. Wiltbank, R., & Boeker, W. (2007). Returns to Angel Investors in Groups. [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1028592) ｜ [PDF](http://www.angelcapitalassociation.org/data/Documents/Resources/AngelGroupResarch/1d%20-%20Resources%20-%20Research/6%20RSCH_-_ACEF_-_Returns_to_Angel_Investor_in_Groups.pdf) ｜ [IRR 勘误](https://rightsidecapital.com/assets/documents/HistoricalAngelReturn.pdf)
16. U.S. Bureau of Labor Statistics. Business Employment Dynamics, Table 7: Survival of private sector establishments by opening year. [链接](https://www.bls.gov/bdm/bdmage.htm)
17. Cambridge Associates LLC. US Venture Capital Index®, 2025 Q4 Benchmark Book. [PDF](https://www.cambridgeassociates.com/wp-content/uploads/2026/06/2025-Q4-USVC-Benchmark-Book.pdf)

### 风险调整收益指标

18. Sharpe, W. F. (1966). Mutual Fund Performance. *Journal of Business*, 39(1, Pt.2), 119–138. [DOI](https://doi.org/10.1086/294846)
19. Sharpe, W. F. (1994). The Sharpe Ratio. *JPM*, 21(1), 49–58. [DOI](https://doi.org/10.3905/jpm.1994.409501) ｜ [作者全文](http://web.stanford.edu/~wfsharpe/art/sr/sr.htm)
20. Lo, A. W. (2002). The Statistics of Sharpe Ratios. *FAJ*, 58(4), 36–52. [DOI](https://doi.org/10.2469/faj.v58.n4.2453) ｜ [Wolf 的评论](https://quantresearch.org/Wolf_Lo_2002.pdf)
21. Goetzmann, W., Ingersoll, J., Spiegel, M., & Welch, I. (2007). Portfolio Performance Manipulation and Manipulation-proof Performance Measures. *RFS*, 20(5), 1503–1546. [DOI](https://doi.org/10.1093/rfs/hhm025) ｜ [工作论文](https://repec.som.yale.edu/icfpub/publications/2471.pdf)
22. Sortino, F. A., & Price, L. N. (1994). Performance Measurement in a Downside Risk Framework. *J. Investing*, 3(3), 59–64. [DOI](https://doi.org/10.3905/joi.3.3.59) ｜ [CFA Institute 说明](https://rpc.cfainstitute.org/sites/default/files/-/media/documents/code/gips/the-sortino-ratio.pdf)
23. Keating, C., & Shadwick, W. F. (2002). A Universal Performance Measure. *J. Performance Measurement*, 6(3). [PDF](http://www.performance-measurement.org/KeatingShadwick2002a.pdf)

### 无风险利率数据源

24. Board of Governors of the Federal Reserve System (US) / FRED. DGS10. [链接](https://fred.stlouisfed.org/series/DGS10)
25. 中央国债登记结算有限责任公司 / 中华人民共和国财政部. 中国国债收益率曲线. [链接](https://yield.chinabond.com.cn/cbweb-czb-web/czb/moreInfo?locale=cn_ZH&nameType=1) ｜ [中债收益率主页](https://yield.chinabond.com.cn/cbweb-pbc-web/)

### 蒙特卡洛与不确定性建模

26. Savage, S. L. (2009/2012). *The Flaw of Averages*. Wiley. [出版社](https://www.wiley.com/en-us/The+Flaw+of+Averages%3A+Why+We+Underestimate+Risk+in+the+Face+of+Uncertainty-p-9781118373583) ｜ [方法论章节](https://www.jenner.com/a/web/mw6mse15uBFYG3Xr2krRr4/4HRMZQ/Chapter_2010.pdf)
27. AACE International. RP 41R-08, *Risk Analysis and Contingency Determination Using Range Estimating*（原版）. [PDF](https://www.wsdot.wa.gov/publications/fulltext/cevp/RangeEstimating.pdf) ｜ [2021 修订说明](https://web.aacei.org/docs/default-source/toc/toc_41r-08.pdf) ｜ [PGD-02 定量风险分析指南](https://library.aacei.org//pgd02/pgd02.shtml)
28. Vose, D. (2008). *Risk Analysis: A Quantitative Guide*, 3rd ed. Wiley.（Beta-PERT 参数化说明：[R prevalence 包文档](https://search.r-project.org/CRAN/refmans/prevalence/html/betaPERT.html)）
29. Iman, R. L., & Conover, W. J. (1982). A distribution-free approach to inducing rank correlation among input variables. *Comm. Stat. — Simul. Comput.*, 11(3), 311–334. [DOI](https://doi.org/10.1080/03610918208812265)
30. Society of Petroleum Engineers. *Petroleum Resources Management System* (P90/P50/P10 定义). [PDF](https://www.spe.org/media/filer_public/0c/83/0c835db9-501f-4ce7-97f1-a1d6bb4e3331/prmgmtsystem_v103.pdf)

### 实物期权与分阶段投资

31. Dixit, A. K., & Pindyck, R. S. (1994). *Investment under Uncertainty*. Princeton UP. [出版社](https://press.princeton.edu/books/hardcover/9780691034102/investment-under-uncertainty) ｜ [导论 PDF](https://msuweb.montclair.edu/~lebelp/DixitPindyck1994.pdf)
32. Gompers, P. A. (1995). Optimal Investment, Monitoring, and the Staging of Venture Capital. *Journal of Finance*, 50(5), 1461–1489. [DOI](https://doi.org/10.1111/j.1540-6261.1995.tb05185.x)
33. McGrath, R. G. (1999). Falling Forward: Real Options Reasoning and Entrepreneurial Failure. *AMR*, 24(1), 13–30. [DOI](https://doi.org/10.5465/amr.1999.1580438)
34. Sahlman, W. A., & Scherlis, D. R. (1987, rev. 2009). A Method For Valuing High-Risk, Long-Term Investments: The "Venture Capital Method". HBS Note 288-006. [链接](https://www.hbs.edu/faculty/Pages/item.aspx?num=6515)

---

## 附录 A：可复现计算

| 文件 | 内容 |
|---|---|
| `risk_methodology_calcs.py` | 本手册全部公式的实现与数值验证；无 scipy 依赖，二分法与逆正态均自行实现 |
| `risk_methodology_output.txt` | 上述脚本在随机种子 20260727 下的完整输出 |

运行方式：

```bash
python risk_methodology_calcs.py
```

脚本覆盖的验证项：

1. 两结果 Kelly 闭式解 vs 通用数值解（偏差 < 1e−12）
2. 多档离散 Kelly 求解（VC 参照系 + 四档创业情景）
3. Fractional Kelly 的 `c(2−c)` 表，及其在离散重尾分布下的失效
4. 估计误差 × 下注比例的联合效应表（与 Thorp 2006 图 5 逐项吻合）
5. 波动率拖累精确式 vs 近似式 vs 蒙特卡洛（1,000,000 次）
6. PERT 采样 + Iman–Conover 秩相关诱导 + P10/P50/P90 + 收敛性检验
7. 夏普 / 索提诺 / Omega 在本项目分布上的实测，及三种"年化收益率"口径的 Jensen 差异
8. IRR ↔ 倍数换算表，含 Wiltbank & Boeker 数据的 IRR 勘误复核

**免责声明**：脚本只保证"给定输入 → 输出"的计算正确性。输入中的所有概率均为主观估计或外部参照系数据，脚本不保证输入本身正确。
