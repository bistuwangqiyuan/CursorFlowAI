"""检查 index.html 中出现的每个字符是否被本地嵌入字体覆盖。

PDF 里出现 CambriaMath / MicrosoftYaHei 说明 Chromium 用系统字体做了回退。
回退字体虽然也被嵌入，成品能正常显示，但字形风格与正文不一致，
且依赖本机恰好装有该字体——换台机器构建就会得到不同的 PDF。
本脚本把「哪些字符触发了回退」精确列出来。
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "assets" / "fonts"
HTML = ROOT / "bp" / "index.html"


def cmap(path: Path) -> set[int]:
    """不装 fontTools 也能用：直接解析 TrueType 的 cmap 表（format 4 与 12）。"""
    d = path.read_bytes()
    u16 = lambda o: int.from_bytes(d[o:o + 2], "big")
    u32 = lambda o: int.from_bytes(d[o:o + 4], "big")

    num_tables = u16(4)
    cmap_off = None
    for i in range(num_tables):
        rec = 12 + i * 16
        if d[rec:rec + 4] == b"cmap":
            cmap_off = u32(rec + 8)
            break
    if cmap_off is None:
        return set()

    best = None
    for i in range(u16(cmap_off + 2)):
        rec = cmap_off + 4 + i * 8
        pid, eid, off = u16(rec), u16(rec + 2), u32(rec + 4)
        # 优先 (3,10) UCS-4，其次 (3,1) BMP
        rank = {(3, 10): 2, (0, 4): 2, (3, 1): 1, (0, 3): 1}.get((pid, eid), 0)
        if rank and (best is None or rank > best[0]):
            best = (rank, cmap_off + off)
    if best is None:
        return set()

    sub = best[1]
    fmt = u16(sub)
    out: set[int] = set()
    if fmt == 4:
        segx2 = u16(sub + 6)
        seg = segx2 // 2
        ends = [u16(sub + 14 + i * 2) for i in range(seg)]
        starts = [u16(sub + 16 + segx2 + i * 2) for i in range(seg)]
        deltas = [u16(sub + 16 + segx2 * 2 + i * 2) for i in range(seg)]
        ro_base = sub + 16 + segx2 * 3
        ranges = [u16(ro_base + i * 2) for i in range(seg)]
        for i in range(seg):
            for c in range(starts[i], min(ends[i], 0xFFFF) + 1):
                if ranges[i] == 0:
                    g = (c + deltas[i]) & 0xFFFF
                else:
                    gi = ro_base + i * 2 + ranges[i] + (c - starts[i]) * 2
                    if gi + 1 >= len(d):
                        continue
                    g = u16(gi)
                    if g:
                        g = (g + deltas[i]) & 0xFFFF
                if g:
                    out.add(c)
    elif fmt == 12:
        n = u32(sub + 12)
        for i in range(n):
            g = sub + 16 + i * 12
            out.update(range(u32(g), u32(g + 4) + 1))
    return out


def main() -> int:
    latin = cmap(FONTS / "Inter-Regular.ttf")
    cjk = cmap(FONTS / "NotoSansSC-Regular.ttf")
    covered = latin | cjk
    print(f"Inter 覆盖 {len(latin):,} 码位；Noto Sans SC 覆盖 {len(cjk):,} 码位")

    html = HTML.read_text(encoding="utf-8")
    # 去掉标签、脚本与样式，只看真正会被排版的文字
    body = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S)
    body = re.sub(r"<[^>]+>", " ", body)

    # SVG 图表里的文字同样要排版，且我先前的检查漏掉了它们
    svg_text, svg_families = [], Counter()
    for f in sorted((ROOT / "outputs" / "figures").glob("*.svg")):
        s = f.read_text(encoding="utf-8")
        svg_text.extend(re.findall(r"<text[^>]*>(.*?)</text>", s, flags=re.S))
        # matplotlib 写出的是整个族列表，逐个拆开检查，不能只看第一个
        for decl in re.findall(r"font-family\s*[:=]\s*([^;\"]+)", s):
            for fam in decl.split(","):
                svg_families[fam.strip().strip("'\"")] += 1

    ok = True
    missing = Counter(ch for ch in body + " ".join(svg_text)
                      if ord(ch) > 0x7F and ord(ch) not in covered)
    if missing:
        ok = False
        print(f"[不通过] {len(missing)} 个字符不在本地字体中，Chromium 会回退到系统字体：")
        for ch, n in missing.most_common():
            src = "Inter" if ord(ch) < 0x2E80 else "Noto"
            print(f"    {ch!r}  U+{ord(ch):04X}  出现 {n:>4} 次   （应由 {src} 提供）")
    else:
        print("[通过] 正文与图表中所有字符均被本地字体覆盖，不触发系统字体回退")

    allowed = {"Inter", "Noto Sans SC", "sans-serif", "DejaVu Sans",
               "Inter, 'Noto Sans SC', sans-serif"}
    stray = {k: v for k, v in svg_families.items() if k not in allowed}
    if stray:
        ok = False
        print(f"[不通过] SVG 中出现非预期字体族：{stray}")
    else:
        print(f"[通过] SVG 字体族仅限 {sorted(set(svg_families))}")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
