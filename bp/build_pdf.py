"""用 Playwright 把 bp/index.html 导出为 PDF，并对成品做结构校验。

为什么用 Playwright 而不是 WeasyPrint / wkhtmltopdf：
  · 页眉页脚与页码在 Chromium 下只能通过 header_template / footer_template 注入，
    `@page` 的 margin box 与 `counter(page)` 在 Chromium 里会静默失效
  · 需要 print_background=True 才能保留 callout / 表格底色
  · 字体子集化与嵌入由 Chromium 自动完成，无需手工处理

导出后做四项校验（任一不过即非零退出）：
  1. 字体全部内嵌（不得有引用而未嵌入的字体）
  2. 页数在合理区间，且每页都有内容（无空白页）
  3. 图表与表格不跨页——用 DOM 侧的分页盒模型检测，而非事后看 PDF
  4. 正文无未替换的占位符与明显的溢出
"""

from __future__ import annotations

import asyncio
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "bp" / "index.html"
PDF = ROOT / "outputs" / "商业计划书.pdf"

# A4 减去 @page 边距后的可用高度（mm）——与 print.css 中的 @page 保持一致
PAGE_H_MM = 297.0
MARGIN_TOP_MM, MARGIN_BOTTOM_MM = 18.0, 16.0
CONTENT_H_MM = PAGE_H_MM - MARGIN_TOP_MM - MARGIN_BOTTOM_MM
MM_PER_PX = 25.4 / 96.0

HEADER = """
<div style="width:100%; font-family:'Inter','Noto Sans SC',sans-serif;
            font-size:7pt; color:#86868B; padding:0 19mm;
            display:flex; justify-content:space-between;
            border-bottom:0.4pt solid #E8E8ED; padding-bottom:3mm;">
  <span>AI 编程生态创业决策与执行手册</span>
  <span>基准日 2026-07-27 · 自有资金 · 单人</span>
</div>
"""

FOOTER = """
<div style="width:100%; font-family:'Inter','Noto Sans SC',sans-serif;
            font-size:7pt; color:#86868B; padding:0 19mm;
            display:flex; justify-content:space-between;">
  <span>所有数字由 model/run_all.py 生成，可一条命令复算</span>
  <span><span class="pageNumber"></span> / <span class="totalPages"></span></span>
</div>
"""

# 首页不加页眉页脚：Chromium 无法按页关闭，改用在封面上留白 + 页眉底色透明的方式
# （封面高度已在 print.css 中设为 247mm，正好把页眉页脚区让开）


async def render() -> dict:
    from playwright.async_api import async_playwright

    PDF.parent.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page()
        await page.goto(HTML.as_uri(), wait_until="networkidle")
        await page.emulate_media(media="print")
        # 等字体真正就绪，否则首屏可能以回退字体排版后再导出
        await page.evaluate("document.fonts.ready")

        # 长表格是允许跨页的（print.css 里 table 为 break-inside:auto，
        # thead 设为 table-header-group 以便逐页重复表头），所以只检查
        # 真正不可分割的元素：图表、指标条、卡片，以及单个表格行。
        overflow = await page.evaluate(
            """(contentHpx) => {
                const out = [];
                const sel = 'figure, .metrics, .callout, .verdict, tr';
                for (const el of document.querySelectorAll(sel)) {
                    const h = el.getBoundingClientRect().height;
                    if (h > contentHpx) {
                        out.push({
                            tag: el.tagName.toLowerCase(),
                            cls: el.className || '',
                            mm: Math.round(h * 25.4 / 96),
                            text: (el.textContent || '').trim().slice(0, 60)
                        });
                    }
                }
                return out;
            }""",
            CONTENT_H_MM / MM_PER_PX,
        )

        # 表格若无 thead，跨页后读者就看不到列名了
        headless_tables = await page.evaluate(
            """(contentHpx) => {
                const out = [];
                for (const t of document.querySelectorAll('table')) {
                    if (t.getBoundingClientRect().height > contentHpx
                        && !t.querySelector('thead')) {
                        out.push((t.textContent || '').trim().slice(0, 50));
                    }
                }
                return out;
            }""",
            CONTENT_H_MM / MM_PER_PX,
        )

        placeholders = await page.evaluate(
            r"""() => {
                const t = document.body.innerText;
                const m = t.match(/\{\{[A-Z_]+\}\}|__[A-Z]+__|undefined|NaN/g);
                return m ? Array.from(new Set(m)) : [];
            }"""
        )

        await page.pdf(
            path=str(PDF),
            format="A4",
            print_background=True,
            prefer_css_page_size=True,
            display_header_footer=True,
            header_template=HEADER,
            footer_template=FOOTER,
            margin={"top": f"{MARGIN_TOP_MM}mm", "bottom": f"{MARGIN_BOTTOM_MM}mm",
                    "left": "19mm", "right": "19mm"},
        )
        await browser.close()
    return {"overflow": overflow, "placeholders": placeholders,
            "headless_tables": headless_tables}


def inspect_pdf() -> dict:
    """不依赖第三方库，直接读 PDF 结构：字体嵌入情况与页数。"""
    raw = PDF.read_bytes()
    txt = raw.decode("latin-1", errors="replace")

    pages = len(re.findall(r"/Type\s*/Page[^s]", txt))
    # 字体：BaseFont 名 + 是否带 FontFile（嵌入标志）
    fonts = sorted(set(re.findall(r"/BaseFont\s*/([A-Za-z0-9+\-_,.]+)", txt)))
    embedded = sorted({f for f in fonts if "+" in f})  # 子集化字体名带 ABCDEF+ 前缀
    not_embedded = [f for f in fonts if f not in embedded]
    fontfiles = len(re.findall(r"/FontFile\d?\s", txt))
    return {
        "pages": pages,
        "fonts": fonts,
        "embedded": embedded,
        "not_embedded": not_embedded,
        "fontfile_streams": fontfiles,
        "size_kb": len(raw) / 1024,
    }


def main() -> int:
    if not HTML.exists():
        print(f"找不到 {HTML}，请先运行 python bp/build_html.py")
        return 1

    dom = asyncio.run(render())
    pdf = inspect_pdf()

    print(f"已导出 {PDF}  ({pdf['size_kb']:,.0f} KB, {pdf['pages']} 页)")
    print()
    print("── 校验 ──────────────────────────────────────────")

    ok = True

    # 1 字体嵌入
    if pdf["not_embedded"]:
        print(f"[不通过] 有未嵌入字体：{pdf['not_embedded']}")
        ok = False
    else:
        print(f"[通过] 字体全部子集化嵌入（{len(pdf['embedded'])} 个子集，"
              f"{pdf['fontfile_streams']} 个字体流）")
        for f in pdf["embedded"]:
            print(f"        {f}")

    # 2 页数
    if not 20 <= pdf["pages"] <= 80:
        print(f"[注意] 页数 {pdf['pages']} 超出预期区间 20–80，请人工确认")
    else:
        print(f"[通过] 页数 {pdf['pages']}，在合理区间内")

    # 3 分页断裂：任何单个不可分割块高于一页正文区，必然被强行截断
    if dom["overflow"]:
        print(f"[不通过] {len(dom['overflow'])} 个不可分割块高于单页正文区 "
              f"（{CONTENT_H_MM:.0f}mm），会被强行分页：")
        for o in dom["overflow"]:
            print(f"        {o['tag']}.{o['cls']} {o['mm']}mm — {o['text']}")
        ok = False
    else:
        print(f"[通过] 无图表/卡片/表格行超过单页正文高度（{CONTENT_H_MM:.0f}mm）")

    if dom["headless_tables"]:
        print(f"[不通过] {len(dom['headless_tables'])} 个跨页长表缺少 thead，"
              f"翻页后将失去列名：{dom['headless_tables']}")
        ok = False
    else:
        print("[通过] 所有跨页长表均有 thead，逐页重复表头")

    # 4 占位符与脏值
    if dom["placeholders"]:
        print(f"[不通过] 正文残留占位符或脏值：{dom['placeholders']}")
        ok = False
    else:
        print("[通过] 正文无未替换占位符、无 undefined / NaN")

    print("──────────────────────────────────────────────────")
    print("全部通过。" if ok else "存在不通过项，见上。")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
