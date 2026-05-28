"""
scraper_js.py — Fallback Playwright pour les pages React/JS
(XPENG event.xpeng.com, Zeekr si besoin)

Utilise uniquement si scraper.py ne récupère pas les mensualités
depuis les pages officielles (rendu côté client).

Usage :
  python scraper_js.py                  # scrappe et affiche
  python scraper_js.py --save           # sauvegarde dans data/
"""

import asyncio
import json
import re
import argparse
from datetime import date, datetime
from pathlib import Path

from playwright.async_api import async_playwright

OUTPUT_DIR = Path(__file__).parent / "data"

TARGETS = [
    {
        "url": "https://event.xpeng.com/fr/t79710.html",
        "model": "G9", "brand": "XPENG",
    },
    {
        "url": "https://event.xpeng.com/fr/3y01dt.html",
        "model": "G6", "brand": "XPENG",
    },
    {
        "url": "https://fr.zeekr.com/offers",  # à ajuster quand le site FR sera live
        "model": "7X", "brand": "ZEEKR",
    },
]

def parse_price(text):
    clean = re.sub(r"[^\d]", "", text)
    return float(clean) if clean else None

async def scrape_page(browser, target):
    page = await browser.new_page()
    offers = []
    try:
        await page.goto(target["url"], wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)  # laisse le JS se charger
        text = await page.inner_text("body")

        monthly = None
        m = re.search(r"(\d{3,4})\s*€\s*/?\s*mois", text, re.IGNORECASE)
        if m:
            monthly = float(m.group(1))

        first = None
        m2 = re.search(r"1er\s+loyer[^€]*?([\d\s]+)\s*€", text, re.IGNORECASE)
        if m2:
            first = parse_price(m2.group(1))

        duration, km = None, None
        m3 = re.search(r"(\d+)\s+mois\s+et\s+([\d\s]+)\s*km", text)
        if m3:
            duration = int(m3.group(1))
            km = int(re.sub(r"\s", "", m3.group(2)))

        versions = re.findall(r"AUTONOMIE\s+(STANDARD|ÉTENDUE|ETENDUE)", text, re.IGNORECASE)
        version = ", ".join(sorted(set(v.capitalize() for v in versions))) or "Standard"

        print(f"[{target['model']}] {target['url']}")
        print(f"  Mensualité : {monthly} €/mois")
        print(f"  1er loyer  : {first} €")
        print(f"  Durée/km   : {duration} mois / {km} km")
        print(f"  Version    : {version}")

        if monthly:
            offers.append({
                "model": target["model"],
                "brand": target["brand"],
                "version": f"Autonomie {version}",
                "type": "neuf",
                "price_monthly": monthly,
                "first_payment": first,
                "duration_months": duration,
                "km_per_year": km // (duration // 12) if (km and duration) else None,
                "source_name": f"{target['brand'].lower()}.com (officiel JS)",
                "source_url": target["url"],
                "note": "Scraping via Playwright (page dynamique)",
                "scraped_at": datetime.now().isoformat(timespec="seconds"),
                "scraped_date": date.today().isoformat(),
            })
    except Exception as e:
        print(f"  ERREUR : {e}")
    finally:
        await page.close()
    return offers


async def main(save: bool = False):
    all_offers = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        for target in TARGETS:
            offers = await scrape_page(browser, target)
            all_offers.extend(offers)
        await browser.close()

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "date": date.today().isoformat(),
        "count": len(all_offers),
        "offers": all_offers,
        "source": "playwright_js",
    }

    print(json.dumps(payload, ensure_ascii=False, indent=2))

    if save:
        OUTPUT_DIR.mkdir(exist_ok=True)
        out = OUTPUT_DIR / f"lld_js_{date.today().isoformat()}.json"
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nSauvegardé : {out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--save", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(save=args.save))
