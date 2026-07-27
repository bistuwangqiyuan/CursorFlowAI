"""
风险量化方法论手册 —— 全部公式的可复现计算脚本
Reproducible computations for RISK_METHODOLOGY.md

运行环境: Python 3.12.10, numpy 2.5.1
运行方式: python risk_methodology_calcs.py
本脚本不依赖 scipy, 所有数值求解均自行实现(二分法), 便于任何第三方复现。

注意: 脚本中所有"概率"输入均为主观估计或来自公开参照系数据,
      脚本本身只保证"给定输入 -> 输出"的计算正确性, 不保证输入本身正确。
"""

import numpy as np

RNG_SEED = 20260727


# ---------------------------------------------------------------------------
# 1. Kelly 准则: 离散两结果情形
#    f* = (b*p - q) / b,  其中 b = 净赔率, p = 胜率, q = 1 - p
# ---------------------------------------------------------------------------

def kelly_two_outcome(p: float, b: float) -> float:
    """两结果 Kelly 闭式解。赢: +b 倍本金; 输: -1 倍本金(全损)。"""
    q = 1.0 - p
    return (b * p - q) / b


def log_growth_two_outcome(f: float, p: float, b: float) -> float:
    """g(f) = p*ln(1+f*b) + q*ln(1-f)"""
    q = 1.0 - p
    return p * np.log(1 + f * b) + q * np.log(1 - f)


# ---------------------------------------------------------------------------
# 2. Kelly 准则: 多结果 / 离散多档分布
#    max_f  g(f) = sum_i p_i * ln(1 + f * x_i)
#    一阶条件: g'(f) = sum_i p_i * x_i / (1 + f * x_i) = 0
#    g 在 f 上严格凹(见手册推导), 故一阶条件的根唯一, 可用二分法求解。
# ---------------------------------------------------------------------------

def kelly_growth(f: float, probs: np.ndarray, payoffs: np.ndarray) -> float:
    """g(f) = E[ln(1 + f*X)]，X 为每单位下注的净收益率。"""
    return float(np.sum(probs * np.log(1.0 + f * payoffs)))


def kelly_derivative(f: float, probs: np.ndarray, payoffs: np.ndarray) -> float:
    """g'(f) = E[X / (1 + f*X)]"""
    return float(np.sum(probs * payoffs / (1.0 + f * payoffs)))


def kelly_multi_outcome(probs, payoffs, tol=1e-12, max_iter=500):
    """
    多档离散分布下的 Kelly 最优比例, 二分法求 g'(f)=0。
    可行域: f ∈ [0, f_max), f_max = 1/|min(payoffs)| (保证 1+f*x > 0, 即不破产)。
    返回 (f_star, g_at_f_star)。
    """
    probs = np.asarray(probs, dtype=float)
    payoffs = np.asarray(payoffs, dtype=float)
    assert abs(probs.sum() - 1.0) < 1e-9, "概率必须归一"

    if kelly_derivative(0.0, probs, payoffs) <= 0:      # E[X] <= 0, 无正期望, 不下注
        return 0.0, 0.0

    worst = payoffs.min()
    f_hi = 1.0 / abs(worst) - 1e-9 if worst < 0 else 1e6   # 有全损档时上界 < 1/|x_min|
    if kelly_derivative(f_hi, probs, payoffs) > 0:          # 角点解
        return f_hi, kelly_growth(f_hi, probs, payoffs)

    lo, hi = 0.0, f_hi
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        if kelly_derivative(mid, probs, payoffs) > 0:
            lo = mid
        else:
            hi = mid
        if hi - lo < tol:
            break
    f_star = 0.5 * (lo + hi)
    return f_star, kelly_growth(f_star, probs, payoffs)


# ---------------------------------------------------------------------------
# 3. Fractional Kelly: 连续/对数正态近似下的增长率折损
#    Thorp (2006) eq.(7.7):  g(c f*) = (m-r)^2 * (c - c^2/2) / s^2 + r
#    => 超额增长率 g(c f*) - r  相对最大值之比 = c(2-c)
# ---------------------------------------------------------------------------

def fractional_kelly_growth_ratio(c: float) -> float:
    """c 倍 Kelly 时, 超额几何增长率相对全 Kelly 的比例 = c(2-c)。"""
    return c * (2.0 - c)


# ---------------------------------------------------------------------------
# 4. 波动率拖累 / 几何 vs 算术期望
#    g ≈ mu - sigma^2 / 2   (对数正态精确, 一般分布为二阶近似)
# ---------------------------------------------------------------------------

def volatility_drag_check(mu: float, sigma: float, n=2_000_000, seed=RNG_SEED):
    """
    用对数正态精确关系验证: 若 1+R 服从对数正态且 E[R]=mu, sd(R)=sigma,
    则 g = E[ln(1+R)] = ln(1+mu) - 0.5*ln(1 + sigma^2/(1+mu)^2)。
    同时给出常用近似 mu - sigma^2/2 的误差, 以及蒙特卡洛校验。
    """
    m1 = 1.0 + mu
    var_ratio = (sigma / m1) ** 2
    g_exact = np.log(m1) - 0.5 * np.log(1.0 + var_ratio)     # 对数正态精确解
    g_approx = mu - 0.5 * sigma ** 2                          # 常用近似

    mu_ln = g_exact
    sd_ln = np.sqrt(np.log(1.0 + var_ratio))
    rng = np.random.default_rng(seed)
    draws = rng.lognormal(mean=mu_ln, sigma=sd_ln, size=n)
    g_mc = float(np.mean(np.log(draws)))
    return g_exact, g_approx, g_mc, float(np.mean(draws)) - 1.0


# ---------------------------------------------------------------------------
# 5. 胜率 / 盈亏比 / 期望值 / Profit Factor
# ---------------------------------------------------------------------------

def payoff_stats(probs, multiples):
    """
    probs:     各档概率
    multiples: 各档回报倍数 M (投入 1 收回 M, 净收益 X = M - 1)
    返回: 胜率 p(M>1), 期望倍数 E[M], 期望净收益 E[X],
          盈亏比 (平均盈利/平均亏损), profit factor (总盈利/总亏损)
    """
    probs = np.asarray(probs, float)
    multiples = np.asarray(multiples, float)
    net = multiples - 1.0

    win = net > 0
    loss = net < 0
    p_win = float(probs[win].sum())
    e_mult = float(np.sum(probs * multiples))
    e_net = float(np.sum(probs * net))

    avg_win = float(np.sum(probs[win] * net[win]) / probs[win].sum()) if probs[win].sum() > 0 else np.nan
    avg_loss = float(-np.sum(probs[loss] * net[loss]) / probs[loss].sum()) if probs[loss].sum() > 0 else np.nan
    payoff_ratio = avg_win / avg_loss if avg_loss and avg_loss > 0 else np.inf

    gross_profit = float(np.sum(probs[win] * net[win]))
    gross_loss = float(-np.sum(probs[loss] * net[loss]))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else np.inf

    return dict(p_win=p_win, e_multiple=e_mult, e_net=e_net,
                avg_win=avg_win, avg_loss=avg_loss,
                payoff_ratio=payoff_ratio, profit_factor=profit_factor)


# ---------------------------------------------------------------------------
# 6. PERT (Beta-PERT) 分布采样 + Iman-Conover 秩相关
# ---------------------------------------------------------------------------

def pert_sample(a, m, b, size, rng, lam=4.0):
    """
    经典 Beta-PERT: mean = (a + lam*m + b)/(lam+2), lam=4 时即 (a+4m+b)/6。
    alpha = 1 + lam*(m-a)/(b-a);  beta = 1 + lam*(b-m)/(b-a)
    """
    if b <= a:
        raise ValueError("要求 b > a")
    alpha = 1.0 + lam * (m - a) / (b - a)
    beta = 1.0 + lam * (b - m) / (b - a)
    return a + (b - a) * rng.beta(alpha, beta, size)


def iman_conover(samples: np.ndarray, target_corr: np.ndarray, rng) -> np.ndarray:
    """
    Iman & Conover (1982): 通过重排序在保持各列边际分布不变的前提下,
    诱导出接近目标(秩)相关矩阵的相关结构。
    samples: (n, k) 独立样本; target_corr: (k, k) 目标相关矩阵。
    """
    n, k = samples.shape
    # van der Waerden 记分, 构造参考正态矩阵
    scores = np.sort(_normal_scores(n))
    ref = np.column_stack([rng.permutation(scores) for _ in range(k)])
    # 去除参考矩阵自身相关, 再施加目标相关
    e = np.linalg.cholesky(np.corrcoef(ref, rowvar=False))
    p = np.linalg.cholesky(target_corr)
    ref_star = ref @ np.linalg.inv(e).T @ p.T
    # 按 ref_star 的秩序重排每一列原始样本
    out = np.empty_like(samples)
    for j in range(k):
        order_target = np.argsort(np.argsort(ref_star[:, j]))
        out[:, j] = np.sort(samples[:, j])[order_target]
    return out


def _normal_scores(n):
    """van der Waerden 分数 Phi^{-1}(i/(n+1)), 用有理逼近避免依赖 scipy。"""
    probs = np.arange(1, n + 1) / (n + 1.0)
    return _norm_ppf(probs)


def _norm_ppf(p):
    """Acklam 逆正态累积分布有理逼近, 绝对误差 < 1.15e-9。"""
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    p = np.asarray(p, float)
    out = np.empty_like(p)
    lo, hi = p < 0.02425, p > 1 - 0.02425
    mid = ~(lo | hi)

    q = np.sqrt(-2 * np.log(p[lo]))
    out[lo] = (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q = np.sqrt(-2 * np.log(1 - p[hi]))
    out[hi] = -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q = p[mid] - 0.5
    r = q * q
    out[mid] = (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)
    return out


# ---------------------------------------------------------------------------
# 主程序: 逐条输出手册中引用的每一个数字
# ---------------------------------------------------------------------------

def main():
    np.set_printoptions(precision=4, suppress=True)
    line = "=" * 78

    print(line)
    print("[1] 两结果 Kelly: f* = (b*p - q)/b")
    print(line)
    for p, b in [(0.60, 1.0), (0.51, 1.0), (0.10, 20.0), (0.05, 30.0)]:
        f_cf = kelly_two_outcome(p, b)
        # 用通用多结果求解器交叉验证闭式解
        f_num, g_num = kelly_multi_outcome([p, 1 - p], [b, -1.0])
        print(f"  p={p:.2f}, b={b:>5.1f} -> 闭式 f*={f_cf: .6f} | 数值 f*={f_num: .6f} "
              f"| 差={abs(f_cf-f_num):.2e} | g(f*)={g_num:.6f}")

    print()
    print(line)
    print("[2] 多档离散分布 Kelly (以 Correlation Ventures 融资级别结果分布为参照系)")
    print("    档位概率来源: Correlation Ventures 2004-2013 约 21,000 笔融资(见手册出处)")
    print("    各档代表性倍数为本手册的假设值, 非原始数据, 使用时须标注为假设")
    print(line)
    vc_probs = np.array([0.65, 0.25, 0.06, 0.025, 0.010, 0.004])
    vc_probs = vc_probs / vc_probs.sum()
    vc_mult = np.array([0.20, 2.0, 7.0, 14.0, 30.0, 70.0])   # 假设的档内代表倍数
    vc_net = vc_mult - 1.0
    stats = payoff_stats(vc_probs, vc_mult)
    f_vc, g_vc = kelly_multi_outcome(vc_probs, vc_net)
    print(f"  归一后概率      : {vc_probs}")
    print(f"  代表倍数(假设)  : {vc_mult}")
    print(f"  胜率 p(M>1)     : {stats['p_win']:.4f}")
    print(f"  期望倍数 E[M]   : {stats['e_multiple']:.4f}")
    print(f"  期望净收益 E[X] : {stats['e_net']:.4f}")
    print(f"  平均盈利/平均亏损(盈亏比): {stats['payoff_ratio']:.4f}")
    print(f"  Profit Factor   : {stats['profit_factor']:.4f}")
    print(f"  Kelly f*        : {f_vc:.4f}  ({f_vc*100:.2f}% 的可投资本)")
    print(f"  g(f*)           : {g_vc:.6f}  (每次下注的对数增长率)")
    print(f"  半 Kelly g(0.5f*): {kelly_growth(0.5*f_vc, vc_probs, vc_net):.6f}")
    print(f"  全押 f=1 时 g   : E[ln] = {kelly_growth(1.0, vc_probs, vc_net):.6f} "
          f"(<0, 即长期几何增长率为负; 本档位设定最差为 0.2x 而非归零, 故 f=1 仍在可行域内)")

    print()
    print(line)
    print("[3] 四档创业情景 (全损 / 回本 / 小成 / 大成) —— 概率为占位假设, 须替换为自有估计")
    print(line)
    scen_names = ["全损", "回本", "小成", "大成"]
    scenarios = {
        "情景 A(悲观档位)": (np.array([0.70, 0.15, 0.12, 0.03]), np.array([0.0, 1.0, 3.0, 15.0])),
        "情景 B(中性档位)": (np.array([0.60, 0.20, 0.15, 0.05]), np.array([0.0, 1.0, 4.0, 25.0])),
    }
    for label, (scen_probs, scen_mult) in scenarios.items():
        scen_net = scen_mult - 1.0     # 全损档 M=0 => 净收益 -1, Kelly 可行域上界 f<1
        s2 = payoff_stats(scen_probs, scen_mult)
        f_s, g_s = kelly_multi_outcome(scen_probs, scen_net)
        print(f"  --- {label} ---")
        for nm, pr, mu_ in zip(scen_names, scen_probs, scen_mult):
            print(f"    {nm}: p={pr:.3f}, 倍数={mu_:.1f}")
        print(f"    期望倍数 E[M]   : {s2['e_multiple']:.4f}")
        print(f"    期望净收益 E[X] : {s2['e_net']:.4f}")
        print(f"    Kelly f*        : {f_s:.4f}")
        print(f"    g(f*)           : {g_s:.6f}")
        if f_s <= 0:
            print("    -> E[X] <= 0: Kelly 的答案是「一分钱都不要下」。")
            print("       这不是模型故障, 而是模型在给定输入下的正确输出;")
            print("       若仍决定创业, 依据必须来自 Kelly 框架之外(见手册第 1.4 节)。")
        else:
            for c in (0.5, 0.25):
                gc = kelly_growth(c * f_s, scen_probs, scen_net)
                print(f"    {c:g}x Kelly 时 g : {gc:.6f} ({gc/g_s*100:.1f}% of g(f*))")
            g2 = kelly_growth(min(2 * f_s, 1 - 1e-9), scen_probs, scen_net)
            print(f"    2x Kelly 时 g   : {g2:.6f} ({g2/g_s*100:.1f}% of g(f*))")
        print()

    print()
    print(line)
    print("[4] Fractional Kelly 增长率折损 (连续/对数正态近似): ratio = c(2-c)")
    print("    出处: Thorp (2006) eq.(7.7)  g(cf*) = (m-r)^2 (c - c^2/2)/s^2 + r")
    print(line)
    print("     c      c(2-c)    含义")
    for c in [0.25, 0.5, 0.75, 1.0, 1.5, 2.0]:
        r = fractional_kelly_growth_ratio(c)
        note = ""
        if abs(c - 0.5) < 1e-9:
            note = "半 Kelly: 保留 75% 超额增长率, 波动率降为 50%"
        if abs(c - 2.0) < 1e-9:
            note = "两倍 Kelly: 超额增长率归零"
        print(f"   {c:4.2f}   {r:7.4f}    {note}")

    print()
    print("  [4b] 估计误差 x 下注比例 的联合影响 (Thorp 2006, Fig.5 的解析复现)")
    print("       令 k = m_true / m_est, c = f / f*_est, r = 0;")
    print("       g(c f*_est) = (m_est^2 / 2 s^2) * (2ck - c^2), 下表单位为 m_est^2/(2 s^2)")
    print("       k \\ c        0.50      1.00      1.50")
    for k in (0.5, 1.0, 1.5):
        row = [2 * c * k - c ** 2 for c in (0.5, 1.0, 1.5)]
        print(f"       k={k:<4.1f}   " + "".join(f"{v:>9.2f}" for v in row))
    print("       读法: 真实收益只有估计值一半(k=0.5)时, 满 Kelly 增长率归零(0.00),")
    print("             1.5 倍 Kelly 则为 -0.75(必然破产); 而半 Kelly 仍取得该情形下的最大值 0.25。")
    print("             这就是「高估边际时, 过度下注的代价远大于不足下注」的量化含义。")

    print()
    print(line)
    print("[5] 波动率拖累 g ≈ mu - sigma^2/2 的数值校验 (对数正态)")
    print(line)
    for mu, sd in [(0.10, 0.20), (0.30, 0.60), (0.50, 1.20)]:
        g_ex, g_ap, g_mc, mu_chk = volatility_drag_check(mu, sd, n=1_000_000)
        print(f"  mu={mu:.2f}, sigma={sd:.2f} | 精确 g={g_ex:.6f} | 近似 mu-s^2/2={g_ap:.6f} "
              f"| 蒙特卡洛 g={g_mc:.6f} | MC 校验 E[R]={mu_chk:.4f}")
    print("  说明: sigma 越大, 近似式 mu - sigma^2/2 的误差越大; 高波动情形应使用精确式或直接模拟。")

    print()
    print(line)
    print("[6] 蒙特卡洛: PERT 边际 + Iman-Conover 秩相关, 报告 P10/P50/P90")
    print(line)
    rng = np.random.default_rng(RNG_SEED)
    n_iter = 100_000
    # 变量: 付费用户数(PERT), ARPU(PERT), 毛利率(PERT), 年成本(PERT)
    users = pert_sample(200, 900, 4000, n_iter, rng)
    arpu = pert_sample(200, 480, 1200, n_iter, rng)
    gm = pert_sample(0.55, 0.75, 0.88, n_iter, rng)
    cost = pert_sample(60_000, 110_000, 260_000, n_iter, rng)

    raw = np.column_stack([users, arpu, gm, cost])
    target = np.array([
        [1.00, -0.35, 0.00, 0.45],   # 用户数与 ARPU 负相关(走量则降价), 与成本正相关
        [-0.35, 1.00, 0.20, 0.00],
        [0.00, 0.20, 1.00, -0.15],
        [0.45, 0.00, -0.15, 1.00],
    ])
    corr_in = np.corrcoef(raw, rowvar=False)
    correlated = iman_conover(raw, target, rng)
    corr_out = np.corrcoef(correlated, rowvar=False)

    u, a, g_, c_ = correlated.T
    profit = u * a * g_ - c_
    p10, p50, p90 = np.percentile(profit, [10, 50, 90])
    print(f"  迭代次数            : {n_iter:,}")
    print(f"  独立采样时的相关矩阵 (对角外应≈0):\n{corr_in}")
    print(f"  施加 Iman-Conover 后:\n{corr_out}")
    print(f"  目标相关矩阵:\n{target}")
    print(f"  年毛利润 P10 = {p10:>12,.0f}")
    print(f"  年毛利润 P50 = {p50:>12,.0f}")
    print(f"  年毛利润 P90 = {p90:>12,.0f}")
    print(f"  年毛利润 均值 = {profit.mean():>11,.0f}  (均值 != P50, 即 Flaw of Averages)")
    print(f"  P(亏损) = {float((profit < 0).mean()):.4f}")

    print()
    print("  [6b] 迭代次数收敛性: P50 的重复抽样标准差")
    for n in [1_000, 5_000, 10_000, 50_000, 100_000]:
        meds = []
        for k in range(30):
            r2 = np.random.default_rng(RNG_SEED + 1000 + k)
            uu = pert_sample(200, 900, 4000, n, r2)
            aa = pert_sample(200, 480, 1200, n, r2)
            gg = pert_sample(0.55, 0.75, 0.88, n, r2)
            cc = pert_sample(60_000, 110_000, 260_000, n, r2)
            meds.append(np.median(uu * aa * gg - cc))
        meds = np.array(meds)
        print(f"    n={n:>7,} -> P50 均值={meds.mean():>12,.0f}, 跨次标准差={meds.std(ddof=1):>10,.0f} "
              f"({meds.std(ddof=1)/abs(meds.mean())*100:5.2f}%)")

    print()
    print(line)
    print("[7] 风险调整指标: 以 2026-07 无风险利率为基准")
    print("    美国 10Y = 4.71% (FRED DGS10, 2026-07-23)")
    print("    中国 10Y = 1.73% (中债国债收益率曲线, 2026-07-24)")
    print(line)
    rf_us, rf_cn = 0.0471, 0.0173
    # 用第 3 节"情景 B", 假定 3 年退出, 折算年化
    scen_probs, scen_mult = scenarios["情景 B(中性档位)"]
    horizon = 3.0
    ann = scen_mult ** (1.0 / horizon) - 1.0     # 各档年化收益率(全损档为 -100%)
    e_ann = float(np.sum(scen_probs * ann))
    sd_ann = float(np.sqrt(np.sum(scen_probs * (ann - e_ann) ** 2)))
    downside = np.minimum(ann - rf_cn, 0.0)
    dd = float(np.sqrt(np.sum(scen_probs * downside ** 2)))
    print(f"  各档年化收益率  : {ann}")
    print(f"  E[年化]         : {e_ann:.4f}")
    print(f"  sd(年化)        : {sd_ann:.4f}")
    print(f"  Sharpe (rf=中国10Y) = {(e_ann - rf_cn)/sd_ann:.4f}")
    print(f"  Sharpe (rf=美国10Y) = {(e_ann - rf_us)/sd_ann:.4f}")
    print(f"  下行偏差(MAR=rf_cn) = {dd:.4f}")
    print(f"  Sortino (MAR=rf_cn) = {(e_ann - rf_cn)/dd:.4f}")
    # Omega, 阈值取 rf_cn
    thr = rf_cn
    gain = float(np.sum(scen_probs * np.maximum(ann - thr, 0)))
    loss = float(np.sum(scen_probs * np.maximum(thr - ann, 0)))
    print(f"  Omega(阈值={thr:.4f})  = {gain/loss:.4f}")
    print("  警告: 本组指标建立在只有 4 个离散点、且概率为主观估计的分布上,")
    print("        其数值精度远低于其小数位数所暗示的精度, 仅可作为量级参考。")
    print()
    print("  [7b] Jensen 不等式演示: 三种「年化收益率」互不相等, 必须说明用的是哪一个")
    e_m = float(np.sum(scen_probs * scen_mult))
    e_logm = float(np.sum(scen_probs[scen_mult > 0] * np.log(scen_mult[scen_mult > 0])))
    p_survive = float(scen_probs[scen_mult > 0].sum())
    print(f"    (a) 期望倍数先算再年化   : E[M]^(1/T)-1 = {e_m ** (1/horizon) - 1: .4f}")
    print(f"    (b) 各档先年化再取期望   : E[M^(1/T)-1] = {e_ann: .4f}")
    print(f"    (c) 条件于未全损的几何均值: exp(E[lnM]|M>0)^(1/T)-1 = "
          f"{np.exp(e_logm / p_survive) ** (1/horizon) - 1: .4f} (存活概率 {p_survive:.0%})")
    print("    三者相差极大。商业计划书中出现「年化 XX%」时, 必须写明属于哪一种口径,")
    print("    否则该数字不具备可验证性。(a) 是最容易被误读为「预期收益」的一种。")

    print()
    print(line)
    print("[8] 天使/VC 要求回报率与倍数的换算 (IRR <-> 倍数)")
    print(line)
    for irr in [0.20, 0.27, 0.30, 0.40, 0.50, 0.60, 0.70]:
        print(f"  IRR={irr:.0%}: 3年={1.0*(1+irr)**3:6.2f}x, 5年={(1+irr)**5:6.2f}x, "
              f"7年={(1+irr)**7:7.2f}x")
    print("  反向校验 Wiltbank & Boeker (2007): 2.6x / 3.5年")
    print(f"    -> IRR = 2.6^(1/3.5) - 1 = {2.6 ** (1/3.5) - 1:.4f}")
    print("    (原报告写作 ~27%; Right Side Capital 指出按平均值口径正确算法应为 31%,")
    print("     按逐笔现金流口径为 30%。见手册出处。)")

    print()
    print(line)
    print("计算完毕。以上全部数字均由本脚本在固定随机种子下生成, 可完全复现。")
    print(f"随机种子 = {RNG_SEED}")
    print(line)


if __name__ == "__main__":
    main()
