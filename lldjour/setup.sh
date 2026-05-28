#!/usr/bin/env bash
# setup.sh — Installation de l'agent LLD et configuration du cron
# Usage : bash setup.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON=$(which python3)
VENV="$SCRIPT_DIR/.venv"

echo "=== Agent LLD XPENG / Zeekr — Setup ==="

# 1. Virtualenv
if [ ! -d "$VENV" ]; then
  echo "[1/4] Création du virtualenv..."
  $PYTHON -m venv "$VENV"
else
  echo "[1/4] Virtualenv existant, skip."
fi

source "$VENV/bin/activate"

# 2. Dépendances
echo "[2/4] Installation des dépendances..."
pip install --quiet --upgrade pip
pip install --quiet requests beautifulsoup4

# Playwright (pour les sites JS si nécessaire)
pip install --quiet playwright
python -m playwright install chromium --with-deps 2>/dev/null || echo "  Playwright chromium : installation manuelle peut être nécessaire"

# 3. Dossier data
mkdir -p "$SCRIPT_DIR/data"
echo "[3/4] Dossier data/ créé."

# 4. Cron quotidien à 07h00
CRON_CMD="0 7 * * * cd $SCRIPT_DIR && $VENV/bin/python scraper.py >> $SCRIPT_DIR/agent.log 2>&1"
EXISTING=$(crontab -l 2>/dev/null | grep -F "scraper.py" || true)

if [ -z "$EXISTING" ]; then
  (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
  echo "[4/4] Cron ajouté : 07h00 chaque matin."
else
  echo "[4/4] Cron déjà présent, skip."
fi

echo ""
echo "=== Installation terminée ==="
echo "  Run manuel   : source .venv/bin/activate && python scraper.py"
echo "  Dry run      : source .venv/bin/activate && python scraper.py --dry-run"
echo "  Logs         : tail -f $SCRIPT_DIR/agent.log"
echo "  Données      : $SCRIPT_DIR/data/latest.json"
echo "  Cron actuel  :"
crontab -l | grep scraper || echo "  (aucun)"
