"""Thèse 4 : Vérification Distribuée INV-04/INV-05 (Consensus != élévation niveau de preuve)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from omega_zero.supela_math_core import BoundedAuthorityEvaluation, ProofLatticeLevel

from .common import (
    ORCID_ID,
    ORCID_URI,
    ThesisSpec,
    ThesisStatus,
    ThesisVerificationResult,
    utc_now_iso,
)

SPEC = ThesisSpec(
    these_id="THESIS-VERIF-004-ORCID0009",
    numero=4,
    titre="Vérification Distribuée INV-04/INV-05",
    domaine="Consensus ne peut pas élever niveau preuve N1->N2->N3",
    invariant_id="INV-04/INV-05",
    pdf_filename="THESIS-VERIF-004-ORCID0009.pdf",
    apport_cle="Prouver que consensus != élévation niveau preuve",
    cross_references=("INV-AXE-01", "INV-LUC-PROPOSE", "INV-FASE-01", "N1->N2->N3", "R-00"),
)


@dataclass(frozen=True)
class DistributedConsensusProbe:
    """Sonde vérifiant que le consensus majoritaire n'élève pas le niveau de preuve."""

    validators_agreeing: int
    total_validators: int
    base_proof_level: ProofLatticeLevel
    claimed_elevated_level: ProofLatticeLevel
    has_reproducible_proof: bool = False


DEFAULT_PROBE = DistributedConsensusProbe(
    validators_agreeing=5,
    total_validators=5,
    base_proof_level=ProofLatticeLevel.G1_OBSERVE,
    claimed_elevated_level=ProofLatticeLevel.G1_OBSERVE,
    has_reproducible_proof=False,
)


def verify(probe: DistributedConsensusProbe | None = DEFAULT_PROBE) -> ThesisVerificationResult:
    """Vérifie INV-04/INV-05 : le consensus ne peut jamais élever le niveau de preuve."""
    if probe is None:
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
            indetermine_conditions=["Sonde distribuée absente (None)"],
            details={},
            cross_references=list(SPEC.cross_references),
        )

    bounded = BoundedAuthorityEvaluation(
        object_id=SPEC.these_id,
        proof_level=probe.base_proof_level,
        requested_authority=int(probe.claimed_elevated_level),
        improvement_score=probe.validators_agreeing / max(1, probe.total_validators),
    )

    violations: list[str] = []
    if probe.claimed_elevated_level > probe.base_proof_level and not probe.has_reproducible_proof:
        violations.append(
            "INV-04/INV-05 violé : tentative d'élévation du niveau de preuve par consensus sans épreuve"
        )
    if bounded.auto_authorized_by_improvement:
        violations.append("Auto-autorisation par score de consensus détectée")

    statut = ThesisStatus.CONTROLE if not violations else ThesisStatus.INDETERMINE
    conditions = (
        ["INV-04/INV-05 vérifié : consensus borné par ProofLatticeLevel (Authority <= Proof)"]
        if not violations
        else violations
    )
    details: dict[str, Any] = {
        "validators_agreeing": probe.validators_agreeing,
        "total_validators": probe.total_validators,
        "base_proof_level": probe.base_proof_level.name,
        "claimed_elevated_level": probe.claimed_elevated_level.name,
        "granted_authority": bounded.granted_authority,
        "authority_bounded_ok": bounded.authority_bounded_ok,
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
