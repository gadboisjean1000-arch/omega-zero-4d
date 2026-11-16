from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, ValidationError

from omega_zero.models import canonical_sha256
from scripts.verify_a12 import verify_a12

ROOT_DIR = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT_DIR / "docs" / "constitution" / "supela-article-registry-1.json"
SCHEMA_PATH = ROOT_DIR / "schemas" / "supela_article_registry_1.schema.json"


def _load_json(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


def _collect_keys_and_strings(node: Any) -> tuple[set[str], list[str]]:
    keys: set[str] = set()
    values: list[str] = []
    if isinstance(node, dict):
        for k, v in node.items():
            keys.add(str(k))
            sub_k, sub_v = _collect_keys_and_strings(v)
            keys.update(sub_k)
            values.extend(sub_v)
    elif isinstance(node, list):
        for item in node:
            sub_k, sub_v = _collect_keys_and_strings(item)
            keys.update(sub_k)
            values.extend(sub_v)
    elif isinstance(node, str):
        values.append(node)
    return keys, values


def test_registry_validates_against_draft_2020_12_and_stays_open() -> None:
    schema = _load_json(SCHEMA_PATH)
    registry = _load_json(REGISTRY_PATH)

    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(registry)

    # Barrière épistémique : tant qu'aucune reproduction n'est exécutée, OUVERT + AnalysisCandidate obligatoires
    assert registry["hook"] == "AnalysisCandidate"
    assert registry["verdict_final"] == "OUVERT"
    assert registry["validation_dep"] == "NON_ACQUISE"
    assert registry["reproduction_exp"] == "NON_EXECUTEE"
    assert registry["metadonnees_supela"]["ENTREE_NORMATIVE"] == "NON"


def test_registry_normalized_keys_unique_steps_and_article_invariants() -> None:
    registry = _load_json(REGISTRY_PATH)
    all_keys, all_strings = _collect_keys_and_strings(registry)

    # Normalisation imposée avant intégration
    assert " mecanisme" not in all_keys
    assert "mécanisme" not in all_keys
    assert "NON_ESTABLIE" not in all_strings
    assert "NON_ACQUISEE" not in all_strings
    assert registry["branches"]["A"]["dependance_directe"] == "NON_ETABLIE"
    for branch_id in ("A", "B", "C", "D", "E"):
        assert "mecanisme" in registry["branches"][branch_id]

    # Les 6 articles sont distincts et aucun n'est promu normativement
    article_ids = [art["id"] for art in registry["articles"]]
    assert article_ids == ["ART-01", "ART-02", "ART-03", "ART-04", "ART-05", "ART-06"]
    assert all(art["entree_normative"] == "NON" for art in registry["articles"])
    assert all(art["reproduction"] == "NON" for art in registry["articles"])

    # Unicité E0..E6 (suppression du doublon E4)
    etapes = [step["etape"] for step in registry["protocole_validation_exp"]["etapes"]]
    assert etapes == ["E0", "E1", "E2", "E3", "E4", "E5", "E6"]

    # Trace déterministe UTF-8 SHA-256
    digest_a = canonical_sha256(registry)
    digest_b = canonical_sha256(_load_json(REGISTRY_PATH))
    assert digest_a == digest_b and len(digest_a) == 64


@pytest.mark.parametrize(
    "mutator_name",
    [
        "premature_task_complete_hook",
        "premature_verdict_closed",
        "leading_space_mecanisme_key",
        "normative_promotion_without_repro",
    ],
)
def test_schema_rejects_premature_promotion_and_dirty_keys(mutator_name: str) -> None:
    schema = _load_json(SCHEMA_PATH)
    bad = copy.deepcopy(_load_json(REGISTRY_PATH))

    if mutator_name == "premature_task_complete_hook":
        bad["hook"] = "TaskComplete"
    elif mutator_name == "premature_verdict_closed":
        bad["verdict_final"] = "CLOTURE_SOUS_PREUVE"
    elif mutator_name == "leading_space_mecanisme_key":
        del bad["branches"]["B"]["mecanisme"]
        bad["branches"]["B"][" mecanisme"] = "typo"
    elif mutator_name == "normative_promotion_without_repro":
        bad["articles"][0]["entree_normative"] = "OUI"

    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(bad)


def test_rule_a12_bidirectional_integrity_and_orphan_detection(tmp_path: Path) -> None:
    # 1. Vérification positive réelle sur le dépôt complet
    ok, details = verify_a12(ROOT_DIR)
    assert ok is True
    assert details == {"orphans": [], "broken_links": [], "drift": []}

    # 2. Vérification négative isolée : un fichier orphelin doit faire échouer verify_a12
    sandbox = tmp_path / "repo_a12"
    shutil.copytree(ROOT_DIR / "docs", sandbox / "docs")
    shutil.copytree(ROOT_DIR / "schemas", sandbox / "schemas")
    shutil.copytree(ROOT_DIR / "src", sandbox / "src")
    shutil.copytree(ROOT_DIR / "tests", sandbox / "tests")
    shutil.copytree(ROOT_DIR / "policies", sandbox / "policies")
    shutil.copytree(ROOT_DIR / "runtime", sandbox / "runtime")
    shutil.copytree(ROOT_DIR / "scripts", sandbox / "scripts")
    shutil.copytree(ROOT_DIR / "reports", sandbox / "reports")
    shutil.copytree(ROOT_DIR / ".github", sandbox / ".github")

    orphan_file = sandbox / "docs" / "constitution" / "ORPHELIN_NON_INDEXE.json"
    orphan_file.write_text('{"orphan": true}\n', encoding="utf-8")

    ok_orphan, details_orphan = verify_a12(sandbox)
    assert ok_orphan is False
    assert "docs/constitution/ORPHELIN_NON_INDEXE.json" in details_orphan["orphans"]

    # 3. Suppression de l'orphelin + injection d'un lien cassé -> doit échouer sur broken_links
    orphan_file.unlink()
    idx_file = sandbox / "docs" / "constitution" / "INDEX_CONSTITUTION.md"
    idx_file.write_text(
        idx_file.read_text(encoding="utf-8") + "\n- [Fichier inexistant](FICHIER_INEXISTANT.json)\n",
        encoding="utf-8",
    )
    ok_broken, details_broken = verify_a12(sandbox)
    assert ok_broken is False
    assert "docs/constitution/FICHIER_INEXISTANT.json" in details_broken["broken_links"]
