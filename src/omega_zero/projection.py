from __future__ import annotations

from copy import deepcopy
from typing import Any

from .models import (
    CORE_INVARIANTS,
    AuthorityLevel,
    CloudOmega,
    Manque,
    ManqueStatus,
    RaccordStatus,
    ZeroState,
)


class TransitionError(ValueError):
    """Levée lorsqu'une transition de statut du Manque viole la machine à états ou M1–M5."""


# Transitions autorisées : (from_status, to_status) -> guard_id
ALLOWED_TRANSITIONS: dict[tuple[ManqueStatus, ManqueStatus], str] = {
    (ManqueStatus.OUVERT, ManqueStatus.SOUS_EXPLORATION): "TR-01",
    (ManqueStatus.OUVERT, ManqueStatus.REQUALIFIE): "TR-02",
    (ManqueStatus.OUVERT, ManqueStatus.INACCESSIBLE_DANS_LE_PERIMETRE): "TR-03",
    (ManqueStatus.OUVERT, ManqueStatus.REFUTE_COMME_PROBLEME): "TR-04",
    (ManqueStatus.SOUS_EXPLORATION, ManqueStatus.PARTIELLEMENT_REDUIT): "TR-05",
    (ManqueStatus.SOUS_EXPLORATION, ManqueStatus.RESOLU): "TR-06",
    (ManqueStatus.SOUS_EXPLORATION, ManqueStatus.OUVERT): "TR-07",
    (ManqueStatus.SOUS_EXPLORATION, ManqueStatus.REFUTE_COMME_PROBLEME): "TR-08",
    (ManqueStatus.SOUS_EXPLORATION, ManqueStatus.REQUALIFIE): "TR-09",
    (ManqueStatus.SOUS_EXPLORATION, ManqueStatus.INACCESSIBLE_DANS_LE_PERIMETRE): "TR-10",
    (ManqueStatus.PARTIELLEMENT_REDUIT, ManqueStatus.SOUS_EXPLORATION): "TR-11",
    (ManqueStatus.PARTIELLEMENT_REDUIT, ManqueStatus.RESOLU): "TR-12",
    (ManqueStatus.PARTIELLEMENT_REDUIT, ManqueStatus.REQUALIFIE): "TR-13",
    (ManqueStatus.RESOLU, ManqueStatus.SOUS_EXPLORATION): "TR-14",
    (ManqueStatus.INACCESSIBLE_DANS_LE_PERIMETRE, ManqueStatus.OUVERT): "TR-15",
    (ManqueStatus.REFUTE_COMME_PROBLEME, ManqueStatus.OUVERT): "TR-16",
}


class ManqueStateMachine:
    """Machine à états formelle des 7 statuts canoniques du Manque."""

    @staticmethod
    def transition(
        manque: Manque,
        target_status: ManqueStatus,
        *,
        reason: str,
        actor: str,
        timestamp: str,
        evidence_ref: str | None = None,
        children_ids: list[str] | None = None,
    ) -> str:
        if not reason or not actor or not timestamp:
            raise TransitionError(
                "Toute transition exige reason, actor et timestamp (traçabilité I2)."
            )

        key = (manque.statut, target_status)
        if key not in ALLOWED_TRANSITIONS:
            raise TransitionError(
                f"Transition interdite : {manque.statut.value} -> {target_status.value}"
            )

        guard_id = ALLOWED_TRANSITIONS[key]

        # Gardes spécifiques anti-fabrication (M3 / Autorité ≤ Preuve)
        if target_status == ManqueStatus.RESOLU and not evidence_ref:
            raise TransitionError(
                "Transition vers RÉSOLU refusée sans evidence_ref vérifiable (M3)."
            )
        if target_status == ManqueStatus.SOUS_EXPLORATION and not (
            evidence_ref or manque.tentatives
        ):
            raise TransitionError(
                "Transition vers SOUS_EXPLORATION exige une tentative ou une preuve d'ouverture."
            )
        if target_status == ManqueStatus.REQUALIFIE and not children_ids:
            raise TransitionError(
                "Transition vers REQUALIFIÉ exige au moins un sous-manque enfant traçable."
            )
        if target_status == ManqueStatus.INACCESSIBLE_DANS_LE_PERIMETRE and not evidence_ref:
            raise TransitionError(
                "Transition vers INACCESSIBLE_DANS_LE_PÉRIMÈTRE exige la preuve de barrière."
            )
        if target_status == ManqueStatus.REFUTE_COMME_PROBLEME and not evidence_ref:
            raise TransitionError(
                "Transition vers RÉFUTÉ_COMME_PROBLÈME exige la preuve de fausse prémisse."
            )

        prev = manque.statut
        manque.statut = target_status
        if children_ids:
            for cid in children_ids:
                if cid not in manque.children_ids:
                    manque.children_ids.append(cid)

        manque.transition_log.append(
            {
                "guard_id": guard_id,
                "from": prev.value,
                "to": target_status.value,
                "reason": reason,
                "actor": actor,
                "timestamp": timestamp,
                "evidence_ref": evidence_ref,
            }
        )
        return guard_id


class Pi0Projector:
    """Opérateur de projection Π₀(S_t) = {I, P, M, A, H}."""

    def project(self, state: CloudOmega | ZeroState) -> ZeroState:
        if isinstance(state, ZeroState):
            # Idempotence stricte : Π₀(Π₀(S_t)) = Π₀(S_t)
            return ZeroState(
                invariants=tuple(state.invariants),
                proofs=deepcopy(state.proofs),
                refutations=deepcopy(state.refutations),
                manques=deepcopy(state.manques),
                authorities=dict(state.authorities),
                history=deepcopy(state.history),
                dropped_provisional=[],
            )

        proofs: dict[str, dict[str, Any]] = {}
        refutations: dict[str, dict[str, Any]] = {}
        dropped: list[str] = []

        for rid, raccord in state.raccords.items():
            # Bornage strict : Autorité(c) ≤ Preuve(c)
            if raccord.status == RaccordStatus.REFUTE:
                refutations[rid] = {
                    "id": rid,
                    "label": raccord.label,
                    "authority": AuthorityLevel.AUCUNE.name,
                    "reason": raccord.refutation_reason or "refuted_in_scope",
                    "provenance": raccord.provenance,
                }
            elif (
                raccord.status == RaccordStatus.SUPPORTE_SOUS_CONDITIONS
                and raccord.evidence_level > AuthorityLevel.AUCUNE
            ):
                bounded_auth = min(raccord.authority_level, raccord.evidence_level)
                proofs[rid] = {
                    "id": rid,
                    "label": raccord.label,
                    "authority": bounded_auth.name,
                    "evidence": raccord.evidence_level.name,
                    "conditions": list(raccord.conditions),
                    "scope": raccord.scope,
                }
            elif (
                raccord.status == RaccordStatus.ETABLI
                and raccord.evidence_level >= AuthorityLevel.INTERDISCIPLINAIRE_QUALIFIEE
            ):
                bounded_auth = min(raccord.authority_level, raccord.evidence_level)
                proofs[rid] = {
                    "id": rid,
                    "label": raccord.label,
                    "authority": bounded_auth.name,
                    "evidence": raccord.evidence_level.name,
                    "conditions": list(raccord.conditions),
                    "scope": raccord.scope,
                }
            else:
                # Candidat ou inconnu sans preuve suffisante : autorité retirée au retour au Vide
                dropped.append(f"{rid}:{raccord.status.value}")

        for pid, pval in state.proofs.items():
            if pid not in proofs:
                proofs[pid] = deepcopy(pval)

        # Manques conservés : tout manque non clôturé ou portant une mémoire évolutive
        preserved_manques: dict[str, Manque] = {}
        for mid, manque in state.manques.items():
            if manque.statut != ManqueStatus.RESOLU:
                preserved_manques[mid] = deepcopy(manque)

        minimal_history = [
            entry
            for entry in state.history
            if entry.get("kind") != "PROVISIONAL_DRAFT"
        ]

        return ZeroState(
            invariants=CORE_INVARIANTS,
            proofs=proofs,
            refutations=refutations,
            manques=preserved_manques,
            authorities=dict(state.authorities),
            history=minimal_history,
            dropped_provisional=dropped,
        )

    def verify_idempotence(self, state: CloudOmega | ZeroState) -> bool:
        z1 = self.project(state)
        z2 = self.project(z1)
        return z1.canonical_hash() == z2.canonical_hash() and z1.is_non_empty()
