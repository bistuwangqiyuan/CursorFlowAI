"""验证「同一台机器上重跑一次，产出完全相同」这句话是真的。

起因（红队自检）：README 与正文都声称随机种子固定、结果可复核。第一次真去核
就发现不成立——results.json 里含构建时刻、git 版本号与耗时，SVG 里含 <dc:date>
和随机生成的 clipPath id。数字确实一样，但文件不一样，于是「可逐位复核」这句话
当时是假的。

处置分两步：
  · 治本：figures.py 固定 svg.hashsalt 并去掉 <dc:date>，让图表逐字节确定；
  · 守住：本工具重跑一遍模型，比对 **剔除构建元数据后** 的 results.json
    与全部 SVG。构建元数据（时间、git rev、耗时）本就该每次不同，
    把它们算进比对只会让检查永远失败，那就等于没有检查。

用法：python tools/verify_reproducible.py
注意：它会重跑一次完整模型（约 25 秒）并覆盖 outputs/，所以不放进 build.py
默认流程，而是在改动模型后手动跑一次。
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "outputs" / "results.json"
FIG_DIR = ROOT / "outputs" / "figures"

# 这些字段每次构建必然不同，且不携带任何结论。它们不参与比对。
#
# 关于 bytes：results.json 的清单里有一条指向它自己，而那条记录的
# 文件大小其实是**上一次**构建留下的文件——本次内容还没写完。它会随
# elapsed_seconds 的字符数（"9.1" 与 "12.4"）漂移一个字节。这是纯粹的
# 构建元数据，不是结论。真正该守的是清单里那 8 张 SVG，而它们在下面
# 被逐字节直接比对，不依赖清单转述。
BUILD_META = {"generated_at_utc", "git_rev", "elapsed_seconds", "sha256", "bytes"}


def strip_meta(obj):
    """递归剔除构建元数据，只留下实质内容。"""
    if isinstance(obj, dict):
        return {k: strip_meta(v) for k, v in obj.items() if k not in BUILD_META}
    if isinstance(obj, list):
        return [strip_meta(x) for x in obj]
    return obj


def snapshot() -> dict[str, str]:
    """给当前产出拍一张指纹快照。

    比对范围是全部 JSON 产出（不只是汇总的 results.json）加全部 SVG。
    逐个子模型都比，才能在出问题时直接指出是哪个模型不确定，
    而不是只看到「汇总文件变了」。
    """
    snap = {}
    for js in sorted(RESULTS.parent.glob("*.json")):
        blob = json.dumps(strip_meta(json.loads(js.read_text(encoding="utf-8"))),
                          ensure_ascii=False, sort_keys=True)
        snap[f"{js.name}（剔除构建元数据）"] = hashlib.sha256(blob.encode()).hexdigest()
    for svg in sorted(FIG_DIR.glob("*.svg")):
        snap[svg.name] = hashlib.sha256(svg.read_bytes()).hexdigest()
    return snap


def main() -> int:
    if not RESULTS.exists():
        print("找不到 outputs/results.json，请先运行 python build.py")
        return 1

    before = snapshot()
    print(f"已记录 {len(before)} 份产出的指纹，重跑模型……\n")

    r = subprocess.run([sys.executable, "model/run_all.py"], cwd=ROOT,
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("重跑失败：\n" + (r.stderr or r.stdout)[-2000:])
        return r.returncode

    after = snapshot()
    diff = [k for k in before if before[k] != after.get(k)]

    if diff:
        print(f"[不通过] {len(diff)} 份产出在重跑后发生变化，"
              f"说明存在未固定的随机性或残留的时间戳：")
        for k in diff:
            print(f"    {k}")
        print("\n请检查：随机种子是否全部固定；写文件时是否嵌入了构建时刻。")
        return 1

    n_json = sum(1 for k in before if k.endswith("）"))
    print(f"[通过] {len(before)} 份产出重跑后完全一致"
          f"（{n_json} 份 JSON 的实质内容 + {len(before) - n_json} 张 SVG 逐字节）。")
    print("      构建元数据（时间、git rev、耗时、自指的文件大小）按设计每次不同，不参与比对。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
