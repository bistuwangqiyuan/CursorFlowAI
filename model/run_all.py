"""一键复现：跑完全部模型，产出 outputs/results.json 与矢量 SVG 图表。

    python model/run_all.py

设计要求（对应工作原则第十三条「数据可证」）：
  · **固定随机种子**，任何人任意时间重跑都得到逐位相同的数字
  · 所有模型共用 `model/assumptions.py` 这一个假设来源，禁止别处硬编码
  · 产出单一事实源 `outputs/results.json`；BP 正文的每个数字都必须能在其中找到
  · 附 `key_numbers` 索引与 `manifest`（含各文件 SHA-256），供正文逐条对账

**若本脚本报错退出，说明 BP 中至少有一个数字失去了来源，不得交付。**
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "outputs"
sys.path.insert(0, str(ROOT / "model"))

import assumptions as A          # noqa: E402
import opportunity_scoring       # noqa: E402
import funnel                    # noqa: E402
import unit_economics            # noqa: E402
import acquisition               # noqa: E402
import monte_carlo as MC         # noqa: E402
import kelly                     # noqa: E402
import gates                     # noqa: E402
import figures                   # noqa: E402


def _git_rev() -> str | None:
    try:
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                           capture_output=True, text=True, timeout=10)
        return r.stdout.strip() or None
    except Exception:
        return None


def ev_sweep(rates=(0.0001, 2, 4, 6, 8, 10, 12, 14, 16, 20, 25, 30, 40, 50, 60),
             n: int = 100_000) -> list[dict]:
    """期望值随「时间机会成本」变化的扫描曲线（无差异点图的数据源）。

    **必须与主模拟同规模。** 早先这里用 n=20,000 图快，结果是 r→0 处算出
    +$5,821，而正文现金口径写的是 +$6,476——同一个量出现两个数。差额并非
    建模差异，纯粹是右尾在 2 万次下没收敛（期望值由极少数大成路径决定，
    正是收敛最慢的部分）。用同样的种子与样本量后，r→0 处会精确复现现金口径，
    这一条已写入 `_cross_checks` 作为硬校验。
    """
    out = []
    for r in rates:
        res = MC.simulate(n=n, overrides={"hourly_cost": max(r, 1e-4)})
        W = res["meta"]["full_wager_usd"]
        out.append({
            "hourly_usd": 0.0 if r < 0.01 else float(r),
            "wager_usd": W,
            "mean_multiple": res["outcomes_full"]["mean"],
            "ev_usd": (res["outcomes_full"]["mean"] - 1.0) * W,
            "p_gain": res["outcomes_full"]["p_gain"],
        })
    return out


def key_numbers(r: dict) -> dict:
    """BP 正文允许引用的数字白名单。**正文出现的数不在此表内，即为无源。**"""
    mc, k, g = r["monte_carlo"], r["kelly"], r["gates"]
    fa = k["full_accounting"]
    acq = r["acquisition"]["gap_analysis"]
    ue = r["unit_economics"]
    return {
        "赌注_全口径_美元": mc["meta"]["full_wager_usd"],
        "赌注_仅现金_美元": mc["meta"]["full_wager_cash_usd"],
        "时间占赌注比例": 1 - mc["meta"]["full_wager_cash_usd"] / mc["meta"]["full_wager_usd"],
        "止于Gate0B比例": mc["stop_distribution"].get("止于 Gate 0-B（流量验证）"),
        "止于Gate1比例": mc["stop_distribution"].get("止于 Gate 1（付费意愿）"),
        "活到经营期比例": mc["survival_to_operation"],
        "收益倍数_P10": mc["outcomes_full"]["P10"],
        "收益倍数_P50": mc["outcomes_full"]["P50"],
        "收益倍数_P90": mc["outcomes_full"]["P90"],
        "收益倍数_均值": mc["outcomes_full"]["mean"],
        "期望值_全口径_美元": mc["expected_value_usd"]["full_accounting"],
        "期望值_仅现金_美元": mc["expected_value_usd"]["cash_only"],
        "胜率_全口径": fa["win_loss"]["win_rate_p"],
        "盈亏比_全口径": fa["win_loss"]["payoff_ratio_b"],
        "保本所需胜率": fa["win_loss"]["breakeven_win_rate"],
        "Kelly比例_全口径": fa["kelly"]["f_star"],
        "Kelly比例_现金口径": k["cash_only"]["kelly"]["f_star"],
        "无差异时薪_美元每小时": k["indifference_hourly_rate"].get("indifference_hourly_usd"),
        "无差异年收入_美元": k["indifference_hourly_rate"].get("annual_equivalent_usd"),
        "年化_口径A": fa["annualization"]["A_expect_then_annualize"]["value"],
        "年化_口径B": fa["annualization"]["B_annualize_then_expect"]["value"],
        "年化_口径C": fa["annualization"]["C_geometric_conditional_on_survival"]["value"],
        "年化_口径D": fa["annualization"]["D_true_geometric_all_paths"]["value"],
        "P_达1000MRR": mc["business_metrics"]["p_reach_1000_mrr"],
        "P_达真实盈亏平衡MRR": mc["business_metrics"]["p_reach_3018_mrr_full_breakeven"],
        "MRR_P50_第36月": mc["business_metrics"]["mrr_P50"],
        "MRR_P90_第36月": mc["business_metrics"]["mrr_P90"],
        "所需月访客_要卡": acq["required_uv_for_1000_mrr_with_card"],
        "所需月访客_不要卡": acq["required_uv_for_1000_mrr_no_card"],
        "计划月访客_第36月": acq["planned_steady_uv_month36"],
        "渠道覆盖率_要卡": acq["coverage_with_card"],
        "渠道覆盖率_不要卡": acq["coverage_no_card"],
        "单客月贡献_美元": ue["per_customer_base"]["contribution_margin_usd"],
        "LTV_美元": ue["per_customer_base"]["ltv_usd"],
        "真实盈亏平衡客户数": ue["breakeven"]["full_breakeven"]["customers"],
        "门机制总价值_美元": g["gate_value"]["all_gates_removed"]["total_gate_value_usd"],
        "Gate1价值_美元": next(x["gate_value_usd"] for x in g["gate_value"]["per_gate"]
                              if "Gate 1" in x["gate"]),
        "累计工时_36月": g["stop_loss"]["tail_after_final_gate"]["total_hours_36m"],
        "累计现金_36月": g["stop_loss"]["tail_after_final_gate"]["total_cash_36m"],
        "候选总数": r["scoring"]["meta"]["n_candidates"],
        "硬过滤淘汰数": r["scoring"]["meta"]["n_eliminated"],
        "入围数": r["scoring"]["meta"]["n_survivors"],
        "头号候选": r["scoring"]["survivors"][0]["cid"],
        "头号候选得分": r["scoring"]["survivors"][0]["total"],
    }


def consistency_checks(r: dict, kn: dict) -> list[str]:
    """交叉校验：同一个量在不同模型里算出来必须一致。

    这不是形式主义。三个模型各自独立实现了漏斗，若口径漂移，
    BP 正文就会出现互相矛盾的数字而作者浑然不觉。
    """
    errs = []

    def close(a, b, tol=0.02, name=""):
        if a is None or b is None:
            errs.append(f"{name}: 存在 None（{a} vs {b}）")
        elif abs(a - b) > tol * max(abs(a), abs(b), 1e-9):
            errs.append(f"{name}: {a:.4f} vs {b:.4f} 相差超过 {tol:.0%}")

    # 1. 漏斗：acquisition 与 assumptions 的「所需访客」口径须一致
    close(kn["所需月访客_不要卡"], A.visitors_needed_for_mrr(1000.0, False),
          name="所需月访客(不要卡) acquisition vs assumptions")
    close(kn["所需月访客_要卡"], A.visitors_needed_for_mrr(1000.0, True),
          name="所需月访客(要卡) acquisition vs assumptions")

    # 2. 期望值：monte_carlo 与 kelly 必须来自同一分布
    close(kn["收益倍数_均值"] - 1.0, r["kelly"]["full_accounting"]["win_loss"]["expected_value"],
          tol=0.001, name="期望值 monte_carlo vs kelly")

    # 3. 赌注口径：monte_carlo 与 assumptions 一致
    expected_w = (A.CASH_CAP_USD + A.ENTITY_SETUP_RESERVE_USD
                  + A.HOURS_PER_YEAR * 3 * A.HOURLY_OPPORTUNITY_COST_USD)
    close(kn["赌注_全口径_美元"], expected_w, tol=1e-6, name="全额赌注口径")

    # 4. 止损台账不得超预算
    if kn["累计工时_36月"] > A.HOURS_PER_YEAR * A.HORIZON_YEARS:
        errs.append(f"累计工时 {kn['累计工时_36月']:.0f} 超预算")
    if kn["累计现金_36月"] > A.CASH_CAP_USD + A.ENTITY_SETUP_RESERVE_USD:
        errs.append(f"累计现金 ${kn['累计现金_36月']:.0f} 超预算")

    # 5. 扫描曲线在 r→0 处必须回到现金口径期望值
    #    时薪为 0 时，时间不计价，全口径退化为现金口径——这是恒等式，
    #    对不上就说明两处用了不同的样本量、种子或口径。
    sweep0 = next((s for s in r.get("ev_sweep", []) if s["hourly_usd"] == 0.0), None)
    if sweep0 is None:
        errs.append("ev_sweep 缺少 r=0 采样点，无法与现金口径对账")
    else:
        close(sweep0["ev_usd"], kn["期望值_仅现金_美元"], tol=0.01,
              name="ev_sweep(r→0) vs 现金口径期望值")

    # 6. 无差异时薪必须落在扫描曲线的变号区间内
    ind = kn["无差异时薪_美元每小时"]
    sw = r.get("ev_sweep", [])
    if ind is not None and sw:
        lo = max((s["hourly_usd"] for s in sw if s["ev_usd"] > 0), default=None)
        hi = min((s["hourly_usd"] for s in sw if s["ev_usd"] <= 0), default=None)
        if lo is not None and hi is not None and not lo <= ind <= hi:
            errs.append(f"无差异时薪 {ind:.2f} 不在曲线变号区间 [{lo}, {hi}] 内")

    # 7. 白名单不得有空值
    for k, v in kn.items():
        if v is None:
            errs.append(f"关键数字 {k} 为空")

    # 8. 各子模型自身的自检
    errs += [f"assumptions: {e}" for e in A.self_check()]
    errs += [f"gates: {e}" for e in r["gates"]["self_check_errors"]]
    return errs


def manifest(paths: list[Path]) -> list[dict]:
    out = []
    for p in sorted(paths):
        if p.exists():
            out.append({
                "file": str(p.relative_to(ROOT)).replace("\\", "/"),
                "bytes": p.stat().st_size,
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest()[:16],
            })
    return out


def main() -> None:
    t0 = time.time()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("  一键复现：CursorFlow AI 商业计划书全部模型")
    print("=" * 78)

    steps = [
        ("赛道量化筛选", "scoring", opportunity_scoring.run),
        ("漏斗模型", "funnel", funnel.run),
        ("单位经济学", "unit_economics", unit_economics.run),
        ("获客模型", "acquisition", acquisition.run),
        ("蒙特卡洛", "monte_carlo", MC.run),
        ("胜率/盈亏比/Kelly", "kelly", kelly.run),
        ("阶段门与止损", "gates", gates.run),
    ]
    results: dict = {}
    for label, key, fn in steps:
        t = time.time()
        results[key] = fn()
        print(f"  [{time.time() - t:6.1f}s] {label}")

    t = time.time()
    sweep = ev_sweep()
    results["ev_sweep"] = sweep
    print(f"  [{time.time() - t:6.1f}s] 时薪-期望值扫描（无差异点曲线）")

    t = time.time()
    samples = MC.simulate()["_samples"]
    svgs = figures.build_all(results, samples, sweep)
    print(f"  [{time.time() - t:6.1f}s] SVG 矢量图表 × {len(svgs)}")

    kn = key_numbers(results)
    errs = consistency_checks(results, kn)

    results["assumptions"] = A.export()
    results["key_numbers"] = kn
    results["figures"] = svgs
    results["meta"] = {
        "base_date": A.BASE_DATE,
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "seed": MC.SEED,
        "n_sims": MC.N_SIMS,
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "platform": platform.platform(),
        "git_rev": _git_rev(),
        "reproduce": "python build.py",
        "elapsed_seconds": round(time.time() - t0, 1),
    }

    p = OUT_DIR / "results.json"
    p.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=float),
                 encoding="utf-8")
    results["meta"]["manifest"] = manifest(
        [p] + [OUT_DIR / "figures" / s for s in svgs])
    p.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=float),
                 encoding="utf-8")

    print("\n【关键数字白名单】BP 正文只允许引用下列数值")
    for k, v in kn.items():
        if isinstance(v, float):
            s = f"{v:,.4f}" if abs(v) < 1000 else f"{v:,.0f}"
        else:
            s = str(v)
        print(f"  {k:<28} {s:>16}")

    print(f"\n【交叉校验】{len(errs)} 项问题")
    if errs:
        for e in errs:
            print(f"  [FAIL] {e}")
        print("\n**校验未通过：BP 中至少有一个数字失去来源，不得交付。**")
        raise SystemExit(1)
    print("  全部通过：三个模型的漏斗口径一致，期望值同源，台账未超预算。")

    print(f"\n  results.json  {p.stat().st_size / 1024:,.0f} KB")
    print(f"  figures/      {len(svgs)} 个 SVG")
    print(f"  总耗时        {time.time() - t0:.1f}s")
    print(f"  git           {results['meta']['git_rev'] or '(非 git 仓库)'}")


if __name__ == "__main__":
    main()
