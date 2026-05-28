# Agent LLD — XPENG G9, G6 / Zeekr 7X

Scrape quotidiennement les offres de Location Longue Durée (LLD) pour les modèles XPENG G9, G6 et Zeekr 7X,
en neuf et en occasion. Produit un fichier JSON horodaté pour alimenter un dashboard.

## Structure

```
lld_agent/
├── scraper.py        # agent principal (requests + BeautifulSoup)
├── scraper_js.py     # fallback Playwright pour pages JS dynamiques
├── setup.sh          # installation + cron automatique
├── agent.log         # logs d'exécution (créé au 1er run)
├── data/
│   ├── latest.json               # toujours la dernière version
│   └── lld_YYYY-MM-DD.json       # historique par jour
└── README.md
```

## Installation rapide

```bash
git clone <votre-repo> lld_agent
cd lld_agent
bash setup.sh
```

Le script :
- Crée un virtualenv Python
- Installe `requests`, `beautifulsoup4`, `playwright`
- Installe le navigateur Chromium (pour le fallback JS)
- Configure un **cron à 07h00 chaque matin**

## Utilisation manuelle

```bash
source .venv/bin/activate

# Run complet
python scraper.py

# Dry-run (affiche sans sauvegarder)
python scraper.py --dry-run

# Fallback Playwright (si les pages officielles sont en JS pur)
python scraper_js.py
python scraper_js.py --save
```

## Format JSON de sortie

```json
{
  "generated_at": "2026-05-28T07:00:00",
  "date": "2026-05-28",
  "count": 5,
  "offers": [
    {
      "model": "G6",
      "brand": "XPENG",
      "version": "Autonomie Standard",
      "type": "neuf",
      "price_monthly": 359.0,
      "first_payment": 3550.0,
      "duration_months": 48,
      "km_per_year": 10000,
      "source_name": "even-motors.com",
      "source_url": "https://...",
      "note": "Sous condition de reprise 1 800 €.",
      "scraped_at": "2026-05-28T07:00:12",
      "scraped_date": "2026-05-28"
    }
  ]
}
```

## Sources scrapées

| Source | Cible | Type |
|---|---|---|
| `even-motors.com` | Offres LLD XPENG G6 / G9 | Neuf |
| `event.xpeng.com/fr` | Pages officielles XPENG | Neuf |
| `vivacar.fr` | LLD/LOA XPENG occasion | Occasion |
| `zeekr.eu` | Zeekr 7X (réseau FR en déploiement) | Neuf |

## Limites connues

- Les pages `event.xpeng.com` sont rendues en React côté client → si les mensualités
  ne sont pas dans le HTML statique, utiliser `scraper_js.py` (Playwright).
- Zeekr France n'a pas encore de site dédié FR ni d'offre LLD publiée (mai 2026).
  L'agent génère une entrée "à surveiller" avec `price_monthly: null`.
- Certains sites peuvent bloquer les bots. En cas d'erreur répétée :
  - Augmenter `DELAY_BETWEEN_REQUESTS` dans `scraper.py`
  - Basculer sur Playwright pour la source concernée
  - Ajouter une rotation de User-Agents

## Cron

Le cron est configuré par `setup.sh` :
```
0 7 * * * cd /chemin/lld_agent && .venv/bin/python scraper.py >> agent.log 2>&1
```

Vérification :
```bash
crontab -l
tail -f agent.log
```

## Historique des données

Les fichiers `data/lld_YYYY-MM-DD.json` s'accumulent chaque jour.
Pour comparer l'évolution des prix :

```bash
# Lister tous les fichiers
ls data/lld_*.json

# Voir les mensualités du jour
cat data/latest.json | python -c "
import json, sys
d = json.load(sys.stdin)
for o in d['offers']:
    print(f\"{o['brand']} {o['model']} {o['version']} ({o['type']}) : {o['price_monthly']} €/mois\")
"
```
