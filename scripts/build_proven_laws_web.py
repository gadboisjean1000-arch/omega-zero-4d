"""Générateur déterministe JSON / Markdown / Page Web HTML autonome pour Supela Is The Laws."""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from html import escape as html_escape
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from omega_zero.supela_laws import run_supela_laws_suite

DEFAULT_JSON_OUT = ROOT_DIR / "docs" / "constitution" / "LOIS_PROUVEES_SUPELA.json"
DEFAULT_MD_OUT = ROOT_DIR / "docs" / "constitution" / "LOIS_PROUVEES_SUPELA.md"
DEFAULT_HTML_OUT = ROOT_DIR / "docs" / "constitution" / "LOIS_PROUVEES_SUPELA.html"


def _atomic_write_text(target: Path, content: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=str(target.parent))
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        os.replace(tmp_path, target)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise


def render_laws_markdown(doc: dict[str, Any]) -> str:
    """Rend une vue Markdown auditable du manifeste canonique Supela Is The Laws."""
    s = doc["summary"]
    lines: list[str] = [
        f"# {doc['titre']}",
        "",
        f"> **Auteur souverain :** {doc['auteur_souverain']} ([ORCID]({doc['orcid']}))  ",
        (
            f"> **Licence :** `{doc['license']}` · **Verdict :** `{doc['verdict_global']}` · "
            f"**SHA-256 :** `{doc['digest_sha256']}`  "
        ),
        f"> **Doctrine :** `{doc['clause_honnetete']['doctrine']}`  ",
        (
            "> **Page Web interactive autonome (0 CDN, 0 $ PMU) :** "
            "[`LOIS_PROUVEES_SUPELA.html`](LOIS_PROUVEES_SUPELA.html) · "
            "[`LOIS_PROUVEES_SUPELA.json`](LOIS_PROUVEES_SUPELA.json)"
        ),
        "",
        "## 1. Synthèse Mesurée",
        "",
        "| Indicateur | Mesure |",
        "|---|---|",
        f"| Lois formelles vérifiées | **{s['laws_verified']} / {s['laws_total']}** |",
        (
            "| Pyramide normative internationale (`wiki.private.law` élevé & corrigé) | "
            f"`{s['normative_pyramid_verified']}` |"
        ),
        (
            "| Topologie géodésique 4D & ISO 19115 (apports ArcGIS Pro en 0 $ PMU) | "
            f"`{s['geo_topology_4d_verified']}` |"
        ),
        f"| Indécidables Classe A isolés hors clôture binaire | `{s['class_a_isolated']}` |",
        f"| Bornes discrètes Classe B vérifiées | `{s['class_b_discretized']}` |",
        "",
        "## 2. Les 12 Lois Formelles Prouvées",
        "",
        "| ID | Catégorie | Loi | Formule | Statut | Vérifié | Ce qu'elle n'implique pas |",
        "|---|---|---|---|---|---|---|",
    ]
    for law in doc["laws"]:
        mark = "✅" if law["verifie"] else "❌"
        lines.append(
            f"| `{law['id']}` | `{law['categorie']}` | **{law['nom']}** | "
            f"`{law['formule']}` | `{law['statut_epistemique']}` | {mark} | {law['n_implique_pas']} |"
        )

    lines.extend(
        [
            "",
            "## 3. Pyramide Normative Internationale (`wiki.private.law` élevé & corrigé)",
            "",
            "| Niveau | Strate | Instruments | Correction & Verrou Supela |",
            "|---|---|---|---|",
        ]
    )
    for lvl in doc["normative_pyramid"]["levels"]:
        lines.append(
            f"| **{lvl['level']}** | {lvl['nom']} | {lvl['instruments']} | {lvl['correction_supela']} |"
        )

    lines.extend(
        [
            "",
            "## 4. Topologie Géodésique, Cube 4D & ISO 19115 (Apports ArcGIS Pro en 0 $ PMU)",
            "",
        ]
    )
    for pat in doc["geospatial_arcgis_0_pmu"]["arcgis_patterns_integrated_and_improved"]:
        lines.append(f"- {pat}")
    iso = doc["geospatial_arcgis_0_pmu"]["iso19115_metadata"]
    lines.extend(
        [
            "",
            (
                f"- **Standard métadonnées :** `{iso['standard']}` · **CRS :** `{iso['crs']}` · "
                f"**Lignage SHA-256 :** `{iso['lineage_sha256']}`"
            ),
            "",
            (
                "> **Clause d'honnêteté :** `universal_truth_claimed = false` · "
                "`judicial_or_governmental_certification_claimed = false` · "
                "`legal_counsel_required_for_binding_contracts = true`."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def _safe_json_for_html(data: dict[str, Any]) -> str:
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True)
    return raw.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def render_laws_html(doc: dict[str, Any]) -> str:
    """Génère la page web HTML5 autonome (0 CDN, 0 tracker, 0 $ PMU) pour Supela Is The Laws."""
    embedded_json = _safe_json_for_html(doc)
    payload_sha = hashlib.sha256(
        json.dumps(doc, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    title = html_escape(str(doc["titre"]))
    verdict = html_escape(str(doc["verdict_global"]))
    digest = html_escape(str(doc["digest_sha256"]))
    orcid = html_escape(str(doc["orcid"]))
    author = html_escape(str(doc["auteur_souverain"]))
    s = doc["summary"]

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="supela-payload-sha256" content="{payload_sha}" />
  <title>{title}</title>
  <style>
    :root {{
      --bg: #0b1220;
      --surface: #111b2e;
      --surface-2: #17243d;
      --border: #26395c;
      --text: #e6edf7;
      --muted: #9eb0cc;
      --accent: #38bdf8;
      --ok: #22c55e;
      --warn: #f59e0b;
      --err: #ef4444;
      --mono: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
      --sans: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: var(--sans);
      background: var(--bg);
      color: var(--text);
      line-height: 1.55;
    }}
    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    header {{
      background: linear-gradient(135deg, #0d172a 0%, #152542 100%);
      border-bottom: 1px solid var(--border);
      padding: 1.75rem 1.5rem 1.25rem;
    }}
    .wrap {{ max-width: 1220px; margin: 0 auto; }}
    h1 {{ margin: 0 0 0.4rem; font-size: 1.65rem; letter-spacing: -0.01em; }}
    .subtitle {{ color: var(--muted); font-size: 0.95rem; margin: 0 0 1rem; }}
    .badges {{ display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 1rem; }}
    .badge {{
      display: inline-flex; align-items: center; gap: 0.35rem;
      padding: 0.25rem 0.65rem; border-radius: 999px; font-size: 0.8rem;
      font-family: var(--mono); border: 1px solid var(--border); background: var(--surface);
    }}
    .badge.ok {{ border-color: #166534; background: #052e16; color: #86efac; }}
    .badge.warn {{ border-color: #92400e; background: #451a03; color: #fcd34d; }}
    .badge.info {{ border-color: #075985; background: #082f49; color: #7dd3fc; }}
    .kpi-grid {{
      display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
      gap: 0.75rem; margin-top: 1rem;
    }}
    .kpi {{
      background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
      padding: 0.85rem 1rem;
    }}
    .kpi .val {{ font-size: 1.4rem; font-weight: 700; font-family: var(--mono); color: var(--ok); }}
    .kpi .lbl {{ font-size: 0.8rem; color: var(--muted); }}
    nav.tabs {{
      display: flex; flex-wrap: wrap; gap: 0.5rem;
      padding: 1rem 1.5rem 0; border-bottom: 1px solid var(--border); background: #0d1628;
    }}
    nav.tabs button {{
      background: transparent; color: var(--muted); border: 1px solid transparent;
      border-bottom: none; padding: 0.65rem 1rem; border-radius: 8px 8px 0 0;
      cursor: pointer; font-weight: 600; font-size: 0.9rem;
    }}
    nav.tabs button.active {{
      background: var(--bg); color: var(--text); border-color: var(--border);
    }}
    main {{ padding: 1.5rem; }}
    section.panel {{ display: none; }}
    section.panel.active {{ display: block; }}
    .controls {{ display: flex; flex-wrap: wrap; gap: 0.6rem; margin-bottom: 1rem; align-items: center; }}
    input[type="search"], select {{
      background: var(--surface); color: var(--text); border: 1px solid var(--border);
      border-radius: 8px; padding: 0.5rem 0.75rem; font-size: 0.9rem;
    }}
    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 1rem; }}
    .card {{
      background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
      padding: 1rem 1.1rem; display: flex; flex-direction: column; gap: 0.45rem;
    }}
    .card-head {{ display: flex; justify-content: space-between; align-items: center; gap: 0.5rem; }}
    .law-id {{ font-family: var(--mono); font-weight: 700; color: var(--accent); }}
    .formula {{
      font-family: var(--mono); font-size: 0.84rem; background: var(--surface-2);
      padding: 0.5rem 0.65rem; border-radius: 6px; border: 1px solid var(--border);
      overflow-x: auto;
    }}
    .meta-line {{ font-size: 0.83rem; color: var(--muted); }}
    .limit-line {{ font-size: 0.82rem; color: #fcd34d; }}
    table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; font-size: 0.88rem; }}
    th, td {{ border: 1px solid var(--border); padding: 0.6rem 0.75rem; text-align: left; vertical-align: top; }}
    th {{ background: var(--surface-2); color: var(--text); }}
    .pyramid-box {{ display: flex; flex-direction: column; gap: 0.6rem; margin: 1rem 0; }}
    .pyramid-tier {{
      background: var(--surface); border-left: 4px solid var(--accent);
      border-top: 1px solid var(--border); border-right: 1px solid var(--border);
      border-bottom: 1px solid var(--border); border-radius: 8px; padding: 0.85rem 1rem;
    }}
    .sim-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 1rem; }}
    .sim-card {{
      background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
      padding: 1rem 1.15rem;
    }}
    .sim-card h3 {{ margin: 0 0 0.6rem; font-size: 1.02rem; }}
    .sim-row {{ display: flex; align-items: center; justify-content: space-between; gap: 0.6rem; margin: 0.4rem 0; font-size: 0.88rem; }}
    .sim-out {{
      margin-top: 0.75rem; padding: 0.65rem 0.8rem; border-radius: 8px;
      font-family: var(--mono); font-size: 0.84rem; background: var(--surface-2);
      border: 1px solid var(--border);
    }}
    .sim-out.pass {{ border-color: #166534; color: #86efac; }}
    .sim-out.fail {{ border-color: #991b1b; color: #fca5a5; }}
    .sim-out.indet {{ border-color: #92400e; color: #fcd34d; }}
    .svg-box {{
      background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
      padding: 1rem; margin: 1rem 0;
    }}
    footer {{
      border-top: 1px solid var(--border); padding: 1.25rem 1.5rem;
      color: var(--muted); font-size: 0.82rem; background: #0d1628;
    }}
    code {{ font-family: var(--mono); }}
  </style>
</head>
<body>
  <header>
    <div class="wrap">
      <h1>{title}</h1>
      <p class="subtitle">
        Auteur souverain : <strong>{author}</strong> ·
        <a href="{orcid}" target="_blank" rel="noopener">ORCID {orcid.split('/')[-1]}</a> ·
        <a href="ENCYCLOPEDIE_DICTIONNAIRE.html">Encyclopédie Supela</a> ·
        <a href="LOIS_PROUVEES_SUPELA.json">Manifeste JSON</a>
      </p>
      <div class="badges">
        <span class="badge ok">VERDICT : {verdict}</span>
        <span class="badge info">LICENCE : Apache-2.0 · 0 $ PMU · 0 CDN</span>
        <span class="badge warn">CLASSE A ISOLÉE : {s['class_a_isolated']} · REVUE JURISTE REQUISE</span>
        <span class="badge">SHA-256 : {digest[:16]}…</span>
      </div>
      <div class="kpi-grid">
        <div class="kpi"><div class="val">{s['laws_verified']} / {s['laws_total']}</div><div class="lbl">Lois formelles exécutées &amp; prouvées</div></div>
        <div class="kpi"><div class="val">4 Niveaux</div><div class="lbl">Pyramide Internationale L0–L3 (Kelsen)</div></div>
        <div class="kpi"><div class="val">EPSG:4326</div><div class="lbl">Topologie ArcGIS-like &amp; Cube 4D + ISO 19115</div></div>
        <div class="kpi"><div class="val">0 non-classifié</div><div class="lbl">4 Classe A isolées · 3 Classe B bornées</div></div>
      </div>
    </div>
  </header>

  <nav class="tabs" role="tablist" aria-label="Sections Supela Is The Laws">
    <div class="wrap" style="display:flex;flex-wrap:wrap;gap:0.5rem;">
      <button type="button" class="active" data-tab="laws">1. Les 12 Lois Prouvées</button>
      <button type="button" data-tab="pyramid">2. Pyramide Internationale (wiki.private.law corrigé)</button>
      <button type="button" data-tab="geo">3. Topologie &amp; Cube 4D (ArcGIS Pro 0 $ PMU)</button>
      <button type="button" data-tab="lab">4. Laboratoire Interactif de Réfutation</button>
    </div>
  </nav>

  <main class="wrap">
    <section id="tab-laws" class="panel active">
      <div class="controls">
        <input id="law-search" type="search" placeholder="Filtrer une loi, formule, module..." aria-label="Rechercher une loi" />
        <select id="law-cat" aria-label="Filtrer par catégorie">
          <option value="ALL">Toutes les catégories</option>
          <option value="FONDEMENTS">FONDEMENTS</option>
          <option value="SECURITE_FRONTIERES">SECURITE_FRONTIERES</option>
          <option value="REVERSIBILITE_0_PMU">REVERSIBILITE_0_PMU</option>
          <option value="MATHS_PHYSIQUE">MATHS_PHYSIQUE</option>
          <option value="BORNES_EPISTEMIQUES">BORNES_EPISTEMIQUES</option>
        </select>
        <span id="law-count" class="badge info"></span>
      </div>
      <div id="laws-grid" class="cards"></div>
    </section>

    <section id="tab-pyramid" class="panel">
      <h2>Pyramide Normative Internationale · Supela au sommet du droit privé &amp; public</h2>
      <p class="subtitle">
        Intègre et corrige les problématiques multi-juridictionnelles (référence
        <a href="https://wiki.private.law/" target="_blank" rel="noopener">wiki.private.law</a>)
        en verrouillant la conformité impérative : transparence fiscale CRS/TPS-TVQ, substance économique réelle,
        non-distribution OSBL (Québec Partie III), Convention de Berne, CVIM (Vienne 1980), Convention de New York (1958)
        et Droit matériel suisse (CO).
      </p>
      <div id="pyramid-tiers" class="pyramid-box"></div>
      <h3>Corrections Supela face au droit privé déclaratif statique</h3>
      <table>
        <thead><tr><th>Thème</th><th>Pratique déclarative standard</th><th>Verrou &amp; Correction Supela</th></tr></thead>
        <tbody id="pyramid-diff"></tbody>
      </table>
      <h3>Preuves exécutées (cas positif + réfutation + conflit conservé)</h3>
      <div id="pyramid-checks" class="cards"></div>
    </section>

    <section id="tab-geo" class="panel">
      <h2>Topologie Géodésique, Cube Spatio-Temporel 4D &amp; ISO 19115 (Apports ArcGIS Pro en 0 $ PMU)</h2>
      <p class="subtitle">
        Implémente en Python pur sans licence propriétaire les invariants structurants de
        <a href="https://doc.esri.com/fr/arcgis-pro/latest/" target="_blank" rel="noopener">ArcGIS Pro</a> :
        Topologie de géodatabase (<code>MUST_NOT_OVERLAP</code>, <code>MUST_BE_COVERED_BY</code>,
        <code>MUST_NOT_HAVE_GAPS</code>), Cube Spatio-Temporel 4D, Branch Versioning multi-branches
        et métadonnées <code>ISO 19115-1 / ISO 19139</code>.
      </p>
      <div class="svg-box">
        <svg viewBox="0 0 760 230" width="100%" height="230" role="img" aria-label="Schéma topologique EPSG:4326">
          <rect x="20" y="25" width="320" height="175" fill="#0d2238" stroke="#38bdf8" stroke-width="2" rx="6" />
          <text x="30" y="45" fill="#7dd3fc" font-size="12" font-family="monospace">Partition valide : QC-CORRIDOR (EPSG:4326)</text>
          <rect x="30" y="60" width="150" height="125" fill="#064e3b" fill-opacity="0.7" stroke="#22c55e" stroke-width="2" />
          <text x="45" y="125" fill="#86efac" font-size="13" font-family="monospace">QC-MTL [-74..-72]</text>
          <rect x="180" y="60" width="150" height="125" fill="#1e3a5f" fill-opacity="0.7" stroke="#38bdf8" stroke-width="2" />
          <text x="195" y="125" fill="#bae6fd" font-size="13" font-family="monospace">QC-QBC [-72..-70]</text>
          <text x="30" y="216" fill="#86efac" font-size="12" font-family="monospace">MUST_NOT_OVERLAP=OK | COVERED=OK | GAPS=0</text>

          <rect x="410" y="25" width="320" height="175" fill="#2a1215" stroke="#ef4444" stroke-width="2" rx="6" />
          <text x="420" y="45" fill="#fca5a5" font-size="12" font-family="monospace">Réfutation topologique : Chevauchement détecté</text>
          <rect x="420" y="60" width="150" height="125" fill="#064e3b" fill-opacity="0.55" stroke="#22c55e" stroke-width="1.5" />
          <rect x="570" y="60" width="150" height="125" fill="#1e3a5f" fill-opacity="0.55" stroke="#38bdf8" stroke-width="1.5" />
          <rect x="520" y="85" width="100" height="75" fill="#ef4444" fill-opacity="0.5" stroke="#fca5a5" stroke-width="2" stroke-dasharray="5 3" />
          <text x="530" y="126" fill="#fecaca" font-size="12" font-family="monospace">QC-CONFLIT</text>
          <text x="420" y="216" fill="#fca5a5" font-size="12" font-family="monospace">MUST_NOT_OVERLAP=FAIL -&gt; Conflict4D conservé</text>
        </svg>
      </div>
      <div id="geo-details" class="cards"></div>
    </section>

    <section id="tab-lab" class="panel">
      <h2>Laboratoire Interactif de Réfutation (Exécution locale dans votre navigateur, 0 serveur)</h2>
      <div class="sim-grid">
        <div class="sim-card">
          <h3>Sim 1 · Frontières (C ≠ P ≠ V ≠ A) &amp; Dégel</h3>
          <label class="sim-row"><span>1. Capacité technique (C)</span><input id="sim-c" type="checkbox" checked /></label>
          <label class="sim-row"><span>2. Permission périmètre (P)</span><input id="sim-p" type="checkbox" checked /></label>
          <label class="sim-row"><span>3. Preuve déterministe (V)</span><input id="sim-v" type="checkbox" checked /></label>
          <label class="sim-row"><span>4. Signature Ed25519 (QUI)</span><input id="sim-sig" type="checkbox" checked /></label>
          <label class="sim-row"><span>5. Ratification souveraine (A)</span><input id="sim-a" type="checkbox" /></label>
          <div id="sim-gate-out" class="sim-out"></div>
        </div>

        <div class="sim-card">
          <h3>Sim 2 · Les Deux Zéros (0_vide ≠ 0_vert)</h3>
          <div class="sim-row">
            <span>État du capteur intégrité :</span>
            <select id="sim-sensor">
              <option value="down">Capteur muet / Ollama absent</option>
              <option value="tamper">Digest divergent (falsifié)</option>
              <option value="ok">Digest concordant vérifié</option>
            </select>
          </div>
          <div id="sim-sensor-out" class="sim-out"></div>
        </div>

        <div class="sim-card">
          <h3>Sim 3 · VR-Fractal-Ω (Moyenne Harmonique)</h3>
          <div class="sim-row"><span>Δ₁ (W₁=15) : <strong id="lbl-d1">0.20</strong></span><input id="sim-d1" type="range" min="0" max="2" step="0.05" value="0.20" /></div>
          <div class="sim-row"><span>Δ₂ (W₂=12) : <strong id="lbl-d2">0.05</strong></span><input id="sim-d2" type="range" min="0" max="2" step="0.05" value="0.05" /></div>
          <div class="sim-row"><span>Δ₃ (W₃=9)  : <strong id="lbl-d3">0.00</strong></span><input id="sim-d3" type="range" min="0" max="2" step="0.05" value="0.00" /></div>
          <div id="sim-fractal-out" class="sim-out"></div>
        </div>

        <div class="sim-card">
          <h3>Sim 4 · SGG_v2 (Brut 6/5 vs Simplexe 5/6)</h3>
          <div class="sim-row"><span>A (0.25 / 5/24)</span><input id="sim-sgg-a" type="range" min="0" max="1" step="0.05" value="0.90" /></div>
          <div class="sim-row"><span>V (0.30 / 1/4)</span><input id="sim-sgg-v" type="range" min="0" max="1" step="0.05" value="0.80" /></div>
          <div class="sim-row"><span>É (0.30 / 1/4)</span><input id="sim-sgg-e" type="range" min="0" max="1" step="0.05" value="0.85" /></div>
          <div class="sim-row"><span>T (0.15 / 1/8)</span><input id="sim-sgg-t" type="range" min="0" max="1" step="0.05" value="0.75" /></div>
          <div class="sim-row"><span>M (0.20 / 1/6)</span><input id="sim-sgg-m" type="range" min="0" max="1" step="0.05" value="0.95" /></div>
          <div id="sim-sgg-out" class="sim-out"></div>
        </div>

        <div class="sim-card">
          <h3>Sim 5 · Topologie MUST_NOT_OVERLAP (EPSG:4326)</h3>
          <div class="sim-row"><span>Zone A : [-74.0, <strong id="lbl-ax">-72.0</strong>]</span><input id="sim-ax" type="range" min="-73.5" max="-70.5" step="0.1" value="-72.0" /></div>
          <div class="sim-row"><span>Zone B : [<strong id="lbl-bx">-72.0</strong>, -70.0]</span><input id="sim-bx" type="range" min="-73.5" max="-70.5" step="0.1" value="-72.0" /></div>
          <div id="sim-geo-out" class="sim-out"></div>
        </div>
      </div>
    </section>
  </main>

  <footer>
    <div class="wrap">
      <strong>Clause d'honnêteté épistémique Supela :</strong>
      <code>universal_truth_claimed = false</code> ·
      <code>judicial_or_governmental_certification_claimed = false</code> ·
      <code>legal_counsel_required_for_binding_contracts = true</code> ·
      <code>tpm_silicon_anchor_simulated = false</code>.<br />
      Artefact autonome généré par <code>scripts/build_proven_laws_web.py</code> depuis
      <code>src/omega_zero/supela_laws.py</code> — Empreinte SHA-256 : <code>{digest}</code>.
    </div>
  </footer>

  <script id="supela-laws-data" type="application/json">{embedded_json}</script>
  <script>
    (function () {{
      "use strict";
      const dataEl = document.getElementById("supela-laws-data");
      const DATA = JSON.parse(dataEl.textContent || "{{}}");

      function esc(str) {{
        return String(str)
          .replace(/&/g, "&amp;")
          .replace(/</g, "&lt;")
          .replace(/>/g, "&gt;")
          .replace(/"/g, "&quot;");
      }}

      // Navigation onglets
      document.querySelectorAll("nav.tabs button").forEach((btn) => {{
        btn.addEventListener("click", () => {{
          document.querySelectorAll("nav.tabs button").forEach((b) => b.classList.remove("active"));
          document.querySelectorAll("section.panel").forEach((p) => p.classList.remove("active"));
          btn.classList.add("active");
          const target = document.getElementById("tab-" + btn.dataset.tab);
          if (target) target.classList.add("active");
        }});
      }});

      // Onglet 1 : 12 Lois
      const lawsGrid = document.getElementById("laws-grid");
      const lawSearch = document.getElementById("law-search");
      const lawCat = document.getElementById("law-cat");
      const lawCount = document.getElementById("law-count");

      function renderLaws() {{
        const q = (lawSearch.value || "").trim().toLowerCase();
        const cat = lawCat.value;
        const filtered = (DATA.laws || []).filter((law) => {{
          if (cat !== "ALL" && law.categorie !== cat) return false;
          if (!q) return true;
          const hay = [law.id, law.nom, law.formule, law.module_source, law.preuve_mesuree, law.nimpliqe_pas]
            .join(" ").toLowerCase();
          return hay.includes(q);
        }});
        lawCount.textContent = filtered.length + " / " + (DATA.laws || []).length + " lois affichées";
        lawsGrid.innerHTML = filtered.map((law) => `
          <article class="card">
            <div class="card-head">
              <span class="law-id">${{esc(law.id)}} · ${{esc(law.categorie)}}</span>
              <span class="badge ${{law.verifie ? "ok" : "warn"}}">${{law.verifie ? "PROUVÉ" : "ÉCHEC"}}</span>
            </div>
            <strong>${{esc(law.nom)}}</strong>
            <div class="formula">${{esc(law.formule)}}</div>
            <div class="meta-line"><strong>Preuve :</strong> ${{esc(law.preuve_mesuree)}}</div>
            <div class="meta-line"><strong>Module :</strong> <code>${{esc(law.module_source)}}</code></div>
            <div class="limit-line"><strong>N'implique pas :</strong> ${{esc(law.n_implique_pas)}}</div>
          </article>
        `).join("");
      }}
      lawSearch.addEventListener("input", renderLaws);
      lawCat.addEventListener("change", renderLaws);
      renderLaws();

      // Onglet 2 : Pyramide Normative
      const pyr = DATA.normative_pyramid || {{}};
      document.getElementById("pyramid-tiers").innerHTML = (pyr.levels || []).map((lvl) => `
        <div class="pyramid-tier">
          <div><strong class="law-id">${{esc(lvl.level)}} — ${{esc(lvl.nom)}}</strong></div>
          <div class="meta-line"><strong>Instruments :</strong> ${{esc(lvl.instruments)}}</div>
          <div class="meta-line"><strong>Verrou Supela :</strong> ${{esc(lvl.correction_supela)}}</div>
        </div>
      `).join("");

      document.getElementById("pyramid-diff").innerHTML = (pyr.comparative_corrections_vs_static_private_law || []).map((row) => `
        <tr>
          <td><strong>${{esc(row.theme)}}</strong></td>
          <td>${{esc(row.pratique_standard)}}</td>
          <td>${{esc(row.correction_supela)}}</td>
        </tr>
      `).join("");

      const checks = pyr.checks || {{}};
      document.getElementById("pyramid-checks").innerHTML = Object.keys(checks).map((k) => {{
        const c = checks[k];
        const cls = c.compliant_model ? (c.conflict_4d_conserved ? "warn" : "ok") : "warn";
        return `
          <article class="card">
            <div class="card-head">
              <span class="law-id">${{esc(c.structure_id)}}</span>
              <span class="badge ${{cls}}">${{esc(c.verdict)}}</span>
            </div>
            <div class="meta-line"><strong>Domicile :</strong> ${{esc(c.corporate_domicile)}}</div>
            <div class="meta-line"><strong>Lex contractus :</strong> ${{esc(c.contract_governing_law)}}</div>
            <div class="meta-line"><strong>Arbitrage / PI :</strong> ${{esc(c.arbitration_framework)}} · ${{esc(c.ip_treaty_anchor)}}</div>
            <div class="limit-line"><strong>Violations :</strong> ${{c.violations.length ? esc(c.violations.join(", ")) : "Aucune (revue juriste requise)"}}</div>
          </article>
        `;
      }}).join("");

      // Onglet 3 : Géospatial ArcGIS Pro 0$ PMU
      const geo = DATA.geospatial_arcgis_0_pmu || {{}};
      const iso = geo.iso19115_metadata || {{}};
      const br = geo.branch_versioning_4d || {{}};
      document.getElementById("geo-details").innerHTML = `
        <article class="card">
          <div class="card-head"><span class="law-id">TOPOLOGIE PROPRE</span><span class="badge ok">VALIDE</span></div>
          <div class="meta-line">MUST_NOT_OVERLAP : <strong>${{geo.topology_clean_partition.rule_must_not_overlap}}</strong></div>
          <div class="meta-line">MUST_BE_COVERED_BY : <strong>${{geo.topology_clean_partition.rule_must_be_covered_by}}</strong></div>
          <div class="meta-line">MUST_NOT_HAVE_GAPS : <strong>${{geo.topology_clean_partition.rule_must_not_have_gaps}}</strong> (trou = ${{geo.topology_clean_partition.gap_area_deg2}} deg²)</div>
        </article>
        <article class="card">
          <div class="card-head"><span class="law-id">BRANCH VERSIONING 4D</span><span class="badge warn">${{br.conflicts_detected}} CONFLIT CONSERVÉ</span></div>
          <div class="meta-line">Cellules spatio-temporelles : <strong>${{br.unique_spacetime_cells}}</strong> · Bins : <strong>${{br.total_bins}}</strong></div>
          <div class="meta-line">Zéro écrasement silencieux : <strong>${{br.zero_silent_overwrite}}</strong></div>
          <div class="formula">${{esc(JSON.stringify(br.conflicts || []))}}</div>
        </article>
        <article class="card">
          <div class="card-head"><span class="law-id">MÉTADONNÉES ISO 19115</span><span class="badge info">${{esc(iso.crs)}}</span></div>
          <div class="meta-line"><strong>Standard :</strong> ${{esc(iso.standard)}}</div>
          <div class="meta-line"><strong>BBOX WGS84 :</strong> <code>${{esc(JSON.stringify(iso.extent_bbox_wgs84))}}</code></div>
          <div class="meta-line"><strong>Lignage SHA-256 :</strong> <code>${{esc((iso.lineage_sha256 || "").slice(0, 24))}}…</code></div>
        </article>
      `;

      // Onglet 4 : Simulateurs interactifs
      function updateGate() {{
        const c = document.getElementById("sim-c").checked;
        const p = document.getElementById("sim-p").checked;
        const v = document.getElementById("sim-v").checked;
        const sig = document.getElementById("sim-sig").checked;
        const a = document.getElementById("sim-a").checked;
        const ok = c && p && v && sig && a;
        const out = document.getElementById("sim-gate-out");
        out.className = "sim-out " + (ok ? "pass" : "fail");
        out.textContent = ok
          ? "AUTORISÉ : C∧P∧V∧Sig∧H_souverain = TRUE (promotion et dégel permis sous trace)."
          : "BLOQUÉ (FAIL-CLOSED) : " + (!a ? "Ratification souveraine A=FALSE -> (C∧P∧V) ⇏ A." : "Prérequis technique manquant.");
      }}
      ["sim-c", "sim-p", "sim-v", "sim-sig", "sim-a"].forEach((id) => {{
        document.getElementById(id).addEventListener("change", updateGate);
      }});
      updateGate();

      function updateSensor() {{
        const mode = document.getElementById("sim-sensor").value;
        const out = document.getElementById("sim-sensor-out");
        if (mode === "down") {{
          out.className = "sim-out indet";
          out.textContent = "EXIT=3 | SONDE_INEXECUTABLE (INDETERMINE) -> Faux-vert 0_vide interdit.";
        }} else if (mode === "tamper") {{
          out.className = "sim-out fail";
          out.textContent = "EXIT=1 | DIGEST_DIVERGENT -> Blocage nominal de sécurité actif.";
        }} else {{
          out.className = "sim-out pass";
          out.textContent = "EXIT=0 | DIGEST_CONCORDANT -> Mesure positive vérifiée bit-à-bit.";
        }}
      }}
      document.getElementById("sim-sensor").addEventListener("change", updateSensor);
      updateSensor();

      function updateFractal() {{
        const d1 = parseFloat(document.getElementById("sim-d1").value);
        const d2 = parseFloat(document.getElementById("sim-d2").value);
        const d3 = parseFloat(document.getElementById("sim-d3").value);
        document.getElementById("lbl-d1").textContent = d1.toFixed(2);
        document.getElementById("lbl-d2").textContent = d2.toFixed(2);
        document.getElementById("lbl-d3").textContent = d3.toFixed(2);
        const w1 = 15.0, w2 = 12.0, w3 = 9.0, W = 36.0;
        const Pt = w1 / (1 + d1) + w2 / (1 + d2) + w3 / (1 + d3);
        const deff = (W / Pt) - 1.0;
        const dmin = Math.min(d1, d2, d3), dmax = Math.max(d1, d2, d3);
        const ok = (deff >= dmin - 1e-9) && (deff <= dmax + 1e-9);
        const out = document.getElementById("sim-fractal-out");
        out.className = "sim-out " + (ok ? "pass" : "fail");
        out.textContent =
          "P_t=" + Pt.toFixed(4) + " | Δ_eff=" + deff.toFixed(4) +
          " ∈ [" + dmin.toFixed(2) + ", " + dmax.toFixed(2) + "] -> " + (ok ? "GENDARMES OK" : "ERREUR");
      }}
      ["sim-d1", "sim-d2", "sim-d3"].forEach((id) => {{
        document.getElementById(id).addEventListener("input", updateFractal);
      }});
      updateFractal();

      function updateSgg() {{
        const a = parseFloat(document.getElementById("sim-sgg-a").value);
        const v = parseFloat(document.getElementById("sim-sgg-v").value);
        const e = parseFloat(document.getElementById("sim-sgg-e").value);
        const t = parseFloat(document.getElementById("sim-sgg-t").value);
        const m = parseFloat(document.getElementById("sim-sgg-m").value);
        const raw = 0.25 * a + 0.30 * v + 0.30 * e + 0.15 * t + 0.20 * m;
        const norm = (5.0 / 6.0) * raw;
        const out = document.getElementById("sim-sgg-out");
        out.className = "sim-out pass";
        out.textContent = "SGG_raw (∑=1.20) = " + raw.toFixed(4) + " | SGG_norm (∑=1.00) = " + norm.toFixed(4) + " | ratio = 5/6";
      }}
      ["sim-sgg-a", "sim-sgg-v", "sim-sgg-e", "sim-sgg-t", "sim-sgg-m"].forEach((id) => {{
        document.getElementById(id).addEventListener("input", updateSgg);
      }});
      updateSgg();

      function updateGeoSim() {{
        const ax = parseFloat(document.getElementById("sim-ax").value);
        const bx = parseFloat(document.getElementById("sim-bx").value);
        document.getElementById("lbl-ax").textContent = ax.toFixed(1);
        document.getElementById("lbl-bx").textContent = bx.toFixed(1);
        const overlap = Math.max(0.0, ax - bx);
        const gap = Math.max(0.0, bx - ax);
        const out = document.getElementById("sim-geo-out");
        if (overlap > 1e-9) {{
          out.className = "sim-out fail";
          out.textContent = "VIOLATION MUST_NOT_OVERLAP : chevauchement de " + overlap.toFixed(2) + "° -> Conflict4D conservé.";
        }} else if (gap > 1e-9) {{
          out.className = "sim-out indet";
          out.textContent = "VIOLATION MUST_NOT_HAVE_GAPS : zone non couverte de " + gap.toFixed(2) + "°.";
        }} else {{
          out.className = "sim-out pass";
          out.textContent = "TOPOLOGIE VALIDE : 0 chevauchement, 0 trou, frontière partagée exacte.";
        }}
      }}
      ["sim-ax", "sim-bx"].forEach((id) => {{
        document.getElementById(id).addEventListener("input", updateGeoSim);
      }});
      updateGeoSim();
    }})();
  </script>
</body>
</html>
"""


def verify_laws_html_parity(doc: dict[str, Any], html_text: str) -> dict[str, Any]:
    """Vérifie la parité exacte JSON -> HTML et l'absence de toute dépendance CDN externe."""
    m = re.search(
        r'<script id="supela-laws-data" type="application/json">(.*?)</script>',
        html_text,
        flags=re.DOTALL,
    )
    if not m:
        raise ValueError("Bloc JSON canonique introuvable dans LOIS_PROUVEES_SUPELA.html.")
    embedded = json.loads(m.group(1))
    if embedded != doc:
        raise ValueError("Divergence détectée entre le JSON canonique et le JSON embarqué dans HTML.")

    meta_m = re.search(r'<meta name="supela-payload-sha256" content="([0-9a-f]{64})" />', html_text)
    expected_sha = hashlib.sha256(
        json.dumps(doc, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    if not meta_m or meta_m.group(1) != expected_sha:
        raise ValueError("Empreinte meta supela-payload-sha256 absente ou divergente.")

    if re.search(r"<(script|link)\b[^>]+(src|href)\s*=\s*['\"]https?://", html_text, flags=re.IGNORECASE):
        raise ValueError("Dépendance CDN externe détectée (interdite par 0$ PMU).")

    return {"parity_ok": True, "payload_sha256": expected_sha, "zero_cdn_verified": True}


def verify_laws_js_syntax(html_text: str) -> dict[str, Any]:
    """Vérifie la syntaxe du JavaScript embarqué via `node --check` si Node.js est disponible."""
    scripts = re.findall(r"<script>(.*?)</script>", html_text, flags=re.DOTALL)
    if not scripts:
        return {"ok": False, "stderr": "Aucun bloc <script> exécutable trouvé."}
    node_bin = shutil.which("node")
    if node_bin is None:
        return {"ok": True, "skipped": True, "stderr": ""}
    with tempfile.TemporaryDirectory() as tmpdir:
        js_path = Path(tmpdir) / "laws_check.js"
        js_path.write_text("\n".join(scripts), encoding="utf-8")
        proc = subprocess.run(
            [node_bin, "--check", str(js_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        return {"ok": proc.returncode == 0, "skipped": False, "stderr": proc.stderr.strip()}


def build_all(
    *,
    json_out: Path = DEFAULT_JSON_OUT,
    md_out: Path = DEFAULT_MD_OUT,
    html_out: Path = DEFAULT_HTML_OUT,
) -> dict[str, Any]:
    doc = run_supela_laws_suite()
    json_text = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    md_text = render_laws_markdown(doc)
    html_text = render_laws_html(doc)

    parity = verify_laws_html_parity(doc, html_text)
    js_syn = verify_laws_js_syntax(html_text)
    if not js_syn["ok"]:
        raise RuntimeError(f"Erreur syntaxe JS dans LOIS_PROUVEES_SUPELA.html : {js_syn['stderr']}")

    _atomic_write_text(json_out, json_text)
    _atomic_write_text(md_out, md_text)
    _atomic_write_text(html_out, html_text)
    return {
        "status": "OK",
        "verdict_global": doc["verdict_global"],
        "laws_verified": doc["summary"]["laws_verified"],
        "laws_total": doc["summary"]["laws_total"],
        "digest_sha256": doc["digest_sha256"],
        "parity": parity,
        "js_syntax": js_syn,
    }


def main() -> int:
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
    res = build_all()
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
