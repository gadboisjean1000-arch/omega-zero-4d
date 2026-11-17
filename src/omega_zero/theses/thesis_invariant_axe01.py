"""Thèse 1 : Systèmes d'Invariants INV-AXE-01 (Cadre à 5 questions)."""

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
    these_id="THESIS-INV-001-ORCID0009",
    numero=1,
    titre="Systèmes d'Invariants INV-AXE-01",
    domaine="Cadre à 5 questions (origine, dépendances, maintien, perte, remplacement)",
    invariant_id="INV-AXE-01",
    pdf_filename="THESIS-INV-001-ORCID0009.pdf",
    apport_cle="Formaliser quand les énoncés mathématiques sont INDETERMINE vs. CONTROLE",
    cross_references=("INV-LUC-PROPOSE", "INV-FASE-01", "INV-04/INV-05", "N1->N2->N3", "R-00"),
)

REQUIRED_QUESTIONS: tuple[str, ...] = (
    "origine",
    "dependances",
    "maintien",
    "perte",
    "remplacement",
)


@dataclass(frozen=True)
class FiveQuestionsFrame:
    """Cadre autonome à 5 questions pour INV-AXE-01."""

    origine: str = ""
    dependances: str = ""
    maintien: str = ""
    perte: str = ""
    remplacement: str = ""

    def missing_questions(self) -> list[str]:
        missing: list[str] = []
        for q in REQUIRED_QUESTIONS:
            val = getattr(self, q)
            if not isinstance(val, str) or not val.strip():
                missing.append(q)
        return missing

    def answered_count(self) -> int:
        return len(REQUIRED_QUESTIONS) - len(self.missing_questions())


DEFAULT_CANONICAL_FRAME = FiveQuestionsFrame(
    origine="Axiome d'ancrage explicite S_0 dans omega-zero-4d (MAT-00)",
    dependances="Invariants locaux + registre monotone K_t sans dépendance cachée",
    maintien="Vérification continue par revidage PREPARE->VERIFY->COMMIT->CLEAN",
    perte="Toute réponse manquante ou effacement silencieux rétrograde vers INDETERMINE",
    remplacement="Substitution uniquement par épreuve reproductible horodatée et tracée",
)


def verify(frame: FiveQuestionsFrame | None = DEFAULT_CANONICAL_FRAME) -> ThesisVerificationResult:
    """Vérifie le cadre INV-AXE-01 : CONTROLE si 5/5 réponses, INDETERMINE sinon, ABSENT si None."""
    if frame is None:
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
            indetermine_conditions=["Cadre à 5 questions absent (None)"],
            details={"answered": 0, "required": 5, "missing": list(REQUIRED_QUESTIONS)},
            cross_references=list(SPEC.cross_references),
        )

    missing = frame.missing_questions()
    statut = ThesisStatus.CONTROLE if not missing else ThesisStatus.INDETERMINE
    conditions = (
        ["Aucune condition INDETERMINE active : 5/5 questions renseignées"]
        if not missing
        else [f"Question manquante ou vide : {q}" for q in missing]
    )
    details: dict[str, Any] = {
        "answered": frame.answered_count(),
        "required": len(REQUIRED_QUESTIONS),
        "missing": missing,
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
    result = verify(DEFAULT_CANONICAL_FRAME)
    print(json.dumps(result.to_metadata_dict(), indent=2, ensure_ascii=False))
    return 0 if result.statut == ThesisStatus.CONTROLE else 1


if __name__ == "__main__":
    raise SystemExit(main())
