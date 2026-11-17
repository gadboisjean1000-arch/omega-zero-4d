"""Framework autonome des 6 thèses Supela liées à ORCID 0009-0001-5361-6795."""

from . import (
    thesis_architecture_3niveaux,
    thesis_dependance_souveraine,
    thesis_fase_one,
    thesis_invariant_axe01,
    thesis_luc_promise,
    thesis_verification_distrib,
)
from .common import (
    ORCID_ID,
    ORCID_URI,
    SOVEREIGNTY_CLAUSE,
    ThesisSpec,
    ThesisStatus,
    ThesisVerificationResult,
    build_bibtex_entry,
    build_citation_network,
    build_orcid_work_v3,
    write_thesis_pdf,
)

ALL_THESIS_MODULES = (
    thesis_invariant_axe01,
    thesis_luc_promise,
    thesis_fase_one,
    thesis_verification_distrib,
    thesis_architecture_3niveaux,
    thesis_dependance_souveraine,
)

__all__ = [
    "ALL_THESIS_MODULES",
    "ORCID_ID",
    "ORCID_URI",
    "SOVEREIGNTY_CLAUSE",
    "ThesisSpec",
    "ThesisStatus",
    "ThesisVerificationResult",
    "build_bibtex_entry",
    "build_citation_network",
    "build_orcid_work_v3",
    "thesis_architecture_3niveaux",
    "thesis_dependance_souveraine",
    "thesis_fase_one",
    "thesis_invariant_axe01",
    "thesis_luc_promise",
    "thesis_verification_distrib",
    "write_thesis_pdf",
]
