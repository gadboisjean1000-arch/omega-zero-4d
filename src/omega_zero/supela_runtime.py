"""Supela Runtime v0.2 & Local Bridge v0.1 — Système nerveux exécutable (L0–L7).

Cycle opérationnel :
CONCEPT (L1) -> CODE (L2) -> EXÉCUTION (L3) -> PREUVE (L4) -> CONTRADICTION (L5)
├── ouverte  --> RÉVISION (L6, generation + 1) --> CODE (L2)
└── absente  --> CANDIDAT À RATIFICATION (L7)
                  └── Jean-François Gadbois (ACCEPT | REFUSE | ADJOURN)
                        └── RÉOUVERTURE POSSIBLE (sans effacement de l'historique)
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from .models import canonical_sha256

HUMAN_NORMATIVE_AUTHORITY = "Jean-François Gadbois"
GENESIS_PREV_HASH = "0" * 64

# Empreintes SHA-256 rapportées dans la conversation Microsoft 365 Copilot
# (conservées avec honnêteté épistémique : RAPPORTÉ hors session Skype ASM, EXÉCUTÉ localement dans omega-zero-4d)
REPORTED_M365_ARTIFACTS: dict[str, dict[str, str]] = {
    "supela-local-bridge-v0.1.zip": {
        "sha256": "650337274c316f1cf76f47be5489eec592fa6bcfbdb5fbc614809cf8c2085710",
        "layer": "L0_TRANSPORT",
        "epistemic_status": "RAPPORTE_M365_REIMPLEMENTE_ET_EXECUTE_LOCALEMENT",
    },
    "supela-runtime-v0.2.zip": {
        "sha256": "b5fab177db18288ed78a60a9cd8e84dd866034e0557c0f1c95ed9c06cdebab83",
        "layer": "L0_TO_L7_NERVOUS_SYSTEM",
        "epistemic_status": "RAPPORTE_M365_REIMPLEMENTE_ET_EXECUTE_LOCALEMENT",
    },
}


class SupelaRuntimeError(RuntimeError):
    """Erreur de base du Runtime Supela v0.2."""


class PathBoundaryError(SupelaRuntimeError):
    """Tentative d'accès à un chemin situé hors de la racine autorisée du dépôt."""


class UnauthorizedCommandError(SupelaRuntimeError):
    """Tentative d'exécution d'une commande absente de la liste blanche L0."""


class LedgerTamperError(SupelaRuntimeError):
    """Altération ou rupture de chaîne SHA-256 détectée dans le registre probatoire JSONL."""


class ContradictionBlocksRatificationError(SupelaRuntimeError):
    """Une contradiction ouverte bloque mécaniquement la soumission à ratification."""


class SupelaAuthorityError(SupelaRuntimeError):
    """Violation de la frontière normative : seul Jean-François Gadbois peut ratifier."""


class InvalidStateTransitionError(SupelaRuntimeError):
    """Transition d'état invalide dans le cycle L1–L7."""


class DossierStatus(StrEnum):
    CONCEPT = "CONCEPT"
    CODE_REGISTERED = "CODE_REGISTERED"
    EXECUTED = "EXECUTED"
    EVIDENCE_COLLECTED = "EVIDENCE_COLLECTED"
    CONTRADICTOIRE = "CONTRADICTOIRE"
    REVISION_REQUESTED = "REVISION_REQUESTED"
    CANDIDAT_A_RATIFICATION = "CANDIDAT_A_RATIFICATION"
    RATIFIED_ACCEPTED = "RATIFIED_ACCEPTED"
    RATIFIED_REFUSED = "RATIFIED_REFUSED"
    RATIFIED_ADJOURNED = "RATIFIED_ADJOURNED"
    REOPENED = "REOPENED"


class RatificationDecision(StrEnum):
    ACCEPT = "ACCEPT"
    REFUSE = "REFUSE"
    ADJOURN = "ADJOURN"


class ObservedOutcome(StrEnum):
    OBSERVED_PASS_IN_SCOPE = "OBSERVED_PASS_IN_SCOPE"
    OBSERVED_FAIL_IN_SCOPE = "OBSERVED_FAIL_IN_SCOPE"


class ProofStatus(StrEnum):
    PASS_IN_SCOPE = "PASS_IN_SCOPE"
    FAIL_IN_SCOPE = "FAIL_IN_SCOPE"
    INCONNU = "INCONNU"


class ContradictionStatus(StrEnum):
    OPEN = "OPEN"
    SUPERSEDED_BY_REVISION = "SUPERSEDED_BY_REVISION"


def _utc_now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def default_allowed_commands(python_exe: str | None = None) -> dict[str, list[str]]:
    """Retourne le catalogue par défaut des commandes explicitement autorisées (sans shell libre)."""
    py = python_exe or sys.executable
    return {
        "python_version": [py, "-c", "import sys; print(sys.version.split()[0])"],
        "probe_pass": [py, "-c", "print('SUPELA_EXEC_PASS_IN_SCOPE')"],
        "probe_fail": [py, "-c", "import sys; print('SUPELA_EXEC_FAIL_IN_SCOPE'); sys.exit(1)"],
        "a12_check": [py, "scripts/verify_a12.py"],
        "vr_check": [py, "scripts/vr_compliance_check.py"],
        "python_tests": [py, "-m", "pytest", "-q", "tests/test_schemas.py"],
    }


@dataclass
class SupelaLocalBridge:
    """Pont local L0 Transport : lecture bornée, commandes en liste blanche et journal SHA-256 append-only."""

    repository_root: Path
    ledger_path: Path
    allowed_commands: dict[str, list[str]] = field(default_factory=default_allowed_commands)

    def __post_init__(self) -> None:
        self.repository_root = self.repository_root.resolve()
        self.ledger_path = self.ledger_path.resolve()
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.ledger_path.exists():
            self.ledger_path.write_text("", encoding="utf-8")

    def resolve_bounded_path(self, relative_or_abs: str | Path) -> Path:
        """Vérifie qu'un chemin reste strictement à l'intérieur de repository_root."""
        raw = Path(relative_or_abs)
        candidate = (raw if raw.is_absolute() else (self.repository_root / raw)).resolve()
        try:
            candidate.relative_to(self.repository_root)
        except ValueError as exc:
            raise PathBoundaryError(
                f"Accès refusé hors du dépôt Supela ({self.repository_root}) : {relative_or_abs}"
            ) from exc
        return candidate

    def read_bounded_file(self, relative_path: str) -> bytes:
        target = self.resolve_bounded_path(relative_path)
        if not target.is_file():
            raise FileNotFoundError(f"Artefact introuvable dans le dépôt : {relative_path}")
        return target.read_bytes()

    def write_bounded_file(self, relative_path: str, content: bytes) -> Path:
        target = self.resolve_bounded_path(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return target

    def append_ledger_event(
        self,
        event_type: str,
        dossier_id: str,
        generation: int,
        payload: dict[str, Any],
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        """Ajoute un événement au journal probatoire JSONL chaîné par SHA-256."""
        verification = self.verify_ledger()
        if not verification["valid"]:
            raise LedgerTamperError(
                f"Impossible d'écrire dans un registre falsifié : {verification['error']}"
            )
        prev_hash = str(verification["head_hash"])
        index = int(verification["entry_count"]) + 1
        ts = timestamp or _utc_now_iso()
        payload_sha256 = canonical_sha256(payload)
        core = {
            "index": index,
            "timestamp": ts,
            "event_type": event_type,
            "dossier_id": dossier_id,
            "generation": generation,
            "payload_sha256": payload_sha256,
            "prev_hash": prev_hash,
        }
        entry_hash = canonical_sha256(core)
        entry = {**core, "entry_hash": entry_hash}
        with self.ledger_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, sort_keys=True, ensure_ascii=False) + "\n")
        return entry

    def verify_ledger(self) -> dict[str, Any]:
        """Vérifie l'intégrité complète de la chaîne SHA-256 du journal probatoire JSONL."""
        if not self.ledger_path.exists():
            return {
                "valid": True,
                "entry_count": 0,
                "head_hash": GENESIS_PREV_HASH,
                "error": None,
            }
        lines = [
            ln.strip()
            for ln in self.ledger_path.read_text(encoding="utf-8").splitlines()
            if ln.strip()
        ]
        prev_hash = GENESIS_PREV_HASH
        for idx, raw in enumerate(lines, start=1):
            try:
                entry = json.loads(raw)
            except json.JSONDecodeError as exc:
                return {
                    "valid": False,
                    "entry_count": idx - 1,
                    "head_hash": prev_hash,
                    "error": f"JSON invalide à la ligne {idx}: {exc}",
                }
            if entry.get("index") != idx:
                return {
                    "valid": False,
                    "entry_count": idx - 1,
                    "head_hash": prev_hash,
                    "error": f"Index séquentiel rompu à la ligne {idx}",
                }
            if entry.get("prev_hash") != prev_hash:
                return {
                    "valid": False,
                    "entry_count": idx - 1,
                    "head_hash": prev_hash,
                    "error": f"Rupture de chaînage prev_hash à la ligne {idx}",
                }
            core = {
                "index": entry.get("index"),
                "timestamp": entry.get("timestamp"),
                "event_type": entry.get("event_type"),
                "dossier_id": entry.get("dossier_id"),
                "generation": entry.get("generation"),
                "payload_sha256": entry.get("payload_sha256"),
                "prev_hash": entry.get("prev_hash"),
            }
            expected_hash = canonical_sha256(core)
            if entry.get("entry_hash") != expected_hash:
                return {
                    "valid": False,
                    "entry_count": idx - 1,
                    "head_hash": prev_hash,
                    "error": f"Empreinte entry_hash altérée à la ligne {idx}",
                }
            prev_hash = expected_hash

        return {
            "valid": True,
            "entry_count": len(lines),
            "head_hash": prev_hash,
            "error": None,
        }

    def run_allowed_command(self, command_key: str, timeout: int = 30) -> dict[str, Any]:
        """Exécute une commande de la liste blanche sans interpréteur shell libre."""
        if command_key not in self.allowed_commands:
            raise UnauthorizedCommandError(
                f"Commande '{command_key}' refusée : absente de la liste blanche L0 ({sorted(self.allowed_commands)})"
            )
        argv = list(self.allowed_commands[command_key])
        if not argv:
            raise UnauthorizedCommandError(f"Commande '{command_key}' vide.")
        proc = subprocess.run(
            argv,
            cwd=self.repository_root,
            shell=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return {
            "command_key": command_key,
            "argv": argv,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip()[:1000],
            "stderr": proc.stderr.strip()[:1000],
        }


class SupelaRuntime:
    """Système nerveux exécutable Supela v0.2 (couches L0 à L7)."""

    def __init__(
        self,
        repository_root: Path,
        state_dir: Path | None = None,
        allowed_commands: dict[str, list[str]] | None = None,
    ) -> None:
        self.repository_root = repository_root.resolve()
        self.state_dir = (state_dir or (self.repository_root / ".omega_vault" / "supela_runtime_v02")).resolve()
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.dossiers_dir = self.state_dir / "dossiers"
        self.dossiers_dir.mkdir(parents=True, exist_ok=True)
        self.bridge = SupelaLocalBridge(
            repository_root=self.repository_root,
            ledger_path=self.state_dir / "ledger.jsonl",
            allowed_commands=allowed_commands or default_allowed_commands(),
        )
        self._dossiers: dict[str, dict[str, Any]] = {}

    def _compute_state_hash(self, state: dict[str, Any]) -> str:
        body = {k: v for k, v in state.items() if k != "state_hash"}
        return canonical_sha256(body)

    def _save_state(self, state: dict[str, Any]) -> dict[str, Any]:
        state["state_hash"] = self._compute_state_hash(state)
        dossier_id = str(state["dossier_id"])
        self._dossiers[dossier_id] = state
        target = self.dossiers_dir / f"{dossier_id}.json"
        target.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
        return state

    def get_state(self, dossier_id: str) -> dict[str, Any]:
        if dossier_id in self._dossiers:
            return self._dossiers[dossier_id]
        target = self.dossiers_dir / f"{dossier_id}.json"
        if not target.exists():
            raise KeyError(f"Dossier Supela inconnu : {dossier_id}")
        loaded: dict[str, Any] = json.loads(target.read_text(encoding="utf-8"))
        expected = self._compute_state_hash(loaded)
        if loaded.get("state_hash") != expected:
            raise LedgerTamperError(f"Empreinte d'état invalide pour le dossier {dossier_id}")
        self._dossiers[dossier_id] = loaded
        return loaded

    def _record_transition(
        self,
        state: dict[str, Any],
        *,
        layer: str,
        to_status: DossierStatus,
        actor: str,
        reason: str,
        timestamp: str,
    ) -> None:
        from_status = state.get("status")
        step = len(state["history"]) + 1
        state["history"].append(
            {
                "step": step,
                "layer": layer,
                "from_status": from_status,
                "to_status": to_status.value,
                "generation": state["generation"],
                "actor": actor,
                "reason": reason,
                "timestamp": timestamp,
            }
        )
        state["status"] = to_status.value

    # ------------------------------------------------------------------
    # L1 : CONCEPT
    # ------------------------------------------------------------------
    def create_concept(
        self,
        dossier_id: str,
        statement: str,
        scope: str,
        provenance: str = "Supela-Research-Loop",
        actor: str = "SupelaAgent",
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        if not dossier_id.strip() or not statement.strip() or not scope.strip():
            raise ValueError("dossier_id, statement et scope doivent être non vides.")
        ts = timestamp or _utc_now_iso()
        state: dict[str, Any] = {
            "schema": "supela-state/0.2",
            "dossier_id": dossier_id,
            "generation": 1,
            "status": DossierStatus.CONCEPT.value,
            "claim": {
                "statement": statement,
                "scope": scope,
                "provenance": provenance,
                "created_at": ts,
            },
            "artifacts": [],
            "executions": [],
            "evidence": [],
            "contradictions": [],
            "revision": None,
            "previous_generations": [],
            "history": [
                {
                    "step": 1,
                    "layer": "L1",
                    "from_status": None,
                    "to_status": DossierStatus.CONCEPT.value,
                    "generation": 1,
                    "actor": actor,
                    "reason": f"Création du concept dans le périmètre '{scope}'",
                    "timestamp": ts,
                }
            ],
            "normative_decision": None,
            "state_hash": "",
        }
        self._save_state(state)
        self.bridge.append_ledger_event(
            "L1_CREATE_CONCEPT",
            dossier_id,
            1,
            {"claim": state["claim"], "state_hash": state["state_hash"]},
            timestamp=ts,
        )
        return state

    # ------------------------------------------------------------------
    # L2 : BUILD / CODE
    # ------------------------------------------------------------------
    def register_code(
        self,
        dossier_id: str,
        artifact_id: str,
        relative_path: str,
        content: str | None = None,
        concept_link: str | None = None,
        actor: str = "SupelaAgent",
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        state = self.get_state(dossier_id)
        allowed_statuses = {
            DossierStatus.CONCEPT.value,
            DossierStatus.CODE_REGISTERED.value,
            DossierStatus.REVISION_REQUESTED.value,
            DossierStatus.REOPENED.value,
        }
        if state["status"] not in allowed_statuses:
            raise InvalidStateTransitionError(
                f"Impossible d'enregistrer du code depuis le statut {state['status']}"
            )
        # Vérifie systématiquement la frontière du dépôt (L0)
        resolved = self.bridge.resolve_bounded_path(relative_path)
        if content is not None:
            raw_bytes = content.encode("utf-8")
            # Si le chemin pointe vers un fichier existant du dépôt qu'on ne veut pas écraser,
            # on ne l'écrit que s'il est dans state_dir ou s'il n'existe pas encore
            if str(resolved).startswith(str(self.state_dir)):
                self.bridge.write_bounded_file(relative_path, raw_bytes)
        else:
            raw_bytes = self.bridge.read_bounded_file(relative_path)

        sha256_hex = hashlib.sha256(raw_bytes).hexdigest()
        ts = timestamp or _utc_now_iso()
        gen = int(state["generation"])
        rel_norm = resolved.relative_to(self.repository_root).as_posix()
        artifact_entry = {
            "artifact_id": artifact_id,
            "relative_path": rel_norm,
            "sha256": sha256_hex,
            "generation": gen,
            "concept_link": concept_link or f"{dossier_id}@G{gen}",
            "registered_at": ts,
        }
        state["artifacts"].append(artifact_entry)
        self._record_transition(
            state,
            layer="L2",
            to_status=DossierStatus.CODE_REGISTERED,
            actor=actor,
            reason=f"Artefact {artifact_id} ({rel_norm}) enregistré avec SHA-256 {sha256_hex[:12]}",
            timestamp=ts,
        )
        self._save_state(state)
        self.bridge.append_ledger_event(
            "L2_REGISTER_CODE",
            dossier_id,
            gen,
            {"artifact": artifact_entry, "state_hash": state["state_hash"]},
            timestamp=ts,
        )
        return state

    # ------------------------------------------------------------------
    # L3 : EXECUTE
    # ------------------------------------------------------------------
    def execute(
        self,
        dossier_id: str,
        command_key: str,
        scope: str | None = None,
        actor: str = "SupelaAgent",
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        state = self.get_state(dossier_id)
        allowed_statuses = {
            DossierStatus.CODE_REGISTERED.value,
            DossierStatus.EXECUTED.value,
        }
        if state["status"] not in allowed_statuses:
            raise InvalidStateTransitionError(
                f"Exécution L3 requiert CODE_REGISTERED ou EXECUTED (actuel: {state['status']})"
            )
        run_res = self.bridge.run_allowed_command(command_key)
        ts = timestamp or _utc_now_iso()
        gen = int(state["generation"])
        exec_id = f"EXEC-G{gen}-{len(state['executions']) + 1:02d}"
        # Un échec d'exécution n'est jamais transformé automatiquement en réfutation universelle :
        # il est conservé comme résultat observé dans son périmètre.
        observed = (
            ObservedOutcome.OBSERVED_PASS_IN_SCOPE
            if run_res["returncode"] == 0
            else ObservedOutcome.OBSERVED_FAIL_IN_SCOPE
        )
        exec_entry = {
            "execution_id": exec_id,
            "command_key": command_key,
            "argv": run_res["argv"],
            "returncode": int(run_res["returncode"]),
            "observed_outcome": observed.value,
            "scope": scope or state["claim"]["scope"],
            "stdout_preview": run_res["stdout"],
            "stderr_preview": run_res["stderr"],
            "generation": gen,
            "executed_at": ts,
        }
        state["executions"].append(exec_entry)
        self._record_transition(
            state,
            layer="L3",
            to_status=DossierStatus.EXECUTED,
            actor=actor,
            reason=f"Exécution {exec_id} ({command_key}) -> {observed.value} (rc={run_res['returncode']})",
            timestamp=ts,
        )
        self._save_state(state)
        self.bridge.append_ledger_event(
            "L3_EXECUTE",
            dossier_id,
            gen,
            {"execution": exec_entry, "state_hash": state["state_hash"]},
            timestamp=ts,
        )
        return state

    # ------------------------------------------------------------------
    # L4 : EVIDENCE
    # ------------------------------------------------------------------
    def collect_evidence(
        self,
        dossier_id: str,
        actor: str = "SupelaAgent",
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        state = self.get_state(dossier_id)
        if state["status"] not in {DossierStatus.EXECUTED.value, DossierStatus.EVIDENCE_COLLECTED.value}:
            raise InvalidStateTransitionError(
                f"Collecte de preuves L4 requiert EXECUTED (actuel: {state['status']})"
            )
        ts = timestamp or _utc_now_iso()
        gen = int(state["generation"])
        gen_execs = [e for e in state["executions"] if e["generation"] == gen]
        gen_arts = [a for a in state["artifacts"] if a["generation"] == gen]
        if not gen_execs:
            proof_status = ProofStatus.INCONNU
        elif all(e["returncode"] == 0 for e in gen_execs):
            proof_status = ProofStatus.PASS_IN_SCOPE
        else:
            proof_status = ProofStatus.FAIL_IN_SCOPE

        env_info = {
            "python_version": sys.version.split()[0],
            "platform": platform.system(),
            "scope": state["claim"]["scope"],
        }
        ev_id = f"EVID-G{gen}-{len(state['evidence']) + 1:02d}"
        ledger_event = self.bridge.append_ledger_event(
            "L4_COLLECT_EVIDENCE",
            dossier_id,
            gen,
            {
                "evidence_id": ev_id,
                "execution_ids": [e["execution_id"] for e in gen_execs],
                "artifact_hashes": [a["sha256"] for a in gen_arts],
                "proof_status": proof_status.value,
            },
            timestamp=ts,
        )
        evidence_entry = {
            "evidence_id": ev_id,
            "generation": gen,
            "execution_ids": [e["execution_id"] for e in gen_execs],
            "artifact_hashes": [a["sha256"] for a in gen_arts],
            "environment": env_info,
            "ledger_entry_hash": ledger_event["entry_hash"],
            "proof_status": proof_status.value,
            "collected_at": ts,
        }
        state["evidence"].append(evidence_entry)
        self._record_transition(
            state,
            layer="L4",
            to_status=DossierStatus.EVIDENCE_COLLECTED,
            actor=actor,
            reason=f"Preuve {ev_id} scellée ({proof_status.value}, ledger={ledger_event['entry_hash'][:12]})",
            timestamp=ts,
        )
        self._save_state(state)
        return state

    # ------------------------------------------------------------------
    # L5 : CONTRADICTION / EVALUATION
    # ------------------------------------------------------------------
    def evaluate(
        self,
        dossier_id: str,
        contradiction_descriptions: list[str] | None = None,
        auto_detect_from_executions: bool = True,
        actor: str = "SupelaAgent",
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        state = self.get_state(dossier_id)
        if state["status"] not in {
            DossierStatus.EVIDENCE_COLLECTED.value,
            DossierStatus.CONTRADICTOIRE.value,
        }:
            raise InvalidStateTransitionError(
                f"Évaluation L5 requiert EVIDENCE_COLLECTED (actuel: {state['status']})"
            )
        ts = timestamp or _utc_now_iso()
        gen = int(state["generation"])
        descriptions = list(contradiction_descriptions or [])

        if auto_detect_from_executions:
            failed_execs = [
                e
                for e in state["executions"]
                if e["generation"] == gen
                and e["observed_outcome"] == ObservedOutcome.OBSERVED_FAIL_IN_SCOPE.value
            ]
            for fe in failed_execs:
                descriptions.append(
                    f"Écart dans le périmètre '{fe['scope']}' : {fe['execution_id']} ({fe['command_key']}) a retourné rc={fe['returncode']}"
                )

        for desc in descriptions:
            cid = f"CONTR-G{gen}-{len(state['contradictions']) + 1:02d}"
            state["contradictions"].append(
                {
                    "contradiction_id": cid,
                    "generation": gen,
                    "description": desc,
                    "scope": state["claim"]["scope"],
                    "status": ContradictionStatus.OPEN.value,
                    "detected_at": ts,
                    "resolved_in_generation": None,
                }
            )

        open_contradictions = [
            c
            for c in state["contradictions"]
            if c["status"] == ContradictionStatus.OPEN.value
        ]
        if open_contradictions:
            self._record_transition(
                state,
                layer="L5",
                to_status=DossierStatus.CONTRADICTOIRE,
                actor=actor,
                reason=f"{len(open_contradictions)} contradiction(s) ouverte(s) : ratification mécaniquement bloquée",
                timestamp=ts,
            )
        else:
            self._record_transition(
                state,
                layer="L5",
                to_status=DossierStatus.EVIDENCE_COLLECTED,
                actor=actor,
                reason="Aucune contradiction ouverte dans le périmètre ; dossier éligible au seuil de ratification",
                timestamp=ts,
            )
        self._save_state(state)
        self.bridge.append_ledger_event(
            "L5_EVALUATE",
            dossier_id,
            gen,
            {
                "open_contradictions": [c["contradiction_id"] for c in open_contradictions],
                "status": state["status"],
                "state_hash": state["state_hash"],
            },
            timestamp=ts,
        )
        return state

    # ------------------------------------------------------------------
    # L6 : REVISION (generation + 1 sans effacer l'ancienne trace)
    # ------------------------------------------------------------------
    def request_revision(
        self,
        dossier_id: str,
        reason: str,
        actor: str = "SupelaAgent",
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        if not reason or not reason.strip():
            raise ValueError("Une révision L6 doit être explicitement motivée (reason non vide).")
        state = self.get_state(dossier_id)
        if state["status"] not in {
            DossierStatus.CONTRADICTOIRE.value,
            DossierStatus.EVIDENCE_COLLECTED.value,
            DossierStatus.REOPENED.value,
        }:
            raise InvalidStateTransitionError(
                f"Révision L6 non permise depuis le statut {state['status']}"
            )
        ts = timestamp or _utc_now_iso()
        old_gen = int(state["generation"])
        new_gen = old_gen + 1

        # Archive l'empreinte de la génération courante sans jamais supprimer ses traces
        state["previous_generations"].append(
            {
                "generation": old_gen,
                "status_at_archive": state["status"],
                "state_hash": state["state_hash"],
                "reason": reason.strip(),
                "archived_at": ts,
            }
        )

        open_cids: list[str] = []
        for c in state["contradictions"]:
            if c["status"] == ContradictionStatus.OPEN.value:
                open_cids.append(str(c["contradiction_id"]))
                c["status"] = ContradictionStatus.SUPERSEDED_BY_REVISION.value
                c["resolved_in_generation"] = new_gen

        rev_id = f"REV-G{old_gen}-TO-G{new_gen}"
        state["revision"] = {
            "revision_id": rev_id,
            "from_generation": old_gen,
            "to_generation": new_gen,
            "reason": reason.strip(),
            "triggered_by_contradictions": open_cids,
            "requested_at": ts,
        }
        state["generation"] = new_gen
        self._record_transition(
            state,
            layer="L6",
            to_status=DossierStatus.REVISION_REQUESTED,
            actor=actor,
            reason=f"Révision {rev_id} motivée : {reason.strip()}",
            timestamp=ts,
        )
        self._save_state(state)
        self.bridge.append_ledger_event(
            "L6_REQUEST_REVISION",
            dossier_id,
            new_gen,
            {"revision": state["revision"], "state_hash": state["state_hash"]},
            timestamp=ts,
        )
        return state

    # ------------------------------------------------------------------
    # L7 : SEUIL DE RATIFICATION, AUTORITÉ HUMAINE & RÉOUVERTURE
    # ------------------------------------------------------------------
    def submit_ratification(
        self,
        dossier_id: str,
        actor: str = "SupelaAgent",
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        state = self.get_state(dossier_id)
        open_contradictions = [
            c
            for c in state["contradictions"]
            if c["status"] == ContradictionStatus.OPEN.value
        ]
        if open_contradictions or state["status"] == DossierStatus.CONTRADICTOIRE.value:
            raise ContradictionBlocksRatificationError(
                f"Soumission à ratification bloquée : {len(open_contradictions)} contradiction(s) ouverte(s)."
            )
        if state["status"] != DossierStatus.EVIDENCE_COLLECTED.value:
            raise InvalidStateTransitionError(
                f"Soumission à ratification requiert EVIDENCE_COLLECTED sans contradiction (actuel: {state['status']})"
            )
        gen = int(state["generation"])
        gen_evidence = [e for e in state["evidence"] if e["generation"] == gen]
        if not gen_evidence or not any(
            e["proof_status"] == ProofStatus.PASS_IN_SCOPE.value for e in gen_evidence
        ):
            raise InvalidStateTransitionError(
                f"Aucune preuve PASS_IN_SCOPE disponible pour la génération {gen}."
            )
        ts = timestamp or _utc_now_iso()
        self._record_transition(
            state,
            layer="L7",
            to_status=DossierStatus.CANDIDAT_A_RATIFICATION,
            actor=actor,
            reason=f"Soumis au seuil normatif pour ratification par {HUMAN_NORMATIVE_AUTHORITY}",
            timestamp=ts,
        )
        self._save_state(state)
        self.bridge.append_ledger_event(
            "L7_SUBMIT_RATIFICATION",
            dossier_id,
            gen,
            {"status": state["status"], "state_hash": state["state_hash"]},
            timestamp=ts,
        )
        return state

    def ratify(
        self,
        dossier_id: str,
        actor: str,
        decision: str,
        rationale: str,
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        """Franchit la frontière normative : réservé exclusivement à Jean-François Gadbois."""
        if actor != HUMAN_NORMATIVE_AUTHORITY:
            raise SupelaAuthorityError(
                f"Auto-ratification ou acteur '{actor}' refusé : seul '{HUMAN_NORMATIVE_AUTHORITY}' peut franchir la frontière normative."
            )
        if not rationale or not rationale.strip():
            raise ValueError("La décision normative doit inclure une justification (rationale).")
        state = self.get_state(dossier_id)
        open_contradictions = [
            c
            for c in state["contradictions"]
            if c["status"] == ContradictionStatus.OPEN.value
        ]
        if open_contradictions:
            raise ContradictionBlocksRatificationError(
                "Ratification impossible tant qu'une contradiction est ouverte."
            )
        if state["status"] != DossierStatus.CANDIDAT_A_RATIFICATION.value:
            raise InvalidStateTransitionError(
                f"Ratification requiert CANDIDAT_A_RATIFICATION (actuel: {state['status']})"
            )
        norm_decision = RatificationDecision(decision)
        status_map = {
            RatificationDecision.ACCEPT: DossierStatus.RATIFIED_ACCEPTED,
            RatificationDecision.REFUSE: DossierStatus.RATIFIED_REFUSED,
            RatificationDecision.ADJOURN: DossierStatus.RATIFIED_ADJOURNED,
        }
        target_status = status_map[norm_decision]
        ts = timestamp or _utc_now_iso()
        gen = int(state["generation"])
        state["normative_decision"] = {
            "actor": HUMAN_NORMATIVE_AUTHORITY,
            "decision": norm_decision.value,
            "rationale": rationale.strip(),
            "generation": gen,
            "decided_at": ts,
        }
        self._record_transition(
            state,
            layer="L7",
            to_status=target_status,
            actor=HUMAN_NORMATIVE_AUTHORITY,
            reason=f"Décision normative {norm_decision.value} : {rationale.strip()}",
            timestamp=ts,
        )
        self._save_state(state)
        self.bridge.append_ledger_event(
            "L7_NORMATIVE_RATIFICATION",
            dossier_id,
            gen,
            {
                "normative_decision": state["normative_decision"],
                "state_hash": state["state_hash"],
            },
            timestamp=ts,
        )
        return state

    def reopen(
        self,
        dossier_id: str,
        reason: str,
        actor: str = HUMAN_NORMATIVE_AUTHORITY,
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        """Réouvre un dossier ratifié, refusé ou ajourné sans effacer l'historique (RATIFICATION != FIN)."""
        if not reason or not reason.strip():
            raise ValueError("La réouverture d'un dossier requiert une raison explicite.")
        state = self.get_state(dossier_id)
        allowed_reopen = {
            DossierStatus.RATIFIED_ACCEPTED.value,
            DossierStatus.RATIFIED_REFUSED.value,
            DossierStatus.RATIFIED_ADJOURNED.value,
        }
        if state["status"] not in allowed_reopen:
            raise InvalidStateTransitionError(
                f"Seul un état ratifié/refusé/ajourné peut être rouvert (actuel: {state['status']})"
            )
        ts = timestamp or _utc_now_iso()
        gen = int(state["generation"])
        self._record_transition(
            state,
            layer="L7",
            to_status=DossierStatus.REOPENED,
            actor=actor,
            reason=f"Réouverture du dossier : {reason.strip()}",
            timestamp=ts,
        )
        self._save_state(state)
        self.bridge.append_ledger_event(
            "L7_REOPEN_DOSSIER",
            dossier_id,
            gen,
            {"reason": reason.strip(), "actor": actor, "state_hash": state["state_hash"]},
            timestamp=ts,
        )
        return state

    def verify_ledger(self) -> dict[str, Any]:
        return self.bridge.verify_ledger()


def run_supela_runtime_complete_cycle_demo(
    repository_root: Path,
    work_dir: Path | None = None,
) -> dict[str, Any]:
    """Exécute une démonstration déterministe complète L0–L7 (Génération 1 contradictoire -> Révision Génération 2 -> Ratification -> Réouverture)."""
    import tempfile

    def _run_in_dir(target_dir: Path) -> dict[str, Any]:
        runtime = SupelaRuntime(repository_root=repository_root, state_dir=target_dir)
        dossier_id = "DOSSIER-SUPELA-V02-001"

        # 1. L1 Concept (Gen 1)
        runtime.create_concept(
            dossier_id=dossier_id,
            statement="Le système nerveux Supela v0.2 fait circuler un concept jusqu'au seuil de l'autorité sans auto-promotion.",
            scope="omega-zero-4d/runtime-v0.2",
            provenance="M365-Copilot-Bridge-v0.1-to-Runtime-v0.2",
            timestamp="2026-11-17T23:50:00Z",
        )

        # 2. L2 Code (Gen 1)
        runtime.register_code(
            dossier_id=dossier_id,
            artifact_id="ART-G1-SCHEMA",
            relative_path="schemas/supela-state.schema.json",
            timestamp="2026-11-17T23:50:05Z",
        )

        # 3. L3 Execute (Gen 1 : échec observé dans le périmètre)
        runtime.execute(
            dossier_id=dossier_id,
            command_key="probe_fail",
            timestamp="2026-11-17T23:50:10Z",
        )

        # 4. L4 Evidence (Gen 1)
        runtime.collect_evidence(
            dossier_id=dossier_id,
            timestamp="2026-11-17T23:50:15Z",
        )

        # 5. L5 Contradiction (Gen 1 -> CONTRADICTOIRE)
        state_g1 = runtime.evaluate(
            dossier_id=dossier_id,
            timestamp="2026-11-17T23:50:20Z",
        )
        g1_snapshot_status = state_g1["status"]
        g1_snapshot_hash = state_g1["state_hash"]

        # Vérifie que la soumission à ratification est mécaniquement bloquée en Gen 1
        ratification_blocked_on_contradiction = False
        try:
            runtime.submit_ratification(dossier_id)
        except ContradictionBlocksRatificationError:
            ratification_blocked_on_contradiction = True

        # 6. L6 Révision motivée -> Génération 2 (sans effacer Génération 1)
        runtime.request_revision(
            dossier_id=dossier_id,
            reason="Correction de la sonde d'exécution après échec observé en génération 1.",
            timestamp="2026-11-17T23:50:25Z",
        )

        # 7. L2 Code (Gen 2) + L3 Execute (Gen 2 PASS) + L4 Evidence + L5 Evaluate
        runtime.register_code(
            dossier_id=dossier_id,
            artifact_id="ART-G2-RUNTIME",
            relative_path="schemas/supela-state.schema.json",
            timestamp="2026-11-17T23:50:30Z",
        )
        runtime.execute(
            dossier_id=dossier_id,
            command_key="probe_pass",
            timestamp="2026-11-17T23:50:35Z",
        )
        runtime.collect_evidence(
            dossier_id=dossier_id,
            timestamp="2026-11-17T23:50:40Z",
        )
        runtime.evaluate(
            dossier_id=dossier_id,
            timestamp="2026-11-17T23:50:45Z",
        )

        # 8. L7 Soumission au seuil de ratification
        runtime.submit_ratification(
            dossier_id=dossier_id,
            timestamp="2026-11-17T23:50:50Z",
        )

        # Vérifie le refus mécanique de l'auto-ratification par l'IA
        ai_ratification_refused = False
        try:
            runtime.ratify(
                dossier_id=dossier_id,
                actor="M365 Copilot",
                decision="ACCEPT",
                rationale="Tentative d'auto-ratification IA",
            )
        except SupelaAuthorityError:
            ai_ratification_refused = True

        # 9. L7 Ratification humaine par Jean-François Gadbois
        ratified_state = json.loads(
            json.dumps(
                runtime.ratify(
                    dossier_id=dossier_id,
                    actor=HUMAN_NORMATIVE_AUTHORITY,
                    decision="ACCEPT",
                    rationale="Cycle L0-L7 vérifié localement avec blocage de contradiction et registre SHA-256 intact.",
                    timestamp="2026-11-17T23:50:55Z",
                )
            )
        )

        # 10. L7 Réouverture motivée (RATIFICATION != FIN)
        reopened_state = runtime.reopen(
            dossier_id=dossier_id,
            reason="Inspection post-ratification pour ajout d'une sonde multi-moteurs.",
            actor=HUMAN_NORMATIVE_AUTHORITY,
            timestamp="2026-11-17T23:51:00Z",
        )

        ledger_check = runtime.verify_ledger()
        from .attestation import AttestationSigner

        executed_at_utc = _utc_now_iso()
        core_report: dict[str, Any] = {
            "schema": "supela-runtime-v02-cycle-report/1",
            "executed_at_utc": executed_at_utc,
            "protocol_sha256": canonical_sha256(REPORTED_M365_ARTIFACTS),
            "reported_m365_artifacts": REPORTED_M365_ARTIFACTS,
            "invariants_verified": {
                "g1_status_was_contradictoire": g1_snapshot_status == DossierStatus.CONTRADICTOIRE.value,
                "g1_hash_preserved_in_previous_generations": (
                    reopened_state["previous_generations"][0]["state_hash"] == g1_snapshot_hash
                ),
                "ratification_blocked_on_open_contradiction": ratification_blocked_on_contradiction,
                "ai_self_ratification_refused": ai_ratification_refused,
                "human_ratification_succeeded": ratified_state["status"] == DossierStatus.RATIFIED_ACCEPTED.value,
                "reopen_preserved_full_history": len(reopened_state["history"]) == 13,
                "ledger_chain_valid": ledger_check["valid"],
            },
            "ledger_verification": ledger_check,
            "ratified_snapshot": ratified_state,
            "final_reopened_state": reopened_state,
        }
        report_sha256 = canonical_sha256(core_report)
        signer = AttestationSigner()
        signed = signer.sign_report(core_report, producer_id="supela-runtime-v0.2", timestamp=executed_at_utc)
        sig_ok = AttestationSigner.verify(signed, core_report)
        core_report["invariants_verified"]["ed25519_verified"] = sig_ok
        return {
            **core_report,
            "report_sha256": report_sha256,
            "ed25519_attestation": {
                "producer_id": signed.producer_id,
                "timestamp": signed.timestamp,
                "protocol_sha256": signed.protocol_sha256,
                "report_sha256": signed.report_sha256,
                "public_key_b64": signed.public_key_b64,
                "signature_b64": signed.signature_b64,
                "verified": sig_ok,
            },
        }

    if work_dir is not None:
        return _run_in_dir(work_dir)
    with tempfile.TemporaryDirectory() as tmp:
        return _run_in_dir(Path(tmp))
