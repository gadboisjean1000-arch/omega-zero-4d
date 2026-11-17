"""Socle commun autonome pour les 6 thèses Supela liées à ORCID 0009-0001-5361-6795."""

from __future__ import annotations

import json
import unicodedata
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from omega_zero.models import canonical_sha256

ORCID_ID = "0009-0001-5361-6795"
ORCID_URI = f"https://orcid.org/{ORCID_ID}"

SOVEREIGNTY_CLAUSE = (
    "Ce système peut être contesté, audité, réévalué.\n"
    "Il ne peut pas modifier son histoire sans que cela apparaisse.\n"
    "La forme permanente n'est pas l'absence de contestation.\n"
    "C'est l'impossibilité de contester silencieusement.\n"
    "Douter oblige à annoncer pourquoi on agit, sur quelles preuves,\n"
    "avec quelles limites, et dans quelles conditions on changera de décision.\n"
    "Un protocole qui interdit d'agir sous incertitude produit de la paralysie,\n"
    "pas de la rigueur."
)


class ThesisStatus(StrEnum):
    """Statut épistémique strict d'une thèse Supela (aucune zone grise)."""

    CONTROLE = "CONTROLE"
    INDETERMINE = "INDETERMINE"
    ABSENT = "ABSENT"


@dataclass(frozen=True)
class ThesisSpec:
    """Spécification canonique d'une thèse autonome Supela."""

    these_id: str
    numero: int
    titre: str
    domaine: str
    invariant_id: str
    pdf_filename: str
    apport_cle: str
    cross_references: tuple[str, ...]
    autonomie: str = "complete_self_contained"


@dataclass(frozen=True)
class ThesisVerificationResult:
    """Résultat reproductible d'une vérification autonome de thèse."""

    these_id: str
    orcid: str
    orcid_uri: str
    titre: str
    domaine: str
    invariant_id: str
    statut: ThesisStatus
    timestamp_utc: str
    autonomie: str
    apport_cle: str
    indetermine_conditions: list[str]
    details: dict[str, Any]
    cross_references: list[str]
    sovereignty_clause: str = field(default=SOVEREIGNTY_CLAUSE)

    def to_metadata_dict(self, *, pdf_sha256: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema": "supela-thesis-metadata/1.0",
            "these_id": self.these_id,
            "orcid": self.orcid,
            "orcid_uri": self.orcid_uri,
            "titre": self.titre,
            "domaine": self.domaine,
            "invariant_id": self.invariant_id,
            "statut": self.statut.value,
            "timestamp": self.timestamp_utc,
            "autonomie": self.autonomie,
            "apport_cle": self.apport_cle,
            "indetermine_conditions": self.indetermine_conditions,
            "cross_references": self.cross_references,
            "sovereignty_clause": self.sovereignty_clause,
            "details": self.details,
        }
        if pdf_sha256 is not None:
            payload["pdf_sha256"] = pdf_sha256
        payload["metadata_sha256"] = canonical_sha256(
            {k: v for k, v in payload.items() if k != "metadata_sha256"}
        )
        return payload


def utc_now_iso() -> str:
    """Horodatage UTC ISO-8601 sans ambiguïté."""
    return datetime.now(UTC).isoformat()


def _to_pdf_ascii(text: str) -> str:
    """Normalise en ASCII sûr pour police Type1 Helvetica PDF 1.4."""
    replacements = {
        "→": "->",
        "≠": "!=",
        "≤": "<=",
        "≥": ">=",
        "⊆": "c=",
        "∅": "{}",
        "Π": "Pi",
        "Ω": "Omega",
        "«": '"',
        "»": '"',
        "’": "'",
        "–": "-",
        "—": "-",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    normalized = unicodedata.normalize("NFKD", text)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    return ascii_only.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def write_thesis_pdf(result: ThesisVerificationResult, out_path: Path) -> str:
    """Génère un PDF 1.4 autonome et déterministe, retourne son SHA-256."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = [
        f"SUPELA THESIS DEPOSIT | {result.these_id}",
        f"ORCID: {result.orcid} ({result.orcid_uri})",
        f"Title: {result.titre}",
        f"Domain: {result.domaine} | Invariant: {result.invariant_id}",
        f"Status: {result.statut.value} | Autonomy: {result.autonomie}",
        f"Timestamp UTC: {result.timestamp_utc}",
        "-" * 72,
        f"Key Contribution: {result.apport_cle}",
        "-" * 72,
        "INDETERMINE Conditions:",
        *[f"  - {cond}" for cond in result.indetermine_conditions],
        "-" * 72,
        "Cross-References:",
        f"  {', '.join(result.cross_references)}",
        "-" * 72,
        "Sovereignty Clause:",
        *[f"  {line}" for line in result.sovereignty_clause.splitlines()],
        "-" * 72,
        f"Verification Details: {json.dumps(result.details, ensure_ascii=True, sort_keys=True)[:180]}",
    ]

    content_ops = ["BT", "/F1 10 Tf", "50 760 Td", "14 TL"]
    for idx, line in enumerate(lines[:48]):
        safe = _to_pdf_ascii(line[:92])
        if idx == 0:
            content_ops.append(f"({safe}) Tj")
        else:
            content_ops.append(f"T* ({safe}) Tj")
    content_ops.append("ET")
    stream_bytes = "\n".join(content_ops).encode("latin-1")

    objects: list[bytes] = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        (
            b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        ),
        (
            f"4 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n".encode("ascii")
            + stream_bytes
            + b"\nendstream\nendobj\n"
        ),
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
    ]

    pdf = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = [0]
    for obj in objects:
        offsets.append(len(pdf))
        pdf.extend(obj)

    xref_pos = len(pdf)
    pdf.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        pdf.extend(f"{off:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        (
            f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\n"
            f"startxref\n{xref_pos}\n%%EOF\n"
        ).encode("ascii")
    )

    out_path.write_bytes(bytes(pdf))
    return canonical_sha256(out_path.read_bytes().hex())


def build_bibtex_entry(result: ThesisVerificationResult) -> str:
    """Construit une entrée BibTeX prête pour import ORCID / LaTeX."""
    year = result.timestamp_utc[:4]
    cite_key = result.these_id.lower().replace("-", "_")
    return (
        f"@misc{{{cite_key},\n"
        f"  author = {{Supela (ORCID: {result.orcid})}},\n"
        f"  title = {{{result.titre} ({result.invariant_id})}},\n"
        f"  year = {{{year}}},\n"
        f"  note = {{ORCID: {result.orcid_uri} | Statut: {result.statut.value} | "
        f"Timestamp: {result.timestamp_utc}}},\n"
        f"  howpublished = {{Supela Autonomous Thesis Framework (omega-zero-4d)}}\n"
        f"}}"
    )


def build_orcid_work_v3(result: ThesisVerificationResult, *, pdf_sha256: str) -> dict[str, Any]:
    """Construit un objet JSON conforme au schéma ORCID Work v3.0 (prêt pour dépôt)."""
    year = result.timestamp_utc[:4]
    month = result.timestamp_utc[5:7]
    day = result.timestamp_utc[8:10]
    return {
        "title": {
            "title": {"value": f"{result.titre} [{result.invariant_id}]"},
            "subtitle": {"value": result.domaine},
        },
        "type": "working-paper",
        "publication-date": {
            "year": {"value": year},
            "month": {"value": month},
            "day": {"value": day},
        },
        "short-description": (
            f"{result.apport_cle} | Statut: {result.statut.value} | "
            f"Autonomie: {result.autonomie} | PDF SHA-256: {pdf_sha256}"
        ),
        "external-ids": {
            "external-id": [
                {
                    "external-id-type": "other-id",
                    "external-id-value": result.these_id,
                    "external-id-relationship": "self",
                }
            ]
        },
        "url": {"value": ORCID_URI},
    }


def build_citation_network(results: list[ThesisVerificationResult]) -> dict[str, Any]:
    """Construit le graphe de références croisées entre les 6 thèses autonomes."""
    nodes = [
        {
            "these_id": r.these_id,
            "invariant_id": r.invariant_id,
            "domaine": r.domaine,
            "statut": r.statut.value,
            "orcid": r.orcid,
            "autonomie": r.autonomie,
            "timestamp_utc": r.timestamp_utc,
        }
        for r in results
    ]
    edges: list[dict[str, str]] = []
    for r in results:
        for target in r.cross_references:
            edges.append(
                {
                    "source": r.these_id,
                    "target_invariant": target,
                    "relation": "invariant_cross_reference",
                }
            )
    payload: dict[str, Any] = {
        "schema": "supela-citation-network/1.0",
        "orcid": ORCID_ID,
        "orcid_uri": ORCID_URI,
        "thesis_count": len(results),
        "all_controle": all(r.statut == ThesisStatus.CONTROLE for r in results),
        "nodes": nodes,
        "edges": edges,
        "generated_at_utc": utc_now_iso(),
    }
    payload["network_sha256"] = canonical_sha256(
        {k: v for k, v in payload.items() if k not in {"network_sha256", "generated_at_utc"}}
    )
    return payload


def thesis_summary_dict(result: ThesisVerificationResult) -> dict[str, Any]:
    return asdict(result)
