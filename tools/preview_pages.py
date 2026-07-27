"""把 index.html 按 A4 宽度、打印媒体渲染成分段 PNG，用于人工目检版式。

只看 PDF 不便于快速翻查，这里输出若干张连续截图，
外加一份「code 元素实际解析到哪个字体」的诊断，
因为 CSS 里写的族名与浏览器真正选中的字体经常不是一回事。
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "bp" / "index.html"
OUT = ROOT / "outputs" / "preview"

A4_W_PX = 794          # 210mm @96dpi
VIEW_H = 1400
SCALE = 2


async def main(n_shots: int) -> None:
    from playwright.async_api import async_playwright

    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.png"):
        old.unlink()

    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page(
            viewport={"width": A4_W_PX, "height": VIEW_H},
            device_scale_factor=SCALE)
        await page.goto(HTML.as_uri(), wait_until="networkidle")
        await page.emulate_media(media="print")
        await page.evaluate("document.fonts.ready")

        diag = await page.evaluate(
            """() => {
                const pick = (sel) => {
                    const el = document.querySelector(sel);
                    if (!el) return null;
                    const cs = getComputedStyle(el);
                    return {declared: cs.fontFamily, size: cs.fontSize,
                            weight: cs.fontWeight};
                };
                return {
                    body: pick('body'),
                    code: pick('code'),
                    h1:   pick('h1'),
                    table: pick('table td'),
                };
            }"""
        )
        print("── 计算后样式 ──")
        for k, v in diag.items():
            print(f"  {k:<6} {v}")

        total = await page.evaluate("document.body.scrollHeight")
        print(f"\n文档总高 {total}px ≈ {total / 1123:.0f} 个 A4 页面高")

        for i in range(n_shots):
            y = i * VIEW_H
            if y >= total:
                break
            await page.evaluate(f"window.scrollTo(0, {y})")
            await page.wait_for_timeout(120)
            p = OUT / f"p{i:02d}.png"
            await page.screenshot(path=str(p))
            print(f"  {p.name}")
        await browser.close()
    print(f"\n输出目录 {OUT}")


if __name__ == "__main__":
    asyncio.run(main(int(sys.argv[1]) if len(sys.argv) > 1 else 8))
