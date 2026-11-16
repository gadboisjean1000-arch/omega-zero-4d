from __future__ import annotations

import base64
import zlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .models import canonical_sha256


class GuardKernelError(ValueError):
    """Levée lors d'une violation de SUP-ICI-01 ou des règles de passage G0..G5."""


class CompressionFailureError(GuardKernelError):
    """Levée lorsque le test de perte de sens retourne COMPRESSION-FAIL."""


class GenerationStage(str, Enum):
    G0 = "G0"  # SOURCE
    G1 = "G1"  # TRAVAIL
    G2 = "G2"  # VALIDATION
    G3 = "G3"  # CONSOLIDATION
    G4 = "G4"  # NON-RÉCLAMÉ
    G5 = "G5"  # DERNIER PASSAGE


class CompressionLevel(str, Enum):
    C0 = "C0"  # Conservation intégrale
    C1 = "C1"  # Compression réversible
    C2 = "C2"  # Résidu sémantique


class AccessibilityMode(str, Enum):
    DIRECT = "DIRECT"
    REFERENTIAL = "REFERENTIAL"
    RECONSTRUCTIBLE = "RECONSTRUCTIBLE"


class KernelObjectStatus(str, Enum):
    HYPOTHESE = "HYPOTHESE"
    FAIT = "FAIT"
    CONTRADICTION = "CONTRADICTION"
    REFUTATION = "REFUTATION"
    INCONNU = "INCONNU"
    NON_RECLAME = "NON-RÉCLAMÉ"
    RECLAME = "RÉCLAMÉ"


class G5Decision(str, Enum):
    CONSERVATION_MINIMALE = "CONSERVATION_MINIMALE"
    TRANSFERT = "TRANSFERT"
    REJET_JUSTIFIE = "REJET_JUSTIFIE"


CONTINUITY_KERNEL_ELEMENTS: tuple[str, ...] = (
    "identite",
    "provenance",
    "decisions",
    "preuves",
    "limites",
    "dependances",
    "transformation",
)

SEMANTIC_RESIDUE_REQUIRED_FIELDS: tuple[str, ...] = (
    "identity",
    "provenance",
    "original_hash",
    "status",
    "scope",
    "dependencies",
    "transformation",
    "reason",
    "reopening_conditions",
    "location",
)


@dataclass
class SemanticResidue:
    """Résidu sémantique minimal R_min(O) pour la compression C2."""

    identity: dict[str, str]
    provenance: dict[str, str]
    original_hash: str
    status: str
    scope: str
    dependencies: list[str]
    transformation: str
    reason: str
    reopening_conditions: list[str]
    location: str
    decisions: list[str] = field(default_factory=list)
    proof_refs: list[str] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity": dict(self.identity),
            "provenance": dict(self.provenance),
            "original_hash": self.original_hash,
            "status": self.status,
            "scope": self.scope,
            "dependencies": list(self.dependencies),
            "transformation": self.transformation,
            "reason": self.reason,
            "reopening_conditions": list(self.reopening_conditions),
            "location": self.location,
            "decisions": list(self.decisions),
            "proof_refs": list(self.proof_refs),
            "contradictions": list(self.contradictions),
        }

    def residue_hash(self) -> str:
        return canonical_sha256(self.to_dict())


@dataclass
class SemanticLossTestResult:
    """Résultat du test de perte de sens sur les 8 questions critiques."""

    passed: bool
    verdict: str
    answers: dict[str, bool]
    missing_answers: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "verdict": self.verdict,
            "answers": dict(self.answers),
            "missing_answers": list(self.missing_answers),
        }


@dataclass
class KernelObject:
    """Objet traçable traversant les générations G0..G5 sous SUP-ICI-01."""

    object_id: str
    object_type: str
    generation: GenerationStage
    author: str
    origin: str
    creation_context: str
    raw_content: bytes | None
    compressed_b64: str | None
    original_hash: str
    status: KernelObjectStatus
    scope: str
    dependencies: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    proof_refs: list[str] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)
    compression_level: CompressionLevel = CompressionLevel.C0
    accessibility_mode: AccessibilityMode = AccessibilityMode.DIRECT
    location: str = "inline://active-store"
    reopening_conditions: list[str] = field(default_factory=list)
    authority: str = "PENDING_HUMAN_RATIFICATION"
    residue: SemanticResidue | None = None
    transformation_history: list[dict[str, Any]] = field(default_factory=list)
    rejection_register_preserved: bool = True

    def continuity_kernel(self) -> dict[str, Any]:
        return {
            "identite": {"id": self.object_id, "type": self.object_type},
            "provenance": {
                "author": self.author,
                "origin": self.origin,
                "context": self.creation_context,
            },
            "decisions": list(self.decisions),
            "preuves": list(self.proof_refs),
            "limites": self.scope,
            "dependances": list(self.dependencies),
            "transformation": list(self.transformation_history),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "object_id": self.object_id,
            "object_type": self.object_type,
            "generation": self.generation.value,
            "author": self.author,
            "origin": self.origin,
            "creation_context": self.creation_context,
            "original_hash": self.original_hash,
            "status": self.status.value,
            "scope": self.scope,
            "dependencies": list(self.dependencies),
            "decisions": list(self.decisions),
            "proof_refs": list(self.proof_refs),
            "contradictions": list(self.contradictions),
            "compression_level": self.compression_level.value,
            "accessibility_mode": self.accessibility_mode.value,
            "location": self.location,
            "reopening_conditions": list(self.reopening_conditions),
            "authority": self.authority,
            "residue": self.residue.to_dict() if self.residue else None,
            "transformation_history": list(self.transformation_history),
            "rejection_register_preserved": self.rejection_register_preserved,
        }


@dataclass
class GenerationTransitionRecord:
    """Entrée structurée du registre de génération (schema supela-guard-kernel/1)."""

    object_id: str
    from_generation: str
    to_generation: str
    previous_hash: str
    residue_hash: str
    compression_level: str
    preserved_fields: list[str]
    removed_content: str
    reason: str
    reversible: bool
    authority: str
    accessibility_mode: str
    semantic_loss_passed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "object_id": self.object_id,
            "from_generation": self.from_generation,
            "to_generation": self.to_generation,
            "previous_hash": self.previous_hash,
            "residue_hash": self.residue_hash,
            "compression_level": self.compression_level,
            "preserved_fields": list(self.preserved_fields),
            "removed_content": self.removed_content,
            "reason": self.reason,
            "reversible": self.reversible,
            "authority": self.authority,
            "accessibility_mode": self.accessibility_mode,
            "semantic_loss_passed": self.semantic_loss_passed,
        }


ALLOWED_GENERATION_FLOW: set[tuple[GenerationStage, GenerationStage]] = {
    (GenerationStage.G0, GenerationStage.G1),
    (GenerationStage.G1, GenerationStage.G2),
    (GenerationStage.G2, GenerationStage.G3),
    (GenerationStage.G3, GenerationStage.G4),
    (GenerationStage.G4, GenerationStage.G5),
    # Réclamation depuis G4 vers cycle actif
    (GenerationStage.G4, GenerationStage.G1),
    (GenerationStage.G4, GenerationStage.G2),
    # Compaction directe autorisée vers G4 depuis travail/validation si non réclamé
    (GenerationStage.G2, GenerationStage.G4),
}


class SupelaGuardKernel:
    """Noyau exécutable Supela-Guard-Kernel (SUP-ICI-01, C0/C1/C2, G0..G5)."""

    def __init__(self) -> None:
        self.objects: dict[str, KernelObject] = {}
        self.registry: list[GenerationTransitionRecord] = []
        self.rejection_registry: list[dict[str, Any]] = []

    def create_g0_object(
        self,
        *,
        object_id: str,
        object_type: str,
        content: bytes,
        author: str,
        origin: str,
        creation_context: str,
        status: KernelObjectStatus = KernelObjectStatus.HYPOTHESE,
        scope: str = "PERIMETRE_INITIAL",
        dependencies: list[str] | None = None,
        proof_refs: list[str] | None = None,
        contradictions: list[str] | None = None,
        reopening_conditions: list[str] | None = None,
    ) -> KernelObject:
        if not object_id or not author or not origin:
            raise GuardKernelError("G0 exige identifiant, auteur et origine non vides (SUP-ICI-01).")
        if not content:
            raise GuardKernelError("G0 exige un contenu initial non vide.")

        digest = canonical_sha256(base64.b64encode(content).decode("ascii"))
        obj = KernelObject(
            object_id=object_id,
            object_type=object_type,
            generation=GenerationStage.G0,
            author=author,
            origin=origin,
            creation_context=creation_context,
            raw_content=content,
            compressed_b64=None,
            original_hash=digest,
            status=status,
            scope=scope,
            dependencies=list(dependencies or []),
            decisions=[],
            proof_refs=list(proof_refs or []),
            contradictions=list(contradictions or []),
            compression_level=CompressionLevel.C0,
            accessibility_mode=AccessibilityMode.DIRECT,
            location=f"cas://sha256/{digest}",
            reopening_conditions=list(
                reopening_conditions or ["Nouvelle preuve, nouvelle dépendance ou contradiction"]
            ),
            authority="PENDING_HUMAN_RATIFICATION",
        )
        self.objects[object_id] = obj
        return obj

    @staticmethod
    def run_semantic_loss_test(
        before_obj: KernelObject,
        residue: SemanticResidue,
        *,
        reversible: bool,
    ) -> SemanticLossTestResult:
        """Évalue les 8 questions essentielles du test de perte de sens."""
        answers: dict[str, bool] = {
            "q1_identity": bool(
                residue.identity.get("id") == before_obj.object_id
                and residue.identity.get("type") == before_obj.object_type
            ),
            "q2_origin": bool(
                residue.provenance.get("origin") == before_obj.origin and residue.provenance.get("origin")
            ),
            "q3_contributor": bool(
                residue.provenance.get("author") == before_obj.author and residue.provenance.get("author")
            ),
            "q4_status": bool(residue.status) and not (
                before_obj.status == KernelObjectStatus.HYPOTHESE
                and residue.status == KernelObjectStatus.FAIT.value
                and len(residue.proof_refs) <= len(before_obj.proof_refs)
            ),
            "q5_transformation_reason": bool(residue.transformation and residue.reason),
            "q6_dependencies": set(before_obj.dependencies).issubset(set(residue.dependencies)),
            "q7_scope": bool(residue.scope) and residue.scope == before_obj.scope,
            "q8_retrievable_or_reopenable": bool(residue.reopening_conditions)
            and bool(residue.original_hash == before_obj.original_hash)
            and (reversible or bool(residue.location)),
        }
        # Règles strictes d'interdiction SUP-ICI-01
        if set(before_obj.contradictions) - set(residue.contradictions):
            answers["q6_contradictions_preserved"] = False
        if set(before_obj.proof_refs) - set(residue.proof_refs):
            answers["q8_proofs_preserved"] = False

        missing = [k for k, ok in answers.items() if not ok]
        passed = len(missing) == 0
        return SemanticLossTestResult(
            passed=passed,
            verdict="PASS" if passed else "COMPRESSION-FAIL",
            answers=answers,
            missing_answers=missing,
        )

    @staticmethod
    def verify_sup_ici_01(before: KernelObject, after: KernelObject) -> tuple[bool, list[str]]:
        """Vérifie K_n ⊆ Accessible(G_{n+1}) et les interdictions intercycles."""
        violations: list[str] = []
        k_before = before.continuity_kernel()
        k_after = after.continuity_kernel()

        if k_after["identite"] != k_before["identite"]:
            violations.append("identite_perdue_ou_modifiee")
        if (
            k_after["provenance"].get("author") != k_before["provenance"].get("author")
            or k_after["provenance"].get("origin") != k_before["provenance"].get("origin")
            or not k_after["provenance"].get("author")
            or not k_after["provenance"].get("origin")
        ):
            violations.append("provenance_auteur_ou_origine_perdue")
        if not set(k_before["decisions"]).issubset(set(k_after["decisions"])):
            violations.append("decisions_perdues")
        if not set(k_before["preuves"]).issubset(set(k_after["preuves"])):
            violations.append("preuves_remplacees_ou_perdues")
        if not k_after["limites"]:
            violations.append("limites_perdues")
        if not set(k_before["dependances"]).issubset(set(k_after["dependances"])):
            violations.append("dependances_perdues")
        if not k_after["transformation"]:
            violations.append("transformation_non_documentee")
        if not set(before.contradictions).issubset(set(after.contradictions)):
            violations.append("contradiction_active_effacee")
        if (
            before.status == KernelObjectStatus.HYPOTHESE
            and after.status == KernelObjectStatus.FAIT
            and len(after.proof_refs) <= len(before.proof_refs)
        ):
            violations.append("hypothese_promue_en_fait_par_compression")
        if (
            after.accessibility_mode == AccessibilityMode.RECONSTRUCTIBLE
            and (not after.location or not after.original_hash or not after.transformation_history)
        ):
            violations.append("reconstructibilite_declaree_sans_preuve")
        if after.compression_level == CompressionLevel.C2 and after.raw_content is not None:
            violations.append("c2_pretend_copie_integrale")
        return len(violations) == 0, violations

    def compress_and_advance(
        self,
        object_id: str,
        *,
        target_generation: GenerationStage,
        compression_level: CompressionLevel,
        reason: str,
        transformation: str,
        new_status: KernelObjectStatus | None = None,
        added_decisions: list[str] | None = None,
        added_proofs: list[str] | None = None,
        claim_full_copy: bool = False,
        authority: str = "PENDING_HUMAN_RATIFICATION",
        inherit_authority_silently: bool = False,
    ) -> tuple[KernelObject, GenerationTransitionRecord]:
        if object_id not in self.objects:
            raise GuardKernelError(f"Objet inconnu : {object_id}")

        before = self.objects[object_id]
        if (before.generation, target_generation) not in ALLOWED_GENERATION_FLOW:
            raise GuardKernelError(
                f"Transition de génération interdite : {before.generation.value} -> {target_generation.value}"
            )
        if inherit_authority_silently:
            raise GuardKernelError(
                "Interdit SUP-ICI-01 : héritage silencieux de l'autorité normative précédente."
            )
        if compression_level == CompressionLevel.C2 and claim_full_copy:
            raise CompressionFailureError(
                "COMPRESSION-FAIL : C2 ne doit jamais être présenté comme une copie complète."
            )

        status_out = new_status or (
            KernelObjectStatus.NON_RECLAME
            if target_generation == GenerationStage.G4
            else before.status
        )
        if (
            before.status == KernelObjectStatus.HYPOTHESE
            and status_out == KernelObjectStatus.FAIT
            and not added_proofs
        ):
            raise GuardKernelError(
                "Interdit SUP-ICI-01 : impossible de transformer une hypothèse en fait sans nouvelle preuve."
            )

        decisions_out = list(before.decisions) + list(added_decisions or [])
        proofs_out = list(before.proof_refs) + list(added_proofs or [])

        compressed_b64: str | None = before.compressed_b64
        raw_out: bytes | None = before.raw_content
        reversible = True
        removed_content = "none"
        accessibility = AccessibilityMode.DIRECT

        if compression_level == CompressionLevel.C0:
            if before.raw_content is None:
                raise CompressionFailureError("COMPRESSION-FAIL : C0 exige les octets intégraux.")
            removed_content = "none"
            accessibility = AccessibilityMode.DIRECT
        elif compression_level == CompressionLevel.C1:
            if before.raw_content is None:
                raise CompressionFailureError("COMPRESSION-FAIL : C1 exige une source restaurable.")
            compressed_bytes = zlib.compress(before.raw_content, level=9)
            if zlib.decompress(compressed_bytes) != before.raw_content:
                raise CompressionFailureError("COMPRESSION-FAIL : échec de restitution exacte C1.")
            compressed_b64 = base64.b64encode(compressed_bytes).decode("ascii")
            raw_out = None
            removed_content = "none_reversible_zlib"
            accessibility = AccessibilityMode.RECONSTRUCTIBLE
        elif compression_level == CompressionLevel.C2:
            raw_out = None
            compressed_b64 = None
            reversible = False
            removed_content = "declared"
            accessibility = AccessibilityMode.REFERENTIAL
            if target_generation == GenerationStage.G4 and new_status is None:
                status_out = KernelObjectStatus.NON_RECLAME

        residue = SemanticResidue(
            identity={"id": before.object_id, "type": before.object_type},
            provenance={
                "author": before.author,
                "origin": before.origin,
                "context": before.creation_context,
            },
            original_hash=before.original_hash,
            status=status_out.value,
            scope=before.scope,
            dependencies=list(before.dependencies),
            transformation=transformation,
            reason=reason,
            reopening_conditions=list(before.reopening_conditions),
            location=before.location,
            decisions=decisions_out,
            proof_refs=proofs_out,
            contradictions=list(before.contradictions),
        )
        loss_test = self.run_semantic_loss_test(before, residue, reversible=reversible)
        if not loss_test.passed:
            raise CompressionFailureError(
                f"COMPRESSION-FAIL : perte critique sur {loss_test.missing_answers}"
            )

        tx_entry = {
            "from": before.generation.value,
            "to": target_generation.value,
            "compression": compression_level.value,
            "transformation": transformation,
            "reason": reason,
        }
        after = KernelObject(
            object_id=before.object_id,
            object_type=before.object_type,
            generation=target_generation,
            author=before.author,
            origin=before.origin,
            creation_context=before.creation_context,
            raw_content=raw_out,
            compressed_b64=compressed_b64,
            original_hash=before.original_hash,
            status=status_out,
            scope=before.scope,
            dependencies=list(before.dependencies),
            decisions=decisions_out,
            proof_refs=proofs_out,
            contradictions=list(before.contradictions),
            compression_level=compression_level,
            accessibility_mode=accessibility,
            location=before.location,
            reopening_conditions=list(before.reopening_conditions),
            authority=authority,
            residue=residue,
            transformation_history=list(before.transformation_history) + [tx_entry],
            rejection_register_preserved=before.rejection_register_preserved,
        )

        ok, violations = self.verify_sup_ici_01(before, after)
        if not ok:
            raise GuardKernelError(f"Violation SUP-ICI-01 : {violations}")

        record = GenerationTransitionRecord(
            object_id=after.object_id,
            from_generation=before.generation.value,
            to_generation=target_generation.value,
            previous_hash=before.original_hash,
            residue_hash=residue.residue_hash(),
            compression_level=compression_level.value,
            preserved_fields=[
                "identity",
                "provenance",
                "status",
                "scope",
                "dependencies",
                "reopening_conditions",
            ],
            removed_content=removed_content,
            reason=reason,
            reversible=reversible,
            authority=authority,
            accessibility_mode=accessibility.value,
            semantic_loss_passed=loss_test.passed,
        )
        self.objects[object_id] = after
        self.registry.append(record)
        return after, record

    def decompress_c1(self, object_id: str) -> bytes:
        obj = self.objects[object_id]
        if obj.raw_content is not None:
            return obj.raw_content
        if obj.compression_level != CompressionLevel.C1 or not obj.compressed_b64:
            raise GuardKernelError(f"Restitution directe impossible hors C0/C1 pour {object_id}.")
        return zlib.decompress(base64.b64decode(obj.compressed_b64))

    def reclaim_from_g4(
        self,
        object_id: str,
        *,
        target_generation: GenerationStage = GenerationStage.G1,
        trigger_reason: str,
    ) -> tuple[KernelObject, GenerationTransitionRecord]:
        obj = self.objects[object_id]
        if obj.generation != GenerationStage.G4:
            raise GuardKernelError("La réclamation ne s'applique qu'aux objets en G4 (NON-RÉCLAMÉ).")
        if target_generation not in {GenerationStage.G1, GenerationStage.G2}:
            raise GuardKernelError("Un objet réclamé doit revenir vers G1 ou G2.")
        return self.compress_and_advance(
            object_id,
            target_generation=target_generation,
            compression_level=CompressionLevel.C2,
            reason=trigger_reason,
            transformation="reclaim_from_g4_to_active_cycle",
            new_status=KernelObjectStatus.RECLAME,
            added_decisions=[f"RECLAME:{trigger_reason}"],
            authority="PENDING_HUMAN_RATIFICATION",
        )

    def last_passage_g5(
        self,
        object_id: str,
        *,
        decision: G5Decision,
        dependencies_checked: bool,
        reason: str,
        human_ratified: bool,
    ) -> tuple[KernelObject, GenerationTransitionRecord]:
        obj = self.objects[object_id]
        if obj.generation != GenerationStage.G4:
            raise GuardKernelError("G5 (DERNIER PASSAGE) exige un passage préalable par G4.")
        if not dependencies_checked:
            raise GuardKernelError("G5 exige la recherche d'incidences et vérification des dépendances.")
        if not reason:
            raise GuardKernelError("G5 exige un motif explicite.")
        if decision == G5Decision.REJET_JUSTIFIE and not human_ratified:
            raise GuardKernelError(
                "Le rejet définitif exige l'autorité normative humaine (human_ratified=True)."
            )

        authority = "RATIFIED_HUMAN" if human_ratified else "PENDING_HUMAN_RATIFICATION"
        after, record = self.compress_and_advance(
            object_id,
            target_generation=GenerationStage.G5,
            compression_level=CompressionLevel.C2,
            reason=reason,
            transformation=f"g5_last_passage:{decision.value}",
            added_decisions=[f"G5:{decision.value}"],
            authority=authority,
        )
        if decision == G5Decision.REJET_JUSTIFIE:
            # RejetDuContenu ≠ EffacementDeLExistenceHistorique
            self.rejection_registry.append(
                {
                    "object_id": after.object_id,
                    "original_hash": after.original_hash,
                    "residue_hash": record.residue_hash,
                    "reason": reason,
                    "dependencies": list(after.dependencies),
                    "authority": authority,
                    "historical_existence_preserved": True,
                }
            )
        return after, record
