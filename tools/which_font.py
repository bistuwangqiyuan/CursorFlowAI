"""报告页面上各类元素**实际**用到的平台字体。

`getComputedStyle().fontFamily` 只是 CSS 里声明的族列表，不代表渲染器
真正选中了哪一个。用 CDP 的 CSS.getPlatformFontsForNode 才能看到实际字体，
这是排查「声明了却没生效」类字体问题的唯一可靠办法。
"""

from __future__ import annotations

import asyncio
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "bp" / "index.html"

TARGETS = [
    ("body p", "正文段落"),
    ("dl.defs dd", "定义正文"),
    ("code", "行内代码"),
    (".mono", "等宽栏位"),
    ("a[href^='http']", "外链文字"),
    ("table td", "表格单元"),
    ("h1", "一级标题"),
    (".metric-value", "指标数字"),
]


async def main() -> None:
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page()
        await page.goto(HTML.as_uri(), wait_until="networkidle")
        await page.emulate_media(media="print")
        await page.evaluate("document.fonts.ready")

        loaded = await page.evaluate(
            """() => ['Inter','Noto Sans SC','JetBrains Mono']
                     .map(f => f + ': ' + document.fonts.check(`12px "${f}"`))"""
        )
        print("── @font-face 是否可用 ──")
        for line in loaded:
            print(f"  {line}")

        cdp = await page.context.new_cdp_session(page)
        await cdp.send("DOM.enable")
        await cdp.send("CSS.enable")
        doc = await cdp.send("DOM.getDocument")

        print("\n── 实际选中的平台字体 ──")
        for sel, label in TARGETS:
            node = await cdp.send("DOM.querySelector",
                                  {"nodeId": doc["root"]["nodeId"], "selector": sel})
            if not node["nodeId"]:
                print(f"  {label:<10} (页面上没有 {sel})")
                continue
            fonts = await cdp.send("CSS.getPlatformFontsForNode",
                                   {"nodeId": node["nodeId"]})
            used = ", ".join(f"{f['familyName']}×{f['glyphCount']}"
                             for f in fonts["fonts"])
            print(f"  {label:<10} {used or '(无文本)'}")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
