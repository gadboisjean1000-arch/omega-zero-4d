"""Thèse 3 : Non-indépendance Fase One INV-FASE-01 (TOI/NOUS + trace écrite rang 10)."""

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
    these_id="THESIS-FASE-003-ORCID0009",
    numero=3,
    titre="Non-indépendance Fase One INV-FASE-01",
    domaine='Non-indépendance "TOI/NOUS" avec trace écrite obligatoire (rang 10)',
    invariant_id="INV-FASE-01",
    pdf_filename="THESIS-FASE-003-ORCID0009.pdf",
    apport_cle='Modéliser les structures "TOI/NOUS" dans la découverte mathématique',
    cross_references=("INV-AXE-01", "INV-LUC-PROPOSE", "INV-04/INV-05", "N1->N2->N3", "R-00"),
)

MANDATORY_RANK = 10


@dataclass(frozen=True)
class FaseOneCoupling:
    """Structure couplée TOI/NOUS avec trace écrite obligatoire de rang 10."""

    toi_actor: str
    nous_collective: str
    written_trace_id: str
    trace_rank: int
    claimed_independence: bool = False


DEFAULT_COUPLING = FaseOneCoupling(
    toi_actor="Chercheur ORCID 0009-0001-5361-6795",
    nous_collective="Réseau formel Supela Omega-Zero-4D",
    written_trace_id="TRACE-RANG10-FASE01-001",
    trace_rank=MANDATORY_RANK,
    claimed_independence=False,
)


def verify(coupling: FaseOneCoupling | None = DEFAULT_COUPLING) -> ThesisVerificationResult:
    """Vérifie INV-FASE-01 : non-indépendance assumée + trace écrite obligatoire de rang >= 10."""
    if coupling is None:
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
            indetermine_conditions=["Structure TOI/NOUS absente (None)"],
            details={"mandatory_rank": MANDATORY_RANK},
            cross_references=list(SPEC.cross_references),
        )

    violations: list[str] = []
    if not coupling.toi_actor.strip() or not coupling.nous_collective.strip():
        violations.append("Acteur TOI ou collectif NOUS vide")
    if coupling.claimed_independence:
        violations.append("Prétention d'indépendance incompatible avec INV-FASE-01")
    if not coupling.written_trace_id.strip():
        violations.append("Trace écrite obligatoire absente")
    if coupling.trace_rank < MANDATORY_RANK:
        violations.append(f"Rang de trace insuffisant ({coupling.trace_rank} < {MANDATORY_RANK})")

    statut = ThesisStatus.CONTROLE if not violations else ThesisStatus.INDETERMINE
    conditions = (
        ["Non-indépendance TOI/NOUS déclarée avec trace écrite de rang >= 10"]
        if not violations
        else violations
    )
    details: dict[str, Any] = {
        "toi_actor": coupling.toi_actor,
        "nous_collective": coupling.nous_collective,
        "written_trace_id": coupling.written_trace_id,
        "trace_rank": coupling.trace_rank,
        "mandatory_rank": MANDATORY_RANK,
        "non_independent": not coupling.claimed_independence,
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
