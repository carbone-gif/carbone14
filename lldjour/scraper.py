"""
Agent de veille LLD — XPENG G9, G6 / Zeekr 7X
Scrape les offres quotidiennement et produit un fichier JSON horodaté.

Sources :
  - even-motors.com      (offres XPENG France détaillées)
  - event.xpeng.com/fr   (pages offres officielles)
  - vivacar.fr           (occasion LLD/LOA)
  - zeekr.eu / zeekr.fr  (Zeekr 7X)

Usage :
  python scraper.py              # run immédiat
  python scraper.py --dry-run    # affiche sans sauvegarder
  python scraper.py --mode pw    # force Playwright (bypass anti-bot)
"""

import json
import re
import time
import asyncio
import logging
import argparse
from datetime import date, datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OUTPUT_DIR = Path(__file__).parent / "data"
LOG_FILE   = Path(__file__).parent / "agent.log"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

DELAY = 2  # secondes entre requêtes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Modèle de données
# ---------------------------------------------------------------------------

@dataclass
class Offer:
    model: str
    brand: str
    version: str
    type: str                         # neuf | occasion
    price_monthly: Optional[float]
    first_payment: Optional[float]
    duration_months: Optional[int]
    km_per_year: Optional[int]
    source_name: str
    source_url: str
    note: str
    scraped_at: str
    scraped_date: str

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def now_iso(): return datetime.now().isoformat(timespec="seconds")
def today_str(): return date.today().isoformat()

def parse_price(text: str) -> Optional[float]:
    if not text: return None
    clean = re.sub(r"[^\d]", "", str(text))
    return float(clean) if clean else None

def parse_offer_fields(text: str):
    """Extrait mensualité, 1er loyer, durée, km depuis un bloc de texte."""
    monthly = None
    m = re.search(r"loyers?\s+mensuels?\s+[àa]\s+([\d\s]+)\s*€", text, re.IGNORECASE)
    if m: monthly = parse_price(m.group(1))
    if not monthly:
        m = re.search(r"(\d{3,4})\s*€\s*(?:TTC\s*)?(?:/\s*mois|par\s+mois)", text, re.IGNORECASE)
        if m: monthly = float(m.group(1))

    first = None
    m2 = re.search(r"1er\s+loyer\s+major[ée]\s+de\s+([\d\s]+)\s*€", text, re.IGNORECASE)
    if m2: first = parse_price(m2.group(1))

    duration, km_total = None, None
    m3 = re.search(r"(\d+)\s+mois\s+et\s+([\d\s]+)\s*km", text, re.IGNORECASE)
    if m3:
        duration = int(m3.group(1))
        km_total = int(re.sub(r"\s", "", m3.group(2)))

    km_per_year = (km_total // (duration // 12)) if (km_total and duration) else None
    return monthly, first, duration, km_per_year

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

def get_html(url: str) -> Optional[str]:
    """GET simple, 2 tentatives."""
    for attempt in range(2):
        try:
            r = SESSION.get(url, timeout=15)
            r.raise_for_status()
            time.sleep(DELAY)
            return r.text
        except requests.RequestException as e:
            log.warning(f"[attempt {attempt+1}] {url} — {e}")
            time.sleep(4)
    return None

# ---------------------------------------------------------------------------
# Scraper requests + BeautifulSoup
# ---------------------------------------------------------------------------

def _make_offer(model, brand, version, otype, monthly, first, duration, km_year,
                src_name, src_url, note) -> Offer:
    return Offer(
        model=model, brand=brand, version=version, type=otype,
        price_monthly=monthly, first_payment=first,
        duration_months=duration, km_per_year=km_year,
        source_name=src_name, source_url=src_url, note=note,
        scraped_at=now_iso(), scraped_date=today_str(),
    )

EVEN_MOTORS_PAGES = [
    {
        "url": "https://even-motors.com/nouveau-xpeng-g6-une-offre-en-lld-des-359e-mois/",
        "model": "G6", "version": "Autonomie Standard",
    },
    {
        "url": "https://even-motors.com/nouveau-xpeng-g6-en-lld-a-partir-de-425e-mois/",
        "model": "G6", "version": "Autonomie Standard (sans reprise)",
    },
    {
        "url": "https://even-motors.com/nouveau-xpeng-g9-profitez-dune-offre-en-lld-des-565e-mois/",
        "model": "G9", "version": "Autonomie Étendue",
    },
]

XPENG_OFFICIAL_PAGES = [
    {"url": "https://event.xpeng.com/fr/t79710.html", "model": "G9"},
    {"url": "https://event.xpeng.com/fr/3y01dt.html", "model": "G6"},
]

VIVACAR_PAGES = [
    {"url": "https://www.vivacar.fr/voiture-occasion/xpeng/g6", "model": "G6"},
    {"url": "https://www.vivacar.fr/voiture-occasion/xpeng/g9", "model": "G9"},
]

ZEEKR_PAGES = [
    "https://www.zeekr.eu/fr-fr/offers",
    "https://www.zeekr.eu/fr-be/offers/zeekr7x-long-range",
]


def scrape_even_motors_static() -> list[Offer]:
    offers = []
    for p in EVEN_MOTORS_PAGES:
        log.info(f"[even-motors] {p['url']}")
        html = get_html(p["url"])
        if not html:
            continue
        text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
        monthly, first, duration, km_year = parse_offer_fields(text)

        note = ""
        m = re.search(r"(sous\s+conditions?\s+de\s+reprise[^.]+\.)", text, re.IGNORECASE)
        if m: note = m.group(1).strip()
        m2 = re.search(r"(avant\s+le?\s+3[01]\s+\w+\s+202\d)", text, re.IGNORECASE)
        if m2: note += (" — " if note else "") + m2.group(1).strip()

        offers.append(_make_offer(
            p["model"], "XPENG", p["version"], "neuf",
            monthly, first, duration, km_year,
            "even-motors.com", p["url"], note,
        ))
        log.info(f"  → {p['model']} {p['version']} : {monthly}€/mois")
    return offers


def scrape_xpeng_official_static() -> list[Offer]:
    offers = []
    for p in XPENG_OFFICIAL_PAGES:
        log.info(f"[xpeng officiel] {p['url']}")
        html = get_html(p["url"])
        if not html: continue
        text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
        monthly, first, duration, km_year = parse_offer_fields(text)
        versions = re.findall(r"AUTONOMIE\s+(STANDARD|ÉTENDUE|ETENDUE)", text, re.IGNORECASE)
        version = ", ".join(sorted(set(v.capitalize() for v in versions))) or "Standard"
        if monthly:
            offers.append(_make_offer(
                p["model"], "XPENG", f"Autonomie {version}", "neuf",
                monthly, first, duration, km_year,
                "xpeng.com (officiel)", p["url"], "Source officielle XPENG France",
            ))
            log.info(f"  → {p['model']} : {monthly}€/mois")
        else:
            log.info(f"  → {p['model']} : page JS, pas de prix en HTML statique")
    return offers


def scrape_vivacar_static() -> list[Offer]:
    offers = []
    for p in VIVACAR_PAGES:
        log.info(f"[vivacar] {p['url']}")
        html = get_html(p["url"])
        if not html: continue
        text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
        prices = re.findall(r"(\d{3,4})\s*€/mois", text)
        durations = re.findall(r"Dur[ée]e?\s+(\d+)\s+mois", text, re.IGNORECASE)
        apports = re.findall(r"([\d\s]+)\s*€\s+d.apport", text, re.IGNORECASE)
        for i, price_str in enumerate(prices[:4]):
            monthly = float(price_str)
            duration = int(durations[i]) if i < len(durations) else 60
            apport = parse_price(apports[i]) if i < len(apports) else None
            offers.append(_make_offer(
                p["model"], "XPENG", "Voir site", "occasion",
                monthly, apport, duration, None,
                "vivacar.fr", p["url"], "Offre occasion LOA/LLD via Vivacar",
            ))
            log.info(f"  → {p['model']} occasion : {monthly}€/mois")
    return offers


def scrape_zeekr_static() -> list[Offer]:
    for url in ZEEKR_PAGES:
        log.info(f"[zeekr] {url}")
        html = get_html(url)
        if not html: continue
        text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
        if "7x" not in text.lower(): continue
        monthly, first, duration, km_year = parse_offer_fields(text)
        note = "Zeekr lancé en France le 2 avril 2026. Réseau en déploiement."
        if not monthly: note += " Offre LLD FR non encore publiée — prix catalogue 52 990 €."
        return [_make_offer("7X", "ZEEKR", "Standard", "neuf",
                            monthly, first, duration, km_year,
                            "zeekr.eu", url, note)]
    # fallback sans prix
    return [_make_offer("7X", "ZEEKR", "Standard", "neuf",
                        None, None, None, None,
                        "zeekr.eu", ZEEKR_PAGES[0],
                        "Zeekr lancé en France le 2 avril 2026. Prix catalogue 52 990 €. Offre LLD FR non encore publiée.")]

# ---------------------------------------------------------------------------
# Scraper Playwright (bypass anti-bot)
# ---------------------------------------------------------------------------

async def _pw_fetch(url: str) -> str:
    """Charge une URL via Playwright et retourne le texte du body."""
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_extra_http_headers({"Accept-Language": "fr-FR,fr;q=0.9"})
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(3)
            return await page.inner_text("body")
        finally:
            await page.close()
            await browser.close()

def scrape_with_playwright() -> list[Offer]:
    """Version Playwright pour contourner les protections anti-bot."""
    log.info("[playwright] mode activé")
    offers = []

    all_targets = (
        [(p["url"], p["model"], "G", p.get("version", "Standard")) for p in EVEN_MOTORS_PAGES]
        + [(p["url"], p["model"], "G", "Standard") for p in XPENG_OFFICIAL_PAGES]
        + [("https://www.vivacar.fr/voiture-occasion/xpeng/g6", "G6", "occ", "—"),
           ("https://www.vivacar.fr/voiture-occasion/xpeng/g9", "G9", "occ", "—")]
        + [(u, "7X", "Z", "Standard") for u in ZEEKR_PAGES[:1]]
    )

    for url, model, prefix, version in all_targets:
        log.info(f"  PW → {url}")
        try:
            text = asyncio.run(_pw_fetch(url))
            monthly, first, duration, km_year = parse_offer_fields(text)
            brand = "ZEEKR" if model == "7X" else "XPENG"
            otype = "occasion" if prefix == "occ" else "neuf"

            versions_found = re.findall(r"AUTONOMIE\s+(STANDARD|ÉTENDUE|ETENDUE)", text, re.IGNORECASE)
            if versions_found and version == "Standard":
                version = "Autonomie " + ", ".join(sorted(set(v.capitalize() for v in versions_found)))

            prices_in_page = re.findall(r"(\d{3,4})\s*€/mois", text) if otype == "occasion" else []
            if prices_in_page and not monthly:
                for pr in prices_in_page[:3]:
                    offers.append(_make_offer(model, brand, "Voir site", otype,
                        float(pr), None, 60, None,
                        "vivacar.fr (PW)", url, "Occasion LOA/LLD"))
                continue

            note = ""
            if model == "7X" and not monthly:
                note = "Zeekr lancé en France le 2 avril 2026. Prix catalogue 52 990 €. Offre LLD FR non encore publiée."

            offers.append(_make_offer(model, brand, version, otype,
                monthly, first, duration, km_year,
                f"{'even-motors.com' if 'even' in url else url.split('/')[2]} (PW)",
                url, note))
            log.info(f"    → {model} : {monthly}€/mois")
        except Exception as e:
            log.error(f"    PW ERREUR {url}: {e}")

    return offers

# ---------------------------------------------------------------------------
# Orchestrateur
# ---------------------------------------------------------------------------

def run(dry_run: bool = False, mode: str = "auto") -> list[dict]:
    log.info("=" * 60)
    log.info(f"Agent LLD — {today_str()} | mode={mode}")
    log.info("=" * 60)

    all_offers: list[Offer] = []

    if mode == "pw":
        all_offers = scrape_with_playwright()
    else:
        # Mode auto : requests en premier, Playwright en fallback si 0 résultats
        scrapers = [
            ("even-motors",    scrape_even_motors_static),
            ("xpeng officiel", scrape_xpeng_official_static),
            ("vivacar",        scrape_vivacar_static),
            ("zeekr",          scrape_zeekr_static),
        ]
        for name, fn in scrapers:
            try:
                r = fn()
                all_offers.extend(r)
                log.info(f"[{name}] → {len(r)} offre(s)")
            except Exception as e:
                log.error(f"[{name}] ERREUR : {e}", exc_info=True)

        # Si trop peu d'offres avec prix, bascule sur Playwright
        with_price = [o for o in all_offers if o.price_monthly]
        if len(with_price) < 2 and mode != "static":
            log.info("[auto] Peu de résultats — bascule Playwright")
            all_offers = scrape_with_playwright()

    # Dédoublonnage
    seen = set()
    deduped = []
    for o in all_offers:
        key = (o.model, o.version, o.price_monthly, o.type)
        if key not in seen:
            seen.add(key)
            deduped.append(o)

    deduped.sort(key=lambda o: (o.brand, o.model, o.price_monthly or 9999))

    payload = {
        "generated_at": now_iso(),
        "date": today_str(),
        "count": len(deduped),
        "offers": [asdict(o) for o in deduped],
    }

    if dry_run:
        log.info("[dry-run] Résultat :")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        OUTPUT_DIR.mkdir(exist_ok=True)
        out_path = OUTPUT_DIR / f"lld_{today_str()}.json"
        latest_path = OUTPUT_DIR / "latest.json"
        for path in [out_path, latest_path]:
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        log.info(f"Fichiers : {out_path} + {latest_path}")

    log.info(f"Total dédoublonné : {len(deduped)} offres")
    return payload["offers"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agent veille LLD XPENG/Zeekr")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--mode", choices=["auto", "pw", "static"], default="auto",
                        help="auto=requests+fallback PW | pw=Playwright seul | static=pas de scraping")
    args = parser.parse_args()
    run(dry_run=args.dry_run, mode=args.mode)
