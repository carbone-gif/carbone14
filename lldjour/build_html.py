"""
build_html.py — Génère un index.html autonome pour Netlify Drop
Lit data/latest.json et produit un site HTML complet tout-en-un.

Usage :
  python build_html.py              # génère dist/index.html
  python build_html.py --open       # génère + ouvre dans le navigateur
"""

import json
import argparse
import subprocess
import sys
from pathlib import Path
from datetime import datetime

SRC  = Path(__file__).parent / "data" / "latest.json"
DIST = Path(__file__).parent / "dist"

def load_data() -> dict:
    if not SRC.exists():
        print(f"ERREUR : {SRC} introuvable. Lance d'abord : python scraper.py")
        sys.exit(1)
    return json.loads(SRC.read_text(encoding="utf-8"))

def format_date(iso: str) -> str:
    try:
        d = datetime.fromisoformat(iso)
        mois = ["jan","fév","mar","avr","mai","juin","juil","août","sep","oct","nov","déc"]
        return f"{d.day} {mois[d.month-1]} {d.year}"
    except Exception:
        return iso

def build(data: dict) -> str:
    offers_json = json.dumps(data["offers"], ensure_ascii=False)
    date_label  = format_date(data.get("date", data.get("generated_at", "")))
    count       = data.get("count", len(data["offers"]))

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="#ffffff">
<title>Veille LLD — XPENG · Zeekr</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --bg:#ffffff;--bg2:#f5f5f3;--bg3:#ebebea;
  --txt:#1a1a1a;--txt2:#6b6b69;--txt3:#9b9b99;
  --border:rgba(0,0,0,0.1);--border2:rgba(0,0,0,0.18);
  --blue-bg:#e6f1fb;--blue-txt:#0c447c;
  --green-bg:#eaf3de;--green-txt:#27500a;
  --purple-bg:#eeedfe;--purple-txt:#3c3489;
  --teal:#1d9e75;
  --radius:8px;--radius-lg:12px;
}}
@media(prefers-color-scheme:dark){{
  :root{{
    --bg:#1c1c1a;--bg2:#252523;--bg3:#2e2e2c;
    --txt:#f0f0ee;--txt2:#a0a09e;--txt3:#6b6b69;
    --border:rgba(255,255,255,0.1);--border2:rgba(255,255,255,0.18);
    --blue-bg:#0c447c;--blue-txt:#b5d4f4;
    --green-bg:#27500a;--green-txt:#c0dd97;
    --purple-bg:#3c3489;--purple-txt:#cecbf6;
  }}
}}
body{{
  font-family:'Inter',system-ui,sans-serif;
  background:var(--bg3);
  color:var(--txt);
  min-height:100vh;
  font-size:15px;
  line-height:1.5;
}}
.page{{max-width:520px;margin:0 auto;padding:0 1rem 3rem}}

/* Header */
.header{{
  padding:1.25rem 0 1rem;
  border-bottom:0.5px solid var(--border);
  margin-bottom:1.25rem;
  display:flex;align-items:center;justify-content:space-between;
}}
.header-left h1{{font-size:16px;font-weight:500;color:var(--txt)}}
.header-left .sub{{font-size:12px;color:var(--txt3);margin-top:2px;display:flex;align-items:center;gap:5px}}
.dot{{width:6px;height:6px;border-radius:50%;background:var(--teal);display:inline-block;flex-shrink:0}}
.badge-count{{font-size:12px;background:var(--bg2);border:0.5px solid var(--border);border-radius:99px;padding:3px 10px;color:var(--txt2)}}

/* Stats */
.stats{{display:grid;grid-template-columns:repeat(2,1fr);gap:8px;margin-bottom:1.25rem}}
.stat{{background:var(--bg2);border-radius:var(--radius);padding:.75rem 1rem}}
.stat-label{{font-size:11px;color:var(--txt2);margin-bottom:3px}}
.stat-val{{font-size:20px;font-weight:500;color:var(--txt)}}

/* Filtres */
.filters{{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:1rem}}
.pill{{
  font-size:12px;padding:5px 12px;border-radius:99px;
  border:0.5px solid var(--border2);background:var(--bg);
  color:var(--txt2);cursor:pointer;transition:all .15s;
  -webkit-tap-highlight-color:transparent;
}}
.pill:hover{{background:var(--bg2)}}
.pill.active{{background:var(--txt);color:var(--bg);border-color:transparent}}

/* Cartes */
.cards{{display:flex;flex-direction:column;gap:10px}}
.card{{
  background:var(--bg);border:0.5px solid var(--border);
  border-radius:var(--radius-lg);padding:1rem;
}}
.card-top{{display:flex;align-items:center;justify-content:space-between;margin-bottom:8px}}
.model-tag{{font-size:11px;font-weight:500;padding:2px 9px;border-radius:99px}}
.tag-g9{{background:var(--blue-bg);color:var(--blue-txt)}}
.tag-g6{{background:var(--green-bg);color:var(--green-txt)}}
.tag-7x{{background:var(--purple-bg);color:var(--purple-txt)}}
.type-badge{{
  font-size:10px;padding:2px 7px;border-radius:99px;
  background:var(--bg2);color:var(--txt2);border:0.5px solid var(--border);
}}
.card-version{{font-size:13px;font-weight:500;color:var(--txt);margin-bottom:4px}}
.card-price{{font-size:28px;font-weight:500;color:var(--txt);line-height:1;margin-bottom:10px}}
.card-price span{{font-size:13px;font-weight:400;color:var(--txt2)}}
.no-price{{font-size:13px;color:var(--txt3);font-style:italic;margin-bottom:10px}}
.card-rows{{border-top:0.5px solid var(--border);padding-top:8px;display:flex;flex-direction:column;gap:5px}}
.card-row{{display:flex;justify-content:space-between;font-size:12px}}
.card-row-label{{color:var(--txt2)}}
.card-row-val{{color:var(--txt);font-weight:500}}
.card-link{{color:#185fa5;text-decoration:none;font-weight:400}}
.card-link:hover{{text-decoration:underline}}
.card-note{{font-size:11px;color:var(--txt3);font-style:italic;margin-top:7px;line-height:1.4}}

/* Vide */
.empty{{text-align:center;padding:2.5rem 1rem;color:var(--txt3);font-size:14px}}

/* Footer */
.footer{{margin-top:1.5rem;padding-top:1rem;border-top:0.5px solid var(--border);font-size:11px;color:var(--txt3);line-height:1.6}}
</style>
</head>
<body>
<div class="page">

  <div class="header">
    <div class="header-left">
      <h1>Veille LLD</h1>
      <div class="sub">
        <span class="dot"></span>
        Mise à jour le {date_label}
      </div>
    </div>
    <span class="badge-count" id="badge">{count} offres</span>
  </div>

  <div class="stats">
    <div class="stat"><div class="stat-label">Offres</div><div class="stat-val" id="s-count">{count}</div></div>
    <div class="stat"><div class="stat-label">Mensualité min.</div><div class="stat-val" id="s-min">—</div></div>
    <div class="stat"><div class="stat-label">Mensualité max.</div><div class="stat-val" id="s-max">—</div></div>
    <div class="stat"><div class="stat-label">Modèles suivis</div><div class="stat-val">3</div></div>
  </div>

  <div class="filters" id="filters">
    <button class="pill active" data-f="all">Tous</button>
    <button class="pill" data-f="G9">G9</button>
    <button class="pill" data-f="G6">G6</button>
    <button class="pill" data-f="7X">7X</button>
    <button class="pill" data-f="neuf">Neuf</button>
    <button class="pill" data-f="occasion">Occasion</button>
  </div>

  <div class="cards" id="cards"></div>

  <div class="footer">
    Sources : xpeng.com &middot; even-motors.com &middot; vivacar.fr &middot; zeekr.eu<br>
    Données collectées automatiquement chaque matin à 07h00.
  </div>

</div>

<script>
const OFFERS = {offers_json};
let active = 'all';

function tagClass(m){{
  return m==='G9'?'tag-g9':m==='G6'?'tag-g6':'tag-7x';
}}

function fmt(n){{
  return n != null ? n.toLocaleString('fr-FR') : '—';
}}

function render(){{
  const filtered = OFFERS.filter(o => {{
    if(active==='all') return true;
    if(active==='neuf'||active==='occasion') return o.type===active;
    return o.model===active;
  }});

  const prices = filtered.filter(o=>o.price_monthly).map(o=>o.price_monthly);
  const minP = prices.length ? Math.min(...prices) : null;
  const maxP = prices.length ? Math.max(...prices) : null;

  document.getElementById('s-count').textContent = filtered.length;
  document.getElementById('s-min').textContent = minP ? minP+'€' : '—';
  document.getElementById('s-max').textContent = maxP ? maxP+'€' : '—';
  document.getElementById('badge').textContent = filtered.length+' offre'+(filtered.length>1?'s':'');

  document.querySelectorAll('.pill').forEach(p => {{
    const map = {{'all':'Tous','neuf':'Neuf','occasion':'Occasion'}};
    const label = map[active] || active;
    p.classList.toggle('active', p.dataset.f === active);
  }});

  if(!filtered.length){{
    document.getElementById('cards').innerHTML = '<div class="empty">Aucune offre pour ce filtre.</div>';
    return;
  }}

  document.getElementById('cards').innerHTML = filtered.map(o => `
    <div class="card">
      <div class="card-top">
        <span class="model-tag ${{tagClass(o.model)}}">${{o.brand}} ${{o.model}}</span>
        <span class="type-badge">${{o.type}}</span>
      </div>
      <div class="card-version">${{o.version}}</div>
      ${{o.price_monthly
        ? `<div class="card-price">${{o.price_monthly}} €<span>/mois</span></div>`
        : `<div class="no-price">Offre LLD non publiée</div>`
      }}
      <div class="card-rows">
        ${{o.duration_months ? `<div class="card-row"><span class="card-row-label">Durée</span><span class="card-row-val">${{o.duration_months}} mois · ${{fmt(o.km_per_year)}} km/an</span></div>` : ''}}
        ${{o.first_payment ? `<div class="card-row"><span class="card-row-label">1er loyer</span><span class="card-row-val">${{fmt(o.first_payment)}} €</span></div>` : ''}}
        <div class="card-row">
          <span class="card-row-label">Source</span>
          <span class="card-row-val"><a class="card-link" href="${{o.source_url}}" target="_blank" rel="noopener">${{o.source_name}} ↗</a></span>
        </div>
      </div>
      ${{o.note ? `<div class="card-note">${{o.note}}</div>` : ''}}
    </div>
  `).join('');
}}

document.getElementById('filters').addEventListener('click', e => {{
  const btn = e.target.closest('.pill');
  if(!btn) return;
  active = btn.dataset.f;
  render();
}});

render();
</script>
</body>
</html>"""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--open", action="store_true", help="Ouvre dans le navigateur après génération")
    args = parser.parse_args()

    data = load_data()
    html = build(data)

    DIST.mkdir(exist_ok=True)
    out = DIST / "index.html"
    out.write_text(html, encoding="utf-8")

    size_kb = round(out.stat().st_size / 1024, 1)
    print(f"✓ Généré : {out}  ({size_kb} Ko)")
    print(f"  {data['count']} offres · mise à jour du {data.get('date', '—')}")
    print(f"\n  → Glisse le dossier dist/ sur https://app.netlify.com/drop")

    if args.open:
        import webbrowser
        webbrowser.open(out.as_uri())

if __name__ == "__main__":
    main()
