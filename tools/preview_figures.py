"""把 outputs/figures/*.svg 拼成一张预览图，用于人工目检图表渲染是否正常。

不是交付物的一部分，只是开发期的验收工具。
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIGS = ROOT / "outputs" / "figures"
FONTS = (ROOT / "assets" / "fonts").as_uri()


def build_html() -> Path:
    svgs = sorted(FIGS.glob("*.svg"))
    blocks = "\n".join(
        f'<figure><figcaption>{p.name}</figcaption>{p.read_text(encoding="utf-8")}</figure>'
        for p in svgs)
    html = f"""<!doctype html><meta charset="utf-8">
<style>
@font-face {{ font-family:"Inter"; src:url("{FONTS}/Inter-Regular.ttf"); font-weight:400; }}
@font-face {{ font-family:"Inter"; src:url("{FONTS}/Inter-Medium.ttf"); font-weight:500; }}
@font-face {{ font-family:"Inter"; src:url("{FONTS}/Inter-SemiBold.ttf"); font-weight:600; }}
@font-face {{ font-family:"Inter"; src:url("{FONTS}/Inter-Bold.ttf"); font-weight:700; }}
@font-face {{ font-family:"Noto Sans SC"; src:url("{FONTS}/NotoSansSC-Regular.ttf"); font-weight:400; }}
@font-face {{ font-family:"Noto Sans SC"; src:url("{FONTS}/NotoSansSC-Medium.ttf"); font-weight:500; }}
@font-face {{ font-family:"Noto Sans SC"; src:url("{FONTS}/NotoSansSC-SemiBold.ttf"); font-weight:600; }}
@font-face {{ font-family:"Noto Sans SC"; src:url("{FONTS}/NotoSansSC-Bold.ttf"); font-weight:700; }}
body {{ font-family:Inter,"Noto Sans SC",sans-serif; background:#fff; margin:32px; width:820px; }}
figure {{ margin:0 0 28px; }}
figcaption {{ font-size:11px; color:#86868B; margin-bottom:6px; }}
svg {{ max-width:100%; height:auto; }}
</style>
{blocks}
"""
    p = ROOT / "outputs" / "_preview.html"
    p.write_text(html, encoding="utf-8")
    return p


def main() -> None:
    from playwright.sync_api import sync_playwright
    page_path = build_html()
    out = ROOT / "outputs" / "_preview.png"
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 900, "height": 1200},
                        device_scale_factor=2)
        pg.goto(page_path.as_uri())
        pg.wait_for_timeout(1200)
        pg.screenshot(path=str(out), full_page=True)
        b.close()
    print(f"预览已生成: {out}")


if __name__ == "__main__":
    sys.exit(main())
