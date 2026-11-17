"""Thèse 2 : Axiome de Lucidité INV-LUC-PROPOSE (zéro zone grise)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
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
    these_id="THESIS-LUC-002-ORCID0009",
    numero=2,
    titre="Axiome de Lucidité INV-LUC-PROPOSE",
    domaine="Ce qui peut être omis vs ce qui doit rester visible (pas de zone grise)",
    invariant_id="INV-LUC-PROPOSE",
    pdf_filename="THESIS-LUC-002-ORCID0009.pdf",
    apport_cle="Distinguer démontré vs non-démontré sans zones grises",
    cross_references=("INV-AXE-01", "INV-FASE-01", "INV-04/INV-05", "N1->N2->N3", "R-00"),
)


class EpistemicVisibility(StrEnum):
    """Partition binaire stricte : aucune zone grise autorisée."""

    DEMONTRE = "DEMONTRE"
    NON_DEMONTRE = "NON_DEMONTRE"
    ZONE_GRISE = "ZONE_GRISE"


@dataclass(frozen=True)
class LucidityStatement:
    statement_id: str
    visibility: EpistemicVisibility
    proof_ref: str | None = None
    omission_declared: bool = False


DEFAULT_STATEMENTS: tuple[LucidityStatement, ...] = (
    LucidityStatement(
        statement_id="LUC-STMT-01",
        visibility=EpistemicVisibility.DEMONTRE,
        proof_ref="sha256:reproducible-proof-pi0",
        omission_declared=False,
    ),
    LucidityStatement(
        statement_id="LUC-STMT-02",
        visibility=EpistemicVisibility.NON_DEMONTRE,
        proof_ref=None,
        omission_declared=True,
    ),
)


def verify(statements: tuple[LucidityStatement, ...] | None = DEFAULT_STATEMENTS) -> ThesisVerificationResult:
    """Vérifie INV-LUC-PROPOSE : aucune zone grise, toute non-démonstration est visible."""
    if statements is None or len(statements) == 0:
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
            indetermine_conditions=["Aucun énoncé fourni pour le contrôle de lucidité"],
            details={"total_statements": 0},
            cross_references=list(SPEC.cross_references),
        )

    violations: list[str] = []
    for st in statements:
        if st.visibility == EpistemicVisibility.ZONE_GRISE:
            violations.append(f"{st.statement_id}: ZONE_GRISE interdite")
        elif st.visibility == EpistemicVisibility.DEMONTRE and not (st.proof_ref and st.proof_ref.strip()):
            violations.append(f"{st.statement_id}: DEMONTRE sans proof_ref")
        elif st.visibility == EpistemicVisibility.NON_DEMONTRE and not st.omission_declared:
            violations.append(f"{st.statement_id}: NON_DEMONTRE non explicitement déclaré visible")

    statut = ThesisStatus.CONTROLE if not violations else ThesisStatus.INDETERMINE
    conditions = (
        ["Partition stricte DEMONTRE / NON_DEMONTRE respectée sans zone grise"]
        if not violations
        else violations
    )
    details: dict[str, Any] = {
        "total_statements": len(statements),
        "violations_count": len(violations),
        "violations": violations,
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
