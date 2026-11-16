from __future__ import annotations

import base64
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from .models import canonical_sha256


@dataclass
class SignedAttestation:
    """Attestation cryptographique Ed25519 non-répudiable liée au rapport et au protocole."""

    producer_id: str
    provenance: str
    nonce: str
    timestamp: str
    protocol_sha256: str
    report_sha256: str
    signature_b64: str
    public_key_b64: str

    def canonical_payload(self) -> bytes:
        data: dict[str, Any] = {
            "producer_id": self.producer_id,
            "provenance": self.provenance,
            "nonce": self.nonce,
            "timestamp": self.timestamp,
            "protocol_sha256": self.protocol_sha256,
            "report_sha256": self.report_sha256,
        }
        return canonical_sha256(data).encode("utf-8")

    def to_opa_dict(self) -> dict[str, str]:
        return {
            "producer_id": self.producer_id,
            "provenance": self.provenance,
            "signature": self.signature_b64,
            "nonce": self.nonce,
            "timestamp": self.timestamp,
            "protocol_sha256": self.protocol_sha256,
        }


class AttestationSigner:
    """Signe et vérifie les rapports Ω-ZERO via Ed25519 (mécanisme cryptographique local)."""

    def __init__(self, private_key: Ed25519PrivateKey | None = None) -> None:
        self._private_key = private_key or Ed25519PrivateKey.generate()
        self._public_key = self._private_key.public_key()

    @property
    def public_key_b64(self) -> str:
        raw = self._public_key.public_bytes_raw()
        return base64.b64encode(raw).decode("ascii")

    def sign_report(
        self,
        report: dict[str, Any],
        *,
        producer_id: str = "omega-zero-harness",
        provenance: str = "HARNAIS_TEST_ESCALADE_4D.py",
        timestamp: str | None = None,
        nonce: str | None = None,
    ) -> SignedAttestation:
        ts = timestamp or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        n = nonce or secrets.token_hex(16)
        protocol_sha = str(report["protocol_sha256"])
        report_sha = canonical_sha256(report)

        draft = SignedAttestation(
            producer_id=producer_id,
            provenance=provenance,
            nonce=n,
            timestamp=ts,
            protocol_sha256=protocol_sha,
            report_sha256=report_sha,
            signature_b64="",
            public_key_b64=self.public_key_b64,
        )
        sig = self._private_key.sign(draft.canonical_payload())
        draft.signature_b64 = base64.b64encode(sig).decode("ascii")
        return draft

    @staticmethod
    def verify(attestation: SignedAttestation, report: dict[str, Any]) -> bool:
        if attestation.protocol_sha256 != report.get("protocol_sha256"):
            return False
        if attestation.report_sha256 != canonical_sha256(report):
            return False
        try:
            pub_bytes = base64.b64decode(attestation.public_key_b64)
            sig_bytes = base64.b64decode(attestation.signature_b64)
            pub_key = Ed25519PublicKey.from_public_bytes(pub_bytes)
            pub_key.verify(sig_bytes, attestation.canonical_payload())
            return True
        except (InvalidSignature, ValueError):
            return False
