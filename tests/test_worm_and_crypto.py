from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from omega_zero import AttestationSigner, WormVault
from omega_zero.harness import evaluate_escalation_protocol
from scripts.verify_a12 import verify_a12

ROOT_DIR = Path(__file__).resolve().parents[1]
COSIGN_CANDIDATE = ROOT_DIR / ".venv" / "bin" / "cosign"
COSIGN_BIN = str(COSIGN_CANDIDATE) if COSIGN_CANDIDATE.exists() else shutil.which("cosign")


def test_worm_vault_idempotence_and_tamper_detection(tmp_path: Path) -> None:
    proto_path = ROOT_DIR / "docs" / "constitution" / "PLAN-4D-ΩZERO-ESC-01.json"
    proto_sha = hashlib.sha256(proto_path.read_bytes()).hexdigest()

    vault = WormVault(tmp_path / "vault")
    r1 = vault.init_idempotent(proto_sha)
    r2 = vault.init_idempotent(proto_sha)

    assert r1.manifest_created is True
    assert r2.manifest_created is False
    assert r1.manifest_readonly is True
    assert r2.manifest_sha256 == r1.manifest_sha256
    assert r2.ledger_lines == r1.ledger_lines + 1
    assert r2.chain_valid is True

    # Altération du ledger -> doit être immédiatement détectée
    lines = vault.ledger_path.read_text(encoding="utf-8").splitlines()
    tampered = json.loads(lines[0])
    tampered["payload"]["idempotent"] = True
    lines[0] = json.dumps(tampered)
    vault.ledger_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    ok, reason = vault.verify_chain()
    assert ok is False
    assert "entry_hash_altere_ligne_1" == reason


def test_ed25519_attestation_sign_verify_and_tamper_rejection() -> None:
    report = evaluate_escalation_protocol(
        ROOT_DIR / "docs" / "constitution" / "PLAN-4D-ΩZERO-ESC-01.json",
        ROOT_DIR / "schemas",
    )
    signer = AttestationSigner()
    att = signer.sign_report(report)
    assert AttestationSigner.verify(att, report) is True

    # Modification d'un seul champ du rapport -> signature rejetée
    tampered_report = json.loads(json.dumps(report))
    tampered_report["promotion"] = "AUTOMATIQUE"
    assert AttestationSigner.verify(att, tampered_report) is False

    # Clé publique différente -> signature rejetée
    other_signer = AttestationSigner()
    att_bad_key = signer.sign_report(report)
    att_bad_key.public_key_b64 = other_signer.public_key_b64
    assert AttestationSigner.verify(att_bad_key, report) is False


@pytest.mark.skipif(COSIGN_BIN is None, reason="cosign CLI non installé")
def test_cosign_v3_bundle_sign_and_verify_on_live_report(tmp_path: Path) -> None:
    report = evaluate_escalation_protocol(
        ROOT_DIR / "docs" / "constitution" / "PLAN-4D-ΩZERO-ESC-01.json",
        ROOT_DIR / "schemas",
    )
    artifact = tmp_path / "report.json"
    artifact.write_text(json.dumps(report, indent=2), encoding="utf-8")
    bundle = tmp_path / "report.json.bundle"

    env = {**os.environ, "COSIGN_PASSWORD": "omega-ci-throwaway-test"}
    subprocess.run(
        [COSIGN_BIN, "generate-key-pair"],
        cwd=tmp_path,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            COSIGN_BIN,
            "sign-blob",
            "--key",
            str(tmp_path / "cosign.key"),
            "--yes",
            "--bundle",
            str(bundle),
            str(artifact),
        ],
        cwd=tmp_path,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    verify = subprocess.run(
        [
            COSIGN_BIN,
            "verify-blob",
            "--key",
            str(tmp_path / "cosign.pub"),
            "--bundle",
            str(bundle),
            str(artifact),
        ],
        cwd=tmp_path,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "Verified OK" in (verify.stdout + verify.stderr)


def test_rule_a12_no_orphans_no_broken_links_no_drift() -> None:
    ok, details = verify_a12(ROOT_DIR)
    assert details["orphans"] == []
    assert details["broken_links"] == []
    assert details["drift"] == []
    assert ok is True
