from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
CITATION_PATH = ROOT_DIR / "CITATION.cff"
AUDIT_PACK_PATH = ROOT_DIR / "docs" / "constitution" / "PACK_AUDIT_EXTERNE_ZENODO.md"
RELEASE_WORKFLOW_PATH = ROOT_DIR / ".github" / "workflows" / "release-provenance-zenodo.yml"

ZENODO_DOI_RE = re.compile(r"^10\.5281/zenodo\.[1-9][0-9]{4,}$")
PLACEHOLDER_TOKENS = ("...", "…", "xxxx", "todo", "tbd", "placeholder", "<chiffres")


def parse_top_level_cff_fields(text: str) -> dict[str, str]:
    """Parseur YAML CFF strict sans dépendance tierce (clé racine -> valeur scalaire ou bloc)."""
    fields: dict[str, str] = {}
    current_key: str | None = None
    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        if "\t" in raw_line:
            raise ValueError(f"Tabulation YAML interdite dans CITATION.cff ligne {lineno}.")
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not raw_line.startswith(" "):
            if ":" not in raw_line:
                raise ValueError(f"Clé YAML invalide ligne {lineno}: {raw_line!r}")
            key, _, val = raw_line.partition(":")
            key_clean = key.strip()
            val_clean = val.strip().strip('"').strip("'")
            fields[key_clean] = val_clean
            current_key = key_clean
        elif current_key is not None:
            fields[current_key] = f"{fields[current_key]}\n{stripped}".strip()
    return fields


def validate_zenodo_doi(doi: str) -> bool:
    """N'accepte qu'un DOI numérique réel Zenodo (refuse tout placeholder ou troncature)."""
    lowered = doi.strip().lower()
    if any(tok in lowered for tok in PLACEHOLDER_TOKENS):
        return False
    return bool(ZENODO_DOI_RE.fullmatch(doi.strip()))


def test_citation_cff_yaml_structure_and_required_metadata() -> None:
    assert CITATION_PATH.is_file()
    raw = CITATION_PATH.read_text(encoding="utf-8")
    assert "\r\n" not in raw, "CITATION.cff doit utiliser des fins de ligne LF."

    fields = parse_top_level_cff_fields(raw)
    assert fields["cff-version"] == "1.2.0"
    assert fields["type"] == "software"
    assert fields["license"] == "Apache-2.0"
    assert fields["repository-code"] == "https://github.com/gadboisjean1000-arch/omega-zero-4d"
    assert "0009-0001-5361-6795" in fields["authors"]
    assert "Gadbois" in fields["authors"]
    assert "Supela-K3-Omega" in fields["references"]

    # Barrière anti-placeholder : tout DOI (champ `doi` ou `identifiers`) doit être strictement numérique
    doi_val = fields.get("doi")
    if doi_val:
        assert validate_zenodo_doi(doi_val), f"DOI Zenodo invalide ou placeholder: {doi_val!r}"
    identifiers_block = fields.get("identifiers", "")
    if "zenodo" in identifiers_block.lower():
        matches = re.findall(r"10\.5281/zenodo\.[^\s\"']+", identifiers_block)
        assert matches and all(validate_zenodo_doi(m) for m in matches), (
            f"Placeholder DOI interdit dans CITATION.cff identifiers: {identifiers_block!r}"
        )


@pytest.mark.parametrize(
    ("candidate", "expected"),
    [
        ("10.5281/zenodo.12345678", True),
        ("10.5281/zenodo.98765", True),
        ("10.5281/zenodo.…", False),
        ("10.5281/zenodo....", False),
        ("10.5281/zenodo.XXXX", False),
        ("10.5281/zenodo.00000", False),
        ("10.5281/zenodo.TODO", False),
        ("", False),
    ],
)
def test_zenodo_doi_validator_rejects_placeholders(candidate: str, expected: bool) -> None:
    assert validate_zenodo_doi(candidate) is expected


def test_external_audit_package_10_steps_and_epistemic_doi_lock() -> None:
    assert AUDIT_PACK_PATH.is_file()
    pack_text = AUDIT_PACK_PATH.read_text(encoding="utf-8")

    expected_steps = (
        "### 1. Identifier",
        "### 2. Geler",
        "### 3. Reconstruire",
        "### 4. Exécuter",
        "### 5. Vérifier la provenance",
        "### 6. Vérifier l'attestation matérielle",
        "### 7. Chercher les contradictions",
        "### 8. Vérifier la portée",
        "### 9. Produire le rapport",
        "### 10. Soumettre à décision humaine",
    )
    for step in expected_steps:
        assert step in pack_text, f"Étape manquante dans PACK_AUDIT_EXTERNE_ZENODO.md : {step}"

    assert "NOTICE-HDR-ISO-Monolithe-Probant.md" in pack_text
    assert "scellé en production" in pack_text
    assert "tpm2_quote" in pack_text
    assert "docs/zenodo-doi-canonical" in pack_text

    # Verrou épistémique strict : impossible de proclamer RESOLU_VERIFIE sans DOI numérique réel dans CITATION.cff
    cff_fields = parse_top_level_cff_fields(CITATION_PATH.read_text(encoding="utf-8"))
    has_real_doi = bool(cff_fields.get("doi")) and validate_zenodo_doi(cff_fields["doi"])
    if has_real_doi:
        assert "ZENODO_DOI_STATUS: RESOLU_VERIFIE" in pack_text
    else:
        assert "ZENODO_DOI_STATUS: DECLARE_EN_ATTENTE_DOI_REEL" in pack_text
        assert "ZENODO_DOI_STATUS: RESOLU_VERIFIE" not in pack_text


def test_release_provenance_zenodo_workflow_enforces_fulcio_oidc() -> None:
    assert RELEASE_WORKFLOW_PATH.is_file()
    wf_text = RELEASE_WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "id-token: write" in wf_text
    assert "cosign sign-blob --yes --bundle SHA256SUMS.txt.sigstore.json SHA256SUMS.txt" in wf_text
    assert "cosign verify-blob SHA256SUMS.txt" in wf_text
    assert 'https://token.actions.githubusercontent.com' in wf_text
    assert "gh release upload" in wf_text
