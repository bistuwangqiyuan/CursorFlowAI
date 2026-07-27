"""按 CSS 选择器把单个元素高倍截图，用于确认字距/断行之类的细节。

低分辨率整页截图会把渲染细节和图像缩放的模糊混在一起，
容易把不存在的排版问题当成真的。
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "bp" / "index.html"
OUT = ROOT / "outputs" / "preview"


async def main(selector: str, index: int, name: str) -> None:
    from playwright.async_api import async_playwright

    OUT.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page(viewport={"width": 794, "height": 1200},
                                      device_scale_factor=5)
        await page.goto(HTML.as_uri(), wait_until="networkidle")
        await page.emulate_media(media="print")
        await page.evaluate("document.fonts.ready")
        el = page.locator(selector).nth(index)
        p = OUT / f"zoom_{name}.png"
        await el.screenshot(path=str(p))
        print(p)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 0,
                     sys.argv[3] if len(sys.argv) > 3 else "el"))
