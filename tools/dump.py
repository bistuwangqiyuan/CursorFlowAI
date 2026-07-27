"""开发期辅助：按路径打印 results.json 的片段，便于撰稿时核对口径。"""
import json
import sys
from pathlib import Path

R = json.loads((Path(__file__).resolve().parent.parent / "outputs" / "results.json")
               .read_text(encoding="utf-8"))


def get(path: str):
    cur = R
    for part in path.split("."):
        cur = cur[int(part)] if part.isdigit() else cur[part]
    return cur


if __name__ == "__main__":
    for p in sys.argv[1:]:
        print(f"--- {p} ---")
        print(json.dumps(get(p), ensure_ascii=False, indent=2, default=float)[:3000])
