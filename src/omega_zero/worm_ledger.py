from __future__ import annotations

import hashlib
import json
import os
import stat
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .models import canonical_sha256


class WormTamperError(RuntimeError):
    """Levée lorsque le manifeste verrouillé ou la chaîne append-only WORM est altérée."""


SUBDIRS_4D: tuple[str, ...] = (
    "Local_L",
    "Cloud_C",
    "Vide_Pi0",
    "Manque_M",
)


@dataclass
class VaultRunResult:
    vault_path: Path
    manifest_path: Path
    ledger_path: Path
    manifest_sha256: str
    manifest_created: bool
    manifest_readonly: bool
    ledger_lines: int
    chain_valid: bool


class WormVault:
    """Coffre-fort WORM logique (manifeste lecture seule + ledger append-only chaîné SHA-256).

    Transparence : garantit un WORM logique vérifiable par chaîne de hachage et permissions
    système (0o444). Ne constitue pas un stockage WORM matériel ni un ancrage TPM/TEE.
    """

    def __init__(self, vault_path: Path) -> None:
        self.vault_path = vault_path
        self.manifest_path = vault_path / "omega_vault_manifest.json"
        self.ledger_path = vault_path / "ledger_append_only.jsonl"
        self.seal_path = vault_path / "omega_seal.txt"

    def init_idempotent(self, protocol_sha256: str) -> VaultRunResult:
        self.vault_path.mkdir(parents=True, exist_ok=True)
        for sub in SUBDIRS_4D:
            (self.vault_path / sub).mkdir(exist_ok=True)

        now_utc = datetime.now(UTC).isoformat()
        created = False

        if not self.manifest_path.exists():
            manifest = {
                "system": "Supela-Omega-ZERO-4D",
                "poles": ["Local_L", "Cloud_C", "Vide_Pi0", "Manque_M"],
                "protocol_sha256": protocol_sha256,
                "created_utc": now_utc,
            }
            self.manifest_path.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            os.chmod(self.manifest_path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
            created = True

        manifest_sha = hashlib.sha256(self.manifest_path.read_bytes()).hexdigest()
        mode = self.manifest_path.stat().st_mode
        is_readonly = (mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)) == 0

        self.append_event(
            event_type="VAULT_INIT_RUN",
            payload={
                "manifest_sha256": manifest_sha,
                "protocol_sha256": protocol_sha256,
                "idempotent": not created,
            },
            timestamp=now_utc,
        )

        lines = self.ledger_path.read_text(encoding="utf-8").splitlines()
        chain_valid, _ = self.verify_chain()

        seal_text = (
            f"Sceau Ω-ZERO (WORM logique)\n"
            f"timestamp_utc   : {now_utc}\n"
            f"manifest_sha256 : {manifest_sha}\n"
            f"ledger_lines    : {len(lines)}\n"
            f"chain_valid     : {chain_valid}\n"
            f"note            : manifeste lecture seule ; ledger chaîné SHA-256 append-only.\n"
        )
        self.seal_path.write_text(seal_text, encoding="utf-8")

        return VaultRunResult(
            vault_path=self.vault_path,
            manifest_path=self.manifest_path,
            ledger_path=self.ledger_path,
            manifest_sha256=manifest_sha,
            manifest_created=created,
            manifest_readonly=is_readonly,
            ledger_lines=len(lines),
            chain_valid=chain_valid,
        )

    def append_event(
        self,
        event_type: str,
        payload: dict[str, Any],
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        ts = timestamp or datetime.now(UTC).isoformat()
        prev_hash = "GENESIS"
        seq = 1
        if self.ledger_path.exists():
            existing = [
                line
                for line in self.ledger_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            if existing:
                last_entry = json.loads(existing[-1])
                prev_hash = last_entry["entry_hash"]
                seq = int(last_entry["seq"]) + 1

        body = {
            "seq": seq,
            "timestamp_utc": ts,
            "event_type": event_type,
            "prev_hash": prev_hash,
            "payload": payload,
        }
        entry_hash = canonical_sha256(body)
        entry = {**body, "entry_hash": entry_hash}
        with self.ledger_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, sort_keys=True, ensure_ascii=False) + "\n")
        return entry

    def verify_chain(self) -> tuple[bool, str]:
        if not self.ledger_path.exists():
            return False, "ledger_absent"

        lines = [
            line
            for line in self.ledger_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if not lines:
            return False, "ledger_vide"

        expected_prev = "GENESIS"
        for idx, raw in enumerate(lines, start=1):
            try:
                entry = json.loads(raw)
            except json.JSONDecodeError:
                return False, f"json_invalide_ligne_{idx}"

            if entry.get("seq") != idx:
                return False, f"sequence_rompue_ligne_{idx}"
            if entry.get("prev_hash") != expected_prev:
                return False, f"prev_hash_invalide_ligne_{idx}"

            body = {
                "seq": entry["seq"],
                "timestamp_utc": entry["timestamp_utc"],
                "event_type": entry["event_type"],
                "prev_hash": entry["prev_hash"],
                "payload": entry["payload"],
            }
            computed = canonical_sha256(body)
            if entry.get("entry_hash") != computed:
                return False, f"entry_hash_altere_ligne_{idx}"
            expected_prev = computed

        return True, "OK"
