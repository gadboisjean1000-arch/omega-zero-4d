from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, ValidationError

from omega_zero.models import canonical_sha256
from scripts.build_encyclopedie import (
    UNIVERSAL_FICHE_KEYS,
    anonymize_local_inventory,
    load_provenance_m365_registry,
    merge_local_inventory,
    parse_simple_yaml_fiche,
    render_html,
    render_markdown,
    render_provenance_markdown,
    scan_repo_tree,
    validate_provenance_m365_registry,
    verify_html_js_syntax,
    verify_html_parity,
)
from scripts.verify_a12 import verify_a12

ROOT_DIR = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT_DIR / "schemas" / "supela_encyclopedie_1.schema.json"
CONTRADICTIONS_SCHEMA_PATH = ROOT_DIR / "schemas" / "supela_contradictions_1.schema.json"
PROVENANCE_SCHEMA_PATH = ROOT_DIR / "schemas" / "supela_provenance_m365_1.schema.json"
REGISTRY_PATH = ROOT_DIR / "docs" / "constitution" / "supela-dictionnaire-encyclopedie-1.json"
CONTRADICTIONS_PATH = ROOT_DIR / "docs" / "constitution" / "REGISTRE_CONTRADICTIONS.json"
CONTRADICTIONS_MD_PATH = ROOT_DIR / "docs" / "constitution" / "REGISTRE_CONTRADICTIONS.md"
PROVENANCE_PATH = ROOT_DIR / "docs" / "constitution" / "REGISTRE_PROVENANCE_M365.json"
PROVENANCE_MD_PATH = ROOT_DIR / "docs" / "constitution" / "REGISTRE_PROVENANCE_M365.md"
FORMULAS_MD_PATH = ROOT_DIR / "docs" / "constitution" / "REGISTRE_FORMULES_SUPELA.md"
FICHES_DIR = ROOT_DIR / "docs" / "constitution" / "fiches"
MD_PATH = ROOT_DIR / "docs" / "constitution" / "ENCYCLOPEDIE_DICTIONNAIRE.md"
HTML_PATH = ROOT_DIR / "docs" / "constitution" / "ENCYCLOPEDIE_DICTIONNAIRE.html"
PS_COLLECTOR_PATH = ROOT_DIR / "scripts" / "collect_local_encyclopedie.ps1"


def _load_json(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


def test_encyclopedie_validates_against_draft_2020_12_and_honest_perimeter() -> None:
    schema = _load_json(SCHEMA_PATH)
    doc = _load_json(REGISTRY_PATH)

    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(doc)

    # Barrière épistémique M3 : sans scan local Windows, aucun disque C:/D: ne peut être proclamé complet
    assert doc["schema"] == "supela-dictionnaire-encyclopedie/1"
    assert doc["local_pc_scan"] == "NON_EXECUTEE"
    assert doc["verdict_couverture"] == "OUVERT_INCOMPLET_C_D_IA_LOCALES"
    assert doc["perimetre"]["statut_global"] == "PARTIEL_VERIFIE_DISTANT"
    assert doc["collecteur_local"]["dernier_import_local"] is None

    disks = {d["lecteur"]: d for d in doc["encyclopedie"]["disques_locaux_windows"]}
    assert set(disks.keys()) == {"C:\\", "D:\\"}
    assert disks["C:\\"]["perimetre_statut"] == "INACCESSIBLE_DANS_LE_PÉRIMÈTRE"
    assert disks["D:\\"]["perimetre_statut"] == "INACCESSIBLE_DANS_LE_PÉRIMÈTRE"
    assert disks["C:\\"]["elements_indexes"] == []
    assert disks["D:\\"]["elements_indexes"] == []


def test_encyclopedie_completeness_counts_and_determinism() -> None:
    doc = _load_json(REGISTRY_PATH)
    stats = doc["statistiques"]
    dictionnaire = doc["dictionnaire"]
    enc = doc["encyclopedie"]

    assert stats["termes_dictionnaire"] == len(dictionnaire) == 62
    assert stats["depots_github_total"] == len(enc["github_depots"]) == 15
    assert stats["depots_github_originaux"] == 4
    assert stats["depots_github_forks"] == 11
    assert stats["discussions_ia_google_docs"] == len(enc["discussions_ia_google_docs"]) >= 54
    assert stats["plateformes_ia_navigateurs"] == len(enc["plateformes_ia_et_navigateurs"]) >= 9
    assert stats["fichiers_omega_zero_4d"] == len(enc["omega_zero_4d_arborescence"])
    assert stats["formules_normalisees"] == len(doc["registre_formules"]) == 25
    assert stats["fiches_yaml_initiales"] == 25
    assert stats["contradictions_conservees"] == doc["registre_contradictions_ref"]["nombre_contradictions"] == 7
    assert stats["sources_m365_candidates"] == doc["registre_provenance_m365_ref"]["sources_m365_candidates"] == 16
    assert doc["registre_provenance_m365_ref"]["politique_locale_defaut"] == "LOCAL_UNIQUEMENT_PAR_DEFAUT"
    assert doc["registre_provenance_m365_ref"]["effacement_interdit"] is True

    # Toutes les catégories du dictionnaire doivent être peuplées et les IDs uniques
    dict_ids = [item["id"] for item in dictionnaire]
    assert len(dict_ids) == len(set(dict_ids))
    categories = {item["categorie"] for item in dictionnaire}
    assert categories == {
        "PROJECTION_PI0",
        "MANQUE_ET_STATUTS",
        "ESCALADE_4D",
        "GDS_ET_SCT",
        "SECURITE_WORM_CRYPTO",
        "IA_ET_GRPO",
        "ECOSYSTEME_OUTILS_IA",
        "GOUVERNANCE_ET_NORMES",
    }

    # Tous les dépôts originaux et forks clés sont présents
    repos = {r["name_with_owner"]: r for r in enc["github_depots"]}
    for required_repo in (
        "gadboisjean1000-arch/omega-zero-4d",
        "gadboisjean1000-arch/Supela-K3-Omega",
        "gadboisjean1000-arch/sevengate-store",
        "gadboisjean1000-arch/utilise",
        "gadboisjean1000-arch/kilocode",
        "gadboisjean1000-arch/cline",
        "gadboisjean1000-arch/git",
    ):
        assert required_repo in repos

    # Toutes les plateformes IA / navigateurs nommées sont suivies
    plats = {p["id"] for p in enc["plateformes_ia_et_navigateurs"]}
    assert {
        "copilot_edge",
        "gemini_google",
        "arc_browser",
        "brave_leo",
        "opera_aria",
        "antigravity_agent",
        "cursor_ide",
        "kilocode_cline_vscode",
        "chatgpt_claude",
    }.issubset(plats)

    # Cohérence exacte avec l'arborescence actuelle de omega-zero-4d soumise à A12
    live_tree = scan_repo_tree(ROOT_DIR)
    assert [(x["chemin"], x["categorie"]) for x in enc["omega_zero_4d_arborescence"]] == [
        (x["chemin"], x["categorie"]) for x in live_tree
    ]
    if os.name == "posix":
        assert enc["omega_zero_4d_arborescence"] == live_tree

    # Déterminisme SHA-256 canonique et synchronisation Markdown
    assert canonical_sha256(doc) == canonical_sha256(_load_json(REGISTRY_PATH))
    md_text = MD_PATH.read_text(encoding="utf-8")
    assert render_markdown(doc) == md_text
    assert "Supela Ω-ZERO" in md_text
    assert "INACCESSIBLE_DANS_LE_PÉRIMÈTRE" in md_text
    assert "gadboisjean1000-arch/omega-zero-4d" in md_text
    assert "PR-M365-01" in md_text


def test_contradictions_registry_validates_and_preserves_t11() -> None:
    c_schema = _load_json(CONTRADICTIONS_SCHEMA_PATH)
    c_doc = _load_json(CONTRADICTIONS_PATH)

    Draft202012Validator.check_schema(c_schema)
    Draft202012Validator(c_schema).validate(c_doc)

    assert c_doc["schema"] == "supela-contradictions/1"
    assert c_doc["effacement_interdit"] is True

    by_id = {c["id"]: c for c in c_doc["contradictions"]}
    assert {
        "CONTR-T11",
        "CONTR-C001",
        "CONTR-GRPO-001",
        "CONTR-TRANSFO-UNDEF",
        "CONTR-PR1-PS1-AUDIT",
        "CONTR-ZERO-INT-MANQUANT",
        "CONTR-Z0-TENSION",
    }.issubset(by_id.keys())

    # L'essai T11 doit conserver simultanément le FAIL historique et le PASS ultérieur
    t11 = by_id["CONTR-T11"]
    assert "FAIL" in t11["constat_fail_historique"]
    assert "PASS" in t11["etat_ulterieur"]
    assert "EFFACEMENT DU PASSÉ" in t11["justification_conservation"]

    # Tension Z0 / Cycle multi-sources (Branche A TZI vs Branche B v3.0) conservée sans effacement
    z0_tension = by_id["CONTR-Z0-TENSION"]
    assert "Branche A" in z0_tension["constat_fail_historique"]
    assert "Branche B" in z0_tension["constat_fail_historique"]
    assert "cycle_def: undefined / non_resolu" in z0_tension["constat_fail_historique"]
    assert z0_tension["statut_contradiction"] == "CONSERVEE_OUVERTE"

    md_contr = CONTRADICTIONS_MD_PATH.read_text(encoding="utf-8")
    assert "CONTR-T11" in md_contr
    assert "CONTR-C001" in md_contr
    assert "CONTR-Z0-TENSION" in md_contr

    # Le schéma refuse toute désactivation de effacement_interdit
    bad_contr = copy.deepcopy(c_doc)
    bad_contr["effacement_interdit"] = False
    with pytest.raises(ValidationError):
        Draft202012Validator(c_schema).validate(bad_contr)


def test_formulas_and_yaml_cards_honesty() -> None:
    doc = _load_json(REGISTRY_PATH)
    rows = doc["registre_formules"]
    rows_by_id = {r["id"]: r for r in rows}

    assert len(doc["taxonomie_math"]) == 9
    assert [f["famille"] for f in doc["taxonomie_math"]] == [
        "MATH/00_FONDEMENTS/",
        "MATH/01_PREUVES/",
        "MATH/02_STATUTS_4D/",
        "MATH/03_REVIDAGE_MIGRATION/",
        "MATH/04_DIMENSIONS_H_L_P/",
        "MATH/05_CONFLITS_FUSION/",
        "MATH/06_RESPONSABILITE_TRANSFO/",
        "MATH/07_IA_GRPO/",
        "MATH/08_TESTS/",
    ]
    assert len(doc["architecture_xiii_sections"]) == 13
    assert [s["roman"] for s in doc["architecture_xiii_sections"]] == [
        "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII"
    ]

    yaml_files = sorted(FICHES_DIR.glob("*.yaml"))
    assert len(yaml_files) == len(rows) == 25
    assert {p.stem for p in yaml_files} == set(rows_by_id.keys())

    formulas_md = FORMULAS_MD_PATH.read_text(encoding="utf-8")
    index_fiches_md = (FICHES_DIR / "INDEX_FICHES.md").read_text(encoding="utf-8")

    for yaml_path in yaml_files:
        parsed = parse_simple_yaml_fiche(yaml_path.read_text(encoding="utf-8"))
        # Les 29 clés exactes du squelette universel (dont "notation_mathématique")
        assert tuple(parsed.keys()) == UNIVERSAL_FICHE_KEYS
        assert "notation_mathématique" in parsed
        fid = str(parsed["id"])
        row = rows_by_id[fid]
        assert parsed["nom"] == row["nom"]
        assert parsed["type"] == row["objet"]
        assert parsed["statut_epistemique"] == row["statut_probatoire"]
        assert parsed["etat_4d"] == row["etat_4d"]
        assert parsed["formulation_brute"] == row["formulation_brute"]
        assert fid in formulas_md
        assert f"{fid}.yaml" in index_fiches_md

    # Garde-fous épistémiques explicites (M3 & Source != Autorité)
    transfo = parse_simple_yaml_fiche((FICHES_DIR / "MAT-06-CHAINE-TRANSFO.yaml").read_text(encoding="utf-8"))
    assert transfo["formulation_brute"] == "undefined"
    assert transfo["statut_epistemique"] == "INCONNU"
    assert transfo["etat_4d"] == "RÉOUVERT"
    assert "Proposition dérivée non sourcée" in str(transfo["formulation_normalisee"])
    assert "PROMOTION_FORBIDDEN" in str(transfo["formulation_normalisee"])
    assert len(transfo["historique_statuts"]) == 2

    refl = parse_simple_yaml_fiche((FICHES_DIR / "MAT-01-REFLPROB.yaml").read_text(encoding="utf-8"))
    assert refl["statut_epistemique"] == "HYPOTHÉTIQUE"
    assert "NE CONSTITUE PAS un théorème mathématique démontré" in str(refl["n_implique_pas"])

    zero_int = parse_simple_yaml_fiche((FICHES_DIR / "MAT-00-ZERO-INT.yaml").read_text(encoding="utf-8"))
    assert zero_int["statut_epistemique"] == "SUPPORTÉ"
    assert zero_int["etat_4d"] == "RÉOUVERT"
    assert "7 primitives" in str(zero_int["formulation_normalisee"])
    assert "semi-formelle" in str(zero_int["formulation_normalisee"]).lower()
    assert len(zero_int["historique_statuts"]) == 2
    assert zero_int["historique_statuts"][0]["statut"] == "INCONNU"
    assert zero_int["historique_statuts"][0]["etat_4d"] == "LATENT"

    reset_raw = (FICHES_DIR / "MAT-03-RESET-STAR.yaml").read_text(encoding="utf-8")
    assert "RUN_PASS" not in reset_raw
    assert "RUN_PASS" not in formulas_md
    reset_star = parse_simple_yaml_fiche(reset_raw)
    assert reset_star["statut_epistemique"] == "SUPPORTÉ"
    assert reset_star["etat_4d"] == "RÉOUVERT"
    assert "vr22.py" in str(reset_star["formulation_brute"])
    assert "R0_NOMINAL" in str(reset_star["formulation_brute"])
    assert "R5_ABSOLU" in str(reset_star["formulation_brute"])
    assert "V_e = Valeur / Complexité ≥ 1.0" in str(reset_star["formulation_brute"])
    assert "RAPPORTÉ" in str(reset_star["formulation_normalisee"])
    assert len(reset_star["historique_statuts"]) == 2
    assert reset_star["historique_statuts"][0]["statut"] == "INCONNU"
    assert reset_star["historique_statuts"][0]["etat_4d"] == "LATENT"

    for corpus_card_id in (
        "MAT-00-XERO-VIDE",
        "MAT-01-PRINCIPES-P1-P12",
        "MAT-03-PRZ-V3",
        "MAT-05-SCDH-TRICOUCHE",
        "MAT-08-PATTERNS-LAS",
    ):
        c_card = parse_simple_yaml_fiche((FICHES_DIR / f"{corpus_card_id}.yaml").read_text(encoding="utf-8"))
        assert c_card["statut_epistemique"] == "SUPPORTÉ"
        assert c_card["statut_epistemique"] != "PROUVÉ"

    treillis = parse_simple_yaml_fiche((FICHES_DIR / "MAT-01-TREILLIS.yaml").read_text(encoding="utf-8"))
    assert treillis["formulation_brute"] == "G_0 ≺ G_1 ≺ G_2 ≺ G_3 ≺ G_4"


def test_html_export_zero_cdn_parity_and_js_syntax() -> None:
    doc = _load_json(REGISTRY_PATH)
    html_text = HTML_PATH.read_text(encoding="utf-8")

    # Déterminisme strict JSON -> HTML
    assert render_html(doc) == html_text
    assert 'id="contradictions-data"' in html_text
    assert 'id="fiches-yaml-data"' in html_text
    assert 'id="provenance-m365-data"' in html_text
    assert 'id="tab-provenance"' in html_text

    # Parité canonique SHA-256 + zéro CDN externe
    js_block = verify_html_parity(doc, html_text)
    assert len(js_block) > 5000
    assert "renderProvenanceM365" in js_block

    # Validation syntaxique JS via node --check (sans exécution)
    if shutil.which("node") is not None:
        syn = verify_html_js_syntax(html_text)
        assert syn["ok"] is True, syn


def test_powershell_collector_contains_strict_secret_exclusions() -> None:
    ps_text = PS_COLLECTOR_PATH.read_text(encoding="utf-8")
    for pattern in ("Cookies", "Login Data", "Local State", ".env", ".ssh", ".kdbx"):
        assert pattern.lower() in ps_text.lower()
    assert "TheBrowserCompany.Arc" in ps_text
    assert "Brave-Browser" in ps_text
    assert "Microsoft\\Edge" in ps_text
    assert "Google\\Chrome" in ps_text
    # Durcissements post-audit PR #1
    for marker in (
        "TrimEnd('\\', '/')",
        "PSObject.Properties[\"children\"]",
        "Redact-SafeUrl",
        "Redact-GitRemote",
        "ReparsePoint",
        "PARTIELLEMENT_INDEXE",
        "SkipBrowserHistory",
        "-wal",
    ):
        assert marker in ps_text


@pytest.mark.parametrize(
    "mutator",
    [
        "premature_complete_verdict",
        "premature_global_complete",
        "partial_with_complete_verdict",
        "complete_without_c_indexed",
        "complete_without_ai_history_source",
        "invalid_drive_letter_format",
        "invalid_epistemic_status",
    ],
)
def test_schema_rejects_premature_completeness_or_invalid_status(mutator: str) -> None:
    schema = _load_json(SCHEMA_PATH)
    bad = copy.deepcopy(_load_json(REGISTRY_PATH))

    if mutator == "premature_complete_verdict":
        bad["verdict_couverture"] = "COMPLETE_SOUS_PREUVE"
    elif mutator == "premature_global_complete":
        bad["perimetre"]["statut_global"] = "COMPLET_SOUS_PREUVE"
    elif mutator == "partial_with_complete_verdict":
        bad["local_pc_scan"] = "PARTIELLE"
        bad["verdict_couverture"] = "COMPLETE_SOUS_PREUVE"
    elif mutator == "complete_without_c_indexed":
        bad["local_pc_scan"] = "EXECUTEE"
        bad["verdict_couverture"] = "COMPLETE_SOUS_PREUVE"
        bad["perimetre"]["statut_global"] = "COMPLET_SOUS_PREUVE"
        for src in bad["perimetre"]["sources_statuts"]:
            src["statut"] = "INDEXE_LOCAL"
        bad["encyclopedie"]["disques_locaux_windows"][1]["perimetre_statut"] = "INDEXE_LOCAL"
    elif mutator == "complete_without_ai_history_source":
        bad["local_pc_scan"] = "EXECUTEE"
        bad["verdict_couverture"] = "COMPLETE_SOUS_PREUVE"
        bad["perimetre"]["statut_global"] = "COMPLET_SOUS_PREUVE"
        for src in bad["perimetre"]["sources_statuts"]:
            if src["source_id"] in {"windows_drive_C", "windows_drive_D"}:
                src["statut"] = "INDEXE_LOCAL"
        for disk in bad["encyclopedie"]["disques_locaux_windows"]:
            disk["perimetre_statut"] = "INDEXE_LOCAL"
    elif mutator == "invalid_drive_letter_format":
        bad["encyclopedie"]["disques_locaux_windows"][0]["lecteur"] = "C:"
    elif mutator == "invalid_epistemic_status":
        bad["dictionnaire"][0]["statut_epistemique"] = "PROUVE_PAR_IMAGINATION"

    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(bad)


def _sample_full_inventory() -> dict[str, Any]:
    return {
        "schema": "supela-local-pc-inventory/1",
        "generated_utc": "2026-11-16T12:00:00Z",
        "machine_name": "WORKSTATION-WIN11",
        "skip_browser_history": False,
        "drives": [
            {
                "lecteur": "C:\\",
                "statut": "INDEXE_LOCAL",
                "dossiers_racine": [
                    {"nom": "Users", "chemin": "C:\\Users", "modifie_utc": "2026-11-16T10:00:00Z"}
                ],
                "total_depots_git": 1,
                "total_fichiers_notables": 1,
                "scan_tronque": False,
                "dossiers_inaccessibles": 0,
            },
            {
                "lecteur": "D:\\",
                "statut": "INDEXE_LOCAL",
                "dossiers_racine": [
                    {"nom": "Archives", "chemin": "D:\\Archives", "modifie_utc": "2026-11-16T10:00:00Z"}
                ],
                "total_depots_git": 0,
                "total_fichiers_notables": 1,
                "scan_tronque": False,
                "dossiers_inaccessibles": 0,
            },
        ],
        "git_repos": [
            {
                "chemin": "C:\\Users\\Group\\Documents\\antigravity\\excited-meitner",
                "lecteur": "C:\\",
                "remote_origin": "https://github.com/gadboisjean1000-arch/omega-zero-4d.git",
            }
        ],
        "notable_files": [
            {
                "chemin": "C:\\Users\\Group\\Documents\\notes_copilot.md",
                "lecteur": "C:\\",
                "extension": ".md",
                "taille_octets": 2048,
                "modifie_utc": "2026-11-16T10:00:00Z",
            },
            {
                "chemin": "D:\\Archives\\conversations.json",
                "lecteur": "D:\\",
                "extension": ".json",
                "taille_octets": 10240,
                "modifie_utc": "2026-11-16T10:00:00Z",
            },
        ],
        "ai_platforms": [
            {
                "id": "copilot_edge",
                "nom": "Microsoft Edge / Copilot",
                "present": True,
                "chemin_detecte": "C:\\Users\\Group\\AppData\\Local\\Microsoft\\Edge\\User Data",
                "total_traces_ia": 2,
                "traces_echantillon": [
                    {
                        "source": "copilot_edge",
                        "titre": "Copilot Discussion",
                        "url": "https://copilot.microsoft.com/",
                        "type": "HISTORIQUE_URL_IA",
                    }
                ],
            },
            {
                "id": "arc_browser",
                "nom": "Arc Browser",
                "present": True,
                "chemin_detecte": "C:\\Users\\Group\\AppData\\Local\\Packages\\TheBrowserCompany.Arc",
                "total_traces_ia": 1,
                "traces_echantillon": [
                    {
                        "source": "arc_browser",
                        "titre": "Arc Space",
                        "url": "https://arc.net",
                        "type": "PROFIL_ARC",
                    }
                ],
            },
            {
                "id": "brave_leo",
                "nom": "Brave / Brave Leo",
                "present": True,
                "chemin_detecte": "C:\\Users\\Group\\AppData\\Local\\BraveSoftware\\Brave-Browser\\User Data",
                "total_traces_ia": 1,
                "traces_echantillon": [
                    {
                        "source": "brave_leo",
                        "titre": "Gemini in Brave",
                        "url": "https://gemini.google.com/",
                        "type": "HISTORIQUE_URL_IA",
                    }
                ],
            },
        ],
    }


def test_merge_local_inventory_full_and_partial_modes(tmp_path: Path) -> None:
    schema = _load_json(SCHEMA_PATH)
    base_doc = _load_json(REGISTRY_PATH)
    full_inventory = _sample_full_inventory()

    merged = merge_local_inventory(base_doc, full_inventory, ROOT_DIR)
    Draft202012Validator(schema).validate(merged)

    assert merged["local_pc_scan"] == "EXECUTEE"
    assert merged["verdict_couverture"] == "COMPLETE_SOUS_PREUVE"
    assert merged["perimetre"]["statut_global"] == "COMPLET_SOUS_PREUVE"
    assert merged["statistiques"]["entrees_locales_c_d"] == 7  # 1 git + 2 files + (2+1+1) traces
    assert merged["collecteur_local"]["dernier_import_local"]["machine_name"] == "WORKSTATION-WIN11"

    merged_disks = {d["lecteur"]: d for d in merged["encyclopedie"]["disques_locaux_windows"]}
    assert merged_disks["C:\\"]["perimetre_statut"] == "INDEXE_LOCAL"
    assert merged_disks["D:\\"]["perimetre_statut"] == "INDEXE_LOCAL"

    merged_plats = {p["id"]: p for p in merged["encyclopedie"]["plateformes_ia_et_navigateurs"]}
    assert merged_plats["copilot_edge"]["perimetre_statut"] == "INDEXE_LOCAL"
    assert merged_plats["arc_browser"]["perimetre_statut"] == "INDEXE_LOCAL"
    assert merged_plats["brave_leo"]["perimetre_statut"] == "INDEXE_LOCAL"

    md_merged = render_markdown(merged)
    assert "COMPLETE_SOUS_PREUVE" in md_merged
    assert "WORKSTATION-WIN11" in md_merged

    # Mode CLI de bout en bout en ne scannant que C:\ (mode PARTIELLE) + HTML généré à la volée
    partial_inventory = copy.deepcopy(full_inventory)
    partial_inventory["drives"] = [full_inventory["drives"][0]]
    partial_in = tmp_path / "partial_local.json"
    partial_in.write_text(json.dumps(partial_inventory), encoding="utf-8")
    out_json = tmp_path / "out_enc.json"
    out_md = tmp_path / "out_enc.md"
    out_html = tmp_path / "out_enc.html"

    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT_DIR / "scripts" / "build_encyclopedie.py"),
            "--local-inventory",
            str(partial_in),
            "--out-json",
            str(out_json),
            "--out-md",
            str(out_md),
            "--out-html",
            str(out_html),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert '"status": "OK"' in proc.stdout
    assert '"html_parity_verified": true' in proc.stdout
    partial_out = _load_json(out_json)
    Draft202012Validator(schema).validate(partial_out)
    assert partial_out["local_pc_scan"] == "PARTIELLE"
    assert partial_out["verdict_couverture"] == "PARTIELLE_AVEC_EXPORT_LOCAL"
    assert partial_out["perimetre"]["statut_global"] == "HYBRIDE_LOCAL_DISTANT"
    verify_html_parity(partial_out, out_html.read_text(encoding="utf-8"))


def test_merge_local_inventory_m3_edge_cases() -> None:
    schema = _load_json(SCHEMA_PATH)
    base_doc = _load_json(REGISTRY_PATH)

    # 1. SkipBrowserHistory=True bloque COMPLETE_SOUS_PREUVE même si C: et D: sont INDEXE_LOCAL
    no_hist = _sample_full_inventory()
    no_hist["skip_browser_history"] = True
    res_no_hist = merge_local_inventory(base_doc, no_hist, ROOT_DIR)
    Draft202012Validator(schema).validate(res_no_hist)
    assert res_no_hist["local_pc_scan"] == "PARTIELLE"
    assert res_no_hist["verdict_couverture"] == "PARTIELLE_AVEC_EXPORT_LOCAL"
    src_map = {s["source_id"]: s for s in res_no_hist["perimetre"]["sources_statuts"]}
    assert src_map["historiques_ia_locaux"]["statut"] == "INACCESSIBLE_DANS_LE_PÉRIMÈTRE"

    # 2. Disque tronqué force PARTIELLEMENT_INDEXE et empêche COMPLETE_SOUS_PREUVE
    trunc_inv = _sample_full_inventory()
    trunc_inv["drives"][1]["scan_tronque"] = True
    res_trunc = merge_local_inventory(base_doc, trunc_inv, ROOT_DIR)
    Draft202012Validator(schema).validate(res_trunc)
    assert res_trunc["local_pc_scan"] == "PARTIELLE"
    assert res_trunc["verdict_couverture"] == "PARTIELLE_AVEC_EXPORT_LOCAL"
    disks_trunc = {d["lecteur"]: d for d in res_trunc["encyclopedie"]["disques_locaux_windows"]}
    assert disks_trunc["D:\\"]["perimetre_statut"] == "PARTIELLEMENT_INDEXE"

    # 3. Fusion séquentielle C:\ puis D:\ + rejet d'un export plus ancien (régression horodatage)
    inv_c = _sample_full_inventory()
    inv_c["generated_utc"] = "2026-11-16T11:00:00Z"
    inv_c["drives"] = [inv_c["drives"][0]]
    step1 = merge_local_inventory(base_doc, inv_c, ROOT_DIR)
    assert step1["local_pc_scan"] == "PARTIELLE"

    inv_d = _sample_full_inventory()
    inv_d["generated_utc"] = "2026-11-16T13:00:00Z"
    inv_d["drives"] = [inv_d["drives"][1]]
    step2 = merge_local_inventory(step1, inv_d, ROOT_DIR)
    Draft202012Validator(schema).validate(step2)
    assert step2["local_pc_scan"] == "EXECUTEE"
    assert step2["verdict_couverture"] == "COMPLETE_SOUS_PREUVE"
    assert step2["statistiques"]["entrees_locales_c_d"] == 7

    stale = _sample_full_inventory()
    stale["generated_utc"] = "2026-11-16T12:30:00Z"
    with pytest.raises(ValueError, match="antérieur"):
        merge_local_inventory(step2, stale, ROOT_DIR)


def test_a12_clean_with_encyclopedie_artifacts() -> None:
    ok, details = verify_a12(ROOT_DIR)
    assert ok is True
    assert details == {"orphans": [], "broken_links": [], "drift": []}


@pytest.mark.parametrize(
    "mutator",
    [
        "source_identified_promoted_to_prouve",
        "extracted_promoted_to_prouve",
        "rapporte_promoted_to_prouve",
        "effacement_disabled",
        "windows_user_path_leak_in_public",
        "privacy_mode_disabled",
    ],
)
def test_provenance_m365_registry_and_forbidden_auto_promotions(mutator: str) -> None:
    prov_schema = _load_json(PROVENANCE_SCHEMA_PATH)
    prov_doc = load_provenance_m365_registry(PROVENANCE_PATH)

    Draft202012Validator.check_schema(prov_schema)
    validate_provenance_m365_registry(prov_doc, PROVENANCE_SCHEMA_PATH)

    assert prov_doc["schema"] == "supela-provenance-m365/1"
    assert prov_doc["pr_reference"] == "PR-M365-01"
    assert prov_doc["decision_statut"] == "PR_ACCEPTED_PARTIAL"
    assert prov_doc["acces_reseau_vm"]["controle_vm_onedrive"] == "HTTP/2 403"
    assert len(prov_doc["sources_onedrive_m365"]) == 16
    assert len(prov_doc["candidats_m365"]) == 5
    assert len(prov_doc["reduction_manques_m3"]) == 3
    assert render_provenance_markdown(prov_doc) == PROVENANCE_MD_PATH.read_text(encoding="utf-8")

    bad = copy.deepcopy(prov_doc)
    if mutator == "source_identified_promoted_to_prouve":
        bad["candidats_m365"][0]["stade_provenance"] = "SOURCE_IDENTIFIED"
        bad["candidats_m365"][0]["statut_epistemique"] = "PROUVÉ"
    elif mutator == "extracted_promoted_to_prouve":
        bad["candidats_m365"][0]["stade_provenance"] = "EXTRACTED"
        bad["candidats_m365"][0]["statut_epistemique"] = "PROUVÉ"
    elif mutator == "rapporte_promoted_to_prouve":
        bad["candidats_m365"][1]["stade_provenance"] = "STATUT_EPISTEMIQUE"
        bad["candidats_m365"][1]["human_review_status"] = "APPROUVE_HUMAIN"
        bad["candidats_m365"][1]["preuve_test_niveau"] = "RAPPORTÉ"
        bad["candidats_m365"][1]["statut_epistemique"] = "PROUVÉ"
    elif mutator == "effacement_disabled":
        bad["candidats_m365"][0]["effacement_interdit"] = False
    elif mutator == "windows_user_path_leak_in_public":
        bad["politique_confidentialite_locale"]["elements_publiables"][0]["resume_anonyme"] = (
            "Extrait depuis C:\\Users\\Group\\Secret"
        )
    elif mutator == "privacy_mode_disabled":
        bad["politique_confidentialite_locale"]["collecte_neq_publiable"] = False

    with pytest.raises(ValidationError):
        Draft202012Validator(prov_schema).validate(bad)


def test_anonymize_local_inventory_strips_pii_and_paths(tmp_path: Path) -> None:
    inv = _sample_full_inventory()
    # Ajoute une trace Arc contenant un chemin Windows local (comme StorableSidebar.json) et une trace IDE privée
    inv["ai_platforms"][1]["traces_echantillon"].append(
        {
            "source": "arc_browser",
            "titre": "StorableSidebar",
            "url": "C:\\Users\\Group\\AppData\\Local\\Packages\\TheBrowserCompany.Arc\\StorableSidebar.json",
            "type": "FICHIER_ARC",
        }
    )

    anon = anonymize_local_inventory(inv)
    assert anon["schema"] == "supela-local-pc-inventory-anonyme/1"
    assert anon["politique_confidentialite"] == "LOCAL_UNIQUEMENT_PAR_DEFAUT"
    assert anon["admissible_pr_publique"] is True
    assert anon["totaux"] == {
        "drives": 2,
        "git_repos": 1,
        "notable_files": 2,
        "ai_platforms_suivies": 3,
        "ai_platforms_presentes": 3,
        "total_traces_ia": 4,
    }
    assert "https://copilot.microsoft.com" in anon["domaines_http_counts"]
    assert all(k.startswith(("http://", "https://")) for k in anon["domaines_http_counts"])

    serialized = json.dumps(anon, ensure_ascii=False)
    for secret_fragment in (
        "WORKSTATION-WIN11",
        "C:\\Users",
        "C:\\\\Users",
        "AppData",
        "notes_copilot.md",
        "StorableSidebar.json",
        "excited-meitner",
    ):
        assert secret_fragment.lower() not in serialized.lower()

    # Vérification CLI autonome --anonymize-local / --anonymize-out
    raw_in = tmp_path / "raw_local.json"
    anon_out = tmp_path / "anon_local.json"
    raw_in.write_text(json.dumps(inv), encoding="utf-8")
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT_DIR / "scripts" / "build_encyclopedie.py"),
            "--anonymize-local",
            str(raw_in),
            "--anonymize-out",
            str(anon_out),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    cli_payload = json.loads(proc.stdout)
    assert cli_payload["status"] == "OK"
    assert cli_payload["mode"] == "ANONYMIZE_LOCAL_ONLY"
    assert cli_payload["admissible_pr_publique"] is True
    assert json.loads(anon_out.read_text(encoding="utf-8")) == anon

