#!/usr/bin/env python3
"""Orchestrateur complet de déposition horodatée des 6 thèses Supela (ORCID 0009-0001-5361-6795)."""

from __future__ import annotations

import argparse
import io
import json
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from omega_zero.attestation import AttestationSigner
from omega_zero.models import canonical_sha256
from omega_zero.theses import (
    ALL_THESIS_MODULES,
    ORCID_ID,
    ORCID_URI,
    ThesisStatus,
    ThesisVerificationResult,
    build_bibtex_entry,
    build_citation_network,
    build_orcid_work_v3,
    write_thesis_pdf,
)


def deposit_all_theses(
    out_dir: Path,
    *,
    allow_indetermine: bool = False,
) -> dict[str, Any]:
    """Vérifie, génère PDFs + métadonnées JSON + BibTeX + ORCID v3.0 + signature Ed25519."""
    out_dir.mkdir(parents=True, exist_ok=True)
    deposit_timestamp_utc = datetime.now(UTC).isoformat()

    results: list[ThesisVerificationResult] = []
    deposited_items: list[dict[str, Any]] = []
    bibtex_entries: list[str] = []
    orcid_works: list[dict[str, Any]] = []

    for mod in ALL_THESIS_MODULES:
        res: ThesisVerificationResult = mod.verify()
        if not allow_indetermine and res.statut != ThesisStatus.CONTROLE:
            raise RuntimeError(
                f"Échec fail-closed : {res.these_id} a le statut {res.statut.value} != CONTROLE"
            )
        results.append(res)

        pdf_path = out_dir / mod.SPEC.pdf_filename
        pdf_sha = write_thesis_pdf(res, pdf_path)

        meta_path = out_dir / f"{res.these_id}_metadata.json"
        meta_payload = res.to_metadata_dict(pdf_sha256=pdf_sha)
        meta_path.write_text(
            json.dumps(meta_payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        bibtex_entries.append(build_bibtex_entry(res))
        orcid_works.append(build_orcid_work_v3(res, pdf_sha256=pdf_sha))

        deposited_items.append(
            {
                "these_id": res.these_id,
                "invariant_id": res.invariant_id,
                "statut": res.statut.value,
                "timestamp_utc": res.timestamp_utc,
                "pdf_file": pdf_path.name,
                "pdf_sha256": pdf_sha,
                "metadata_file": meta_path.name,
                "metadata_sha256": meta_payload["metadata_sha256"],
            }
        )

    network = build_citation_network(results)
    network_path = out_dir / "citation_network.json"
    network_path.write_text(
        json.dumps(network, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    bib_path = out_dir / "theses_orcid_0009.bib"
    bib_path.write_text("\n\n".join(bibtex_entries) + "\n", encoding="utf-8")

    orcid_path = out_dir / "orcid_works_v3.json"
    orcid_payload: dict[str, Any] = {
        "schema": "orcid-works-v3-bundle/1.0",
        "orcid": ORCID_ID,
        "orcid_uri": ORCID_URI,
        "generated_at_utc": deposit_timestamp_utc,
        "remote_push_executed": False,
        "honesty_note": (
            "Export ORCID Work v3.0 généré localement et scellé cryptographiquement. "
            "Le dépôt distant vers api.orcid.org requiert un jeton OAuth2 personnel ORCID."
        ),
        "works": orcid_works,
    }
    orcid_path.write_text(
        json.dumps(orcid_payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    manifest_core: dict[str, Any] = {
        "schema": "supela-theses-deposit-manifest/1.0",
        "protocol_sha256": network["network_sha256"],
        "orcid": ORCID_ID,
        "orcid_uri": ORCID_URI,
        "deposit_timestamp_utc": deposit_timestamp_utc,
        "thesis_count": len(deposited_items),
        "all_controle": all(item["statut"] == ThesisStatus.CONTROLE.value for item in deposited_items),
        "theses": deposited_items,
        "citation_network_sha256": network["network_sha256"],
        "bibtex_sha256": canonical_sha256(bib_path.read_text(encoding="utf-8")),
        "orcid_works_sha256": canonical_sha256(orcid_path.read_text(encoding="utf-8")),
    }

    signer = AttestationSigner()
    attestation = signer.sign_report(
        manifest_core,
        producer_id="supela-theses-depositor",
        provenance="scripts/deposit_theses.py",
        timestamp=deposit_timestamp_utc,
    )
    if not AttestationSigner.verify(attestation, manifest_core):
        raise RuntimeError("Auto-vérification Ed25519 du manifeste de déposition échouée")

    full_manifest: dict[str, Any] = {
        **manifest_core,
        "attestation_ed25519": asdict(attestation),
    }
    manifest_path = out_dir / "deposit_manifest.json"
    manifest_path.write_text(
        json.dumps(full_manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return full_manifest


def main() -> int:
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Déposition complète et horodatée des 6 thèses Supela (ORCID 0009-0001-5361-6795)"
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT_DIR / "reports" / "theses_orcid_0009",
        help="Répertoire de sortie des PDFs, métadonnées, BibTeX et manifeste signé",
    )
    parser.add_argument(
        "--allow-indetermine",
        action="store_true",
        help="Autoriser la génération même si une thèse n'est pas CONTROLE",
    )
    args = parser.parse_args()

    manifest = deposit_all_theses(args.out_dir, allow_indetermine=args.allow_indetermine)
    print(
        json.dumps(
            {
                "deposit_ok": manifest["all_controle"],
                "orcid": manifest["orcid"],
                "deposit_timestamp_utc": manifest["deposit_timestamp_utc"],
                "thesis_count": manifest["thesis_count"],
                "out_dir": str(args.out_dir),
                "manifest_file": str(args.out_dir / "deposit_manifest.json"),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
