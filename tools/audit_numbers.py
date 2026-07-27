"""审计正文里的「手打数字」，并把审计结果钉成回归基线。

起因（红队自检）：附录 C 原本声称「正文中的每一个数字都不是手打的」。
这句话经不起查——第 2 章大量引用外部事实（Snyk 的 ARR、Copilot 的定价、
法规生效日期），这些数字本就**不该**来自本项目的模型，它们的出处是脚注。
把它们也算进「不是手打」，等于用一句漂亮话盖住了一个真实的区分。

所以真正的保证应当分成两类：
  1. 模型产出的数字（工时、金额、概率、转化率）——必须经白名单从 results.json 取，
     取不到即构建失败。这是结构性保证。
  2. 外部事实数字——手打，但每处就近标注出处与核查日期。这是引用纪律。

本工具守的是第 1 类不被悄悄侵蚀：把当前所有「带模型量词的硬编码数字」
指纹化存入基线文件，**新增**一处就报错。已在基线里的是我逐条看过、
确认属于第 2 类（外部事实）的。这样既不必一次性重构历史，
又能保证以后每加一个手打数字都必须显式过审（留下 diff）。

用法：
  python tools/audit_numbers.py              # 检查，有新增则退出码 1
  python tools/audit_numbers.py --accept     # 复核过后，把当前状态写为新基线
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "bp" / "build_html.py"
BASELINE = Path(__file__).with_name("hardcoded_baseline.json")

# 明确可接受、不必进基线的字面量：章节/小节编号、法规条款号、日期、版本号、
# 评分制分母等。它们是排版与引用记号，不是数据。
ALLOW_CONTEXT = re.compile(
    r"第\s*\d+|\d+\.\d+\s|Gate\s*\d|Art\.?\s*\d|20\d\d-\d\d|20\d\d\s*年"
    r"|EU\s*\d|EO\s*\d{4,}|M-\d\d-\d\d|arXiv|ISO\s*\d+|SOC\s*2|A4|/10"
)

# 语义上属于「模型输出」的量词：出现这些单位时，数字要么来自模型，要么是外部事实
MODEL_UNITS = re.compile(r"(小时|工时|美元|\$|MRR|访客|客户|个月|倍|%|概率|胜率)")


def scan() -> list[dict]:
    """扫出所有带模型量词的硬编码数字，返回与行号无关的指纹。"""
    out = []
    for ln in SRC.read_text(encoding="utf-8").split("\n"):
        if not re.search(r"[\u4e00-\u9fff]", ln) or ln.lstrip().startswith("#"):
            continue
        # f-string 插值的值来自模型，不是手打，先剔除
        s = re.sub(r"\{[^{}]*\}", "\x00", ln)
        s = re.sub(r"<[^>]*>", " ", s)
        s = re.sub(r"\b(?:pct|usd|num|sgn_usd|K|G|A|D|esc)\b", " ", s)
        for m in re.finditer(r"(?<![\w.])[\d][\d,.]*", s):
            ctx = s[max(0, m.start() - 24):m.end() + 14]
            if ALLOW_CONTEXT.search(ctx) or not MODEL_UNITS.search(ctx):
                continue
            out.append({"num": m.group(0), "ctx": " ".join(ctx.split())})
    return out


def key(f: dict) -> str:
    return f"{f['num']}|{f['ctx']}"


def main() -> int:
    found = scan()
    accept = "--accept" in sys.argv

    if accept:
        BASELINE.write_text(
            json.dumps(sorted({key(f) for f in found}), ensure_ascii=False, indent=1),
            encoding="utf-8")
        print(f"[已接受] 基线更新为 {len(set(map(key, found)))} 处外部事实数字")
        return 0

    if not BASELINE.exists():
        print("[错误] 缺少基线文件，请先复核后运行 --accept")
        return 1

    base = set(json.loads(BASELINE.read_text(encoding="utf-8")))
    now = {key(f) for f in found}
    new, gone = now - base, base - now

    if new:
        print(f"[未通过] 新增 {len(new)} 处手打数字，必须改为从模型取值，"
              f"或复核确认是外部事实后运行 --accept：")
        for k in sorted(new):
            n, c = k.split("|", 1)
            print(f"    {n:<10} …{c}…")
        return 1

    msg = f"[通过] 无新增手打数字（基线 {len(base)} 处，均为已复核的外部事实引用）"
    if gone:
        msg += f"；另有 {len(gone)} 处已改为模型取值，可运行 --accept 收紧基线"
    print(msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
