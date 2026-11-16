from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, ValidationError

from omega_zero.models import canonical_sha256
from scripts.build_encyclopedie import (
    merge_local_inventory,
    render_markdown,
    scan_repo_tree,
)
from scripts.verify_a12 import verify_a12

ROOT_DIR = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT_DIR / "schemas" / "supela_encyclopedie_1.schema.json"
REGISTRY_PATH = ROOT_DIR / "docs" / "constitution" / "supela-dictionnaire-encyclopedie-1.json"
MD_PATH = ROOT_DIR / "docs" / "constitution" / "ENCYCLOPEDIE_DICTIONNAIRE.md"
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

    assert stats["termes_dictionnaire"] == len(dictionnaire)
    assert stats["depots_github_total"] == len(enc["github_depots"]) == 15
    assert stats["depots_github_originaux"] == 4
    assert stats["depots_github_forks"] == 11
    assert stats["discussions_ia_google_docs"] == len(enc["discussions_ia_google_docs"]) >= 54
    assert stats["plateformes_ia_navigateurs"] == len(enc["plateformes_ia_et_navigateurs"]) >= 9
    assert stats["fichiers_omega_zero_4d"] == len(enc["omega_zero_4d_arborescence"])

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

    # Déterminisme SHA-256 canonique
    assert canonical_sha256(doc) == canonical_sha256(_load_json(REGISTRY_PATH))

    # Markdown synchronisé et complet
    md_text = MD_PATH.read_text(encoding="utf-8")
    assert "Supela Ω-ZERO" in md_text
    assert "INACCESSIBLE_DANS_LE_PÉRIMÈTRE" in md_text
    assert "gadboisjean1000-arch/omega-zero-4d" in md_text


def test_powershell_collector_contains_strict_secret_exclusions() -> None:
    ps_text = PS_COLLECTOR_PATH.read_text(encoding="utf-8")
    for pattern in ("Cookies", "Login Data", "Local State", ".env", ".ssh", ".kdbx"):
        assert pattern.lower() in ps_text.lower()
    assert "TheBrowserCompany.Arc" in ps_text
    assert "Brave-Browser" in ps_text
    assert "Microsoft\\Edge" in ps_text
    assert "Google\\Chrome" in ps_text


@pytest.mark.parametrize(
    "mutator",
    [
        "premature_complete_verdict",
        "premature_global_complete",
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
    elif mutator == "invalid_drive_letter_format":
        bad["encyclopedie"]["disques_locaux_windows"][0]["lecteur"] = "C:"
    elif mutator == "invalid_epistemic_status":
        bad["dictionnaire"][0]["statut_epistemique"] = "PROUVE_PAR_IMAGINATION"

    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(bad)


def test_merge_local_inventory_full_and_partial_modes(tmp_path: Path) -> None:
    schema = _load_json(SCHEMA_PATH)
    base_doc = _load_json(REGISTRY_PATH)

    full_inventory = {
        "schema": "supela-local-pc-inventory/1",
        "generated_utc": "2026-11-16T12:00:00Z",
        "machine_name": "WORKSTATION-WIN11",
        "drives": [
            {
                "lecteur": "C:\\",
                "statut": "INDEXE_LOCAL",
                "dossiers_racine": [
                    {"nom": "Users", "chemin": "C:\\Users", "modifie_utc": "2026-11-16T10:00:00Z"}
                ],
                "total_depots_git": 1,
                "total_fichiers_notables": 1,
            },
            {
                "lecteur": "D:\\",
                "statut": "INDEXE_LOCAL",
                "dossiers_racine": [
                    {"nom": "Archives", "chemin": "D:\\Archives", "modifie_utc": "2026-11-16T10:00:00Z"}
                ],
                "total_depots_git": 0,
                "total_fichiers_notables": 1,
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
                    {"source": "arc_browser", "titre": "Arc Space", "url": "https://arc.net", "type": "PROFIL_ARC"}
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

    # Mode CLI de bout en bout en ne scannant que C:\ (mode PARTIELLE)
    partial_inventory = copy.deepcopy(full_inventory)
    partial_inventory["drives"] = [full_inventory["drives"][0]]
    partial_in = tmp_path / "partial_local.json"
    partial_in.write_text(json.dumps(partial_inventory), encoding="utf-8")
    out_json = tmp_path / "out_enc.json"
    out_md = tmp_path / "out_enc.md"

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
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert '"status": "OK"' in proc.stdout
    partial_out = _load_json(out_json)
    Draft202012Validator(schema).validate(partial_out)
    assert partial_out["local_pc_scan"] == "PARTIELLE"
    assert partial_out["verdict_couverture"] == "PARTIELLE_AVEC_EXPORT_LOCAL"
    assert partial_out["perimetre"]["statut_global"] == "HYBRIDE_LOCAL_DISTANT"


def test_a12_clean_with_encyclopedie_artifacts() -> None:
    ok, details = verify_a12(ROOT_DIR)
    assert ok is True
    assert details == {"orphans": [], "broken_links": [], "drift": []}
