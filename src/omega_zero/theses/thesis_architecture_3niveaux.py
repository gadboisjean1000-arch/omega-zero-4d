"""Thèse 5 : Architecture 3 Niveaux N1->N2->N3 (Faits -> Décisions -> Omissions)."""

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
    these_id="THESIS-ARCHI-005-ORCID0009",
    numero=5,
    titre="Architecture 3 Niveaux N1->N2->N3",
    domaine="Hiérarchie Faits->Décisions->Omissions (N1->N2->N3)",
    invariant_id="N1->N2->N3",
    pdf_filename="THESIS-ARCHI-005-ORCID0009.pdf",
    apport_cle="Formaliser l'omission comme état mathématique de première classe",
    cross_references=("INV-AXE-01", "INV-LUC-PROPOSE", "INV-FASE-01", "INV-04/INV-05", "R-00"),
)


@dataclass(frozen=True)
class ThreeLevelArchitecture:
    """Hiérarchie stricte N1 (Faits) -> N2 (Décisions) -> N3 (Omissions explicites)."""

    n1_facts: tuple[str, ...]
    n2_decisions: tuple[str, ...]
    n3_omissions: tuple[str, ...]
    disjoint_layers: bool = True


DEFAULT_ARCH = ThreeLevelArchitecture(
    n1_facts=("Fait N1: Projection Pi0 non vide", "Fait N1: Trace SHA-256 vérifiée"),
    n2_decisions=("Décision N2: Maintien statut OUVERT jusqu'à épreuve",),
    n3_omissions=("Omission N3: Ancrage matériel TPM2 non disponible sur cette VM",),
    disjoint_layers=True,
)


def verify(arch: ThreeLevelArchitecture | None = DEFAULT_ARCH) -> ThesisVerificationResult:
    """Vérifie la séparation stricte N1 -> N2 -> N3 et la présence typée de N3 (omissions)."""
    if arch is None:
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
            indetermine_conditions=["Architecture 3 niveaux absente (None)"],
            details={},
            cross_references=list(SPEC.cross_references),
        )

    violations: list[str] = []
    if not arch.n1_facts:
        violations.append("Couche N1 (Faits) vide")
    if not arch.n2_decisions:
        violations.append("Couche N2 (Décisions) vide")
    if not arch.n3_omissions:
        violations.append("Couche N3 (Omissions) vide : omission doit être état de première classe")
    overlap = (
        (set(arch.n1_facts) & set(arch.n2_decisions))
        | (set(arch.n2_decisions) & set(arch.n3_omissions))
        | (set(arch.n1_facts) & set(arch.n3_omissions))
    )
    if overlap or not arch.disjoint_layers:
        violations.append("Confusion entre couches N1/N2/N3 détectée")

    statut = ThesisStatus.CONTROLE if not violations else ThesisStatus.INDETERMINE
    conditions = (
        ["Hiérarchie N1->N2->N3 disjointe avec omissions N3 formalisées"]
        if not violations
        else violations
    )
    details: dict[str, Any] = {
        "n1_count": len(arch.n1_facts),
        "n2_count": len(arch.n2_decisions),
        "n3_count": len(arch.n3_omissions),
        "disjoint_layers": arch.disjoint_layers and not overlap,
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
