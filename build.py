"""一条命令复现全部产出：python build.py

顺序是有意的，每一步都是下一步的前提：

  1. model/run_all.py     跑完所有模型，写 outputs/results.json 与 SVG 图表；
                          内含跨模型一致性对账，不一致就停在这里
  2. bp/build_html.py     从 results.json 渲染正文；关键数字取不到即失败
  3. tools/audit_numbers.py   守住「模型数字不被手打偷偷替换」（附录 C.3 的保证）
  4. tools/font_coverage.py   守住「所有字符都由随仓库携带的字体覆盖」，
                          否则换台机器构建会静默回退到系统字体
  5. bp/build_pdf.py      导出 PDF 并校验页数、字体嵌入、分页断裂

任何一步非零退出即整体失败并保留退出码——这样它可以直接放进 CI，
不需要人去看输出。这是「无人化」在本项目自身构建上的落实。
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent

STEPS = [
    ("跑模型并生成图表", "model/run_all.py"),
    ("渲染正文 HTML", "bp/build_html.py"),
    ("审计手打数字", "tools/audit_numbers.py"),
    ("检查字体覆盖", "tools/font_coverage.py"),
    ("导出并校验 PDF", "bp/build_pdf.py"),
]


def main() -> int:
    t0 = time.time()
    for i, (label, script) in enumerate(STEPS, 1):
        print(f"\n{'=' * 62}\n[{i}/{len(STEPS)}] {label}  ({script})\n{'=' * 62}")
        r = subprocess.run([sys.executable, script], cwd=ROOT)
        if r.returncode != 0:
            print(f"\n构建失败于第 {i} 步（{label}），退出码 {r.returncode}。"
                  f"\n后续步骤未执行——前一步的产出是后一步的前提，跳过只会掩盖问题。")
            return r.returncode

    print(f"\n{'=' * 62}\n全部 {len(STEPS)} 步通过，耗时 {time.time() - t0:.0f} 秒。"
          f"\n产出：outputs/商业计划书.pdf、bp/index.html、outputs/results.json\n{'=' * 62}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
