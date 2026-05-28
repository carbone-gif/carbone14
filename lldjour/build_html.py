"""
build_html.py — Génère un index.html autonome pour Netlify Drop
Lit data/latest.json + data/competitors.json et produit un site HTML deux onglets.

Usage :
  python build_html.py              # génère index.html à la racine
  python build_html.py --open       # génère + ouvre dans le navigateur
"""

import json
import argparse
import sys
from pathlib import Path
from datetime import datetime

ROOT     = Path(__file__).parent
SRC      = ROOT / "data" / "latest.json"
COMP_SRC = ROOT / "data" / "competitors.json"
OUT      = ROOT / "index.html"

def load_json(path, fallback=None):
    if not path.exists():
        return fallback or []
    return json.loads(path.read_text(encoding="utf-8"))

def format_date(iso):
    try:
        d = datetime.fromisoformat(iso)
        mois = ["jan","fév","mar","avr","mai","juin","juil","août","sep","oct","nov","déc"]
        return f"{d.day} {mois[d.month-1]} {d.year}"
    except:
        return iso

def build():
    data     = load_json(SRC, {"offers": [], "date": ""})
    comp_raw = load_json(COMP_SRC, [])

    offers_json = json.dumps(data.get("offers", []), ensure_ascii=False)
    comp_json   = json.dumps(comp_raw, ensure_ascii=False)
    date_label  = format_date(data.get("date", data.get("generated_at", "")))

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="#ffffff">
<title>Veille LLD — XPENG · Zeekr · Concurrents</title>
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
  --teal-bg:#e1f5ee;--teal-txt:#085041;
  --amber-bg:#faeeda;--amber-txt:#633806;
  --coral-bg:#faece7;--coral-txt:#712b13;
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
    --teal-bg:#085041;--teal-txt:#9fe1cb;
    --amber-bg:#633806;--amber-txt:#fac775;
    --coral-bg:#712b13;--coral-txt:#f5c4b3;
  }}
}}
body{{font-family:'Inter',system-ui,sans-serif;background:var(--bg3);color:var(--txt);min-height:100vh;font-size:15px;line-height:1.5}}
.page{{max-width:520px;margin:0 auto;padding:0 1rem 3rem}}

/* Header */
.header{{padding:1.25rem 0 0;}}
.header h1{{font-size:16px;font-weight:500;color:var(--txt)}}
.header .sub{{font-size:12px;color:var(--txt3);margin-top:2px;display:flex;align-items:center;gap:5px}}
.dot{{width:6px;height:6px;border-radius:50%;background:var(--teal);display:inline-block;flex-shrink:0}}

/* Onglets */
.tabs{{display:flex;gap:0;margin:1rem 0;border-bottom:0.5px solid var(--border)}}
.tab{{font-size:13px;padding:8px 16px;cursor:pointer;color:var(--txt2);border-bottom:2px solid transparent;margin-bottom:-0.5px;background:none;border-left:none;border-right:none;border-top:none;transition:all .15s}}
.tab.active{{color:var(--txt);border-bottom-color:var(--txt);font-weight:500}}

/* Stats */
.stats{{display:grid;grid-template-columns:repeat(2,1fr);gap:8px;margin-bottom:1.25rem}}
.stat{{background:var(--bg2);border-radius:var(--radius);padding:.75rem 1rem}}
.stat-label{{font-size:11px;color:var(--txt2);margin-bottom:3px}}
.stat-val{{font-size:20px;font-weight:500;color:var(--txt)}}

/* Filtres */
.filters{{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:1rem}}
.pill{{font-size:12px;padding:5px 12px;border-radius:99px;border:0.5px solid var(--border2);background:var(--bg);color:var(--txt2);cursor:pointer;transition:all .15s;-webkit-tap-highlight-color:transparent}}
.pill:hover{{background:var(--bg2)}}
.pill.active{{background:var(--txt);color:var(--bg);border-color:transparent}}

/* Cartes */
.cards{{display:flex;flex-direction:column;gap:10px}}
.card{{background:var(--bg);border:0.5px solid var(--border);border-radius:var(--radius-lg);padding:1rem}}
.card-top{{display:flex;align-items:center;justify-content:space-between;margin-bottom:8px}}
.model-tag{{font-size:11px;font-weight:500;padding:2px 9px;border-radius:99px}}
.tag-g9{{background:var(--blue-bg);color:var(--blue-txt)}}
.tag-g6{{background:var(--green-bg);color:var(--green-txt)}}
.tag-7x{{background:var(--purple-bg);color:var(--purple-txt)}}
.tag-ev{{background:var(--teal-bg);color:var(--teal-txt)}}
.tag-phev{{background:var(--amber-bg);color:var(--amber-txt)}}
.type-badge{{font-size:10px;padding:2px 7px;border-radius:99px;background:var(--bg2);color:var(--txt2);border:0.5px solid var(--border)}}
.card-version{{font-size:13px;font-weight:500;color:var(--txt);margin-bottom:4px}}
.card-price{{font-size:28px;font-weight:500;color:var(--txt);line-height:1;margin-bottom:10px}}
.card-price span{{font-size:13px;font-weight:400;color:var(--txt2)}}
.no-price{{font-size:13px;color:var(--txt3);font-style:italic;margin-bottom:10px}}
.card-rows{{border-top:0.5px solid var(--border);padding-top:8px;display:flex;flex-direction:column;gap:5px}}
.card-row{{display:flex;justify-content:space-between;font-size:12px}}
.card-row-label{{color:var(--txt2)}}
.card-row-val{{color:var(--txt);font-weight:500}}
.card-link{{color:#185fa5;text-decoration:none}}
.card-link:hover{{text-decoration:underline}}
.card-note{{font-size:11px;color:var(--txt3);font-style:italic;margin-top:7px;line-height:1.4}}
.empty{{text-align:center;padding:2.5rem 1rem;color:var(--txt3);font-size:14px}}
.footer{{margin-top:1.5rem;padding-top:1rem;border-top:0.5px solid var(--border);font-size:11px;color:var(--txt3);line-height:1.6}}
.section-sep{{font-size:11px;font-weight:500;color:var(--txt3);text-transform:uppercase;letter-spacing:.06em;margin:1.5rem 0 .75rem;padding-bottom:6px;border-bottom:0.5px solid var(--border)}}
</style>
</head>
<body>
<div class="page">

  <div class="header">
    <h1>Veille LLD</h1>
    <div class="sub"><span class="dot"></span> Mise à jour le {date_label}</div>
  </div>

  <div class="tabs">
    <button class="tab active" onclick="switchTab('main',this)">XPENG · Zeekr</button>
    <button class="tab" onclick="switchTab('comp',this)">Concurrents</button>
  </div>

  <!-- ONGLET PRINCIPAL -->
  <div id="tab-main">
    <div class="stats">
      <div class="stat"><div class="stat-label">Offres</div><div class="stat-val" id="s-count">—</div></div>
      <div class="stat"><div class="stat-label">Mensualité min.</div><div class="stat-val" id="s-min">—</div></div>
      <div class="stat"><div class="stat-label">Mensualité max.</div><div class="stat-val" id="s-max">—</div></div>
      <div class="stat"><div class="stat-label">Modèles suivis</div><div class="stat-val">3</div></div>
    </div>
    <div class="filters" id="main-filters">
      <button class="pill active" data-f="all">Tous</button>
      <button class="pill" data-f="G9">G9</button>
      <button class="pill" data-f="G6">G6</button>
      <button class="pill" data-f="7X">7X</button>
      <button class="pill" data-f="neuf">Neuf</button>
      <button class="pill" data-f="occasion">Occasion</button>
    </div>
    <div class="cards" id="main-cards"></div>
  </div>

  <!-- ONGLET CONCURRENTS -->
  <div id="tab-comp" style="display:none">
    <div class="filters" id="comp-filters">
      <button class="pill active" data-f="all">Tous</button>
      <button class="pill" data-f="EV">Électrique</button>
      <button class="pill" data-f="PHEV">PHEV</button>
    </div>
    <div id="comp-cards"></div>
  </div>

  <div class="footer">
    Sources : xpeng.com · even-motors.com · vivacar.fr · zeekr.eu · polestar.com · byd.com · kia.com · toyota.fr · volvocars.com · omoda-jaecoo.fr · automobilepropre.com<br>
    Données collectées automatiquement chaque matin à 07h00.
  </div>

</div>

<script>
const OFFERS = {offers_json};
const COMPETITORS = {comp_json};
let mainFilter = 'all';
let compFilter = 'all';
let currentTab = 'main';

function tagClass(model, brand){{
  if(brand==='ZEEKR') return 'tag-7x';
  if(model==='G9') return 'tag-g9';
  if(model==='G6') return 'tag-g6';
  return 'tag-7x';
}}

function compTag(type){{
  return type==='PHEV' ? 'tag-phev' : 'tag-ev';
}}

function fmt(n){{ return n!=null ? n.toLocaleString('fr-FR') : '—'; }}

function renderMain(){{
  const filtered = OFFERS.filter(o => {{
    if(mainFilter==='all') return true;
    if(mainFilter==='neuf'||mainFilter==='occasion') return o.type===mainFilter;
    return o.model===mainFilter;
  }});
  const prices = filtered.filter(o=>o.price_monthly).map(o=>o.price_monthly);
  document.getElementById('s-count').textContent = filtered.length;
  document.getElementById('s-min').textContent = prices.length ? Math.min(...prices)+'€' : '—';
  document.getElementById('s-max').textContent = prices.length ? Math.max(...prices)+'€' : '—';

  document.querySelectorAll('#main-filters .pill').forEach(p=>p.classList.toggle('active',p.dataset.f===mainFilter));

  document.getElementById('main-cards').innerHTML = filtered.length ? filtered.map(o=>`
    <div class="card">
      <div class="card-top">
        <span class="model-tag ${{tagClass(o.model,o.brand)}}">${{o.brand}} ${{o.model}}</span>
        <span class="type-badge">${{o.type}}</span>
      </div>
      <div class="card-version">${{o.version}}</div>
      ${{o.price_monthly
        ? `<div class="card-price">${{o.price_monthly}} €<span>/mois</span></div>`
        : `<div class="no-price">Offre LLD non publiée</div>`}}
      <div class="card-rows">
        ${{o.duration_months?`<div class="card-row"><span class="card-row-label">Durée</span><span class="card-row-val">${{o.duration_months}} mois · ${{fmt(o.km_per_year)}} km/an</span></div>`:''}}
        ${{o.first_payment?`<div class="card-row"><span class="card-row-label">1er loyer</span><span class="card-row-val">${{fmt(o.first_payment)}} €</span></div>`:''}}
        <div class="card-row"><span class="card-row-label">Source</span><span class="card-row-val"><a class="card-link" href="${{o.source_url}}" target="_blank">${{o.source_name}} ↗</a></span></div>
      </div>
      ${{o.note?`<div class="card-note">${{o.note}}</div>`:''}}
    </div>
  `).join('') : '<div class="empty">Aucune offre pour ce filtre.</div>';
}}

function renderComp(){{
  const evs   = COMPETITORS.filter(c=>c.type==='EV'   && (compFilter==='all'||compFilter==='EV'));
  const phevs = COMPETITORS.filter(c=>c.type==='PHEV' && (compFilter==='all'||compFilter==='PHEV'));

  document.querySelectorAll('#comp-filters .pill').forEach(p=>p.classList.toggle('active',p.dataset.f===compFilter));

  let html = '';

  if(evs.length){{
    html += `<div class="section-sep">Électriques</div><div class="cards">`;
    html += evs.map(c=>`
      <div class="card">
        <div class="card-top">
          <span class="model-tag ${{compTag(c.type)}}">${{c.brand}} ${{c.model}}</span>
          <span class="type-badge">100% élec.</span>
        </div>
        ${{c.price_monthly
          ? `<div class="card-price">${{c.price_monthly}} €<span>/mois</span></div>`
          : `<div class="no-price">Prix indicatif</div>`}}
        <div class="card-rows">
          ${{c.duration_months?`<div class="card-row"><span class="card-row-label">Durée</span><span class="card-row-val">${{c.duration_months}} mois · ${{fmt(c.km_per_year)}} km/an</span></div>`:''}}
          ${{c.first_payment?`<div class="card-row"><span class="card-row-label">1er loyer</span><span class="card-row-val">${{fmt(c.first_payment)}} €</span></div>`:''}}
          <div class="card-row"><span class="card-row-label">Source</span><span class="card-row-val"><a class="card-link" href="${{c.source_url}}" target="_blank">${{c.source_name}} ↗</a></span></div>
        </div>
        ${{c.note?`<div class="card-note">${{c.note}}</div>`:''}}
      </div>
    `).join('');
    html += `</div>`;
  }}

  if(phevs.length){{
    html += `<div class="section-sep">PHEV</div><div class="cards">`;
    html += phevs.map(c=>`
      <div class="card">
        <div class="card-top">
          <span class="model-tag ${{compTag(c.type)}}">${{c.brand}} ${{c.model}}</span>
          <span class="type-badge">PHEV</span>
        </div>
        ${{c.price_monthly
          ? `<div class="card-price">${{c.price_monthly}} €<span>/mois</span></div>`
          : `<div class="no-price">Prix indicatif</div>`}}
        <div class="card-rows">
          ${{c.duration_months?`<div class="card-row"><span class="card-row-label">Durée</span><span class="card-row-val">${{c.duration_months}} mois · ${{fmt(c.km_per_year)}} km/an</span></div>`:''}}
          ${{c.first_payment?`<div class="card-row"><span class="card-row-label">1er loyer</span><span class="card-row-val">${{fmt(c.first_payment)}} €</span></div>`:''}}
          <div class="card-row"><span class="card-row-label">Source</span><span class="card-row-val"><a class="card-link" href="${{c.source_url}}" target="_blank">${{c.source_name}} ↗</a></span></div>
        </div>
        ${{c.note?`<div class="card-note">${{c.note}}</div>`:''}}
      </div>
    `).join('');
    html += `</div>`;
  }}

  if(!html) html = '<div class="empty">Aucune donnée concurrente.</div>';
  document.getElementById('comp-cards').innerHTML = html;
}}

function switchTab(tab, btn){{
  currentTab = tab;
  document.getElementById('tab-main').style.display = tab==='main' ? '' : 'none';
  document.getElementById('tab-comp').style.display = tab==='comp' ? '' : 'none';
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  btn.classList.add('active');
  if(tab==='comp') renderComp();
}}

document.getElementById('main-filters').addEventListener('click', e=>{{
  const btn=e.target.closest('.pill'); if(!btn) return;
  mainFilter=btn.dataset.f; renderMain();
}});
document.getElementById('comp-filters').addEventListener('click', e=>{{
  const btn=e.target.closest('.pill'); if(!btn) return;
  compFilter=btn.dataset.f; renderComp();
}});

renderMain();
</script>
</body>
</html>"""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--open", action="store_true")
    args = parser.parse_args()

    html = build()
    OUT.write_text(html, encoding="utf-8")
    size_kb = round(OUT.stat().st_size / 1024, 1)
    print(f"✓ Généré : {OUT}  ({size_kb} Ko)")

    if args.open:
        import webbrowser
        webbrowser.open(OUT.as_uri())

if __name__ == "__main__":
    main()
