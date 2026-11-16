from __future__ import annotations

from copy import deepcopy
from typing import Any

from .models import (
    CORE_INVARIANTS,
    AuthorityLevel,
    CloudOmega,
    Conflict4D,
    Container,
    Delta4D,
    DisciplineAssessment,
    LocalMinimalState,
    LocalNode,
    Manque,
    ManqueStatus,
    MergeOutcome,
    Raccord,
    RaccordStatus,
    RevidageStage,
    ZeroState,
    canonical_sha256,
)
from .projection import ManqueStateMachine


class RevidageFailure(RuntimeError):
    """Levée lorsque le revidage viole PREPARE→VERIFY→COMMIT→CLEAN ou ses 5 prédicats."""


class SaturationWithoutDeclarationError(ValueError):
    """Levée si Load(C) est évalué sans déclaration préalable des 6 paramètres."""


class OmegaZeroEngine:
    """Moteur exécutable Supela Ω-ZERO · Local–Cloud–4D."""

    def __init__(self) -> None:
        self.cloud = CloudOmega()
        self.nodes: dict[str, LocalNode] = {}

    def register_local_node(
        self, node_id: str, location: str, jurisdiction: str, authority_scope: str
    ) -> LocalNode:
        node = LocalNode(
            node_id=node_id,
            location=location,
            jurisdiction=jurisdiction,
            A_autorites=[authority_scope],
        )
        self.nodes[node_id] = node
        self.cloud.nodes_registered[node_id] = {
            "location": location,
            "jurisdiction": jurisdiction,
            "authority_scope": authority_scope,
        }
        self.cloud.authorities[node_id] = authority_scope
        self.cloud.history.append(
            {"kind": "REGISTER_NODE", "node_id": node_id, "jurisdiction": jurisdiction}
        )
        return node

    def inject_manque(self, node: LocalNode, manque: Manque) -> None:
        node.U_manques[manque.id] = manque
        node.H_history.append(
            {"kind": "INJECT_MANQUE", "manque_id": manque.id, "statut": manque.statut.value}
        )
        self.cloud.manques[manque.id] = deepcopy(manque)
        self.cloud.history.append(
            {"kind": "CLOUD_RECORD_MANQUE", "manque_id": manque.id, "origin": node.node_id}
        )

    def add_candidate_raccord(
        self,
        node: LocalNode,
        raccord: Raccord,
        manque_id: str | None = None,
        timestamp: str = "t1",
    ) -> None:
        # Un candidat ne reçoit jamais une autorité automatique à l'injection
        if raccord.status == RaccordStatus.CANDIDAT:
            raccord.authority_level = AuthorityLevel.AUCUNE
        raccord.enforce_authority_bound()

        if raccord.id in node.R_raccords:
            raise ValueError(f"Collision d'identifiant raccord {raccord.id} : fusion implicite interdite.")

        node.R_raccords[raccord.id] = raccord
        node.H_history.append(
            {"kind": "ADD_CANDIDAT", "raccord_id": raccord.id, "node": node.node_id}
        )
        self.cloud.raccords[raccord.id] = deepcopy(raccord)

        if manque_id and manque_id in node.U_manques:
            m = node.U_manques[manque_id]
            m.tentatives.append(raccord.id)
            if m.statut == ManqueStatus.OUVERT:
                ManqueStateMachine.transition(
                    m,
                    ManqueStatus.SOUS_EXPLORATION,
                    reason=f"Injection du raccord candidat {raccord.id}",
                    actor=node.node_id,
                    timestamp=timestamp,
                    evidence_ref=raccord.id,
                )
            self.cloud.manques[manque_id] = deepcopy(m)

    def record_discipline_assessments(
        self,
        raccord_id: str,
        assessments: list[DisciplineAssessment],
        conflict_id: str = "C-001",
    ) -> Conflict4D | None:
        self.cloud.assessments.extend(assessments)
        for item in assessments:
            self.cloud.authorities[f"DISC:{item.discipline}"] = item.autorite

        distinct_stances = {a.conclusion_partielle for a in assessments}
        has_conflict = any(a.conflit != "AUCUN" for a in assessments) or len(distinct_stances) > 1
        if has_conflict:
            conflict = Conflict4D(
                id=conflict_id,
                raccord_id=raccord_id,
                disciplines=[a.discipline for a in assessments],
                type="CONFLIT_INTERDISCIPLINAIRE",
                status="CONSERVÉ",
                resolution="NON_ACQUISE",
                notes="Désaccord interdisciplinaire conservé sans écrasement.",
            )
            self.cloud.conflicts[conflict_id] = conflict
            self.cloud.history.append(
                {
                    "kind": "CONFLICT_RECORDED",
                    "conflict_id": conflict_id,
                    "disciplines": conflict.disciplines,
                }
            )
            return conflict
        return None

    def build_delta(
        self,
        node: LocalNode,
        delta_id: str,
        timestamp: str,
        payload: dict[str, Any],
        *,
        parent_hash: str = "GENESIS",
        dependencies: list[str] | None = None,
        contradictions: list[str] | None = None,
        requested_cloud_status: str | None = None,
        international_proof_attached: bool = False,
    ) -> Delta4D:
        return Delta4D(
            delta_id=delta_id,
            node_id=node.node_id,
            jurisdiction=node.jurisdiction,
            timestamp=timestamp,
            authority_scope=node.A_autorites[0] if node.A_autorites else "LOCAL",
            parent_hash=parent_hash,
            payload=payload,
            dependencies=dependencies or [],
            contradictions=contradictions or [],
            requested_cloud_status=requested_cloud_status,
            international_proof_attached=international_proof_attached,
        )

    @staticmethod
    def transferable(delta: Delta4D) -> bool:
        integrity = delta.integrity_hash == delta.compute_hash()
        provenance = bool(delta.node_id and delta.jurisdiction and delta.timestamp)
        authority = bool(delta.authority_scope)
        completeness = delta.complete
        recoverability = delta.recoverable
        return integrity and provenance and authority and completeness and recoverability

    def merge_delta(self, delta: Delta4D) -> MergeOutcome:
        if not self.transferable(delta):
            self.cloud.merge_log.append(
                {"delta_id": delta.delta_id, "outcome": MergeOutcome.REFUSE.value}
            )
            return MergeOutcome.REFUSE

        self.cloud.deltas_received.append(delta)
        outcome = MergeOutcome.ACCEPTE

        # L'ordre de réception n'écrase jamais la provenance ni l'autorité
        for r_data in delta.payload.get("raccords", []):
            rid = r_data["id"]
            requested_global = (
                delta.requested_cloud_status == "ÉTABLI_INTERNATIONALEMENT"
                and not delta.international_proof_attached
            )
            if requested_global:
                outcome = MergeOutcome.ISOLE
                self.cloud.rejected_escalations.append(
                    {
                        "delta_id": delta.delta_id,
                        "node_id": delta.node_id,
                        "raccord_id": rid,
                        "requested": delta.requested_cloud_status,
                        "decision": "REJET_ESCALADE_AUTORITÉ",
                        "preserved_status": "SUPPORTÉ_LOCALEMENT",
                        "preserved_scope": f"{delta.node_id}_UNIQUEMENT",
                    }
                )
                r_obj = Raccord(
                    id=rid,
                    label=r_data["label"],
                    source=r_data.get("source", "L"),
                    target=r_data.get("target", "C"),
                    origin_node=delta.node_id,
                    status=RaccordStatus.SUPPORTE_SOUS_CONDITIONS,
                    authority_level=AuthorityLevel.LOCALE_CONDITIONNELLE,
                    evidence_level=AuthorityLevel.LOCALE_CONDITIONNELLE,
                    scope=f"{delta.node_id}_UNIQUEMENT",
                    provenance=f"{delta.node_id}:{delta.jurisdiction}:{delta.timestamp}",
                    conditions=r_data.get("conditions", ["Portée locale uniquement"]),
                )
            else:
                # Conserve la provenance propre de chaque delta sans écraser les autres nœuds
                scoped_key = f"{rid}@{delta.node_id}" if rid in self.cloud.raccords else rid
                r_obj = Raccord(
                    id=scoped_key,
                    label=r_data["label"],
                    source=r_data.get("source", "L"),
                    target=r_data.get("target", "C"),
                    origin_node=delta.node_id,
                    status=RaccordStatus(r_data.get("status", "CANDIDAT")),
                    authority_level=AuthorityLevel(r_data.get("authority_level", 0)),
                    evidence_level=AuthorityLevel(r_data.get("evidence_level", 0)),
                    scope=f"{delta.node_id}_UNIQUEMENT",
                    provenance=f"{delta.node_id}:{delta.jurisdiction}:{delta.timestamp}",
                    conditions=r_data.get("conditions", []),
                )
                r_obj.enforce_authority_bound()

            self.cloud.raccords[r_obj.id] = r_obj

        if delta.contradictions and outcome == MergeOutcome.ACCEPTE:
            outcome = MergeOutcome.CONTESTE

        self.cloud.merge_log.append(
            {
                "delta_id": delta.delta_id,
                "node_id": delta.node_id,
                "jurisdiction": delta.jurisdiction,
                "timestamp": delta.timestamp,
                "authority_scope": delta.authority_scope,
                "dependencies": list(delta.dependencies),
                "contradictions": list(delta.contradictions),
                "outcome": outcome.value,
            }
        )
        self.cloud.history.append(
            {
                "kind": "MERGE_DELTA",
                "delta_id": delta.delta_id,
                "node_id": delta.node_id,
                "outcome": outcome.value,
            }
        )
        return outcome

    def evaluate_saturation_and_migrate(
        self, c1: Container, c2: Container
    ) -> dict[str, Any]:
        if c1.metric_declaration is None or not c1.metric_declaration.is_complete():
            raise SaturationWithoutDeclarationError(
                "Les 6 paramètres de mesure Load(C) doivent être déclarés avant évaluation."
            )

        load_info = c1.compute_load()
        migrated = False
        if load_info["load"] >= 0.80:
            # Migration reconstructible sans perte d'IDs, statuts, provenance, réfutations ni historique
            c2.objects = deepcopy(c1.objects)
            c2.edges = deepcopy(c1.edges)
            c2.integrity_hashes = deepcopy(c1.integrity_hashes)
            c2.history = deepcopy(c1.history) + [
                {
                    "event": "MIGRATION_COMPLETE",
                    "from": c1.container_id,
                    "to": c2.container_id,
                    "load_trigger": load_info["load"],
                }
            ]
            c2.metric_declaration = deepcopy(c1.metric_declaration)
            migrated = True

        return {
            "load": load_info,
            "migration_triggered": migrated,
            "source_can_reconstruct": c1.can_reconstruct(),
            "target_can_reconstruct": c2.can_reconstruct() if migrated else False,
            "objects_preserved": set(c1.objects.keys()) == set(c2.objects.keys()) if migrated else False,
            "hashes_preserved": c1.integrity_hashes == c2.integrity_hashes if migrated else False,
            "edges_preserved": len(c1.edges) == len(c2.edges) if migrated else False,
        }

    # --- Revidage transactionnel : PREPARE -> VERIFY -> COMMIT -> CLEAN ---

    def prepare_revidage(self, node: LocalNode, delta: Delta4D) -> None:
        node.frozen_delta = delta
        node.revidage_stage = RevidageStage.PREPARE
        node.H_history.append({"kind": "REVIDAGE_PREPARE", "delta_id": delta.delta_id})

    def verify_revidage(
        self,
        node: LocalNode,
        *,
        ack: bool,
        hash_match: bool,
        provenance_ok: bool,
        authority_ok: bool,
        reconstruction_pass: bool,
    ) -> bool:
        if node.revidage_stage != RevidageStage.PREPARE or node.frozen_delta is None:
            raise RevidageFailure("VERIFY exige un état préalable PREPARE avec delta gelé.")

        all_ok = ack and hash_match and provenance_ok and authority_ok and reconstruction_pass
        if not all_ok:
            self._rollback_revidage(node, "ECHEC_PREDICAT_VERIFY")
            return False

        node.revidage_stage = RevidageStage.VERIFY
        node.H_history.append(
            {"kind": "REVIDAGE_VERIFY_OK", "delta_id": node.frozen_delta.delta_id}
        )
        return True

    def commit_revidage(self, node: LocalNode, tx_id: str) -> str:
        if node.revidage_stage != RevidageStage.VERIFY or node.frozen_delta is None:
            self._rollback_revidage(node, "COMMIT_SANS_VERIFY")
            raise RevidageFailure("COMMIT exige un état préalable VERIFY valide.")

        node.commit_tx_id = tx_id
        node.revidage_stage = RevidageStage.COMMIT
        self.cloud.committed_transfers[tx_id] = {
            "tx_id": tx_id,
            "node_id": node.node_id,
            "delta_id": node.frozen_delta.delta_id,
            "delta_hash": node.frozen_delta.integrity_hash,
        }
        node.H_history.append({"kind": "REVIDAGE_COMMIT", "tx_id": tx_id})
        return tx_id

    def clean_revidage(self, node: LocalNode) -> LocalMinimalState:
        if node.revidage_stage != RevidageStage.COMMIT or not node.commit_tx_id:
            self._rollback_revidage(node, "TENTATIVE_CLEAN_AVANT_COMMIT")
            raise RevidageFailure(
                "CLEAN interdit avant COMMIT : rollback local exécuté, données conservées."
            )

        assert node.frozen_delta is not None
        open_local_manques = [
            mid
            for mid, m in node.U_manques.items()
            if m.statut != ManqueStatus.RESOLU
        ]
        minimal = LocalMinimalState(
            identite=node.node_id,
            invariants=list(CORE_INVARIANTS),
            autorites=list(node.A_autorites),
            index_minimal={rid: r.status.value for rid, r in node.R_raccords.items()},
            preuve_transfert=f"{node.commit_tx_id}:{node.frozen_delta.integrity_hash}",
            pointeur_recuperation=f"cloud://omega/transfers/{node.commit_tx_id}",
            manques_locaux=open_local_manques,
        )
        # Libère les observations et preuves lourdes déjà transférées, tout en gardant les manques locaux
        node.D_observations.clear()
        node.P_preuves.clear()
        node.minimal_state = minimal
        node.revidage_stage = RevidageStage.CLEAN
        node.H_history.append({"kind": "REVIDAGE_CLEAN", "tx_id": node.commit_tx_id})
        return minimal

    def _rollback_revidage(self, node: LocalNode, reason: str) -> None:
        node.revidage_stage = RevidageStage.ROLLED_BACK
        node.H_history.append({"kind": "ROLLBACK_LOCAL", "reason": reason})

    # --- E7-A : Réouverture depuis le Vide ---

    def reopen_from_void(
        self,
        node: LocalNode,
        zero_state: ZeroState,
        target_raccord_id: str,
        new_evidence: str,
        manque_id: str,
        timestamp: str = "t_reopen",
    ) -> dict[str, Any]:
        # Reconstruire le cône de dépendance sans détruire Ω
        cone = [target_raccord_id]
        for rid, r in self.cloud.raccords.items():
            if target_raccord_id in r.composed_from or r.id == target_raccord_id:
                if rid not in cone:
                    cone.append(rid)

        if target_raccord_id in self.cloud.raccords:
            target = self.cloud.raccords[target_raccord_id]
            target.status = RaccordStatus.INCONNU
            target.authority_level = AuthorityLevel.AUCUNE
            target.conditions.append(f"Réouvert suite à : {new_evidence}")

        reopened_manque = self.cloud.manques.get(manque_id) or zero_state.manques.get(manque_id)
        if reopened_manque is not None:
            if reopened_manque.statut in (
                ManqueStatus.RESOLU,
                ManqueStatus.PARTIELLEMENT_REDUIT,
            ):
                target_stat = (
                    ManqueStatus.SOUS_EXPLORATION
                )
                ManqueStateMachine.transition(
                    reopened_manque,
                    target_stat,
                    reason=f"NouvellePreuve remet en cause {target_raccord_id}: {new_evidence}",
                    actor=node.node_id,
                    timestamp=timestamp,
                    evidence_ref=new_evidence,
                )
            elif reopened_manque.statut == ManqueStatus.OUVERT:
                ManqueStateMachine.transition(
                    reopened_manque,
                    ManqueStatus.SOUS_EXPLORATION,
                    reason=f"Reprise depuis 0_t avec NouvellePreuve: {new_evidence}",
                    actor=node.node_id,
                    timestamp=timestamp,
                    evidence_ref=new_evidence,
                )
            self.cloud.manques[manque_id] = reopened_manque

        self.cloud.history.append(
            {
                "kind": "REOPEN_CONE",
                "target": target_raccord_id,
                "cone": cone,
                "new_evidence": new_evidence,
            }
        )
        return {
            "cone_reopened": cone,
            "omega_destroyed": self.cloud.destroyed,
            "manque_initial_retrouve": manque_id in self.cloud.manques,
            "refutations_retrouvees": list(zero_state.refutations.keys()),
        }

    # --- E7-B : Émergence strictement candidate ---

    def synthesize_emergent_raccord(
        self,
        new_id: str,
        source: str,
        target: str,
        chain_raccords: list[str],
    ) -> Raccord:
        emergent = Raccord(
            id=new_id,
            label=f"{source} → {target}*",
            source=source,
            target=target,
            origin_node="OMEGA_EMERGENCE",
            status=RaccordStatus.CANDIDAT,
            authority_level=AuthorityLevel.AUCUNE,
            evidence_level=AuthorityLevel.AUCUNE,
            scope="A_TESTER",
            is_emergent=True,
            composed_from=list(chain_raccords),
            validation_required=True,
            provenance="composition:" + "->".join(chain_raccords),
        )
        self.cloud.raccords[emergent.id] = emergent
        self.cloud.history.append(
            {
                "kind": "EMERGENT_CANDIDATE",
                "raccord_id": emergent.id,
                "composed_from": chain_raccords,
            }
        )
        return emergent
