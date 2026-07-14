"""Screenshot the Vig screens for the README (headless Chromium via
Playwright). Regenerate whenever the UI changes materially."""

from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
DASH = ROOT / "reports" / "dashboard"
OUT = ROOT / "reports" / "screens"

SHOTS = [("index.html", "vig_desk.png", 1440, 1180),
         ("analysis.html", "vig_analysis.png", 1440, 1050),
         ("screener.html", "vig_screener.png", 1440, 1050),
         ("portfolio.html", "vig_portfolio.png", 1440, 1050)]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for page_file, out_name, w, h in SHOTS:
            pg = browser.new_page(viewport={"width": w, "height": h},
                                  device_scale_factor=2)
            pg.goto((DASH / page_file).as_uri())
            pg.wait_for_timeout(700)  # fonts + client-side tables
            pg.screenshot(path=OUT / out_name)
            print("wrote", OUT / out_name)
            pg.close()
        browser.close()


if __name__ == "__main__":
    main()
