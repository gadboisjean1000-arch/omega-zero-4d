"""Thèse 6 : Dépendance Souveraine R-00 (7 invalidateurs + 25 transitions + souveraineté)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .common import (
    ORCID_ID,
    ORCID_URI,
    ThesisSpec,
    ThesisStatus,
    ThesisVerificationResult,
    utc_now_iso,
)

SPEC = ThesisSpec(
    these_id="THESIS-DEP-006-ORCID0009",
    numero=6,
    titre="Dépendance Souveraine R-00",
    domaine='"De quoi dépends-tu ?" + 7 invalidators + 25 transitions + souveraineté',
    invariant_id="R-00",
    pdf_filename="THESIS-DEP-006-ORCID0009.pdf",
    apport_cle="Souveraineté complète de déclaration de dépendance sans validation externe",
    cross_references=("INV-AXE-01", "INV-LUC-PROPOSE", "INV-FASE-01", "INV-04/INV-05", "N1->N2->N3"),
)

SEVEN_INVALIDATORS: tuple[str, ...] = (
    "INV-R00-1: Dépendance cachée non déclarée",
    "INV-R00-2: Substitution silencieuse de provenance",
    "INV-R00-3: Élévation d'autorité sans épreuve",
    "INV-R00-4: Effacement rétroactif d'historique",
    "INV-R00-5: Zone grise non typée",
    "INV-R00-6: Validation externe imposée comme condition d'existence",
    "INV-R00-7: Rupture de continuité intercycle SUP-ICI-01",
)

STATES_5: tuple[str, ...] = ("ABSENT", "INDETERMINE", "OUVERT", "CONTROLE", "REVOCABLE")
TWENTY_FIVE_TRANSITIONS: tuple[tuple[str, str], ...] = tuple(
    (src, dst) for src in STATES_5 for dst in STATES_5
)


@dataclass(frozen=True)
class SovereignDependencyModel:
    """Modèle complet R-00 : question fondatrice + 7 invalidateurs + 25 transitions."""

    question_r00: str
    declared_dependencies: tuple[str, ...]
    invalidators: tuple[str, ...]
    transitions_count: int
    requires_external_validation: bool = False


DEFAULT_MODEL = SovereignDependencyModel(
    question_r00="De quoi dépends-tu ?",
    declared_dependencies=(
        "Python >= 3.11 + stdlib",
        "omega_zero.supela_math_core (MAT-00..MAT-08)",
        "ORCID 0009-0001-5361-6795 (ancrage auteur souverain)",
    ),
    invalidators=SEVEN_INVALIDATORS,
    transitions_count=len(TWENTY_FIVE_TRANSITIONS),
    requires_external_validation=False,
)


def verify(model: SovereignDependencyModel | None = DEFAULT_MODEL) -> ThesisVerificationResult:
    """Vérifie R-00 : 7 invalidateurs + 25 transitions + souveraineté sans validation externe."""
    if model is None:
        return ThesisVerificationResult(
            these_id=SPEC.these_id,
            orcid=ORCID_ID,
            orcid_uri=ORCID_URI,
            titre=SPEC.titre,
            domaine=SPEC.domaine,
            invariant_id=SPEC.invariant_id,
            statut=ThesisStatus.ABSENT,
            timestamp_utc=utc_now_iso(),
            autonomie=SPEC.autonomie,
            apport_cle=SPEC.apport_cle,
            indetermine_conditions=["Modèle R-00 absent (None)"],
            details={},
            cross_references=list(SPEC.cross_references),
        )

    violations: list[str] = []
    if not model.question_r00.strip():
        violations.append("Question fondatrice R-00 absente")
    if not model.declared_dependencies:
        violations.append("Dépendances non déclarées")
    if len(model.invalidators) != 7:
        violations.append(f"7 invalidateurs requis, trouvé {len(model.invalidators)}")
    if model.transitions_count != 25:
        violations.append(f"25 transitions requises, trouvé {model.transitions_count}")
    if model.requires_external_validation:
        violations.append("Dépendance à une validation externe incompatible avec la souveraineté R-00")

    statut = ThesisStatus.CONTROLE if not violations else ThesisStatus.INDETERMINE
    conditions = (
        ["Théorie R-00 complète : 7 invalidateurs, 25 transitions, souveraineté autonome"]
        if not violations
        else violations
    )
    details: dict[str, Any] = {
        "question_r00": model.question_r00,
        "dependencies_count": len(model.declared_dependencies),
        "invalidators_count": len(model.invalidators),
        "transitions_count": model.transitions_count,
        "sovereign_without_external_validation": not model.requires_external_validation,
    }
    return ThesisVerificationResult(
        these_id=SPEC.these_id,
        orcid=ORCID_ID,
        orcid_uri=ORCID_URI,
        titre=SPEC.titre,
        domaine=SPEC.domaine,
        invariant_id=SPEC.invariant_id,
        statut=statut,
        timestamp_utc=utc_now_iso(),
        autonomie=SPEC.autonomie,
        apport_cle=SPEC.apport_cle,
        indetermine_conditions=conditions,
        details=details,
        cross_references=list(SPEC.cross_references),
    )


def main() -> int:
    result = verify()
    print(json.dumps(result.to_metadata_dict(), indent=2, ensure_ascii=False))
    return 0 if result.statut == ThesisStatus.CONTROLE else 1


if __name__ == "__main__":
    raise SystemExit(main())
