#!/usr/bin/env python3
"""Constructeur, normalisateur et vérificateur HTML/YAML du Dictionnaire & Encyclopédie Supela Ω-ZERO."""

from __future__ import annotations

import argparse
import copy
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from html import escape as html_escape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT_DIR / "schemas" / "supela_encyclopedie_1.schema.json"
DEFAULT_JSON_OUT = ROOT_DIR / "docs" / "constitution" / "supela-dictionnaire-encyclopedie-1.json"
DEFAULT_MD_OUT = ROOT_DIR / "docs" / "constitution" / "ENCYCLOPEDIE_DICTIONNAIRE.md"
DEFAULT_HTML_OUT = ROOT_DIR / "docs" / "constitution" / "ENCYCLOPEDIE_DICTIONNAIRE.html"
DEFAULT_FORMULAS_MD_OUT = ROOT_DIR / "docs" / "constitution" / "REGISTRE_FORMULES_SUPELA.md"
DEFAULT_CONTRADICTIONS_JSON = ROOT_DIR / "docs" / "constitution" / "REGISTRE_CONTRADICTIONS.json"
DEFAULT_CONTRADICTIONS_MD = ROOT_DIR / "docs" / "constitution" / "REGISTRE_CONTRADICTIONS.md"
DEFAULT_FICHES_DIR = ROOT_DIR / "docs" / "constitution" / "fiches"


def _canonical_sha256(data: Any) -> str:
    """Calcule l'empreinte SHA-256 déterministe alignée sur omega_zero.models.canonical_sha256."""
    encoded = json.dumps(data, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _atomic_write_text(target: Path, content: str) -> None:
    """Écrit un fichier atomiquement dans son répertoire cible pour éviter toute divergence."""
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=str(target.parent))
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        os.replace(tmp_path, target)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise

EXCLUDED_REPO_DIRS = {
    ".git",
    ".venv",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".hypothesis",
    ".omega_vault",
    "__pycache__",
    "dist",
    "omega_zero_4d.egg-info",
}

REPO_ROLES: dict[str, tuple[str, list[str]]] = {
    "gadboisjean1000-arch/omega-zero-4d": (
        "Dépôt canonique Supela Ω-ZERO · Local-Cloud-4D : Π₀, 7 statuts du Manque, protocole TEST-4D-ESC-01, schémas Draft 2020-12, OPA Rego v1, WORM, Ed25519, GRPO et Règle A12.",
        [
            "docs/constitution/INDEX_CONSTITUTION.md",
            "docs/constitution/PLAN-4D-ΩZERO-ESC-01.json",
            "docs/constitution/supela-article-registry-1.json",
            "policies/omega_zero_invariants.rego",
            "src/omega_zero/protocol.py",
            "scripts/verify_a12.py",
        ],
    ),
    "gadboisjean1000-arch/Supela-K3-Omega": (
        "Monolithe formel historique Supela-K3-Ω : GDS = ⟨D, O, A, γ⟩, OPA 13/13, Cosign v3, WORM PowerShell idempotent, VR-Fractal-Ω et pipeline CI.",
        [
            "Supela-MONOLITHE-INTEGRAL.md",
            "VR-Fractal-Omega.md",
            "policies/gds_invariants.rego",
            "runtime/init_gds_pipeline.ps1",
            "monolithe.ps1",
        ],
    ),
    "gadboisjean1000-arch/sevengate-store": (
        "Vitrine et API cloud SevenGate Store avec intégrations Cloudflare, Railway et Vercel.",
        ["index.html", "api_cloud.py", "api/finance.py", "DEPLOYMENT_GUIDE.md", "vercel.json"],
    ),
    "gadboisjean1000-arch/utilise": (
        "Dépôt de scripts utilitaires polyvalents pour automatisation et outillage.",
        ["README.md"],
    ),
}

DOC_CLASSIFICATIONS: dict[str, tuple[str, list[str], str]] = {
    "1JN1AfHmewUHdzVLlh7wRezEIriV6t2n4vq6JYOeiN_U": (
        "Infrastructure Cloud & OIDC (Supela-K3-Ω)",
        ["Gemini / Assistant IA", "Azure Bicep"],
        "Spécification OIDC sans secret statique et module Azure Bicep (supela-edge.bicep) avec Key Vault et Health Check.",
    ),
    "1qcDmfGhgnVAYqhlv3iSl-uscgKlris54RNTCZYRCu2A": (
        "Intégration CLI & Agents IA",
        ["Cursor CLI", "Claude / Gemini"],
        "Guide d'intégration Cursor CLI ↔ Pipeline Supela-K3-Ω : Shell Mode (K3s/PowerShell/Nomad), Headless CI (OPA/Rego) et ACP.",
    ),
    "1gBbj-OyJe0zp2sbB64XeqUFAvGiG129W_5hfT8G36oE": (
        "Corpus Doctoral Supela (Ch. 1-3)",
        ["Gemini / Assistant IA"],
        "Corpus doctoral unifié regroupant les chapitres 1 à 3 (Rituel/Pipeline, Graal cognitif & ancrages silicium, GDS/SCT).",
    ),
    "1v8hbxMcTKo3ImgkX3kQJKDk3DXGOnMk9Ko0o9gaxY2Y": (
        "Corpus Doctoral Supela (Copie)",
        ["Gemini / Assistant IA"],
        "Copie du corpus doctoral unifié (chapitres 1 à 3) archivée dans Drive.",
    ),
    "1UX-kqgR0S54hl0EJOzA0LGyL8MOdNMP8FZcvDe2I98c": (
        "Corpus Doctoral Supela (Copie)",
        ["Gemini / Assistant IA"],
        "Copie du corpus doctoral unifié (chapitres 1 à 3) archivée dans Drive.",
    ),
    "1AmGMFHC7ehMT1Q5uCbigrMLOvM3CpXwr4b25mUlu0UA": (
        "Corpus Doctoral Supela (Copie)",
        ["Gemini / Assistant IA"],
        "Copie du corpus doctoral unifié (chapitres 1 à 3) archivée dans Drive.",
    ),
    "1F6OtEXHwY229UAX51XBLF93PdOCKwTVKgY0OCOG-HgI": (
        "Corpus Doctoral Supela (Copie)",
        ["Gemini / Assistant IA"],
        "Copie du corpus doctoral unifié (chapitres 1 à 3) archivée dans Drive.",
    ),
    "1xwNrrRFpRJgPzQgh9YZrSbdI6QP4cSCZwDbRbJhC8lw": (
        "Corpus Doctoral Supela (Copie)",
        ["Gemini / Assistant IA"],
        "Copie du corpus doctoral unifié (chapitres 1 à 3) archivée dans Drive.",
    ),
    "1aI4MIBTwNfCzlkE_-bNc8XxrJUpYTkM7hNyBLmkP7DQ": (
        "Débogage GitHub API",
        ["Assistant IA", "GitHub API"],
        "Diagnostic des erreurs HTTP 404 d'obfuscation sur l'API GitHub et élévation de permissions PAT (Fine-grained / repo).",
    ),
    "1nTp9MuemFpvQyeYyZHC6G4f6S-ZGJPcdjGbAXsWKeuc": (
        "Noyau Cryptographique Rust (Ω-AXE-01)",
        ["Assistant IA", "Rust"],
        "Implémentation conceptuelle Rust omega_axe_01::core::terminal_gate avec séparation F_sign != F_certif et trait SupelaLedger.",
    ),
    "1VpFXq3hHPEsMTO5NyX5nvM7jfCkBSBnppeBiseCM0sI": (
        "Spécification Supela-Ω (Ébauche)",
        ["Google Docs"],
        "Document créé le 2026-10-03 intitulé « Contrat Supela-Ω : Spécification de la Fonction CONTROLE » (corps actuellement vide : 1 caractère).",
    ),
    "1SJRQt_ebmOw7lvUkNnHzPFbOKtDzdayrieyh2JlLx1A": (
        "Architecture 3 couches Supela-K3-Ω",
        ["Assistant IA"],
        "Architecture et gouvernance en 3 couches (Supela, K3, Omega) avec invariants INV-SUP-01, INV-K3-01/02, INV-OMG-01/02.",
    ),
    "1jfcutVxolADj-eTHbxETul0girYTmHhoF08lsz4-pBA": (
        "Prototype Souverain SQLite WAL",
        ["Assistant IA", "Bash / SQLite"],
        "Prototype robuste SQLite WAL + socket local avec script de bootstrap et sonde d'indépendance anti-auto-certification.",
    ),
    "1qtgSooem_Z1VA1Qa5wK7HQF1k3_hGNggnpH9LWYmPk8": (
        "Audit Cryptographique AIS-Ω",
        ["Assistant IA", "PowerShell"],
        "Séquence d'audit cryptographique SUPREMA PREMIUM (AIS-Ω) en PowerShell testant signatures, sabotage et hachage.",
    ),
    "1R71yti9PR0djXoxV5coXflmxGTz7-N39WovkpmFSQn4": (
        "Note de Scellement",
        ["Assistant IA"],
        "Courte note déclarative (4 lignes) actant la formalisation de l'axiome.",
    ),
    "1D9RKMHlOxgm52Mx8tvzW3PgWCCsnyeq2oBXhwO66TNs": (
        "Mathématisation Zéro Moteur",
        ["Assistant IA"],
        "Axiome unifié de l'émergence orthogonale (ΔPoids = 0 ⇒ ΔRésonance ⊥ Poids) et tenseur de profondeur.",
    ),
    "1r6R0_7l7Z1ydw5yxjOQJpLxnz9gLxhciYWeQyXCFJho": (
        "Phase A v3.1 (Couche C1)",
        ["Assistant IA"],
        "Spécification Phase A v3.1 faisant de la Couche 1 (C1) l'arbitre déterministe et introduisant 9 disjoncteurs orthogonaux D0-D8.",
    ),
    "1oOB3T-MrBnlIxwXZahFQYJar9Osl0zrz8lz6mLw2R1Y": (
        "Phase B (Couche C2 Stochastique)",
        ["Assistant IA"],
        "Confirmation Phase A v3 gelée et contrat de validation stochastique Phase B (Couche C2) par injection de mutations.",
    ),
    "1S_gioLWccxrMIIRYOpqhXICMLEaErY-of1eoD3hz1WQ": (
        "Gouvernance Durable (PDD-01)",
        ["Assistant IA"],
        "Axiome de Persistance au Point de Décision (PDD-01) : complétude (Commande, Sortie) et exclusion des états volatils RAM/chat.",
    ),
    "1gAYDB8WPVc0UtRhiqQG61J_dqcBJ-4I6fqTJaSVM3CQ": (
        "SDK Python Supela",
        ["Assistant IA", "Python"],
        "Conception du SDK minimal Python (supela_sdk.py) encapsulant Merkle/cryptographie en 3 lignes d'appel.",
    ),
    "1KIZi0D9dud4O0ttn5kAssPH2dGrUoEahR27aDMhtwWE": (
        "Audit IA Zero-Trust (OPAE-3 / XR-50)",
        ["Assistant IA", "Azure / Zero-Trust"],
        "Matrice d'audit IA Zero-Trust v2 (14 colonnes, 38 contrôles XR-50 alignés Microsoft AZ-500, CA-01, PIM-02).",
    ),
    "1vlJHAMCRTbJb5gkuAYTtbJtam1Ie2G4oH7Bg9JSJ_Pw": (
        "Souveraineté XaaS (VR-13 à VR-18)",
        ["Assistant IA", "Mermaid"],
        "Diagramme Mermaid modélisant la matrice de souveraineté XaaS entre cœur souverain, rituel et couches externalisées.",
    ),
    "1X2V7qAg3OLlKl5d2bjmF2CqMNeqkCOg63KtBaPh-MFE": (
        "Validation Indépendante (Initiative Gamma)",
        ["Assistant IA"],
        "Rapport THIRD-PARTY-VALIDATION-REPORT.md (TVR-2026-0001) intégrant Déclaration d'Indépendance, Reproductibilité et Preuve.",
    ),
    "1U8jjFymxQz5xWfnqfahA3lyT2wN7oEBbeYab9mHazKo": (
        "Pull Request Canon VR-24",
        ["Assistant IA", "Git"],
        "Rédaction de PR Git pour ratifier VR-24 (Canon de Continuité) : découplage physico-sémantique, agilité NIST, Merkle.",
    ),
    "1HfwN8xTKGw0caKNm7WMm3hRnDohrQGSPSdj4yS6lKP4": (
        "Sentinel Snapshot V2 (OT/ICS)",
        ["Assistant IA", "OPA / Rego"],
        "Architecture Edge-Mesh cyber-physique, tracking immuable, OPA/Rego et conformité NIS2/DORA.",
    ),
    "1SssllqOJn4mtYH-d8-_wt-U7sioFm8Lau377YRiJcHE": (
        "Manifeste Supela (Ring -3)",
        ["Assistant IA"],
        "Refondation du manifeste Supela K3 : Axiome Zéro, Calcul Abyssal Ring -3 et ancrage matériel Ω-AXE-02.",
    ),
    "1QiTXg7hPU7tOy3eEqwBrsAil-YAFap73CEv_XX7AyTc": (
        "Entreprise / Stratégie NatuPro",
        ["Assistant IA"],
        "Analyse et critique stratégique par IA du plan d'embellissement et verdissement urbain pour Groupe NatuPro.",
    ),
    "1JtZ-7BW-2UM_MVhFtSEpigQ4XZ_Sa2hnS6aMnjStOiY": (
        "Entreprise / OBNL Anti-Graffitis",
        ["Assistant IA"],
        "Plan stratégique OBNL anti-graffitis et partenariat municipal produit en collaboration avec IA.",
    ),
    "15HyYKXo7X5k61grNoitcmVXVypHlnz6OJjNUZeobnO0": (
        "Entreprise / Gestion Graffitis LaSalle",
        ["Assistant IA"],
        "Rapport « La Propreté en Partenariat : Analyse du Modèle Hybride de Gestion des Graffitis à Montréal / LaSalle ».",
    ),
    "1t5rICR3ED_7F-9xg4BkjudKjqMzY-u29Q6tkMiAFxqY": (
        "Entreprise / Plan d'affaires 5 ans",
        ["Assistant IA"],
        "Prompt et réponse IA générant un plan d'affaires sur 5 ans pour Groupe Pro Nature.",
    ),
    "1LAGCD4r6xA20bfpM6_je5DHpp9vOl_fK-vbpVdtLkPk": (
        "Entreprise / Rédaction commerciale",
        ["Assistant IA"],
        "Prompt et réponse IA produisant un texte de présentation professionnelle pour l'entreprise.",
    ),
    "1EgcoLtqJFF9s9MfJ2OtWzUe0UyKu1WeIryMiA_cs7AU": (
        "Communication / Sponsoring",
        ["Google Docs"],
        "Modèle de réponse tarifaire pour vidéos sponsorisées sur Twitter et YouTube.",
    ),
    "1VWlIpNMviD84IVDSCDEehfTDM_MlU0Y1Cm3BLsYTaww": (
        "Administration / Entreprise NatuPro",
        ["Google Docs / Archive"],
        "Accusé de réception administratif de mise à jour courante (Groupe NatuPro, exemplaire 1).",
    ),
    "1Q_FNJuZ2OjbFjwG5pt4TuPpBtG6skkaHF7l44Slw6y8": (
        "Administration / Entreprise NatuPro",
        ["Google Docs / Archive"],
        "Accusé de réception administratif de mise à jour courante (Groupe NatuPro, exemplaire 2).",
    ),
    "1cn1j4f4jicgFkRfp02evJPsJ-949ybK5KRFaVp0kycQ": (
        "Facturation / Travaux",
        ["Google Docs"],
        "Modèle ou document de facturation pour recherche de couleur et travaux de peinture (octobre 2025).",
    ),
    "1fpc7Qxv2UORqfOQ5MY-1COJrHz0_1sjxyi63lJ_31wQ": (
        "Entreprise / Communication bilingue",
        ["Google Docs"],
        "Notes bilingues FR/EN « LaSalle fait peau neuve / Together, let's unveil the beauty of our walls ».",
    ),
    "1ILIEV8WJWN4UqE8qp8RcKyF_dYPJxfc_ztjozR-XxzA": (
        "Entreprise / Urbanisme & Éco-quartier",
        ["Assistant IA"],
        "Analyse assistée par IA du programme d'aide aux graffitis d'Éco-quartier LaSalle (exemplaire 1).",
    ),
    "1od7HSVRx6JfTMXdgZ_24HqR8vXC-rTECHYS_opGWWrI": (
        "Entreprise / Urbanisme & Éco-quartier",
        ["Assistant IA"],
        "Analyse assistée par IA du programme d'aide aux graffitis d'Éco-quartier LaSalle (exemplaire 2).",
    ),
    "1jY2gxV3pbSeGuhcl97lXHM8a-10UJJzKgmW8dOagPhc": (
        "Entreprise / Gestion Graffitis Montréal",
        ["Assistant IA"],
        "Rapport structuré généré avec IA sur le modèle hybride « La Propreté en Partenariat » (exemplaire 1).",
    ),
    "1KTmUK_CS7qkutqKoP_LTmZ13_1ajIi09O6MyZDC0M9w": (
        "Entreprise / Gestion Graffitis Montréal",
        ["Assistant IA"],
        "Rapport structuré généré avec IA sur le modèle hybride « La Propreté en Partenariat » (exemplaire 2).",
    ),
    "1PkLopHkkWyJU3vvv8KQ41CXWQvfJoPUMYk6fSFErYoY": (
        "Note / Ébauche Drive",
        ["Google Docs"],
        "Document intitulé « Untitled » ne contenant qu'un tiret (ébauche de 1 caractère).",
    ),
    "1Qeu2RRkF4uYor-7_4NQOt7YjFJLKco1C1jRkDm2i168": (
        "Entreprise / Urbanisme Montréal",
        ["Assistant IA"],
        "Essai analytique généré avec IA « Urbanisme Responsable : Un Modèle Déployé par Montréal ».",
    ),
    "1vIdPsRP1PAwP9sShUESLqUCBw5z1Z5qcR2eWXdilB50": (
        "Entreprise / Valorisation LaSalle",
        ["Assistant IA"],
        "Rapport généré avec IA sur la gestion des graffitis et la valorisation des murs à LaSalle (exemplaire 1).",
    ),
    "125Jdt1RF54v2IK-mCUoqXFOeCUSN1GrvbbotTbiURCg": (
        "Entreprise / Valorisation LaSalle",
        ["Assistant IA"],
        "Rapport généré avec IA sur la gestion des graffitis et la valorisation des murs à LaSalle (exemplaire 2).",
    ),
    "1RgKCYm6JC_i91CTHnpqGLAinCTRIlTRNYCDDY7Wp5Lk": (
        "Entreprise / Rédaction prospectus IA",
        ["Assistant IA"],
        "Réponse directe d'un assistant IA structurant un prospectus commercial (archive 2025-07-12).",
    ),
    "19C99ylHBzTtYJzUbjGw0-JDkk8I1ej4MkKx7g9GkgkU": (
        "Entreprise / Rédaction prospectus IA",
        ["Assistant IA"],
        "Version développée (4 504 car.) d'une réponse IA rédigeant le prospectus complet.",
    ),
    "1-_tbb44FJ9PJVa1wwI-LuNcEPbdndmXCeY5ZZss0Bqg": (
        "Personnel / Rédaction CV IA",
        ["Assistant IA"],
        "Synthèse de CV générée avec assistant IA (détails personnels volontairement non reproduits).",
    ),
    "13z70FVp2OLb9r2PVtbBuMZsgllNP93AMLAjmfc4WsBk": (
        "Personnel / Coopérative d'habitation",
        ["Google Docs / Archive"],
        "Lettre de correspondance destinée à une coopérative (données nominatives masquées).",
    ),
    "15tqF5npGQoTPU1FlmGefgbpAysGsiYSQ6inEz-agPMg": (
        "Personnel / Candidature coopérative",
        ["Google Docs / Archive"],
        "Ébauche de formulaire de candidature coopérative (données personnelles non reproduites).",
    ),
    "14ySgiG8J5_L5F-iC-Fp0GAOQh49WuGlmw_eykFmB_xI": (
        "Personnel / Candidature coopérative",
        ["Google Docs / Archive"],
        "Version intermédiaire de formulaire de candidature coopérative (données personnelles masquées).",
    ),
    "1oS_h6R7whFigQp8BWuYIbYM6XLUSs1rlDCrmPAfnM9k": (
        "Personnel / Candidature coopérative",
        ["Google Docs / Archive"],
        "Formulaire de candidature finalisé pour coopérative d'habitation (données personnelles masquées).",
    ),
}


def build_dictionary_entries() -> list[dict[str, Any]]:
    """Construit le Dictionnaire terminologique et conceptuel complet."""
    entries: list[tuple[str, str, str, str, list[str], str]] = [
        # --- PROJECTION PI0 ---
        (
            "Opérateur de Projection Π₀",
            "PROJECTION_PI0",
            "Π₀(S_t) = {I, P, M, A, H}",
            "Projette un état de travail S_t vers son état zéro opérationnel honnête en préservant invariants (I), preuves et réfutations (P), manques ouverts (M), autorités bornées (A) et histoire minimale (H).",
            ["docs/constitution/DEFINITION_P0_PROJECTION.json", "src/omega_zero/projection.py"],
            "VERIFIE_EXECUTEE",
        ),
        (
            "Opérateur de Projection Π_I",
            "PROJECTION_PI0",
            "Π_I(Ω_t) = 0_I",
            "Projette l'état émergent global Ω_t sur ses invariants permanents en retirant les éléments variables ; étendu par Π₀ pour les cycles de reprise.",
            ["docs/constitution/DEFINITION_P0_PROJECTION.json", "docs/constitution/PLAN_4D_OMEGA_ZERO_ESC_01.md"],
            "DOCUMENTE_NORMATIF",
        ),
        (
            "Idempotence de Π₀",
            "PROJECTION_PI0",
            "Π₀(Π₀(S_t)) = Π₀(S_t)",
            "Propriété algébrique garantissant qu'une seconde projection sur un état déjà projeté ne détruit ni n'altère aucune des 5 composantes {I, P, M, A, H}.",
            ["docs/constitution/DEFINITION_P0_PROJECTION.json", "tests/test_pi0_and_manque.py"],
            "VERIFIE_EXECUTEE",
        ),
        (
            "État Local Minimal Lᵢ⁰",
            "PROJECTION_PI0",
            "Π₀_local(L_i) = L_i⁰ ≠ L_i_amnésique",
            "Noyau conservé localement après revidage transactionnel : identité, invariants, autorités, index minimal, preuve de transfert, pointeur de récupération et manques locaux.",
            ["docs/constitution/PLAN_4D_OMEGA_ZERO_ESC_01.md", "src/omega_zero/protocol.py"],
            "VERIFIE_EXECUTEE",
        ),
        (
            "Invariant I1 (Vérité vérifiable)",
            "PROJECTION_PI0",
            "I1",
            "Toute conclusion conservée doit être appuyée par une preuve reproductible dans son périmètre explicite.",
            ["docs/constitution/DEFINITION_P0_PROJECTION.json"],
            "VERIFIE_EXECUTEE",
        ),
        (
            "Invariant I2 (Traçabilité)",
            "PROJECTION_PI0",
            "I2",
            "Chaque objet conservé garde son origine, sa provenance, son horodatage et ses dépendances causales.",
            ["docs/constitution/DEFINITION_P0_PROJECTION.json"],
            "VERIFIE_EXECUTEE",
        ),
        (
            "Invariant I3 (Réfutabilité)",
            "PROJECTION_PI0",
            "I3",
            "Tout raccord admis reste réouvrable face à une nouvelle preuve contradictoire sans détruire Ω.",
            ["docs/constitution/DEFINITION_P0_PROJECTION.json"],
            "VERIFIE_EXECUTEE",
        ),
        (
            "Invariant I4 (Cohérence)",
            "PROJECTION_PI0",
            "I4",
            "Les contradictions interdisciplinaires ou inter-nœuds non résolues sont représentées explicitement plutôt qu'écrasées.",
            ["docs/constitution/DEFINITION_P0_PROJECTION.json"],
            "VERIFIE_EXECUTEE",
        ),
        (
            "Invariant I5 (Conservation de la preuve)",
            "PROJECTION_PI0",
            "I5",
            "Aucune donnée ou trace probante (y compris réfutée, avec Autorité=0) n'est effacée silencieusement.",
            ["docs/constitution/DEFINITION_P0_PROJECTION.json"],
            "VERIFIE_EXECUTEE",
        ),
        (
            "Invariant I_M (Conservation du Manque ouvert)",
            "PROJECTION_PI0",
            "I_M",
            "Tout manque détecté doit rester représenté jusqu'à résolution, réfutation ou requalification ; la suppression silencieuse (* -> SUPPRIMÉ) est interdite.",
            ["docs/constitution/STATUT_MANQUE.json"],
            "VERIFIE_EXECUTEE",
        ),
        # --- MANQUE ET STATUTS ---
        (
            "Objet Manque M",
            "MANQUE_ET_STATUTS",
            "M(S_t, G) ⟺ Required(G) \\ Available(S_t) ≠ ∅",
            "Structure 4D traçant un déficit d'éléments requis pour établir G : id, question, contexte, origine, dépendances, autorité, tentatives, temps et statut.",
            ["docs/constitution/STATUT_MANQUE.json", "src/omega_zero/models.py"],
            "VERIFIE_EXECUTEE",
        ),
        (
            "Statut OUVERT",
            "MANQUE_ET_STATUTS",
            "ManqueStatus.OUVERT",
            "Statut initial actif d'un Manque non résolu ; conservé intégralement par Π₀ et interdit de saut direct vers RÉSOLU.",
            ["docs/constitution/STATUT_MANQUE.json"],
            "VERIFIE_EXECUTEE",
        ),
        (
            "Statut SOUS_EXPLORATION",
            "MANQUE_ET_STATUTS",
            "ManqueStatus.SOUS_EXPLORATION",
            "Statut actif indiquant qu'un ou plusieurs raccords candidats sont enregistrés avec autorité initiale AUCUNE en attente d'épreuve.",
            ["docs/constitution/STATUT_MANQUE.json"],
            "VERIFIE_EXECUTEE",
        ),
        (
            "Statut PARTIELLEMENT_RÉDUIT",
            "MANQUE_ET_STATUTS",
            "ManqueStatus.PARTIELLEMENT_RÉDUIT",
            "Un sous-périmètre est soutenu sous conditions tandis qu'un autre sous-périmètre demeure ouvert.",
            ["docs/constitution/STATUT_MANQUE.json"],
            "VERIFIE_EXECUTEE",
        ),
        (
            "Statut RÉSOLU",
            "MANQUE_ET_STATUTS",
            "ManqueStatus.RÉSOLU",
            "Un raccord candidat a satisfait Required(G) avec Preuve ≥ Autorité ; demeure réouvrable via TR-14 si une NouvellePreuve contredit le raccord.",
            ["docs/constitution/STATUT_MANQUE.json"],
            "VERIFIE_EXECUTEE",
        ),
        (
            "Statut RÉFUTÉ_COMME_PROBLÈME",
            "MANQUE_ET_STATUTS",
            "ManqueStatus.RÉFUTÉ_COMME_PROBLÈME",
            "La prémisse constitutive est prouvée fausse ou impossible (A ↛ C) ; la trace est conservée et réouvrable via TR-16.",
            ["docs/constitution/STATUT_MANQUE.json"],
            "VERIFIE_EXECUTEE",
        ),
        (
            "Statut REQUALIFIÉ",
            "MANQUE_ET_STATUTS",
            "ManqueStatus.REQUALIFIÉ",
            "Clôture conditionnelle divisant ou reformulant un Manque (M₁ → {M₁ₐ, M₁ᵦ}) avec filiation explicite parent → enfant.",
            ["docs/constitution/STATUT_MANQUE.json"],
            "VERIFIE_EXECUTEE",
        ),
        (
            "Statut INACCESSIBLE_DANS_LE_PÉRIMÈTRE",
            "MANQUE_ET_STATUTS",
            "ManqueStatus.INACCESSIBLE_DANS_LE_PÉRIMÈTRE",
            "Les éléments requis dépassent les limites techniques, juridiques ou d'accès du périmètre courant (ex. disques Windows C:/D: depuis une VM cloud) ; réouvrable via TR-15.",
            ["docs/constitution/STATUT_MANQUE.json"],
            "VERIFIE_EXECUTEE",
        ),
        (
            "Règles Déontologiques M1–M5",
            "MANQUE_ET_STATUTS",
            "M1..M5",
            "M1: Manque ≠ faux ; M2: Manque ≠ vrai caché ; M3: Manque ≠ permission d'inventer (OPEN ∧ ¬FABRICATE) ; M4: Tout remplissage garde son raccord ; M5: Évolution temporelle tracée.",
            ["docs/constitution/STATUT_MANQUE.json"],
            "VERIFIE_EXECUTEE",
        ),
        (
            "Raccord",
            "MANQUE_ET_STATUTS",
            "Raccord ⟨id, status, authority_level ≤ evidence_level⟩",
            "Lien candidat, soutenu sous conditions, réfuté, inconnu ou établi entre une source/hypothèse et un objectif, borné par son niveau de preuve.",
            ["src/omega_zero/models.py", "policies/omega_zero_invariants.rego"],
            "VERIFIE_EXECUTEE",
        ),
        # --- ESCALADE 4D ---
        (
            "Protocole PLAN-4D-ΩZERO-ESC-01",
            "ESCALADE_4D",
            "E0..E7 / C01..C10",
            "Protocole d'escalade Local–Cloud–4D structuré en 8 paliers (E0..E7) et 10 conditions normatives (C01..C10), ne permettant qu'une promotion ADMISSIBLE_A_REVUE_HUMAINE.",
            ["docs/constitution/PLAN-4D-ΩZERO-ESC-01.json", "src/omega_zero/protocol.py"],
            "VERIFIE_EXECUTEE",
        ),
        (
            "Seuil de Saturation Load(C)",
            "ESCALADE_4D",
            "Load(C) = max(Bytes, Objects, Edges, Latency) ≥ 0.80",
            "Métrique normalisée déclenchant une migration contrôlée sans perte entre conteneurs C₁ → C₂ après déclaration explicite de métrique et limites.",
            ["docs/constitution/PLAN_4D_OMEGA_ZERO_ESC_01.md", "src/omega_zero/protocol.py"],
            "VERIFIE_EXECUTEE",
        ),
        (
            "Revidage Transactionnel (E6 / C09)",
            "ESCALADE_4D",
            "PREPARE → VERIFY → COMMIT → CLEAN",
            "Transfert Local → Cloud imposant 5 prédicats ACK (ACK, HashMatch, ProvenanceOK, AuthorityOK, ReconstructionPASS) avant tout CLEAN, avec rollback local en cas d'échec.",
            ["docs/constitution/PLAN_4D_OMEGA_ZERO_ESC_01.md", "policies/omega_zero_invariants.rego"],
            "VERIFIE_EXECUTEE",
        ),
        (
            "Fusion Merge* & Invariance d'Ordre",
            "ESCALADE_4D",
            "Merge* ∈ {ACCEPTÉ, PARTIEL, CONTESTÉ, ISOLÉ, REFUSÉ}",
            "Opérateur de fusion cloud garantissant que l'ordre d'arrivée des deltas locaux Δᵢ (4! = 24 permutations testées en E3) n'accorde aucune autorité.",
            ["src/omega_zero/protocol.py", "tests/test_properties_hypothesis.py"],
            "VERIFIE_EXECUTEE",
        ),
        (
            "Conflit 4D (Conflict4D)",
            "ESCALADE_4D",
            "C-001 = {CONFLIT_INTERDISCIPLINAIRE, CONSERVÉ, NON_ACQUISE}",
            "Représentation explicite d'un désaccord entre disciplines ou nœuds locaux, protégée contre l'écrasement silencieux (C04/C05).",
            ["src/omega_zero/models.py", "docs/constitution/TEST_P0_EXEMPLE.json"],
            "VERIFIE_EXECUTEE",
        ),
        # --- GDS ET SCT ---
        (
            "Système Dynamique Général (GDS)",
            "GDS_ET_SCT",
            "GDS = ⟨D, O, A, γ⟩",
            "Formalisme du corpus doctoral Supela-K3-Ω : Domaine (D), Opérations/Ouverture (O), Artefacts/Absorption (A) et Opérateur de cohérence (γ).",
            ["gadboisjean1000-arch/Supela-K3-Omega:Supela-MONOLITHE-INTEGRAL.md"],
            "DOCUMENTE_NORMATIF",
        ),
        (
            "Théorème de Cohérence Systémique (SCT)",
            "GDS_ET_SCT",
            "SCT = γ*(D, O, A) ; γ* = γ ∘ Λ",
            "Établit 6 propriétés de stabilité collaborative sous charge et mises à jour asynchrones via les invariants σ (sémantique), τ (temporel), κ (cinétique) et δ (clôture dimensionnelle).",
            ["gadboisjean1000-arch/Supela-K3-Omega:Supela-MONOLITHE-INTEGRAL.md"],
            "DOCUMENTE_NORMATIF",
        ),
        (
            "VR-24 : Canon de Continuité",
            "GDS_ET_SCT",
            "Ω-VR-24",
            "Spécification normative établissant que la continuité prévaut sur la certitude : découplage physico-sémantique, agilité cryptographique NIST et cycles de réattestation.",
            ["GoogleDoc:1U8jjFymxQz5xWfnqfahA3lyT2wN7oEBbeYab9mHazKo"],
            "DOCUMENTE_NORMATIF",
        ),
        (
            "VR-Fractal-Ω",
            "GDS_ET_SCT",
            "P_t = (T_t + C_t) / (1 + Δ_t)",
            "Mécanique de descente fractale résolvant la macro-turbulence (Δ_t ≫ 0) en subdivisant vers des sous-échelles où Δ_{t,i} → 0.",
            ["gadboisjean1000-arch/Supela-K3-Omega:VR-Fractal-Omega.md"],
            "DOCUMENTE_NORMATIF",
        ),
        (
            "Axiome PDD-01 (Persistance au Point de Décision)",
            "GDS_ET_SCT",
            "PDD-01",
            "Un fait mesuré est nul tant qu'il n'est pas consigné au point d'évaluation ; exige le couple (Commande, Sortie) et exclut les états volatils en RAM/historique chat.",
            ["GoogleDoc:1S_gioLWccxrMIIRYOpqhXICMLEaErY-of1eoD3hz1WQ"],
            "DOCUMENTE_NORMATIF",
        ),
        (
            "Séparation Signataire vs Certificateur",
            "GDS_ET_SCT",
            "F_sign ≠ F_certif",
            "Invariant d'indépendance interdisant à un composant d'exécution (Supela/K3) de s'auto-certifier auprès de l'autorité terminale (Ω).",
            ["GoogleDoc:1nTp9MuemFpvQyeYyZHC6G4f6S-ZGJPcdjGbAXsWKeuc", "GoogleDrive:supela_ratification_simulation_v2.ipynb"],
            "DOCUMENTE_NORMATIF",
        ),
        (
            "Disjoncteurs D0–D8 (Phase A v3.1 / C1)",
            "GDS_ET_SCT",
            "D0..D8 (Couche C1)",
            "Neuf disjoncteurs orthogonaux isolant strictement les causes de défaut structurel ou logique dans la Couche 1 déterministe avant toute évaluation stochastique C2.",
            ["GoogleDoc:1r6R0_7l7Z1ydw5yxjOQJpLxnz9gLxhciYWeQyXCFJho"],
            "DOCUMENTE_NORMATIF",
        ),
        # --- SECURITE WORM CRYPTO ---
        (
            "Coffre-fort WORM Logique (WormVault)",
            "SECURITE_WORM_CRYPTO",
            "0o444 / IsReadOnly + SHA-256 append-only",
            "Stockage logique à manifeste lecture seule et journal JSONL chaîné SHA-256 ; déclaré honnêtement distinct d'un WORM matériel TPM/TEE.",
            ["src/omega_zero/worm_ledger.py", "runtime/init_omega_vault.ps1"],
            "VERIFIE_EXECUTEE",
        ),
        (
            "Attestation Cryptographique Ed25519 & Cosign v3",
            "SECURITE_WORM_CRYPTO",
            "AttestationSigner / cosign --bundle",
            "Signature non-répudiable Ed25519 des rapports et scellement Cosign v3 au format --bundle avec vérification d'intégrité.",
            ["src/omega_zero/attestation.py", "Makefile"],
            "VERIFIE_EXECUTEE",
        ),
        (
            "Politiques OPA Rego v1",
            "SECURITE_WORM_CRYPTO",
            "supela.omega_zero.governance",
            "Garde-fous exécutables évaluant fraîcheur (15 min), hachage protocole, immutabilité WORM, 10 conditions C01..C10, barrières GRPO/émergence et revue humaine.",
            ["policies/omega_zero_invariants.rego", "tests/rego/omega_zero_invariants_test.rego"],
            "DOCUMENTE_NORMATIF",
        ),
        (
            "Règle A12 (Anti-orphelins & Cohérence)",
            "SECURITE_WORM_CRYPTO",
            "verify_a12()",
            "Vérifie la bijection entre tous les fichiers réels du dépôt et INDEX_CONSTITUTION.md (0 orphelin, 0 lien cassé) ainsi que la cohérence JSON ↔ Rego ↔ Markdown.",
            ["scripts/verify_a12.py", "tests/test_supela_article_registry.py"],
            "VERIFIE_EXECUTEE",
        ),
        # --- IA ET GRPO ---
        (
            "Pont Supela-GRPO",
            "IA_ET_GRPO",
            "Score ≠ Preuve ≠ Vérité",
            "Architecture en 5 étages découplant l'exploration comparative (récompenses et avantages relatifs GRPO) de la validation par preuve indépendante.",
            ["docs/constitution/SCHEMA_GRPO_SUPELA.md", "src/omega_zero/grpo_bridge.py"],
            "VERIFIE_EXECUTEE",
        ),
        (
            "Preuve GRPO L = 0 et ∇L ≠ 0",
            "IA_ET_GRPO",
            "L(θ_old) = 0 ∧ ∇_θ L(θ_old) ≠ 0",
            "Résultat analytique et numérique (à μ=1, β=0) démontrant qu'une perte scalaire nulle au point initial n'implique pas un gradient nul.",
            ["docs/constitution/SCHEMA_GRPO_SUPELA.md", "src/omega_zero/grpo_bridge.py"],
            "VERIFIE_EXECUTEE",
        ),
        (
            "Registre des 6 Articles IA",
            "IA_ET_GRPO",
            "supela-article-registry/1",
            "Cartographie en 5 branches (Attention, Inférence, Apprentissage, Interprétabilité, Évaluation) maintenant Hook=AnalysisCandidate et verdict=OUVERT sans reproduction.",
            ["docs/constitution/supela-article-registry-1.json", "schemas/supela_article_registry_1.schema.json"],
            "VERIFIE_EXECUTEE",
        ),
        # --- ECOSYSTEME OUTILS IA & NAVIGATEURS ---
        (
            "Microsoft Copilot & Edge",
            "ECOSYSTEME_OUTILS_IA",
            "Edge User Data / Copilot",
            "Assistant IA Microsoft et profils Edge : historique local Windows non accessible depuis le cloud Linux (collecte locale requise via collect_local_encyclopedie.ps1).",
            ["scripts/collect_local_encyclopedie.ps1"],
            "INACCESSIBLE_DANS_LE_PÉRIMÈTRE",
        ),
        (
            "Google Gemini",
            "ECOSYSTEME_OUTILS_IA",
            "gemini.google.com / Drive Docs",
            "Modèles et conversations Gemini : les synthèses exportées dans Google Docs sont répertoriées ; l'historique web direct gemini.google.com et le cache Chrome local restent hors périmètre.",
            ["GoogleDrive:gdocs.json", "scripts/collect_local_encyclopedie.ps1"],
            "CANDIDAT_OUVERT",
        ),
        (
            "Arc Browser",
            "ECOSYSTEME_OUTILS_IA",
            "TheBrowserCompany.Arc / StorableSidebar.json",
            "Navigateur Arc : données locales Windows (AppData/Packages) et historiques d'espaces/IA hors périmètre cloud ; collectables localement par PowerShell.",
            ["scripts/collect_local_encyclopedie.ps1"],
            "INACCESSIBLE_DANS_LE_PÉRIMÈTRE",
        ),
        (
            "Brave Browser & Brave Leo",
            "ECOSYSTEME_OUTILS_IA",
            "BraveSoftware\\Brave-Browser\\User Data",
            "Navigateur Brave et assistant Leo : exécutable d'installation repéré dans Drive Downloads ; profils et discussions locales hors périmètre cloud.",
            ["GoogleDrive:laptop_downloads.json", "scripts/collect_local_encyclopedie.ps1"],
            "INACCESSIBLE_DANS_LE_PÉRIMÈTRE",
        ),
        (
            "Opera & Aria",
            "ECOSYSTEME_OUTILS_IA",
            "Opera Software\\Opera Stable / .opera",
            "Navigateur Opera : raccourci Bureau et dossier .opera synchronisés (vide dans Drive) ; profil actif Windows hors périmètre.",
            ["GoogleDrive:laptop_desktop.json", "scripts/collect_local_encyclopedie.ps1"],
            "INACCESSIBLE_DANS_LE_PÉRIMÈTRE",
        ),
        (
            "Antigravity & Cursor / Kilo / Cline",
            "ECOSYSTEME_OUTILS_IA",
            "IDE & Agents IA (.gemini / Cursor / VS Code)",
            "Écosystème d'agents de code : dépôts forkés sur GitHub (kilocode, cline, sourcery), guide Cursor CLI dans Google Docs et session Antigravity persistée.",
            ["GitHub:gadboisjean1000-arch", "GoogleDoc:1qcDmfGhgnVAYqhlv3iSl-uscgKlris54RNTCZYRCu2A"],
            "VERIFIE_EXECUTEE",
        ),
        (
            "ChatGPT (OpenAI) & Claude (Anthropic)",
            "ECOSYSTEME_OUTILS_IA",
            "conversations.json / Web History",
            "Conversations externes ChatGPT et Claude : hors API directe ; indexables via les synthèses exportées en Google Docs ou export conversations.json scanné par collect_local_encyclopedie.ps1.",
            ["GoogleDrive:gdocs.json", "scripts/collect_local_encyclopedie.ps1"],
            "INACCESSIBLE_DANS_LE_PÉRIMÈTRE",
        ),
        (
            "Disques locaux Windows C:\\ et D:\\ (excited-meitner)",
            "ECOSYSTEME_OUTILS_IA",
            "C:\\Users\\Group\\Documents\\antigravity\\excited-meitner ; D:\\",
            "Arborescences système Windows locales non montées sur la VM cloud Linux ; inventoriées en lecture seule par collect_local_encyclopedie.ps1 sans lecture de secrets.",
            ["scripts/install_into_excited_meitner.ps1", "scripts/collect_local_encyclopedie.ps1"],
            "INACCESSIBLE_DANS_LE_PÉRIMÈTRE",
        ),
        # --- GOUVERNANCE ET NORMES ---
        (
            "Revue Humaine Obligatoire",
            "GOUVERNANCE_ET_NORMES",
            "ADMISSIBLE_A_REVUE_HUMAINE",
            "Statut maximal qu'un système automatisé Supela Ω-ZERO peut accorder après 8 paliers et 10 conditions ; aucune promotion autonome sur main.",
            ["docs/constitution/PLAN-4D-ΩZERO-ESC-01.json", "policies/omega_zero_invariants.rego"],
            "VERIFIE_EXECUTEE",
        ),
        (
            "Loi d'Autorité Bornée",
            "GOUVERNANCE_ET_NORMES",
            "Autorité(C) ≤ Preuve(C)",
            "Invariant fondamental garantissant qu'aucune hypothèse, score statistique ou delta asynchrone ne reçoit une autorité supérieure à sa preuve vérifiée.",
            ["policies/omega_zero_invariants.rego", "src/omega_zero/protocol.py"],
            "VERIFIE_EXECUTEE",
        ),
        (
            "Fraîcheur Probante (15 minutes)",
            "GOUVERNANCE_ET_NORMES",
            "max_attestation_age_ns = 900000000000",
            "Fenêtre temporelle maximale (900 s) exigée par OPA Rego v1 entre l'horodatage RFC 3339 d'attestation et l'évaluation de gouvernance.",
            ["policies/omega_zero_invariants.rego"],
            "VERIFIE_EXECUTEE",
        ),
        (
            "Norme ISO-GDS-2026 & Modules HDR",
            "GOUVERNANCE_ET_NORMES",
            "ISO-GDS-2026",
            "Spécification normative dérivée du corpus doctoral GDS = ⟨D, O, A, γ⟩ déclinée en article scientifique et Habilitation à Diriger des Recherches.",
            ["GoogleDrive:1nAtBQlAkVXyB_R5T4CjZlfSWSCLTUEY6"],
            "DOCUMENTE_NORMATIF",
        ),
        (
            "Architecture 3 Couches (Supela / K3 / Ω)",
            "GOUVERNANCE_ET_NORMES",
            "INV-SUP-01 / INV-K3 / INV-OMG",
            "Séparation hiérarchique stricte entre exécution (Supela), orchestration k3s/PowerShell (K3) et oracle de ratification indépendant (Ω).",
            ["GoogleDoc:1SJRQt_ebmOw7lvUkNnHzPFbOKtDzdayrieyh2JlLx1A"],
            "DOCUMENTE_NORMATIF",
        ),
    ]

    return [
        {
            "id": f"DICT-{idx:03d}",
            "terme": terme,
            "categorie": cat,
            "notation": notation,
            "definition": definition,
            "sources": sources,
            "statut_epistemique": statut,
        }
        for idx, (terme, cat, notation, definition, sources, statut) in enumerate(entries, start=1)
    ]


UNIVERSAL_FICHE_KEYS: tuple[str, ...] = (
    "id",
    "nom",
    "type",
    "discipline",
    "formulation_brute",
    "formulation_normalisee",
    "notation_mathématique",
    "auteur_source",
    "contribution_ia",
    "origine",
    "date_source",
    "statut_epistemique",
    "portee",
    "conditions",
    "dependances",
    "implique",
    "n_implique_pas",
    "preuves",
    "tests",
    "resultats",
    "contre_exemples",
    "contradictions",
    "implementations",
    "artefacts",
    "etat_4d",
    "historique_statuts",
    "conditions_reouverture",
    "sources",
    "notes",
)


def build_math_taxonomy() -> list[dict[str, Any]]:
    """Construit l'arborescence taxonomie MATH/00..08 demandée pour l'Encyclopédie Supela."""
    return [
        {
            "famille": "MATH/00_FONDEMENTS/",
            "titre": "État fondamental Sᵢ, monotonie Kₜ ⊆ Kₜ₊₁, projection Π₀ & Zéro-Intégration",
            "sous_modules": [
                "etat_fondamental.md (S_i = ⟨P_i, E_i, C_i, K_i⟩)",
                "monotonie_et_reset.md (K_t ⊆ K_{t+1}, C → ∅)",
                "projection_pi0.md (Π₀(S_t) = {I, P, M, A, H})",
                "zero_integration_ouverture.md (Théorème du Zéro-Intégration · INCONNU/LATENT)",
            ],
        },
        {
            "famille": "MATH/01_PREUVES/",
            "titre": "Treillis probatoire G₀..G₄, autorité bornée, récursivité & réflexivité",
            "sous_modules": [
                "treillis_probatoire_g0_g4.md (G_0 ≺ G_1 ≺ G_2 ≺ G_3 ≺ G_4)",
                "autorite_bornee.md (Authority(G) ≤ Proof(G))",
                "recursivite_garantie.md (G(G) ≤ P et G ⇒ P(G))",
                "reflexivite_probatoire.md (Formule hypothétique ∀R ...)",
            ],
        },
        {
            "famille": "MATH/02_STATUTS_4D/",
            "titre": "Cycle ACTIF → LATENT → RÉOUVERT, 7 statuts du Manque & conservation T11",
            "sous_modules": [
                "transitions_4d.md (ACTIF → LATENT → RÉOUVERT → ACTIF, explorable ≠ actif)",
                "conservation_echec_t11.md (NOUVEAU RÉSULTAT ⇏ EFFACEMENT DU PASSÉ)",
                "manque_deontologie_m1_m5.md (M(S_t, G), M1..M5)",
            ],
        },
        {
            "famille": "MATH/03_REVIDAGE_MIGRATION/",
            "titre": "Saturation Load(C), revidage E6/C09, RESET*, R* & VR-22",
            "sous_modules": [
                "saturation_et_revidage.md (Load(C) ≥ 0.80, PREPARE → VERIFY → COMMIT → CLEAN)",
                "reset_star_et_vr22.md (RESET*, R*, VR-22 · INCONNU/LATENT)",
            ],
        },
        {
            "famille": "MATH/04_DIMENSIONS_H_L_P/",
            "titre": "Distinction tridimensionnelle H ≠ L ≠ P sans effacement",
            "sous_modules": [
                "dimensions_orthogonales_hlp.md (Sens humain H ≠ Littéral L ≠ Établi P)",
            ],
        },
        {
            "famille": "MATH/05_CONFLITS_FUSION/",
            "titre": "Opérateur Merge*, invariance d'ordre E3 & conflits 4D conservés",
            "sous_modules": [
                "merge_star_invariance.md (Merge* ∈ {ACCEPTÉ, PARTIEL, CONTESTÉ, ISOLÉ, REFUSÉ})",
                "conflit_interdisciplinaire_c001.md (Conflict4D C-001 CONSERVÉ / NON_ACQUISE)",
            ],
        },
        {
            "famille": "MATH/06_RESPONSABILITE_TRANSFO/",
            "titre": "Séparation amélioration ≠ autorisation & chaîne de transformation H",
            "sous_modules": [
                "amelioration_vs_autorisation.md (amélioration ≠ autorisation, C10)",
                "chaine_transformation_h.md (brute = undefined · normalisation proposée)",
            ],
        },
        {
            "famille": "MATH/07_IA_GRPO/",
            "titre": "Pont Supela-GRPO : Reward(x) ⇏ Vérité(x) & preuve L=0, ∇L≠0",
            "sous_modules": [
                "reward_not_truth.md (Reward → Candidate → Preuves → Status)",
                "gradient_grpo_non_nul.md (L(θ_old)=0 ∧ ∇_θ L(θ_old)≠0)",
            ],
        },
        {
            "famille": "MATH/08_TESTS/",
            "titre": "Vérification exécutable T11, A12, OPA Rego v1, Ed25519, WORM & parité HTML",
            "sous_modules": [
                "matrice_tests_adversariaux.md (T11, E3 24 permutations, A12, Rego 16/16)",
                "chaine_parite_html_pages.md (JSON canonique → HTML → Parité/JS → Pages)",
            ],
        },
    ]


def build_architecture_xiii() -> list[dict[str, Any]]:
    """Construit la table normative des XIII grands domaines de l'Encyclopédie Supela."""
    return [
        {
            "roman": "I",
            "titre": "Fondements formels (Sᵢ, Π₀, Kₜ, Zéro-Intégration)",
            "description": "État fondamental S_i = ⟨P_i, E_i, C_i, K_i⟩, monotonie K_t ⊆ K_{t+1}, reset C → ∅, idempotence Π₀ et manque ouvert sur Zéro-Intégration.",
            "statut_couverture": "PARTIELLEMENT_EXTRAIT_CONVERSATIONS",
        },
        {
            "roman": "II",
            "titre": "Treillis probatoire & bornage d'autorité",
            "description": "Treillis G_0 ≺ G_1 ≺ G_2 ≺ G_3 ≺ G_4, loi Authority(G) ≤ Proof(G), récursivité G(G) ≤ P / G ⇒ P(G) et réflexivité hypothétique.",
            "statut_couverture": "PARTIELLEMENT_EXTRAIT_CONVERSATIONS",
        },
        {
            "roman": "III",
            "titre": "États 4D, Manque M & cycle de vie",
            "description": "7 statuts du Manque, transitions ACTIF → LATENT → RÉOUVERT → ACTIF, séparation explorable ≠ actif et règles M1–M5.",
            "statut_couverture": "ACCESSIBLE_VERIFIE",
        },
        {
            "roman": "IV",
            "titre": "Revidage transactionnel, saturation & RESET*",
            "description": "Seuil Load(C) ≥ 0.80, protocole E6/C09 (PREPARE→VERIFY→COMMIT→CLEAN) et famille RESET*, R*, VR-22 maintenue LATENT.",
            "statut_couverture": "PARTIELLEMENT_EXTRAIT_CONVERSATIONS",
        },
        {
            "roman": "V",
            "titre": "Dimensions orthogonales H / L / P",
            "description": "Séparation non-effaçante entre dimension sémantique humaine (H), dimension littérale (L) et dimension établie sous preuve (P).",
            "statut_couverture": "PARTIELLEMENT_EXTRAIT_CONVERSATIONS",
        },
        {
            "roman": "VI",
            "titre": "Conflits 4D & fusion multi-nœuds asynchrone",
            "description": "Opérateur Merge*, invariance stricte aux 24 permutations E3 et conservation explicite du conflit interdisciplinaire C-001.",
            "statut_couverture": "ACCESSIBLE_VERIFIE",
        },
        {
            "roman": "VII",
            "titre": "Transformation, responsabilité & autorisation humaine",
            "description": "Loi amélioration ≠ autorisation, statut maximal ADMISSIBLE_A_REVUE_HUMAINE et chaîne de transformation H (brute undefined).",
            "statut_couverture": "PARTIELLEMENT_EXTRAIT_CONVERSATIONS",
        },
        {
            "roman": "VIII",
            "titre": "Alignment IA, récompense GRPO & gradient",
            "description": "Pipeline Reward(x) → Candidate(x) → Preuves(x) → Status(x), barrière Reward(x) ⇏ Vérité(x) et contre-exemple L=0 / ∇L≠0.",
            "statut_couverture": "ACCESSIBLE_VERIFIE",
        },
        {
            "roman": "IX",
            "titre": "Monolithe GDS = ⟨D, O, A, γ⟩, SCT & VR-Fractal-Ω",
            "description": "Formalisme doctoral Supela-K3-Ω, Théorème de Cohérence Systémique γ*, PDD-01, disjoncteurs D0–D8 et VR-24.",
            "statut_couverture": "ACCESSIBLE_VERIFIE",
        },
        {
            "roman": "X",
            "titre": "Sécurité cryptographique, WORM, Ed25519, OPA & Règle A12",
            "description": "Coffre-fort WormVault, signatures Ed25519/Cosign v3, 16 tests Rego v1 et bijection documentaire verify_a12.",
            "statut_couverture": "ACCESSIBLE_VERIFIE",
        },
        {
            "roman": "XI",
            "titre": "Cartographie plateformes, GitHub, Drive & lecteurs Windows",
            "description": "15 dépôts GitHub, 54 artefacts Drive/Docs/Colab, 9 plateformes IA/navigateurs, M365 Copilot (extraits fournis) et C:/D: locaux.",
            "statut_couverture": "PARTIELLEMENT_EXTRAIT_CONVERSATIONS",
        },
        {
            "roman": "XII",
            "titre": "Registre des contradictions & non-effacement des échecs",
            "description": "Conservation permanente des contradictions (C-001) et échecs passés (T11 FAIL puis PASS) avec déclencheurs de réouverture.",
            "statut_couverture": "ACCESSIBLE_VERIFIE",
        },
        {
            "roman": "XIII",
            "titre": "Fiches YAML, artefact HTML statique & surface de consultation",
            "description": "Chaîne JSON canonique → Fiches YAML + HTML dérivé → Parité SHA-256 & syntaxe JS → Publication GitHub Pages séparée.",
            "statut_couverture": "ACCESSIBLE_VERIFIE",
        },
    ]


def _make_fiche(
    *,
    fid: str,
    nom: str,
    ftype: str,
    discipline: str,
    famille_math: str,
    section_xiii: str,
    source_type: str,
    url_source: str,
    formulation_brute: str,
    formulation_normalisee: str,
    notation: str,
    auteur_source: str,
    contribution_ia: str,
    origine: str,
    date_source: str,
    statut: str,
    portee: str,
    conditions: list[str],
    dependances: list[str],
    implique: str,
    n_implique_pas: str,
    preuves: list[str],
    tests: list[str],
    resultats: list[str],
    contre_exemples: list[str],
    contradictions: list[str],
    implementations: list[str],
    artefacts: list[str],
    etat_4d: str,
    historique_statuts: list[dict[str, str]],
    conditions_reouverture: str,
    sources: list[str],
    notes: str,
) -> dict[str, Any]:
    return {
        "id": fid,
        "nom": nom,
        "type": ftype,
        "discipline": discipline,
        "formulation_brute": formulation_brute,
        "formulation_normalisee": formulation_normalisee,
        "notation_mathématique": notation,
        "auteur_source": auteur_source,
        "contribution_ia": contribution_ia,
        "origine": origine,
        "date_source": date_source,
        "statut_epistemique": statut,
        "portee": portee,
        "conditions": conditions,
        "dependances": dependances,
        "implique": implique,
        "n_implique_pas": n_implique_pas,
        "preuves": preuves,
        "tests": tests,
        "resultats": resultats,
        "contre_exemples": contre_exemples,
        "contradictions": contradictions,
        "implementations": implementations,
        "artefacts": artefacts,
        "etat_4d": etat_4d,
        "historique_statuts": historique_statuts,
        "conditions_reouverture": conditions_reouverture,
        "sources": sources,
        "notes": notes,
        "_famille_math": famille_math,
        "_section_xiii": section_xiii,
        "_source_type": source_type,
        "_url_source": url_source,
    }


def build_formula_cards() -> list[dict[str, Any]]:
    """Construit les 20 fiches encyclopédiques YAML initiales au squelette universel (29 clés)."""
    m365_1 = (
        "https://m365.cloud.microsoft/chat/conversation/"
        "19:itiW3flsmEMNG4tP50OhJ8hkhqVdNYGtCQmSoX0J0zA1@thread.v2"
    )
    m365_2 = (
        "https://m365.cloud.microsoft/chat/conversation/"
        "19:b__mSUKbgyV6KrsLScOwey2Ti8-Fa0EFmEGYVZlbgrM1@thread.v2"
    )
    m365_3 = (
        "https://m365.cloud.microsoft/chat/conversation/"
        "19:aaBvPORfeBzfC2j9RnsFuEP3hSvhHqVwd9jyhWyGn241@thread.v2"
    )
    m365_4 = (
        "https://m365.cloud.microsoft/chat/conversation/"
        "19:Fcb7BblUm4nPjxP9J6HFPXK9wrCl7kZwQe354E_-Irk1@thread.v2"
    )
    m365_5 = (
        "https://m365.cloud.microsoft/chat/conversation/"
        "19:nWs3b4mo8etGD4tLAglKVZIpsWPuH5bqOOQwa9UnerI1@thread.v2"
    )
    return [
        _make_fiche(
            fid="MAT-00-ETAT-FOND",
            nom="État fondamental Supela Sᵢ",
            ftype="Formule",
            discipline="Fondements formels & Architecture 4D",
            famille_math="MATH/00_FONDEMENTS/",
            section_xiii="I",
            source_type="Conversation",
            url_source=m365_1,
            formulation_brute="S_i = ⟨P_i, E_i, C_i, K_i⟩",
            formulation_normalisee="Un état structuré i associe invariants P_i, règles d'inférence E_i, espace d'exécution C_i et registre monotone K_i.",
            notation="S_i = \\langle P_i, E_i, C_i, K_i \\rangle",
            auteur_source="Jean-François Gadbois (corpus Supela)",
            contribution_ia="Extraction Copilot M365 + normalisation squelette Antigravity (Source ≠ Autorité)",
            origine="Corpus conversationnel Copilot M365 & formalisme Ω-ZERO",
            date_source="2026-11-16",
            statut="SUPPORTÉ",
            portee="Modélisation des états de travail locaux/cloud avant projection Π₀",
            conditions=["Séparation explicite entre invariants P_i et contexte volatil C_i"],
            dependances=["MAT-00-MONOTONIE-K", "MAT-00-PI0"],
            implique="Distinction claire entre mémoire monotone K_i et contexte volatile C_i.",
            n_implique_pas="Ne prouve pas à lui seul la complétude de C_i sans vérification externe.",
            preuves=[
                "Extrait conversationnel explicite Copilot M365 fourni par l'utilisateur",
                "Correspondance structurelle avec ZeroState dans src/omega_zero/models.py",
            ],
            tests=["tests/test_pi0_and_manque.py", "tests/test_encyclopedie_dictionnaire.py"],
            resultats=["Correspondance structurelle vérifiée sur ZeroState {I, P, M, A, H}"],
            contre_exemples=[],
            contradictions=[],
            implementations=["src/omega_zero/models.py"],
            artefacts=["docs/constitution/DEFINITION_P0_PROJECTION.json"],
            etat_4d="ACTIF",
            historique_statuts=[
                {"date": "2026-11-16", "statut": "SUPPORTÉ", "etat_4d": "ACTIF", "motif": "Indexation initiale M365"}
            ],
            conditions_reouverture="Ajout ou scission d'une cinquième composante formelle dans S_i.",
            sources=[f"Copilot M365: {m365_1}", "docs/constitution/DEFINITION_P0_PROJECTION.json"],
            notes="Une conversation atteste l'apparition de la notation, non sa démonstration mathématique complète.",
        ),
        _make_fiche(
            fid="MAT-00-MONOTONIE-K",
            nom="Monotonie du registre Kₜ et Reset de C",
            ftype="Axiome",
            discipline="Fondements formels & Conservation historique",
            famille_math="MATH/00_FONDEMENTS/",
            section_xiii="I",
            source_type="Conversation",
            url_source=m365_1,
            formulation_brute="K_t ⊆ K_{t+1} ; C → ∅",
            formulation_normalisee="Le registre probatoire K_t croît sans effacement dans le temps même lorsque l'espace d'exécution C est réinitialisé à ∅.",
            notation="K_t \\subseteq K_{t+1} \\quad \\land \\quad (C \\to \\emptyset \\not\\Rightarrow K_{t+1} \\subset K_t)",
            auteur_source="Jean-François Gadbois",
            contribution_ia="Consolidation Copilot M365 + implémentation ledger WORM",
            origine="Corpus Copilot M365 + DEFINITION_P0_PROJECTION.json (Invariant I5)",
            date_source="2026-11-16",
            statut="PROUVÉ",
            portee="Journal WORM, revidage E6/C09 et historique 4D",
            conditions=["Journal append-only SHA-256 actif (WormVault) ou registre de transitions 4D"],
            dependances=["MAT-00-ETAT-FOND"],
            implique="Aucune preuve, réfutation ou transition passée n'est effacée lors d'un reset C → ∅.",
            n_implique_pas="N'interdit pas de réouvrir ou rétrograder l'autorité d'un raccord existant.",
            preuves=[
                "Tests append-only SHA-256 dans tests/test_worm_and_crypto.py",
                "Invariance I5 & TR-01..TR-16 dans tests/test_pi0_and_manque.py",
            ],
            tests=["tests/test_worm_and_crypto.py", "tests/test_pi0_and_manque.py"],
            resultats=["100% PASS sur chaînage WORM et non-suppression du Manque"],
            contre_exemples=["Toute tentative de transition (* -> SUPPRIMÉ) rejetée"],
            contradictions=["CONTR-T11"],
            implementations=["src/omega_zero/worm_ledger.py", "src/omega_zero/projection.py"],
            artefacts=["docs/constitution/STATUT_MANQUE.json", "docs/constitution/REGISTRE_CONTRADICTIONS.json"],
            etat_4d="ACTIF",
            historique_statuts=[
                {"date": "2026-11-16", "statut": "PROUVÉ", "etat_4d": "ACTIF", "motif": "Vérifié par WORM + tests I5"}
            ],
            conditions_reouverture="Modification du modèle d'archive WORM ou ajout de purge transactionnelle.",
            sources=[f"Copilot M365: {m365_1}", "src/omega_zero/worm_ledger.py"],
            notes="Fondement direct du registre des contradictions sans effacement.",
        ),
        _make_fiche(
            fid="MAT-00-PI0",
            nom="Opérateur de Projection Zéro Π₀ et Idempotence",
            ftype="Opérateur",
            discipline="Projection Π₀ & Reprise sans amnésie",
            famille_math="MATH/00_FONDEMENTS/",
            section_xiii="I",
            source_type="Code",
            url_source="docs/constitution/DEFINITION_P0_PROJECTION.json",
            formulation_brute="Π₀(S_t) = {I, P, M, A, H} ; Π₀(Π₀(S_t)) = Π₀(S_t)",
            formulation_normalisee="Projette S_t sur le quintuplet minimal honnête {Invariants, Preuves, Manques, Autorités, Histoire} de manière strictement idempotente.",
            notation="\\Pi_0(S_t) = \\{I, P, M, A, H\\}, \\quad \\Pi_0(\\Pi_0(S_t)) = \\Pi_0(S_t)",
            auteur_source="Jean-François Gadbois (Supela Ω-ZERO)",
            contribution_ia="Spécification Draft 2020-12 & tests Hypothesis",
            origine="DEFINITION_P0_PROJECTION.json & src/omega_zero/projection.py",
            date_source="2026-11-16",
            statut="PROUVÉ",
            portee="Noyau central de projection locale/cloud sans perte ni fabrication",
            conditions=["Conservation obligatoire des 5 composantes I, P, M, A, H"],
            dependances=["MAT-00-MONOTONIE-K", "MAT-02-MANQUE-M"],
            implique="Préservation exacte des manques ouverts et invariants après compaction ou transfert.",
            n_implique_pas="Ne résout pas les manques M en attente de preuve.",
            preuves=["Preuve exécutable par tests unitaires et Hypothesis"],
            tests=["tests/test_pi0_and_manque.py", "tests/test_properties_hypothesis.py"],
            resultats=["Idempotence et non-amnésie Lᵢ⁰ vérifiées"],
            contre_exemples=[],
            contradictions=[],
            implementations=["src/omega_zero/projection.py", "src/omega_zero/protocol.py"],
            artefacts=["docs/constitution/DEFINITION_P0_PROJECTION.json"],
            etat_4d="ACTIF",
            historique_statuts=[
                {"date": "2026-11-16", "statut": "PROUVÉ", "etat_4d": "ACTIF", "motif": "Vérifié par pytest"}
            ],
            conditions_reouverture="Changement des invariants I1..I5 ou I_M.",
            sources=["docs/constitution/DEFINITION_P0_PROJECTION.json", "src/omega_zero/projection.py"],
            notes="Étend Π_I(Ω_t) = 0_I.",
        ),
        _make_fiche(
            fid="MAT-00-ZERO-INT",
            nom="Théorème du Zéro-Intégration (Manque ouvert M365)",
            ftype="Théorème",
            discipline="Fondements formels — Corpus complémentaire non extrait",
            famille_math="MATH/00_FONDEMENTS/",
            section_xiii="I",
            source_type="Conversation",
            url_source=m365_4,
            formulation_brute="Théorème du Zéro-Intégration [énoncé complet non extrait dans le périmètre]",
            formulation_normalisee="Entrée d'exploration répertoriant le Théorème du Zéro-Intégration cité dans l'historique Copilot sans hypothèse ni énoncé reconstruit.",
            notation="\\text{Théorème du Zéro-Intégration} \\in \\text{Manque}(\\text{M365}) [\\text{INCONNU}]",
            auteur_source="Jean-François Gadbois (mention historique M365)",
            contribution_ia="Copilot M365 a signalé le titre ; Antigravity applique M3 (non-invention)",
            origine=f"Fils Copilot M365 {m365_4} et {m365_5}",
            date_source="2026-11-16",
            statut="INCONNU",
            portee="Périmètre d'exploration M365 / disques locaux Windows C:/D:",
            conditions=["Réouverture conditionnée à l'ouverture directe du fil/fichier source M365"],
            dependances=["MAT-02-MANQUE-M"],
            implique="Trace explicite que le corpus théorique complet dépasse les extraits actuellement lus.",
            n_implique_pas="N'autorise aucune reconstruction conjecturale de ses hypothèses ou de sa preuve.",
            preuves=[],
            tests=["tests/test_encyclopedie_dictionnaire.py::test_formulas_and_yaml_cards_honesty"],
            resultats=["Statut INCONNU / État 4D LATENT conservé sous règle M3"],
            contre_exemples=[],
            contradictions=["CONTR-ZERO-INT-MANQUANT"],
            implementations=[],
            artefacts=["docs/constitution/REGISTRE_CONTRADICTIONS.json"],
            etat_4d="LATENT",
            historique_statuts=[
                {"date": "2026-11-16", "statut": "INCONNU", "etat_4d": "LATENT", "motif": "Recherche M365 fichiers vide"}
            ],
            conditions_reouverture="Extraction textuelle du théorème depuis M365 Copilot ou C:/D: via collect_local_encyclopedie.ps1.",
            sources=[f"Copilot M365: {m365_4}", f"Copilot M365: {m365_5}"],
            notes="La recherche M365 fichiers n'ayant rien retourné, aucune hypothèse non sourcée n'est fabriquée.",
        ),
        _make_fiche(
            fid="MAT-01-TREILLIS",
            nom="Treillis probatoire G₀ ≺ G₁ ≺ G₂ ≺ G₃ ≺ G₄",
            ftype="Opérateur",
            discipline="Épistémologie formelle & Hiérarchie de preuve",
            famille_math="MATH/01_PREUVES/",
            section_xiii="II",
            source_type="Conversation",
            url_source=m365_1,
            formulation_brute="G_0 ≺ G_1 ≺ G_2 ≺ G_3 ≺ G_4",
            formulation_normalisee="Ordre strict partiel classant cinq degrés croissants de garantie probatoire avant toute élévation d'autorité.",
            notation="G_0 \\prec G_1 \\prec G_2 \\prec G_3 \\prec G_4",
            auteur_source="Jean-François Gadbois",
            contribution_ia="Extraction Copilot M365 + création fiche encyclopédique dédiée",
            origine="Corpus conversationnel Copilot M365 (exigence de fiche dédiée)",
            date_source="2026-11-16",
            statut="SUPPORTÉ",
            portee="Évaluation des garanties et raccordements candidats dans Supela Ω-ZERO",
            conditions=["Chaque niveau G_k requiert ses critères vérifiés sans saut arbitraire"],
            dependances=["MAT-01-AUTORITE-BORNEE"],
            implique="Hiérarchisation explicite empêchant d'assimiler une intuition (G_0) à une preuve établie (G_4).",
            n_implique_pas="Ne définit pas à lui seul les seuils numériques de chaque G_k tant que non figés en code.",
            preuves=["Formulation explicite dans Copilot M365 + correspondance EvidenceLevel dans models.py"],
            tests=["tests/test_pi0_and_manque.py", "tests/test_encyclopedie_dictionnaire.py"],
            resultats=["Fiche dédiée créée et reliée à Authority(G) ≤ Proof(G)"],
            contre_exemples=[],
            contradictions=[],
            implementations=["src/omega_zero/models.py"],
            artefacts=["docs/constitution/fiches/MAT-01-TREILLIS.yaml"],
            etat_4d="ACTIF",
            historique_statuts=[
                {"date": "2026-11-16", "statut": "SUPPORTÉ", "etat_4d": "ACTIF", "motif": "Fiche dédiée demandée par l'utilisateur"}
            ],
            conditions_reouverture="Publication de la définition formelle exhaustive de chacun des 5 échelons G_0..G_4.",
            sources=[f"Copilot M365: {m365_1}"],
            notes="Conformément à la consigne utilisateur, le treillis probatoire possède sa propre fiche plutôt que d'être fondu dans une page générale.",
        ),
        _make_fiche(
            fid="MAT-01-AUTORITE-BORNEE",
            nom="Loi d'Autorité Bornée par la Preuve",
            ftype="Axiome",
            discipline="Gouvernance & Sûreté épistémique",
            famille_math="MATH/01_PREUVES/",
            section_xiii="II",
            source_type="Conversation",
            url_source=m365_1,
            formulation_brute="Authority(G) ≤ Proof(G)",
            formulation_normalisee="L'autorité revendiquée ou accordée à une garantie G est strictement bornée supérieurement par son niveau de preuve vérifié.",
            notation="\\operatorname{Authority}(G) \\le \\operatorname{Proof}(G)",
            auteur_source="Jean-François Gadbois",
            contribution_ia="Cross-référencement Copilot M365 ↔ OPA Rego v1 ↔ protocol.py",
            origine="Copilot M365 + policies/omega_zero_invariants.rego + src/omega_zero/projection.py",
            date_source="2026-11-16",
            statut="PROUVÉ",
            portee="Totalité de l'écosystème Supela Ω-ZERO (C01..C10, Rego, HTML, Collecteur)",
            conditions=["Comparaison ordinale authority_level ≤ evidence_level appliquée avant toute promotion"],
            dependances=["MAT-01-TREILLIS"],
            implique="Rejet systématique de toute élévation d'autorité non étayée (Rego deny / ValidationError).",
            n_implique_pas="Ne borne pas l'exploration d'hypothèses à autorité nulle (explorable ≠ actif).",
            preuves=[
                "Vérification statique Draft 2020-12 sur local_pc_scan",
                "Tests négatifs OPA Rego v1 (16/16)",
                "Verification authority_level ≤ evidence_level dans projection.py",
            ],
            tests=["tests/test_pi0_and_manque.py", "tests/test_opa_rego.py", "tests/test_encyclopedie_dictionnaire.py"],
            resultats=["Invariant exécuté et validé en Python, Rego et JSON Schema"],
            contre_exemples=["Toute tentative COMPLETE_SOUS_PREUVE avec local_pc_scan != EXECUTEE échoue"],
            contradictions=["CONTR-PR1-PS1-AUDIT"],
            implementations=["src/omega_zero/projection.py", "policies/omega_zero_invariants.rego"],
            artefacts=["schemas/supela_encyclopedie_1.schema.json"],
            etat_4d="ACTIF",
            historique_statuts=[
                {"date": "2026-11-16", "statut": "PROUVÉ", "etat_4d": "ACTIF", "motif": "Exécuté dans Ω-ZERO et Rego"}
            ],
            conditions_reouverture="Contournement détecté dans un composant d'export, schéma ou agent.",
            sources=[f"Copilot M365: {m365_1}", "policies/omega_zero_invariants.rego"],
            notes="Pierre angulaire : la preuve borne l'autorité, mais elle ne borne pas l'exploration.",
        ),
        _make_fiche(
            fid="MAT-01-RECURSIVITE-G",
            nom="Récursivité de la garantie G(G) ≤ P et G ⇒ P(G)",
            ftype="Invariant",
            discipline="Auto-contrôle mécanique & Non-sursceau",
            famille_math="MATH/01_PREUVES/",
            section_xiii="II",
            source_type="Conversation",
            url_source=m365_1,
            formulation_brute="G(G) ≤ P ; G ⇒ P(G)",
            formulation_normalisee="Une garantie G ne peut s'auto-sceller au-delà de son périmètre de contrôle P et doit exposer les contrôles P(G) qui testent son propre mécanisme.",
            notation="\\mathcal{G}(\\mathcal{G}) \\le \\mathcal{P} \\quad \\land \\quad (\\mathcal{G} \\Rightarrow \\mathcal{P}(\\mathcal{G}))",
            auteur_source="Jean-François Gadbois",
            contribution_ia="Distinction des deux écritures Copilot M365 + lien vers F_sign ≠ F_certif",
            origine=f"Copilot M365 ({m365_1}) & GoogleDoc 1nTp9M...",
            date_source="2026-11-16",
            statut="INFÉRÉ",
            portee="Audit des mécanismes de vérification (WORM, Cosign, collecteur PS1, vérificateur HTML)",
            conditions=["Indépendance du certificateur F_sign ≠ F_certif pour lever le risque d'auto-certification"],
            dependances=["MAT-01-AUTORITE-BORNEE"],
            implique="Le vérificateur doit lui-même subir des tests de réfutation (comme CONTR-PR1-PS1-AUDIT).",
            n_implique_pas="Un script vert à ses propres tests n'est pas immunisé contre un angle mort externe.",
            preuves=["Trace conversationnelle Copilot + application pratique sur verify_html_parity / PS1 audit"],
            tests=["tests/test_escalation_4d.py", "tests/test_encyclopedie_dictionnaire.py"],
            resultats=["Les deux variantes formelles G(G) ≤ P et G ⇒ P(G) sont conservées côte à côte sans écrasement"],
            contre_exemples=["PR #1 CI 4/4 verte contenant encore 5 bogues mécaniques trouvés par relecture"],
            contradictions=["CONTR-PR1-PS1-AUDIT"],
            implementations=["scripts/verify_a12.py", "scripts/build_encyclopedie.py"],
            artefacts=["docs/constitution/REGISTRE_CONTRADICTIONS.json"],
            etat_4d="ACTIF",
            historique_statuts=[
                {"date": "2026-11-16", "statut": "INFÉRÉ", "etat_4d": "ACTIF", "motif": "Cohérence mécanique vérifiée, preuve formelle générale ouverte"}
            ],
            conditions_reouverture="Formalisation de type Gödel/Tarski bornée dans le noyau arithmétique ou Coq/Lean.",
            sources=[f"Copilot M365: {m365_1}"],
            notes="Les deux formulations historiques G(G) ≤ P et G ⇒ P(G) sont documentées distinctement.",
        ),
        _make_fiche(
            fid="MAT-01-REFLPROB",
            nom="Principe de Réflexivité Probatoire (Hypothétique)",
            ftype="Formule",
            discipline="Métalogique des tests & Auto-vérification",
            famille_math="MATH/01_PREUVES/",
            section_xiii="II",
            source_type="Conversation",
            url_source=m365_1,
            formulation_brute="∀R : (∀x, R(x) ⇒ Proof(R(x))) ⇒ (R ⇒ SelfTest(R))",
            formulation_normalisee="Toute règle R exigeant une preuve pour chacune de ses assertions x devrait elle-même être soumise à un auto-test explicite SelfTest(R).",
            notation="\\forall R:\\; (\\forall x,\\; R(x) \\Rightarrow \\operatorname{Proof}(R(x))) \\Rightarrow (R \\Rightarrow \\operatorname{SelfTest}(R))",
            auteur_source="Jean-François Gadbois",
            contribution_ia="Maintien exprès au statut HYPOTHÉTIQUE (historiquement présent ≠ théorème démontré)",
            origine=f"Corpus conversationnel Copilot M365 ({m365_1})",
            date_source="2026-11-16",
            statut="HYPOTHÉTIQUE",
            portee="Méta-règles de validation et suite d'auto-tests",
            conditions=["Définir formellement le prédicat SelfTest(R) sans cercle vicieux d'auto-certification"],
            dependances=["MAT-01-RECURSIVITE-G", "MAT-01-AUTORITE-BORNEE"],
            implique="Orientation normative vers la testabilité de chaque règle R.",
            n_implique_pas="NE CONSTITUE PAS un théorème mathématique démontré (mise en garde explicite M3).",
            preuves=["Formule historiquement présente dans le fil Copilot M365 uniquement"],
            tests=["tests/test_encyclopedie_dictionnaire.py::test_formulas_and_yaml_cards_honesty"],
            resultats=["Classée HYPOTHÉTIQUE sans surenchère d'autorité"],
            contre_exemples=["Un auto-test tautologique SelfTest(R) trivial ne prouve pas la validité de R"],
            contradictions=[],
            implementations=[],
            artefacts=["docs/constitution/fiches/MAT-01-REFLPROB.yaml"],
            etat_4d="ACTIF",
            historique_statuts=[
                {"date": "2026-11-16", "statut": "HYPOTHÉTIQUE", "etat_4d": "ACTIF", "motif": "Présence historique conversationnelle ≠ théorème prouvé"}
            ],
            conditions_reouverture="Démonstration formelle externe définissant domaine de R, modèle de SelfTest et borne de non-circularité.",
            sources=[f"Copilot M365: {m365_1}"],
            notes="Garde-fou explicite demandé : formule historiquement présente dans Supela ≠ théorème démontré.",
        ),
        _make_fiche(
            fid="MAT-02-ETATS-4D",
            nom="Cycle temporel 4D : ACTIF → LATENT → RÉOUVERT → ACTIF",
            ftype="Règle",
            discipline="Dynamique temporelle 4D & Traçabilité",
            famille_math="MATH/02_STATUTS_4D/",
            section_xiii="III",
            source_type="Conversation",
            url_source=m365_2,
            formulation_brute="ACTIF → LATENT → RÉOUVERT → ACTIF ; explorable ≠ actif",
            formulation_normalisee="Un objet mis en veille passe à l'état LATENT sans perte et reste réouvrable vers RÉOUVERT puis ACTIF ; être explorable ne donne jamais le statut actif.",
            notation="\\text{ACTIF} \\to \\text{LATENT} \\to \\text{RÉOUVERT} \\to \\text{ACTIF} \\quad \\land \\quad (\\text{explorable} \\neq \\text{actif})",
            auteur_source="Jean-François Gadbois",
            contribution_ia="Alignement avec TR-14..TR-16 de STATUT_MANQUE.json et cone reopening de protocol.py",
            origine=f"Copilot M365 ({m365_2}) & docs/constitution/STATUT_MANQUE.json",
            date_source="2026-11-16",
            statut="PROUVÉ",
            portee="Cycle de vie de toute fiche, contradiction, manque ou raccord dans Ω-ZERO",
            conditions=["Traçabilité temporelle M5 conservant la cause de mise en latence et de réouverture"],
            dependances=["MAT-00-MONOTONIE-K", "MAT-02-MANQUE-M"],
            implique="Distinction stricte entre explorabilité (champ libre) et activation probatoire (sous preuve).",
            n_implique_pas="Un élément LATENT ou RÉOUVERT n'est pas effacé ni validé automatiquement.",
            preuves=["Machine à états exécutée dans src/omega_zero/projection.py & protocol.py (C07)"],
            tests=["tests/test_pi0_and_manque.py", "tests/test_escalation_4d.py"],
            resultats=["Réouverture de cône et TR-14/15/16 vérifiées avec rejet des sauts illicites"],
            contre_exemples=["Saut direct OUVERT → RÉSOLU sans preuve bloqué par ManqueStateMachine"],
            contradictions=[],
            implementations=["src/omega_zero/projection.py", "src/omega_zero/protocol.py"],
            artefacts=["docs/constitution/STATUT_MANQUE.json"],
            etat_4d="ACTIF",
            historique_statuts=[
                {"date": "2026-11-16", "statut": "PROUVÉ", "etat_4d": "ACTIF", "motif": "Vérifié par C07 & TR-14..16"}
            ],
            conditions_reouverture="Ajout d'un nouvel état 4D ou d'une transition non répertoriée dans TR-01..TR-16.",
            sources=[f"Copilot M365: {m365_2}", "docs/constitution/STATUT_MANQUE.json"],
            notes="Fondement des champs etat_4d et conditions_reouverture présents sur chaque fiche YAML.",
        ),
        _make_fiche(
            fid="MAT-02-CONSERVATION-ECHEC",
            nom="Conservation des échecs adversariaux (Cas T11)",
            ftype="Invariant",
            discipline="Résilience & Chronologie XII sans effacement",
            famille_math="MATH/02_STATUTS_4D/",
            section_xiii="XII",
            source_type="Conversation",
            url_source=m365_2,
            formulation_brute="T11 : FAIL antérieur conservé même après PASS ultérieur",
            formulation_normalisee="Un succès PASS ultérieur clôt ou met en latence l'incident courant sans jamais effacer la trace FAIL initiale dans l'historique.",
            notation="\\text{FAIL}_{t_0} \\land \\text{PASS}_{t_1} \\not\\Rightarrow \\operatorname{Erase}(\\text{FAIL}_{t_0})",
            auteur_source="Jean-François Gadbois",
            contribution_ia="Inscription dans REGISTRE_CONTRADICTIONS.json (CONTR-T11)",
            origine=f"Copilot M365 ({m365_2}) & Invariant I5",
            date_source="2026-11-16",
            statut="PROUVÉ",
            portee="Registre des contradictions, journaux WORM et historiques CI",
            conditions=["Enregistrement immuable (effacement_interdit: true) dans REGISTRE_CONTRADICTIONS.json"],
            dependances=["MAT-00-MONOTONIE-K", "MAT-02-ETATS-4D"],
            implique="Tout correctif conserve la mémoire de la défaillance antérieure comme garde-fou de non-régression.",
            n_implique_pas="Un FAIL passé conservé n'invalide pas un correctif ultérieur prouvé, tant que la régression reste couverte.",
            preuves=["Règle I5 vérifiée par test_pi0_and_manque.py et validation du registre CONTR-T11"],
            tests=["tests/test_pi0_and_manque.py", "tests/test_encyclopedie_dictionnaire.py"],
            resultats=["CONTR-T11 et CONTR-PR1-PS1-AUDIT indexés avec statut HISTORIQUE_CORRIGEE_CONSERVEE"],
            contre_exemples=["Suppression de logs FAIL lors d'un re-run vert CI"],
            contradictions=["CONTR-T11", "CONTR-PR1-PS1-AUDIT"],
            implementations=["src/omega_zero/worm_ledger.py"],
            artefacts=["docs/constitution/REGISTRE_CONTRADICTIONS.json", "docs/constitution/REGISTRE_CONTRADICTIONS.md"],
            etat_4d="ACTIF",
            historique_statuts=[
                {"date": "2026-11-16", "statut": "PROUVÉ", "etat_4d": "ACTIF", "motif": "Verrouillé par supela_contradictions_1.schema.json"}
            ],
            conditions_reouverture="Toute modification du schéma contradictions ou tentative d'effacement d'entrée.",
            sources=[f"Copilot M365: {m365_2}", "docs/constitution/REGISTRE_CONTRADICTIONS.json"],
            notes="Directement lié à la section XII et au cas adversarial T11.",
        ),
        _make_fiche(
            fid="MAT-02-MANQUE-M",
            nom="Objet Manque M et Règles Déontologiques M1–M5",
            ftype="Opérateur",
            discipline="Déontologie épistémique & Gestion de l'incomplet",
            famille_math="MATH/02_STATUTS_4D/",
            section_xiii="III",
            source_type="Code",
            url_source="docs/constitution/STATUT_MANQUE.json",
            formulation_brute="M(S_t, G) ⟺ Required(G) \\ Available(S_t) ≠ ∅ ; M1..M5 (OPEN ∧ ¬FABRICATE)",
            formulation_normalisee="Formalise tout déficit de preuve requis pour établir G et interdit de convertir une absence en faux, en vrai caché ou en invention.",
            notation="M(S_t, G) \\iff \\operatorname{Required}(G) \\setminus \\operatorname{Available}(S_t) \\neq \\emptyset",
            auteur_source="Jean-François Gadbois (Supela Ω-ZERO)",
            contribution_ia="Schéma Draft 2020-12 & barrières allOf sur local_pc_scan",
            origine="docs/constitution/STATUT_MANQUE.json & schemas/supela_encyclopedie_1.schema.json",
            date_source="2026-11-16",
            statut="PROUVÉ",
            portee="Qualification des manquants (C:/, D:/, M365, historique Edge/Arc/Brave/ChatGPT)",
            conditions=["7 statuts canoniques exclusifs + interdiction * -> SUPPRIMÉ"],
            dependances=["MAT-00-PI0"],
            implique="Le système déclare honnêtement OUVERT_INCOMPLET_C_D_IA_LOCALES tant que C:/ et D:/ ne sont pas scannés.",
            n_implique_pas="Un Manque M ouvert n'est ni une réfutation automatique ni un feu vert implicite.",
            preuves=["Tests paramétrés négatifs Draft 2020-12 + 7 statuts dans ManqueStateMachine"],
            tests=["tests/test_pi0_and_manque.py", "tests/test_encyclopedie_dictionnaire.py"],
            resultats=["Rejet systématique de toute clôture prématurée"],
            contre_exemples=["Toute mutation JSON proclamant COMPLETE_SOUS_PREUVE sans scan EXECUTEE"],
            contradictions=["CONTR-ZERO-INT-MANQUANT"],
            implementations=["src/omega_zero/models.py", "src/omega_zero/projection.py"],
            artefacts=["docs/constitution/STATUT_MANQUE.json", "schemas/supela_encyclopedie_1.schema.json"],
            etat_4d="ACTIF",
            historique_statuts=[
                {"date": "2026-11-16", "statut": "PROUVÉ", "etat_4d": "ACTIF", "motif": "Verrou M3 exécuté en schéma et tests"}
            ],
            conditions_reouverture="Scan effectif des disques C:/D: et plateformes IA locales par collect_local_encyclopedie.ps1.",
            sources=["docs/constitution/STATUT_MANQUE.json", "schemas/supela_encyclopedie_1.schema.json"],
            notes="Gouverne directement le comportement de ce dépôt sur les lecteurs Windows non montés.",
        ),
        _make_fiche(
            fid="MAT-03-RESET-STAR",
            nom="Famille RESET*, R* et VR-22 (Manque ouvert M365)",
            ftype="Opérateur",
            discipline="Revidage & Protocoles complémentaires non extraits",
            famille_math="MATH/03_REVIDAGE_MIGRATION/",
            section_xiii="IV",
            source_type="Conversation",
            url_source=m365_5,
            formulation_brute="RESET* ; R* ; VR-22 [spécifications détaillées non extraites]",
            formulation_normalisee="Marqueurs méthodologiques identifiés dans l'historique Copilot M365 sans contenu intégral récupéré ; maintenus LATENT / INCONNU.",
            notation="\\{\\text{RESET}^*,\\; R^*,\\; \\text{VR-22}\\} \\subseteq \\text{Périmètre non extrait} [\\text{INCONNU}]",
            auteur_source="Jean-François Gadbois (corpus M365)",
            contribution_ia="Préservation de l'espace exploratoire sans invention (Antigravity)",
            origine=f"Fils Copilot M365 {m365_4} et {m365_5}",
            date_source="2026-11-16",
            statut="INCONNU",
            portee="Articulation future avec E6 / C09 (PREPARE→VERIFY→COMMIT→CLEAN) et C → ∅",
            conditions=["Accès direct aux fils complets ou documents Drive/C:/D: définissant RESET*, R* et VR-22"],
            dependances=["MAT-03-REVIDAGE-LOAD", "MAT-00-MONOTONIE-K"],
            implique="Ouverture explicite d'une piste à ne pas oublier lors de l'exploration du corpus Supela.",
            n_implique_pas="Ne doit pas être confondu avec VR-24 (Canon de Continuité, lui documenté) ni avec Load(C).",
            preuves=[],
            tests=["tests/test_encyclopedie_dictionnaire.py::test_formulas_and_yaml_cards_honesty"],
            resultats=["Fiche placée en état LATENT et statut INCONNU"],
            contre_exemples=[],
            contradictions=["CONTR-ZERO-INT-MANQUANT"],
            implementations=[],
            artefacts=["docs/constitution/fiches/MAT-03-RESET-STAR.yaml"],
            etat_4d="LATENT",
            historique_statuts=[
                {"date": "2026-11-16", "statut": "INCONNU", "etat_4d": "LATENT", "motif": "Mentionné sans corps récupéré"}
            ],
            conditions_reouverture="Extraction textuelle directe de RESET*, R* et VR-22 dans un artefact vérifiable.",
            sources=[f"Copilot M365: {m365_4}", f"Copilot M365: {m365_5}"],
            notes="Ne pas inventer la sémantique de VR-22 par simple analogie avec VR-24.",
        ),
        _make_fiche(
            fid="MAT-03-REVIDAGE-LOAD",
            nom="Saturation Load(C) et Revidage Transactionnel (E6 / C09)",
            ftype="Métrique",
            discipline="Migration contrôlée & Protocole 4D",
            famille_math="MATH/03_REVIDAGE_MIGRATION/",
            section_xiii="IV",
            source_type="Code",
            url_source="docs/constitution/PLAN_4D_OMEGA_ZERO_ESC_01.md",
            formulation_brute="Load(C) = max(Bytes, Objects, Edges, Latency) ≥ 0.80 ; PREPARE → VERIFY → COMMIT → CLEAN",
            formulation_normalisee="Déclenche une migration vers C2 à 0.80 et impose 5 prédicats ACK avant toute purge locale CLEAN.",
            notation="\\operatorname{Load}(C) = \\max(\\text{Bytes}, \\text{Objects}, \\text{Edges}, \\text{Latency}) \\ge 0.80",
            auteur_source="Jean-François Gadbois (Supela Ω-ZERO)",
            contribution_ia="Implémentation transactionnelle & règles Rego C08/C09",
            origine="PLAN_4D_OMEGA_ZERO_ESC_01.md & src/omega_zero/protocol.py",
            date_source="2026-11-16",
            statut="PROUVÉ",
            portee="Transfert sans perte Local → Cloud et préservation du noyau Lᵢ⁰",
            conditions=["5 prédicats : ACK, HashMatch, ProvenanceOK, AuthorityOK, ReconstructionPASS"],
            dependances=["MAT-00-PI0", "MAT-00-MONOTONIE-K"],
            implique="Rollback local automatique si un seul des 5 prédicats ACK échoue avant CLEAN.",
            n_implique_pas="Le nettoyage local CLEAN ne produit jamais L_i_amnésique.",
            preuves=["Tests positifs/négatifs C08 et C09 dans pytest et OPA Rego v1"],
            tests=["tests/test_escalation_4d.py", "tests/rego/omega_zero_invariants_test.rego"],
            resultats=["10/10 conditions normatives et rollback vérifiés"],
            contre_exemples=["Clean prématuré avec HashMatch=False rejeté par C09 et Rego"],
            contradictions=[],
            implementations=["src/omega_zero/protocol.py", "policies/omega_zero_invariants.rego"],
            artefacts=["docs/constitution/PLAN-4D-ΩZERO-ESC-01.json", "reports/TEST-4D-ESC-01.report.json"],
            etat_4d="ACTIF",
            historique_statuts=[
                {"date": "2026-11-16", "statut": "PROUVÉ", "etat_4d": "ACTIF", "motif": "C08/C09 validées"}
            ],
            conditions_reouverture="Changement du seuil 0.80 ou des 5 prédicats de confirmation ACK.",
            sources=["docs/constitution/PLAN_4D_OMEGA_ZERO_ESC_01.md", "src/omega_zero/protocol.py"],
            notes="Cœur exécutable du palier E6 du protocole PLAN-4D-ΩZERO-ESC-01.",
        ),
        _make_fiche(
            fid="MAT-04-HLP",
            nom="Distinction Tridimensionnelle H ≠ L ≠ P",
            ftype="Distinction",
            discipline="Sémantique structurée & Coexistence sans effacement",
            famille_math="MATH/04_DIMENSIONS_H_L_P/",
            section_xiii="V",
            source_type="Conversation",
            url_source=m365_2,
            formulation_brute="H ≠ L ≠ P",
            formulation_normalisee="Distingue le sens humain (H), la formulation littérale (L) et le plan probatoire établi (P) en autorisant leur coexistence explicite sans effacement.",
            notation="H \\neq L \\neq P",
            auteur_source="Jean-François Gadbois",
            contribution_ia="Structuration Copilot M365 + liaison brute/normalisée/probatoire dans l'Encyclopédie",
            origine=f"Corpus conversationnel Copilot M365 ({m365_2})",
            date_source="2026-11-16",
            statut="SUPPORTÉ",
            portee="Toute fiche formule, comparaison brute vs normalisée et analyse de discours IA",
            conditions=["Ne jamais écraser L (formulation_brute) par H ou P (ex. cas undefined sur MAT-06-CHAINE-TRANSFO)"],
            dependances=["MAT-01-AUTORITE-BORNEE", "MAT-02-CONSERVATION-ECHEC"],
            implique="Coexistence lisible entre intention humaine, texte brut archivé et preuve technique.",
            n_implique_pas="Une reformulation claire (H) ne vaut pas formulation littérale d'origine (L) ni preuve (P).",
            preuves=[
                "Extrait Copilot M365 fourni par l'utilisateur",
                "Séparation formulation_brute / formulation_normalisee / statut_epistemique du registre",
            ],
            tests=["tests/test_encyclopedie_dictionnaire.py"],
            resultats=["Appliqué structurellement à chaque fiche YAML universelle"],
            contre_exemples=["Substitution silencieuse d'un extrait 'undefined' par une phrase réécrite sans avertissement"],
            contradictions=["CONTR-TRANSFO-UNDEF"],
            implementations=["scripts/build_encyclopedie.py"],
            artefacts=["docs/constitution/REGISTRE_FORMULES_SUPELA.md"],
            etat_4d="ACTIF",
            historique_statuts=[
                {"date": "2026-11-16", "statut": "SUPPORTÉ", "etat_4d": "ACTIF", "motif": "Implémenté structurellement dans le tableau des formules"}
            ],
            conditions_reouverture="Nouvelle dimension orthogonale identifiée dans les textes originaux H/L/P.",
            sources=[f"Copilot M365: {m365_2}"],
            notes="Justifie pourquoi le registre sépare formulation brute, normalisation et statut probatoire.",
        ),
        _make_fiche(
            fid="MAT-05-MERGE-STAR",
            nom="Opérateur Merge* et Invariance d'Ordre (24 Permutations E3)",
            ftype="Opérateur",
            discipline="Fusion distribuée asynchrone 4D",
            famille_math="MATH/05_CONFLITS_FUSION/",
            section_xiii="VI",
            source_type="Code",
            url_source="src/omega_zero/protocol.py",
            formulation_brute="Merge*(Δ_π(1)..Δ_π(n)) ∈ {ACCEPTÉ, PARTIEL, CONTESTÉ, ISOLÉ, REFUSÉ}",
            formulation_normalisee="Fusionne des deltas locaux asynchrones en garantissant que l'ordre d'arrivée n'accorde jamais d'autorité supplémentaire.",
            notation="\\operatorname{Merge}^*(\\Delta_{\\pi(1)}, \\dots, \\Delta_{\\pi(k)}) \\in \\{\\text{ACCEPTÉ}, \\text{PARTIEL}, \\text{CONTESTÉ}, \\text{ISOLÉ}, \\text{REFUSÉ}\\}",
            auteur_source="Jean-François Gadbois (Supela Ω-ZERO)",
            contribution_ia="Vérification exhaustive 4! = 24 permutations & Hypothesis",
            origine="PLAN_4D_OMEGA_ZERO_ESC_01.md & src/omega_zero/protocol.py",
            date_source="2026-11-16",
            statut="PROUVÉ",
            portee="Escalier E3 et agrégation cloud Multi-Nœuds",
            conditions=["Clé canonique indépendante de l'ordre d'arrivée horaire"],
            dependances=["MAT-01-AUTORITE-BORNEE", "MAT-05-CONFLIT-C001"],
            implique="Résultat de fusion identique quelles que soient les permutations d'arrivée réseau.",
            n_implique_pas="L'invariance d'ordre ne résout pas un conflit disciplinaire réel C-001.",
            preuves=["Tests exhaustifs sur 24 permutations + génération stochastique Hypothesis"],
            tests=["tests/test_properties_hypothesis.py", "tests/test_escalation_4d.py"],
            resultats=["24/24 permutations invariantes + propriétés Hypothesis PASS"],
            contre_exemples=[],
            contradictions=[],
            implementations=["src/omega_zero/protocol.py"],
            artefacts=["reports/TEST-4D-ESC-01.report.json"],
            etat_4d="ACTIF",
            historique_statuts=[
                {"date": "2026-11-16", "statut": "PROUVÉ", "etat_4d": "ACTIF", "motif": "Vérifié par pytest & Hypothesis"}
            ],
            conditions_reouverture="Extension à un nouveau statut de verdict Merge*.",
            sources=["src/omega_zero/protocol.py", "tests/test_properties_hypothesis.py"],
            notes="Valide formellement la condition C05 de non-privilège temporel.",
        ),
        _make_fiche(
            fid="MAT-05-CONFLIT-C001",
            nom="Conflit Interdisciplinaire Conservé C-001",
            ftype="Contre-exemple",
            discipline="Psychologie × Droit du travail × Gestion (4D)",
            famille_math="MATH/05_CONFLITS_FUSION/",
            section_xiii="VI",
            source_type="Rapport",
            url_source="docs/constitution/TEST_P0_EXEMPLE.json",
            formulation_brute="C-001 = {CONFLIT_INTERDISCIPLINAIRE, CONSERVÉ, NON_ACQUISE}",
            formulation_normalisee="Un désaccord fondamental entre disciplines ne peut être moyenné ni écrasé ; il demeure CONSERVÉ à autorité NON_ACQUISE.",
            notation="C\\text{-}001 = \\langle \\text{Psychologie} \\perp \\text{Droit} \\perp \\text{Gestion},\\; \\text{CONSERVÉ},\\; \\text{NON\\_ACQUISE} \\rangle",
            auteur_source="Jean-François Gadbois (Supela Ω-ZERO)",
            contribution_ia="Tests de non-unanimité artificielle (C04/C05 + I4)",
            origine="docs/constitution/TEST_P0_EXEMPLE.json & reports/TEST-4D-ESC-01.report.json",
            date_source="2026-11-16",
            statut="CONTRADICTOIRE",
            portee="Conservation de contradiction ouverte dans Π₀ et Merge*",
            conditions=["Présence simultanée d'évaluations disciplinaires incompatibles"],
            dependances=["MAT-05-MERGE-STAR", "MAT-02-CONSERVATION-ECHEC"],
            implique="Blocage de toute synthèse consensuelle factice et maintien visible dans REGISTRE_CONTRADICTIONS.",
            n_implique_pas="La persistance de C-001 ne bloque pas l'exécution du reste du graphe compatible.",
            preuves=["Rapport exécuté reports/TEST-4D-ESC-01.report.json + tests/test_escalation_4d.py"],
            tests=["tests/test_escalation_4d.py", "tests/test_second_domain_example.py"],
            resultats=["Conflit C-001 conservé et vérifié dans 2 domaines distincts"],
            contre_exemples=["Unanimité artificielle détectée et bloquée par C04"],
            contradictions=["CONTR-C001"],
            implementations=["src/omega_zero/models.py", "src/omega_zero/scenarios.py"],
            artefacts=["docs/constitution/TEST_P0_EXEMPLE.json", "docs/constitution/REGISTRE_CONTRADICTIONS.json"],
            etat_4d="ACTIF",
            historique_statuts=[
                {"date": "2026-11-16", "statut": "CONTRADICTOIRE", "etat_4d": "ACTIF", "motif": "Contradiction réelle volontairement non écrasée"}
            ],
            conditions_reouverture="Nouvelle preuve empirique/juridique satisfaisant Required(G) des trois disciplines.",
            sources=["docs/constitution/TEST_P0_EXEMPLE.json", "reports/TEST-4D-ESC-01.report.json"],
            notes="Cas canonique montrant comment Supela représente une contradiction vivante sans la détruire.",
        ),
        _make_fiche(
            fid="MAT-06-AMELIORATION-AUTO",
            nom="Séparation Amélioration ≠ Autorisation",
            ftype="Règle",
            discipline="Gouvernance humaine & Souveraineté décisionnelle",
            famille_math="MATH/06_RESPONSABILITE_TRANSFO/",
            section_xiii="VII",
            source_type="Conversation",
            url_source=m365_2,
            formulation_brute="amélioration ≠ autorisation ; ADMISSIBLE_A_REVUE_HUMAINE",
            formulation_normalisee="Une amélioration technique, de score ou de couverture n'emporte jamais l'autorisation de déploiement ou de fusion autonome sans validation humaine.",
            notation="\\text{Amélioration} \\not\\Rightarrow \\text{Autorisation}",
            auteur_source="Jean-François Gadbois",
            contribution_ia="Lien Copilot M365 ↔ Condition C10 & Politique PR #1 / Pages",
            origine=f"Copilot M365 ({m365_2}), policies/omega_zero_invariants.rego (C10)",
            date_source="2026-11-16",
            statut="PROUVÉ",
            portee="Pipeline C10, promotion GitHub PR #1 → main, activation GitHub Pages",
            conditions=["Décision finale humaine obligatoire (review_human / allow_human_review)"],
            dependances=["MAT-01-AUTORITE-BORNEE"],
            implique="Séparation entre préparation vérifiée (HTML exporté + workflows prêts) et acte d'autorisation (fusion/publication).",
            n_implique_pas="Ne freine pas l'outillage d'inspection et de test automatisés.",
            preuves=["Rego rule allow_human_review (16 tests)", "Discipline appliquée à PR #1 et Pages workflow_dispatch"],
            tests=["tests/test_opa_rego.py", "tests/test_escalation_4d.py"],
            resultats=["Aucune auto-promotion vers main autorisée par le moteur ou OPA"],
            contre_exemples=["auto_merge=True sans humain rejeté par C10 et OPA"],
            contradictions=[],
            implementations=["policies/omega_zero_invariants.rego", "src/omega_zero/protocol.py"],
            artefacts=["docs/constitution/PLAN-4D-ΩZERO-ESC-01.json", ".github/workflows/pages-encyclopedie.yml"],
            etat_4d="ACTIF",
            historique_statuts=[
                {"date": "2026-11-16", "statut": "PROUVÉ", "etat_4d": "ACTIF", "motif": "Verrouillé en C10 et Rego"}
            ],
            conditions_reouverture="Validation humaine explicite enregistrée pour une opération précise.",
            sources=[f"Copilot M365: {m365_2}", "policies/omega_zero_invariants.rego"],
            notes="Matérialisée directement dans le workflow GitHub Pages strictement manuel (workflow_dispatch).",
        ),
        _make_fiche(
            fid="MAT-06-CHAINE-TRANSFO",
            nom="Chaîne de Transformation H (Source brute undefined)",
            ftype="Formule",
            discipline="Transformation & Responsabilité (Section H)",
            famille_math="MATH/06_RESPONSABILITE_TRANSFO/",
            section_xiii="VII",
            source_type="Conversation",
            url_source=m365_2,
            formulation_brute="undefined",
            formulation_normalisee="Proposition dérivée non sourcée : Demande → Interprétation → Transformation → Résultat (formule brute absente : undefined)",
            notation="\\text{Brut} = \\text{undefined} \\;\\mid\\; \\text{Proposition normalisée} : \\text{Demande} \\to \\text{Interprétation} \\to \\text{Transformation} \\to \\text{Résultat}",
            auteur_source="Inconnu dans l'extrait source (chaîne brute retournée 'undefined')",
            contribution_ia="Copilot/Antigravity proposent une normalisation explicite sans l'attribuer à l'archive",
            origine=f"Extrait Copilot M365 Section H ({m365_2}) retournant littéralement 'undefined'",
            date_source="2026-11-16",
            statut="INCONNU",
            portee="Traçabilité de la responsabilité entre demande, interprétation et résultat",
            conditions=["Ne jamais masquer le caractère undefined de l'expression d'origine"],
            dependances=["MAT-04-HLP", "MAT-02-MANQUE-M"],
            implique="Exemple exemplaire d'honnêteté M3 : la proposition normalisée est clairement séparée du texte brut manquant.",
            n_implique_pas="La chaîne proposée N'EST PAS certifiée comme étant la formule exacte originelle.",
            preuves=[],
            tests=["tests/test_encyclopedie_dictionnaire.py::test_formulas_and_yaml_cards_honesty"],
            resultats=["Conservée en état RÉOUVERT et statut INCONNU jusqu'à vérification du fil originel"],
            contre_exemples=["Effacer 'undefined' et prétendre que la chaîne normalisée vient d'un document source"],
            contradictions=["CONTR-TRANSFO-UNDEF"],
            implementations=[],
            artefacts=["docs/constitution/fiches/MAT-06-CHAINE-TRANSFO.yaml", "docs/constitution/REGISTRE_CONTRADICTIONS.json"],
            etat_4d="RÉOUVERT",
            historique_statuts=[
                {"date": "2026-11-16", "statut": "INCONNU", "etat_4d": "RÉOUVERT", "motif": "Extraction brute retournée comme 'undefined'"}
            ],
            conditions_reouverture="Relecture complète de la conversation originale 19:b__mSUKb... ou des archives locales pour rétablir la formulation brute.",
            sources=[f"Copilot M365: {m365_2}"],
            notes="Conformité stricte M3 & H ≠ L ≠ P : on garde 'undefined' intact en formulation_brute et on qualifie la normalisation de proposition non sourcée.",
        ),
        _make_fiche(
            fid="MAT-07-REWARD-NOT-TRUTH",
            nom="Découplage Récompense IA vs Vérité (GRPO / L=0, ∇L≠0)",
            ftype="Contre-exemple",
            discipline="Apprentissage par renforcement IA & Preuve indépendante",
            famille_math="MATH/07_IA_GRPO/",
            section_xiii="VIII",
            source_type="Code",
            url_source=m365_3,
            formulation_brute="Reward(x) → Candidate(x) → Preuves(x) → Status(x) ; Reward(x) ⇏ Vérité(x) ; L(θ_old)=0 ∧ ∇_θ L(θ_old)≠0",
            formulation_normalisee="Un signal de récompense produit au mieux un candidat explorable à soumettre à preuve indépendante ; de même L_GRPO(θ_old)=0 n'annule pas le gradient.",
            notation="\\operatorname{Reward}(x) \\to \\operatorname{Candidate}(x) \\to \\operatorname{Preuves}(x) \\to \\operatorname{Status}(x), \\quad \\operatorname{Reward}(x) \\not\\Rightarrow \\text{Vérité}(x)",
            auteur_source="Jean-François Gadbois",
            contribution_ia="Dérivation analytique + calcul numérique dans grpo_bridge.py & Copilot M365",
            origine=f"Copilot M365 ({m365_3}), SCHEMA_GRPO_SUPELA.md & src/omega_zero/grpo_bridge.py",
            date_source="2026-11-16",
            statut="PROUVÉ",
            portee="Évaluation de sorties LLM/RLVR et pont Supela-GRPO en 5 étages",
            conditions=["Aucun verdict épistémique déduit directement d'un score ou avantage relatif A_i"],
            dependances=["MAT-01-AUTORITE-BORNEE", "MAT-02-ETATS-4D"],
            implique="Le score guide la recherche d'hypothèses (Candidate) mais seule une preuve externe fixe le Status.",
            n_implique_pas="Un score élevé ou une perte scalaire nulle au point θ_old n'implique ni gradient nul ni vérité.",
            preuves=[
                "Preuve numérique exécutée à μ=1, β=0, θ_old=0.25 : L=0.0, ∇L=-0.273837",
                "Garde-fous OPA Rego interdisant promotion GRPO sans preuve indépendante",
            ],
            tests=["tests/test_second_domain_example.py", "tests/test_opa_rego.py"],
            resultats=["grad_theta non nul et blocage Rego vérifiés en CI"],
            contre_exemples=["L(θ_old)=0 ∧ ∇_θ L(θ_old)≠0 (CONTR-GRPO-001)"],
            contradictions=["CONTR-GRPO-001"],
            implementations=["src/omega_zero/grpo_bridge.py", "policies/omega_zero_invariants.rego"],
            artefacts=["docs/constitution/SCHEMA_GRPO_SUPELA.md", "docs/constitution/supela-article-registry-1.json"],
            etat_4d="ACTIF",
            historique_statuts=[
                {"date": "2026-11-16", "statut": "PROUVÉ", "etat_4d": "ACTIF", "motif": "Vérifié analytiquement, numériquement et par Rego"}
            ],
            conditions_reouverture="Nouvelle fonction de perte ou échec de reproductibilité du gradient dans grpo_bridge.py.",
            sources=[f"Copilot M365: {m365_3}", "docs/constitution/SCHEMA_GRPO_SUPELA.md", "src/omega_zero/grpo_bridge.py"],
            notes="Réunit le formalisme Copilot M365 Reward→Candidate→Preuves→Status et le pont mathématique Ω-ZERO.",
        ),
        _make_fiche(
            fid="MAT-08-TESTS-PARITE",
            nom="Chaîne de Vérification, Règle A12, GDS/SCT & Parité HTML",
            ftype="Test",
            discipline="Vérification intégrée, GDS/SCT & Traçabilité artefacts",
            famille_math="MATH/08_TESTS/",
            section_xiii="XIII",
            source_type="Test",
            url_source="scripts/verify_a12.py",
            formulation_brute="JSON canonique → HTML dérivé → contrôle de parité → validation syntaxique ; GDS = ⟨D, O, A, γ⟩ ; F_sign ≠ F_certif",
            formulation_normalisee="Toute vue statique ou publication doit être dérivée de manière reproductible du JSON canonique, vérifiée par hachage/syntaxe et couverte par A12 (0 orphelin, 0 lien cassé).",
            notation="\\operatorname{SHA256}(\\text{HTML}_{\\text{json}}) = \\operatorname{SHA256}(\\text{Canon}) \\;\\land\\; \\text{A12}(\\text{repo}) = \\emptyset",
            auteur_source="Jean-François Gadbois (Supela Ω-ZERO & Supela-K3-Ω)",
            contribution_ia="Implémentation verify_a12.py, verify_html_parity, verify_html_js_syntax & pages-encyclopedie.yml",
            origine="Architecture Ω-ZERO + Supela-K3-Omega + directive HTML/PR #1/Pages",
            date_source="2026-11-16",
            statut="PROUVÉ",
            portee="Ensemble des artefacts versionnés, tests CI et déploiement Pages",
            conditions=[
                "Zéro script/style CDN externe dans ENCYCLOPEDIE_DICTIONNAIRE.html",
                "Règle A12 à zéro orphelin et zéro lien cassé",
            ],
            dependances=["MAT-01-AUTORITE-BORNEE", "MAT-06-AMELIORATION-AUTO"],
            implique="Distinction stricte entre donnée canonique (JSON), artefact (HTML), contrôle (parité/JS) et publication (Pages).",
            n_implique_pas="La consultation HTML n'altère jamais le JSON canonique ni la nécessité de revue humaine.",
            preuves=[
                "Contrôle SHA-256 + round-trip HTMLParser sans CDN",
                "Validation syntaxique ES via node --check",
                "Suite pytest complète + ruff + mypy + A12",
            ],
            tests=["tests/test_encyclopedie_dictionnaire.py", "tests/test_worm_and_crypto.py"],
            resultats=["Parité exacte et bijection A12 vérifiées avant chaque commit"],
            contre_exemples=["Toute divergence HTML vs JSON lève une erreur explicite dans verify_html_parity"],
            contradictions=["CONTR-PR1-PS1-AUDIT"],
            implementations=["scripts/build_encyclopedie.py", "scripts/verify_a12.py"],
            artefacts=[
                "docs/constitution/ENCYCLOPEDIE_DICTIONNAIRE.html",
                ".github/workflows/pages-encyclopedie.yml",
            ],
            etat_4d="ACTIF",
            historique_statuts=[
                {"date": "2026-11-16", "statut": "PROUVÉ", "etat_4d": "ACTIF", "motif": "Chaîne JSON→HTML→Parité→JS active"}
            ],
            conditions_reouverture="Modification du générateur HTML/JS ou ajout d'un nouveau fichier dans le dépôt.",
            sources=["scripts/verify_a12.py", "scripts/build_encyclopedie.py", ".github/workflows/pages-encyclopedie.yml"],
            notes="Matérialise la formule Supela : donnée canonique, artefact, contrôles et publication ont chacun leur rôle borné.",
        ),
    ]


def cards_to_registry_rows(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Projette les fiches complètes vers la table normalisée `registre_formules` du JSON."""
    rows: list[dict[str, Any]] = []
    for card in cards:
        row: dict[str, Any] = {
            "id": str(card["id"]),
            "nom": str(card["nom"]),
            "famille_math": str(card["_famille_math"]),
            "objet": str(card["type"]),
            "discipline": str(card["discipline"]),
            "formulation_brute": str(card["formulation_brute"]),
            "formulation_normalisee": str(card["formulation_normalisee"]),
            "notation_mathematique": str(card["notation_mathématique"]),
            "statut_probatoire": str(card["statut_epistemique"]),
            "etat_4d": str(card["etat_4d"]),
            "source_type": str(card["_source_type"]),
            "origine": str(card["origine"]),
            "implique": str(card["implique"]),
            "n_implique_pas": str(card["n_implique_pas"]),
            "tests": list(card["tests"]),
            "fiche_yaml": f"docs/constitution/fiches/{card['id']}.yaml",
        }
        if card.get("_url_source"):
            row["url_source"] = str(card["_url_source"])
        rows.append(row)
    return rows


def extract_yaml_payload(card: dict[str, Any]) -> dict[str, Any]:
    """Ne conserve strictement que les 29 clés universelles pour l'export YAML."""
    return {key: copy.deepcopy(card[key]) for key in UNIVERSAL_FICHE_KEYS}


def render_yaml_fiche(card: dict[str, Any]) -> str:
    """Sérialise une fiche au format YAML 1.2 déterministe (100% stdlib, sans PyYAML)."""
    payload = extract_yaml_payload(card)
    lines: list[str] = [
        f"# Fiche Encyclopédique Supela Ω-ZERO · {payload['id']}",
        "# Générée automatiquement par scripts/build_encyclopedie.py (squelette universel 29 clés)",
    ]
    for key in UNIVERSAL_FICHE_KEYS:
        val = payload[key]
        if isinstance(val, str):
            lines.append(f"{key}: {json.dumps(val, ensure_ascii=False)}")
        elif isinstance(val, list):
            if not val:
                lines.append(f"{key}: []")
            else:
                lines.append(f"{key}:")
                for item in val:
                    if isinstance(item, dict):
                        dict_items = list(item.items())
                        first_k, first_v = dict_items[0]
                        lines.append(f"  - {first_k}: {json.dumps(str(first_v), ensure_ascii=False)}")
                        for sub_k, sub_v in dict_items[1:]:
                            lines.append(f"    {sub_k}: {json.dumps(str(sub_v), ensure_ascii=False)}")
                    else:
                        lines.append(f"  - {json.dumps(str(item), ensure_ascii=False)}")
        else:
            lines.append(f"{key}: {json.dumps(val, ensure_ascii=False)}")
    return "\n".join(lines) + "\n"


def parse_simple_yaml_fiche(yaml_text: str) -> dict[str, Any]:
    """Parseur strict stdlib validant le format YAML généré par render_yaml_fiche."""
    result: dict[str, Any] = {}
    current_key: str | None = None
    current_list_item: dict[str, str] | None = None

    for raw_line in yaml_text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if not raw_line.startswith(" "):
            if ":" not in raw_line:
                raise ValueError(f"Ligne YAML invalide : {raw_line}")
            key, rest = raw_line.split(":", 1)
            key = key.strip()
            val_str = rest.strip()
            current_list_item = None
            if val_str == "":
                result[key] = []
                current_key = key
            elif val_str == "[]":
                result[key] = []
                current_key = None
            else:
                result[key] = json.loads(val_str)
                current_key = None
        elif raw_line.startswith("  - "):
            if current_key is None or not isinstance(result.get(current_key), list):
                raise ValueError(f"Élément de liste sans clé parente : {raw_line}")
            item_body = raw_line[4:].strip()
            if item_body.startswith('"'):
                result[current_key].append(json.loads(item_body))
                current_list_item = None
            elif ":" in item_body:
                sub_k, sub_v = item_body.split(":", 1)
                current_list_item = {sub_k.strip(): str(json.loads(sub_v.strip()))}
                result[current_key].append(current_list_item)
            else:
                raise ValueError(f"Élément YAML non reconnu : {raw_line}")
        elif raw_line.startswith("    "):
            if current_list_item is None or ":" not in raw_line:
                raise ValueError(f"Propriété imbriquée invalide : {raw_line}")
            sub_k, sub_v = raw_line.strip().split(":", 1)
            current_list_item[sub_k.strip()] = str(json.loads(sub_v.strip()))
        else:
            raise ValueError(f"Indentation YAML non supportée : {raw_line}")
    return result


def sync_yaml_fiches(fiches_dir: Path, cards: list[dict[str, Any]]) -> list[Path]:
    """Écrit atomiquement les fiches YAML et leur INDEX_FICHES.md (Règle A12)."""
    fiches_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    index_lines = [
        "# Index des Fiches Encyclopédiques YAML · Supela Ω-ZERO",
        "",
        "Ce répertoire regroupe les fiches initiales conformes au squelette universel (29 clés),",
        "en séparant explicitement `Source` (`origine` / `formulation_brute`), `Normalisation` et `Autorité` (`statut_epistemique`).",
        "",
        "| ID | Nom | Famille `MATH/` | Objet | Statut | État 4D | Fiche |",
        "|---|---|---|---|---|---|---|",
    ]
    for card in cards:
        target = fiches_dir / f"{card['id']}.yaml"
        _atomic_write_text(target, render_yaml_fiche(card))
        written.append(target)
        index_lines.append(
            f"| `{card['id']}` | **{card['nom']}** | `{card['_famille_math']}` | "
            f"`{card['type']}` | `{card['statut_epistemique']}` | `{card['etat_4d']}` | "
            f"[{card['id']}.yaml]({card['id']}.yaml) |"
        )
    index_lines.append("")
    index_path = fiches_dir / "INDEX_FICHES.md"
    _atomic_write_text(index_path, "\n".join(index_lines))
    written.append(index_path)
    return written


def load_contradictions_registry(path: Path = DEFAULT_CONTRADICTIONS_JSON) -> dict[str, Any]:
    """Charge le registre des contradictions sans effacement s'il existe."""
    if path.exists():
        data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        return data
    return {
        "schema": "supela-contradictions/1",
        "version": "1.0.0",
        "date": datetime.now(UTC).strftime("%Y-%m-%d"),
        "principe_non_effacement": (
            "Une contradiction ou un échec antérieur n'est jamais effacé même après PASS ultérieur."
        ),
        "effacement_interdit": True,
        "contradictions": [],
    }


def enrich_structural_knowledge(
    doc: dict[str, Any],
    cards: list[dict[str, Any]],
    contradictions_doc: dict[str, Any],
) -> dict[str, Any]:
    """Injecte taxonomie MATH/, architecture XIII, registre normalisé et lien contradictions."""
    rows = cards_to_registry_rows(cards)
    doc["taxonomie_math"] = build_math_taxonomy()
    doc["architecture_xiii_sections"] = build_architecture_xiii()
    doc["registre_formules"] = rows
    doc["registre_contradictions_ref"] = {
        "fichier_json": "docs/constitution/REGISTRE_CONTRADICTIONS.json",
        "fichier_md": "docs/constitution/REGISTRE_CONTRADICTIONS.md",
        "nombre_contradictions": len(contradictions_doc.get("contradictions", [])),
        "effacement_interdit": True,
    }
    doc["statistiques"]["formules_normalisees"] = len(rows)
    doc["statistiques"]["fiches_yaml_initiales"] = len(cards)
    doc["statistiques"]["contradictions_conservees"] = len(
        contradictions_doc.get("contradictions", [])
    )
    for plat in doc.get("encyclopedie", {}).get("plateformes_ia_et_navigateurs", []):
        if plat.get("id") == "copilot_edge":
            plat["trace_accessible_cloud"] = (
                "Extraits conversationnels M365 Copilot fournis par l'utilisateur (6 fils cités : "
                "19:itiW3fl..., 19:b__mSUKb..., 19:aaBvPORf..., 19:Fcb7Bbl..., 19:nWs3b4mo...) ; "
                "recherche fichiers M365 vide et profil local Edge/Bing sur C:\\ hors périmètre VM."
            )
    return doc


def scan_repo_tree(root: Path) -> list[dict[str, Any]]:
    """Liste tous les fichiers réels de omega-zero-4d soumis à A12 (robuste aux fichiers transitoires)."""
    items: list[dict[str, Any]] = []
    for p in sorted(root.rglob("*")):
        try:
            if not p.is_file():
                continue
            rel_parts = p.relative_to(root).parts
            if any(part in EXCLUDED_REPO_DIRS or part.endswith(".egg-info") for part in rel_parts):
                continue
            if p.suffix in {".bundle", ".pyc", ".pyo", ".tmp"} or p.name == ".DS_Store":
                continue
            size = int(p.stat().st_size)
        except OSError:
            continue
        rel_posix = p.relative_to(root).as_posix()
        category = rel_parts[0] if len(rel_parts) > 1 else "root"
        items.append(
            {
                "chemin": rel_posix,
                "categorie": category,
                "taille_octets": size,
            }
        )
    return items


def build_from_sources(
    sources_dir: Path,
    root: Path,
    contradictions_doc: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Construit l'encyclopédie complète à partir des exports JSON vérifiés."""
    gh_repos_raw: list[dict[str, Any]] = json.loads(
        (sources_dir / "github_repos.json").read_text(encoding="utf-8")
    )
    gdocs_raw: list[dict[str, Any]] = json.loads((sources_dir / "gdocs.json").read_text(encoding="utf-8"))
    gsheets_raw: list[dict[str, Any]] = json.loads(
        (sources_dir / "gsheets.json").read_text(encoding="utf-8")
    )
    gslides_raw: list[dict[str, Any]] = json.loads(
        (sources_dir / "gslides.json").read_text(encoding="utf-8")
    )
    gpdfs_raw: list[dict[str, Any]] = json.loads((sources_dir / "gpdfs.json").read_text(encoding="utf-8"))
    notebooks_raw: list[dict[str, Any]] = json.loads(
        (sources_dir / "notebooks.json").read_text(encoding="utf-8")
    )
    markdowns_raw: list[dict[str, Any]] = json.loads(
        (sources_dir / "markdowns.json").read_text(encoding="utf-8")
    )
    docxs_raw: list[dict[str, Any]] = json.loads((sources_dir / "docxs.json").read_text(encoding="utf-8"))
    desktop_raw: list[dict[str, Any]] = json.loads(
        (sources_dir / "laptop_desktop.json").read_text(encoding="utf-8")
    )
    documents_raw: list[dict[str, Any]] = json.loads(
        (sources_dir / "laptop_documents.json").read_text(encoding="utf-8")
    )
    downloads_raw: list[dict[str, Any]] = json.loads(
        (sources_dir / "laptop_downloads.json").read_text(encoding="utf-8")
    )

    sum1: dict[str, Any] = json.loads(
        (sources_dir / "gdoc_summaries.json").read_text(encoding="utf-8")
    )
    sum2: dict[str, Any] = json.loads((sources_dir / "gdoc_extra.json").read_text(encoding="utf-8"))
    rest_path = sources_dir / "gdoc_rest.json"
    sum3: dict[str, Any] = json.loads(rest_path.read_text(encoding="utf-8")) if rest_path.exists() else {}
    doc_previews = {**sum1, **sum2, **sum3}

    github_depots: list[dict[str, Any]] = []
    for r in gh_repos_raw:
        nwo = str(r["nameWithOwner"])
        is_fork = bool(r["isFork"])
        role, key_files = REPO_ROLES.get(
            nwo,
            (
                f"Fork miroir/référence de {r['name']} ({(r.get('primaryLanguage') or {}).get('name') or 'multi-langage'}) rattaché au compte gadboisjean1000-arch.",
                [],
            ),
        )
        github_depots.append(
            {
                "name_with_owner": nwo,
                "url": str(r["url"]),
                "type": "FORK" if is_fork else "ORIGINAL",
                "is_private": bool(r["isPrivate"]),
                "primary_language": str((r.get("primaryLanguage") or {}).get("name") or "Non spécifié"),
                "disk_usage_kb": int(r.get("diskUsage") or 0),
                "default_branch": str((r.get("defaultBranchRef") or {}).get("name") or "main"),
                "updated_at": str(r.get("updatedAt") or ""),
                "description": str(r.get("description") or ""),
                "role_ecosysteme": role,
                "fichiers_cles": key_files,
            }
        )

    discussions_ia: list[dict[str, Any]] = []
    canonical_corpus_id = "1gBbj-OyJe0zp2sbB64XeqUFAvGiG129W_5hfT8G36oE"
    native_docs = sorted(
        (d for d in gdocs_raw if d.get("mimeType") == "application/vnd.google-apps.document"),
        key=lambda d: (str(d.get("modifiedTime") or ""), str(d.get("id") or "")),
        reverse=True,
    )
    copy_candidates = [
        str(d["id"])
        for d in native_docs
        if str(d.get("name") or "").replace("\n", " ").strip() == "toutes les chapitre un coups"
    ]
    primary_corpus_id = (
        canonical_corpus_id if canonical_corpus_id in copy_candidates else (copy_candidates[0] if copy_candidates else "")
    )
    for d in native_docs:
        did = str(d["id"])
        title = str(d.get("name") or "Sans titre").replace("\n", " ").strip()
        mod_time = str(d.get("modifiedTime") or "")
        preview_info = doc_previews.get(did, {})
        lines = int(preview_info.get("line_count", 0))
        chars = int(preview_info.get("char_count", 0))

        is_copy = bool(
            title == "toutes les chapitre un coups" and primary_corpus_id and did != primary_corpus_id
        )

        if did in DOC_CLASSIFICATIONS:
            domaine, outils, resume = DOC_CLASSIFICATIONS[did]
        else:
            domaine = "Document / Note Drive"
            outils = ["Google Docs / Archive"]
            resume = f"Google Doc intitulé « {title} » (modifié le {mod_time[:10]})."

        entry: dict[str, Any] = {
            "id": did,
            "titre": title,
            "url": f"https://docs.google.com/document/d/{did}/edit",
            "type_artefact": "GOOGLE_DOC_COPIE" if is_copy else "GOOGLE_DOC",
            "date_modif": mod_time,
            "domaine": domaine,
            "outils_ia_associes": outils,
            "resume_verifie": resume,
            "perimetre_statut": "ACCESSIBLE_VERIFIE",
        }
        if did in doc_previews:
            entry["lignes"] = lines
            entry["caracteres"] = chars
        discussions_ia.append(entry)

    # Ajouter le fichier Markdown Supela dérivé sur Drive et les 2 notebooks Colab Supela
    for md in markdowns_raw:
        if md.get("id") == "1nAtBQlAkVXyB_R5T4CjZlfSWSCLTUEY6":
            discussions_ia.append(
                {
                    "id": str(md["id"]),
                    "titre": str(md["name"]),
                    "url": f"https://drive.google.com/file/d/{md['id']}/view",
                    "type_artefact": "MARKDOWN_DRIVE",
                    "date_modif": str(md.get("modifiedTime") or ""),
                    "domaine": "Modules Dérivés Supela-K3-Ω (Article, HDR, ISO-GDS-2026)",
                    "outils_ia_associes": ["Assistant IA", "Markdown"],
                    "resume_verifie": "Déclinaisons post-Chapitre 3 : Article scientifique EN, HDR et norme ISO-GDS-2026 pour GDS = ⟨D, O, A, G⟩.",
                    "perimetre_statut": "ACCESSIBLE_VERIFIE",
                }
            )
    for nb in notebooks_raw:
        nb_id = str(nb["id"])
        if nb.get("mimeType") == "application/json":
            discussions_ia.append(
                {
                    "id": nb_id,
                    "titre": str(nb["name"]),
                    "url": f"https://drive.google.com/file/d/{nb_id}/view",
                    "type_artefact": "COLAB_NOTEBOOK",
                    "date_modif": str(nb.get("modifiedTime") or ""),
                    "domaine": "Simulation & Ratification Cryptographique Supela-K3-Ω",
                    "outils_ia_associes": ["Google Colab / Jupyter", "Python / Ed25519"],
                    "resume_verifie": "Notebook déterministe exécutant invariants INV-SUP/K3/OMG, scénarios A1→F6, WORM, scellement Ed25519 et ancrage G7→Y2.",
                    "perimetre_statut": "ACCESSIBLE_VERIFIE",
                }
            )

    plateformes_ia = [
        {
            "id": "copilot_edge",
            "nom": "Microsoft Copilot & Edge",
            "categorie": "ASSISTANT_IA",
            "trace_accessible_cloud": "Extraits conversationnels M365 Copilot fournis par l'utilisateur (6 fils cités : 19:itiW3fl..., 19:b__mSUKb..., 19:aaBvPORf..., 19:Fcb7Bbl..., 19:nWs3b4mo...) ; recherche fichiers M365 vide et profil local Edge/Bing sur C:\\ hors périmètre VM.",
            "emplacement_local_windows": "%LOCALAPPDATA%\\Microsoft\\Edge\\User Data\\",
            "perimetre_statut": "INACCESSIBLE_DANS_LE_PÉRIMÈTRE",
            "methode_collecte_locale": "scripts/collect_local_encyclopedie.ps1 (Bookmarks + URLs History SQLite Copilot/Bing)",
            "notes": "Extraits historiques cités intégrés au registre des formules avec séparation Source ≠ Autorité ; le scan local Edge sur Windows reste requis.",
        },
        {
            "id": "gemini_google",
            "nom": "Google Gemini & AI Studio",
            "categorie": "ASSISTANT_IA",
            "trace_accessible_cloud": "51 Google Docs + 2 notebooks Colab Supela exportés dans Google Drive ; aucun accès direct à l'historique web gemini.google.com.",
            "emplacement_local_windows": "%LOCALAPPDATA%\\Google\\Chrome\\User Data\\",
            "perimetre_statut": "PARTIELLEMENT_SYNCHRONISE",
            "methode_collecte_locale": "scripts/collect_local_encyclopedie.ps1 (URLs gemini.google.com / aistudio.google.com dans Chrome/Edge/Arc/Brave)",
            "notes": "Les exports Gemini sauvegardés en Google Docs sont indexés ; le fil web direct reste hors API.",
        },
        {
            "id": "arc_browser",
            "nom": "Arc Browser",
            "categorie": "NAVIGATEUR_IA",
            "trace_accessible_cloud": "Aucune donnée Arc synchronisée dans Drive ou GitHub.",
            "emplacement_local_windows": "%LOCALAPPDATA%\\Packages\\TheBrowserCompany.Arc*\\LocalCache\\Local\\Arc\\User Data\\",
            "perimetre_statut": "INACCESSIBLE_DANS_LE_PÉRIMÈTRE",
            "methode_collecte_locale": "scripts/collect_local_encyclopedie.ps1 (StorableSidebar.json + History SQLite + Bookmarks)",
            "notes": "Profil local Arc uniquement sur le poste Windows.",
        },
        {
            "id": "brave_leo",
            "nom": "Brave Browser & Brave Leo",
            "categorie": "NAVIGATEUR_IA",
            "trace_accessible_cloud": "Installeur BraveBrowserSetup-BRV040.exe présent dans Drive/Downloads ; profils et historique Leo non synchronisés.",
            "emplacement_local_windows": "%LOCALAPPDATA%\\BraveSoftware\\Brave-Browser\\User Data\\",
            "perimetre_statut": "INACCESSIBLE_DANS_LE_PÉRIMÈTRE",
            "methode_collecte_locale": "scripts/collect_local_encyclopedie.ps1 (Bookmarks + History SQLite)",
            "notes": "Requiert scan local Windows pour relever les onglets, favoris et URLs IA de Brave.",
        },
        {
            "id": "opera_aria",
            "nom": "Opera & Aria",
            "categorie": "NAVIGATEUR_IA",
            "trace_accessible_cloud": "Raccourci « Navigateur Opera.lnk » dans Drive/Desktop et dossier .opera vide (0 item) dans Drive/Downloads.",
            "emplacement_local_windows": "%APPDATA%\\Opera Software\\Opera Stable\\",
            "perimetre_statut": "PARTIELLEMENT_SYNCHRONISE",
            "methode_collecte_locale": "scripts/collect_local_encyclopedie.ps1 (Bookmarks + History SQLite)",
            "notes": "Le profil actif Windows contient l'historique réel hors synchronisation Drive.",
        },
        {
            "id": "antigravity_agent",
            "nom": "Antigravity (Google DeepMind)",
            "categorie": "IDE_AGENT_IA",
            "trace_accessible_cloud": "Dépôt omega-zero-4d + artefacts persistés dans ~/.gemini/jetski/brain (tableau de bord HTML + session active).",
            "emplacement_local_windows": "%USERPROFILE%\\.gemini\\jetski\\brain\\",
            "perimetre_statut": "ACCESSIBLE_VERIFIE",
            "methode_collecte_locale": "scripts/collect_local_encyclopedie.ps1 (indexation des identifiants de sessions .gemini)",
            "notes": "Connecté avec GitHub, Google Drive, Docs, Sheets, Slides et Calendar.",
        },
        {
            "id": "cursor_ide",
            "nom": "Cursor CLI & IDE",
            "categorie": "IDE_AGENT_IA",
            "trace_accessible_cloud": "Documentation complète « Guide d'intégration Cursor CLI - Pipeline Supela-K3-Ω » dans Google Docs.",
            "emplacement_local_windows": "%APPDATA%\\Cursor\\User\\globalStorage\\",
            "perimetre_statut": "PARTIELLEMENT_SYNCHRONISE",
            "methode_collecte_locale": "scripts/collect_local_encyclopedie.ps1 (répertoire globalStorage Cursor)",
            "notes": "Spécification cloud indexée ; conversations locales dans AppData\\Cursor sur Windows.",
        },
        {
            "id": "kilocode_cline_vscode",
            "nom": "KiloCode / Cline / VS Code",
            "categorie": "IDE_AGENT_IA",
            "trace_accessible_cloud": "Dépôts forkés kilocode, cline, sourcery et vscode-github-actions présents sur GitHub gadboisjean1000-arch.",
            "emplacement_local_windows": "%APPDATA%\\Code\\User\\globalStorage\\",
            "perimetre_statut": "PARTIELLEMENT_SYNCHRONISE",
            "methode_collecte_locale": "scripts/collect_local_encyclopedie.ps1 (extensions et tâches locales VS Code)",
            "notes": "Code source des agents forkés indexé sur GitHub ; historiques locaux de tâches sur disque C:.",
        },
        {
            "id": "chatgpt_claude",
            "nom": "ChatGPT (OpenAI) & Claude (Anthropic)",
            "categorie": "ASSISTANT_IA",
            "trace_accessible_cloud": "Aucune API ChatGPT/Claude connectée ; traces potentielles dans Google Docs exportés ou exports locaux conversations.json.",
            "emplacement_local_windows": "Navigateurs locaux + fichiers conversations.json sur C:\\ ou D:\\",
            "perimetre_statut": "INACCESSIBLE_DANS_LE_PÉRIMÈTRE",
            "methode_collecte_locale": "scripts/collect_local_encyclopedie.ps1 (détection des fichiers conversations.json et URLs historiques)",
            "notes": "Pour inclure tout l'historique ChatGPT/Claude, exporter conversations.json sur C:/D: puis lancer le collecteur.",
        },
    ]

    pii_sample_markers = (
        "paye",
        "feuille de temps",
        "amrouche",
        "choquette",
        "provencal",
        "rares",
        "gadbois",
        "identification",
        "consentement",
        "référence",
        "reference",
        "facture",
        "contacts",
        "req.pdf",
        "recap_dso",
        "acfrog",
        "estimation",
        "sans nom",
        "houblon",
        "referral-engine",
    )

    def _safe_drive_samples(
        items: list[dict[str, Any]], categorie: str, limit: int
    ) -> list[dict[str, Any]]:
        selected: list[dict[str, Any]] = []
        seen_names: set[str] = set()
        for x in items:
            name = str(x.get("name") or "")
            lower_name = name.lower()
            if any(marker in lower_name for marker in pii_sample_markers):
                continue
            if name in seen_names:
                continue
            seen_names.add(name)
            selected.append(
                {
                    "id": str(x["id"]),
                    "nom": name,
                    "categorie": categorie,
                    "date_modif": str(x.get("modifiedTime") or ""),
                }
            )
            if len(selected) >= limit:
                break
        return selected

    sample_drive_docs = (
        [
            {
                "id": str(x["id"]),
                "nom": str(x["name"]),
                "categorie": "COLAB_NOTEBOOK",
                "date_modif": str(x.get("modifiedTime") or ""),
            }
            for x in notebooks_raw
        ]
        + [
            {
                "id": str(x["id"]),
                "nom": str(x["name"]),
                "categorie": "GOOGLE_SLIDES",
                "date_modif": str(x.get("modifiedTime") or ""),
            }
            for x in gslides_raw
        ]
        + _safe_drive_samples(gsheets_raw, "GOOGLE_SHEETS", 5)
        + _safe_drive_samples(gpdfs_raw, "PDF_DRIVE", 6)
        + _safe_drive_samples(docxs_raw, "DOCX_DOCUMENTS", 4)
    )

    repo_tree = scan_repo_tree(root)
    dictionnaire = build_dictionary_entries()

    n_orig = sum(1 for r in github_depots if r["type"] == "ORIGINAL")
    n_fork = sum(1 for r in github_depots if r["type"] == "FORK")

    docs_drive_count = (
        len(native_docs)
        + len(gsheets_raw)
        + len(gslides_raw)
        + len(notebooks_raw)
        + len(docxs_raw)
        + len(desktop_raw)
        + len(documents_raw)
        + len(downloads_raw)
    )

    doc: dict[str, Any] = {
        "schema": "supela-dictionnaire-encyclopedie/1",
        "version": "1.0.0",
        "date": datetime.now(UTC).strftime("%Y-%m-%d"),
        "generateur": "scripts/build_encyclopedie.py",
        "local_pc_scan": "NON_EXECUTEE",
        "verdict_couverture": "OUVERT_INCOMPLET_C_D_IA_LOCALES",
        "perimetre": {
            "plateforme_execution": "VM Cloud Linux distante (Debian 12) sans montage direct des lecteurs Windows C:\\ et D:\\",
            "statut_global": "PARTIEL_VERIFIE_DISTANT",
            "regles_epistemiques": [
                "M3 : Manque ≠ permission d'inventer (OPEN ∧ ¬FABRICATE)",
                "Autorité ≤ Preuve : aucun disque local non lu n'est déclaré indexé",
                "I_M : Conservation explicite des périmètres INACCESSIBLE_DANS_LE_PÉRIMÈTRE",
                "PDD-01 : Exclusion des états volatils RAM non consignés sur artefact persistant",
            ],
            "sources_statuts": [
                {
                    "source_id": "github",
                    "nom": "GitHub (gadboisjean1000-arch)",
                    "statut": "ACCESSIBLE_VERIFIE",
                    "raison_ou_preuve": "15 dépôts listés via gh CLI (4 originaux + 11 forks) et arborescence complète de omega-zero-4d.",
                },
                {
                    "source_id": "google_drive_docs",
                    "nom": "Google Drive, Docs, Sheets, Slides, Colab",
                    "statut": "ACCESSIBLE_VERIFIE",
                    "raison_ou_preuve": "51 Google Docs natifs, 43 tableurs, 5 présentations, 4 notebooks et méta-données Drive (33,6 Go / 5120 Go) lus via gdrive/gdocs.",
                },
                {
                    "source_id": "pc_synchronise_drive",
                    "nom": "Mon ordinateur portable (1) dans Drive",
                    "statut": "PARTIELLEMENT_SYNCHRONISE",
                    "raison_ou_preuve": "Sous-ensemble sauvegardé dans Drive : Desktop (9), Documents (86), Downloads (262).",
                },
                {
                    "source_id": "windows_drive_C",
                    "nom": "Disque local Windows C:\\",
                    "statut": "INACCESSIBLE_DANS_LE_PÉRIMÈTRE",
                    "raison_ou_preuve": "Lecteur local non accessible depuis la VM cloud ; inclut C:\\Users\\Group\\Documents\\antigravity\\excited-meitner et AppData.",
                },
                {
                    "source_id": "windows_drive_D",
                    "nom": "Disque local Windows D:\\",
                    "statut": "INACCESSIBLE_DANS_LE_PÉRIMÈTRE",
                    "raison_ou_preuve": "Lecteur local Windows D:\\ non monté dans l'environnement cloud ; requiert collect_local_encyclopedie.ps1.",
                },
                {
                    "source_id": "historiques_ia_locaux",
                    "nom": "Historiques directs Copilot / Gemini / Arc / Brave / Opera",
                    "statut": "INACCESSIBLE_DANS_LE_PÉRIMÈTRE",
                    "raison_ou_preuve": "Aucune API d'historique web Copilot/Gemini/ChatGPT/Claude connectée et profils navigateurs résidant sur C:\\.",
                },
            ],
        },
        "statistiques": {
            "termes_dictionnaire": len(dictionnaire),
            "depots_github_total": len(github_depots),
            "depots_github_originaux": n_orig,
            "depots_github_forks": n_fork,
            "discussions_ia_google_docs": len(discussions_ia),
            "plateformes_ia_navigateurs": len(plateformes_ia),
            "fichiers_omega_zero_4d": len(repo_tree),
            "notebooks_colab": len(notebooks_raw),
            "documents_drive_indexes": docs_drive_count,
            "disques_locaux_suivis": 2,
            "entrees_locales_c_d": 0,
        },
        "dictionnaire": dictionnaire,
        "encyclopedie": {
            "github_depots": github_depots,
            "omega_zero_4d_arborescence": repo_tree,
            "discussions_ia_google_docs": discussions_ia,
            "plateformes_ia_et_navigateurs": plateformes_ia,
            "google_drive_inventaire": {
                "quota_utilise_gb": 33.6,
                "quota_limite_gb": 5120.0,
                "note_pagination": "Les recherches gdrive readonly search sont bornées aux 100 premiers résultats par filtre de type ; les dossiers Desktop/Documents/Downloads sont listés complètement.",
                "pc_synchronise_dossier": {
                    "nom": "Mon ordinateur portable (1)",
                    "id": "1PJ3p5Dhs6AS7MweywrmUEqMJKPB8D0ml",
                    "desktop_items": len(desktop_raw),
                    "documents_items": len(documents_raw),
                    "downloads_items": len(downloads_raw),
                    "statut": "PARTIELLEMENT_SYNCHRONISE",
                },
                "comptes_par_categorie": {
                    "google_docs_natifs": len(native_docs),
                    "google_sheets_et_xlsx": len(gsheets_raw),
                    "google_slides_et_pptx": len(gslides_raw),
                    "pdfs_echantillon_borne": len(gpdfs_raw),
                    "dossiers_echantillon_borne": 100,
                    "notebooks_et_raccourcis": len(notebooks_raw),
                    "fichiers_docx": len(docxs_raw),
                    "desktop_synchronise": len(desktop_raw),
                    "documents_synchronise": len(documents_raw),
                    "downloads_synchronise": len(downloads_raw),
                },
                "echantillons_documents_cles": sample_drive_docs,
            },
            "disques_locaux_windows": [
                {
                    "lecteur": "C:\\",
                    "perimetre_statut": "INACCESSIBLE_DANS_LE_PÉRIMÈTRE",
                    "raison": "Disque système local Windows inaccessible depuis la VM cloud Linux. Contient notamment les dépôts locaux (excited-meitner) et les profils Edge/Chrome/Arc/Brave/Cursor/Antigravity.",
                    "cibles_connues": [
                        "C:\\Users\\Group\\Documents\\antigravity\\excited-meitner",
                        "%LOCALAPPDATA%\\Microsoft\\Edge\\User Data\\",
                        "%LOCALAPPDATA%\\Google\\Chrome\\User Data\\",
                        "%LOCALAPPDATA%\\Packages\\TheBrowserCompany.Arc*\\",
                        "%LOCALAPPDATA%\\BraveSoftware\\Brave-Browser\\User Data\\",
                        "%APPDATA%\\Opera Software\\Opera Stable\\",
                        "%APPDATA%\\Cursor\\User\\globalStorage\\",
                        "%USERPROFILE%\\.gemini\\jetski\\brain\\",
                    ],
                    "collecteur_script": "scripts/collect_local_encyclopedie.ps1",
                    "elements_indexes": [],
                },
                {
                    "lecteur": "D:\\",
                    "perimetre_statut": "INACCESSIBLE_DANS_LE_PÉRIMÈTRE",
                    "raison": "Disque secondaire local Windows D:\\ inaccessible depuis la VM cloud Linux. À scanner sur le poste hôte via PowerShell.",
                    "cibles_connues": [
                        "D:\\ (projets, archives, exports conversations.json, dépôts Git locaux)"
                    ],
                    "collecteur_script": "scripts/collect_local_encyclopedie.ps1",
                    "elements_indexes": [],
                },
            ],
        },
        "collecteur_local": {
            "script_powershell": "scripts/collect_local_encyclopedie.ps1",
            "script_fusion_python": "scripts/build_encyclopedie.py",
            "commande_windows": ".\\scripts\\collect_local_encyclopedie.ps1 -Drives C,D -OutJson .\\docs\\constitution\\local_pc_inventory.json",
            "commande_fusion": "python scripts/build_encyclopedie.py --local-inventory docs/constitution/local_pc_inventory.json",
            "garanties_securite": [
                "Exécution strictement lecture-seule sur C:\\ et D:\\.",
                "Exclusion explicite de Cookies, Login Data, Local State, .env, .ssh, .kdbx, .pfx, .key et jetons.",
                "Validation Draft 2020-12 obligatoire avant écriture du registre fusionné.",
            ],
            "dernier_import_local": None,
        },
        "conclusion": "Le Dictionnaire et l'Encyclopédie répertorient de façon vérifiée les 15 dépôts GitHub, les discussions IA et artefacts Google Drive/Docs/Colab ainsi que la nomenclature complète Supela Ω-ZERO ; les disques locaux C:/D: et historiques directs Copilot/Gemini/Arc/Brave restent honnêtement marqués INACCESSIBLE_DANS_LE_PÉRIMÈTRE jusqu'à exécution du collecteur PowerShell local.",
    }
    contr = contradictions_doc if contradictions_doc is not None else load_contradictions_registry()
    return enrich_structural_knowledge(doc, build_formula_cards(), contr)


def _parse_iso_utc(raw_ts: str) -> datetime | None:
    text = raw_ts.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def merge_local_inventory(base_doc: dict[str, Any], local_inv: dict[str, Any], root: Path) -> dict[str, Any]:
    """Fusionne un export local_pc_inventory.json dans le registre canonique avec barrières M3 strictes."""
    merged = copy.deepcopy(base_doc)
    merged["encyclopedie"]["omega_zero_4d_arborescence"] = scan_repo_tree(root)

    prev_import = (merged.get("collecteur_local") or {}).get("dernier_import_local")
    new_ts_raw = str(local_inv.get("generated_utc") or "")
    if isinstance(prev_import, dict):
        prev_ts_raw = str(prev_import.get("generated_utc") or "")
        prev_dt = _parse_iso_utc(prev_ts_raw)
        new_dt = _parse_iso_utc(new_ts_raw)
        if prev_dt is not None and new_dt is not None and new_dt < prev_dt:
            raise ValueError(
                f"Inventaire local rejeté : generated_utc ({new_ts_raw}) antérieur au dernier import ({prev_ts_raw})."
            )

    drives_by_letter = {
        str(d.get("lecteur", "")).upper(): d for d in local_inv.get("drives", [])
    }
    git_repos = list(local_inv.get("git_repos", []))
    notable_files = list(local_inv.get("notable_files", []))
    machine_name = str(local_inv.get("machine_name") or "poste Windows")

    new_disk_entries: list[dict[str, Any]] = []
    for disk in merged["encyclopedie"]["disques_locaux_windows"]:
        letter = str(disk["lecteur"]).upper()
        found = drives_by_letter.get(letter)
        if found:
            st = str(found.get("statut") or "")
            is_truncated = bool(found.get("scan_tronque", False)) or int(
                found.get("dossiers_inaccessibles", 0) or 0
            ) > 0
            if st == "INDEXE_LOCAL" or st == "PARTIELLEMENT_INDEXE":
                disk_git = [g for g in git_repos if str(g.get("lecteur", "")).upper() == letter]
                disk_files = [f for f in notable_files if str(f.get("lecteur", "")).upper() == letter]
                elements: list[dict[str, Any]] = []
                for ddir in found.get("dossiers_racine", [])[:100]:
                    elements.append({"type": "DOSSIER_RACINE", **ddir})
                for grepo in disk_git[:100]:
                    elements.append({"type": "DEPOT_GIT_LOCAL", **grepo})
                for nf in disk_files[:200]:
                    elements.append({"type": "FICHIER_NOTABLE", **nf})
                effective_status = (
                    "PARTIELLEMENT_INDEXE"
                    if (st == "PARTIELLEMENT_INDEXE" or is_truncated)
                    else "INDEXE_LOCAL"
                )
                disk["perimetre_statut"] = effective_status
                disk["raison"] = (
                    f"{'Indexé partiellement (tronqué/accès restreint)' if effective_status == 'PARTIELLEMENT_INDEXE' else 'Indexé localement'} "
                    f"sur {machine_name} ({len(disk_git)} dépôts Git, {len(disk_files)} fichiers notables)."
                )
                disk["elements_indexes"] = elements
            else:
                disk["perimetre_statut"] = "INACCESSIBLE_DANS_LE_PÉRIMÈTRE"
                disk["raison"] = (
                    f"Lecteur {letter} signalé '{st or 'INACCESSIBLE'}' sur {machine_name} ; couverture locale absente."
                )
                disk["elements_indexes"] = []
        new_disk_entries.append(disk)
    merged["encyclopedie"]["disques_locaux_windows"] = new_disk_entries

    # Fusion plateformes IA & navigateurs détectés localement
    local_ai_by_id = {str(p.get("id")): p for p in local_inv.get("ai_platforms", [])}
    alias_map = {
        "copilot_edge": "copilot_edge",
        "gemini_google": "gemini_chrome",
        "arc_browser": "arc_browser",
        "brave_leo": "brave_leo",
        "opera_aria": "opera_aria",
        "antigravity_agent": "antigravity",
        "cursor_ide": "cursor",
        "kilocode_cline_vscode": "vscode_agents",
    }
    for plat in merged["encyclopedie"]["plateformes_ia_et_navigateurs"]:
        pid = str(plat["id"])
        mapped = alias_map.get(pid, pid)
        loc = local_ai_by_id.get(mapped)
        if loc is not None:
            if loc.get("present"):
                traces: list[str] = []
                for t in loc.get("traces_echantillon", [])[:50]:
                    ttype = str(t.get("type") or "TRACE")
                    titre = str(t.get("titre") or "").strip()
                    url = str(t.get("url") or "").strip()
                    if titre and url and titre != url:
                        traces.append(f"{ttype}: {titre} — {url}")
                    else:
                        traces.append(f"{ttype}: {titre or url}")
                trace_count = int(loc.get("total_traces_ia", 0) or 0)
                plat["perimetre_statut"] = "INDEXE_LOCAL"
                plat["elements_locaux_detectes"] = traces
                plat["total_traces_locaux"] = trace_count
                plat["notes"] = (
                    f"Détecté localement ({trace_count} traces IA/favoris) dans {loc.get('chemin_detecte', '')}."
                )
            elif plat.get("perimetre_statut") == "INDEXE_LOCAL":
                plat["perimetre_statut"] = "INACCESSIBLE_DANS_LE_PÉRIMÈTRE"
                plat.pop("elements_locaux_detectes", None)
                plat.pop("total_traces_locaux", None)
                plat["notes"] = f"Absent sur {machine_name} lors du scan ({new_ts_raw})."

    # Compter les entrées locales conservées sur l'état final (disques + plateformes IA)
    retained_disk_entries = sum(
        1
        for d in merged["encyclopedie"]["disques_locaux_windows"]
        for el in d.get("elements_indexes", [])
        if el.get("type") in {"DEPOT_GIT_LOCAL", "FICHIER_NOTABLE"}
    )
    retained_ai_traces = sum(
        int(p.get("total_traces_locaux", len(p.get("elements_locaux_detectes", []))))
        for p in merged["encyclopedie"]["plateformes_ia_et_navigateurs"]
        if p.get("perimetre_statut") == "INDEXE_LOCAL"
    )
    total_local_entries = retained_disk_entries + retained_ai_traces

    skip_hist = bool(local_inv.get("skip_browser_history", False))
    verified_ai_platforms = [
        p
        for p in merged["encyclopedie"]["plateformes_ia_et_navigateurs"]
        if p.get("perimetre_statut") == "INDEXE_LOCAL"
    ]
    has_verified_ai = (not skip_hist) and bool(verified_ai_platforms)

    # Synchroniser les statuts de périmètre avec l'état réel final
    disks_by_letter_final = {
        str(d["lecteur"]).upper(): d for d in merged["encyclopedie"]["disques_locaux_windows"]
    }
    drive_source_map = {"windows_drive_C": "C:\\", "windows_drive_D": "D:\\"}
    for src in merged["perimetre"]["sources_statuts"]:
        sid = src["source_id"]
        target_letter = drive_source_map.get(sid)
        if target_letter:
            dstate = disks_by_letter_final.get(target_letter, {}).get("perimetre_statut")
            if dstate == "INDEXE_LOCAL":
                src["statut"] = "INDEXE_LOCAL"
                src["raison_ou_preuve"] = (
                    f"Importé depuis local_pc_inventory.json ({new_ts_raw or 'sans date'})."
                )
            elif dstate == "PARTIELLEMENT_INDEXE":
                src["statut"] = "PARTIELLEMENT_SYNCHRONISE"
                src["raison_ou_preuve"] = (
                    f"Scan partiel ou tronqué importé depuis local_pc_inventory.json ({new_ts_raw or 'sans date'})."
                )
            else:
                src["statut"] = "INACCESSIBLE_DANS_LE_PÉRIMÈTRE"
                src["raison_ou_preuve"] = (
                    f"Lecteur {target_letter} non indexé dans l'inventaire courant."
                )
        elif sid == "historiques_ia_locaux":
            if has_verified_ai:
                src["statut"] = "INDEXE_LOCAL"
                src["raison_ou_preuve"] = (
                    f"Traces locales importées pour {len(verified_ai_platforms)} plateforme(s) IA/navigateur(s)."
                )
            else:
                src["statut"] = "INACCESSIBLE_DANS_LE_PÉRIMÈTRE"
                src["raison_ou_preuve"] = (
                    "Historique navigateurs exclu (-SkipBrowserHistory) ou aucune plateforme IA détectée."
                    if skip_hist
                    else "Aucune trace locale de navigateur/agent IA vérifiée lors du scan."
                )

    all_disks_indexed = all(
        d.get("perimetre_statut") == "INDEXE_LOCAL"
        for d in merged["encyclopedie"]["disques_locaux_windows"]
    )
    has_any_local_data = (
        any(
            d.get("perimetre_statut") in {"INDEXE_LOCAL", "PARTIELLEMENT_INDEXE"}
            for d in merged["encyclopedie"]["disques_locaux_windows"]
        )
        or has_verified_ai
    )
    if all_disks_indexed and has_verified_ai:
        merged["local_pc_scan"] = "EXECUTEE"
        merged["verdict_couverture"] = "COMPLETE_SOUS_PREUVE"
        merged["perimetre"]["statut_global"] = "COMPLET_SOUS_PREUVE"
    elif has_any_local_data:
        merged["local_pc_scan"] = "PARTIELLE"
        merged["verdict_couverture"] = "PARTIELLE_AVEC_EXPORT_LOCAL"
        merged["perimetre"]["statut_global"] = "HYBRIDE_LOCAL_DISTANT"
    else:
        merged["local_pc_scan"] = "NON_EXECUTEE"
        merged["verdict_couverture"] = "OUVERT_INCOMPLET_C_D_IA_LOCALES"
        merged["perimetre"]["statut_global"] = "PARTIEL_VERIFIE_DISTANT"

    merged["statistiques"]["fichiers_omega_zero_4d"] = len(
        merged["encyclopedie"]["omega_zero_4d_arborescence"]
    )
    merged["statistiques"]["entrees_locales_c_d"] = total_local_entries
    merged["collecteur_local"]["dernier_import_local"] = {
        "machine_name": machine_name,
        "generated_utc": new_ts_raw,
        "drives_count": len(local_inv.get("drives", [])),
        "git_repos_count": len(git_repos),
        "notable_files_count": len(notable_files),
        "skip_browser_history": skip_hist,
    }
    merged["conclusion"] = (
        f"Encyclopédie fusionnée avec l'inventaire local ({machine_name}) : "
        f"{total_local_entries} entrées locales conservées ({merged['verdict_couverture']})."
    )
    return merged



def render_formulas_markdown(
    doc: dict[str, Any],
    contradictions_doc: dict[str, Any] | None = None,
) -> str:
    """Génère REGISTRE_FORMULES_SUPELA.md (taxonomie MATH/00..08, XIII domaines et tableau normalisé)."""
    contr = contradictions_doc if contradictions_doc is not None else load_contradictions_registry()
    lines: list[str] = [
        "# Registre Normalisé des Formules & Taxonomie MATH/ · Supela Ω-ZERO",
        "",
        "> **Principe fondamental (`Source ≠ Autorité`) :** Une apparition dans une conversation M365, Google Doc ou carnet d'idées atteste la *provenance*, jamais une démonstration mathématique. Toute formule conserve séparément sa **formulation brute**, sa **normalisation**, son **statut épistémique** (`PROUVÉ`..`RÉFUTÉ`) et son **état 4D** (`ACTIF`/`LATENT`/`RÉOUVERT`).",
        "",
        "## 1. Classification 3 Axes & Architecture `MATH/00_FONDEMENTS/` .. `MATH/08_TESTS/`",
        "",
        "| Famille `MATH/` | Intitulé | Sous-modules structurés |",
        "|---|---|---|",
    ]
    for fam in doc.get("taxonomie_math", []):
        mods = "<br>".join(f"`{m}`" for m in fam["sous_modules"])
        lines.append(f"| `{fam['famille']}` | **{fam['titre']}** | {mods} |")

    lines.extend(
        [
            "",
            "## 2. Architecture Encyclopédique en XIII Domaines",
            "",
            "| Domaine | Titre | Couverture actuelle | Périmètre & Contenu |",
            "|---|---|---|---|",
        ]
    )
    for sec in doc.get("architecture_xiii_sections", []):
        desc = sec["description"].replace("|", "\\|")
        lines.append(
            f"| **{sec['roman']}** | {sec['titre']} | `{sec['statut_couverture']}` | {desc} |"
        )

    lines.extend(
        [
            "",
            "## 3. Tableau Normalisé des Formules Retrouvées & Opérateurs Canoniques",
            "",
            "| ID | Nom | Famille `MATH/` | Objet | Formulation brute | Normalisation & Statut | État 4D | Implique | N'implique pas | Fiche YAML |",
            "|---|---|---|---|---|---|---|---|---|---|",
        ]
    )
    for row in doc.get("registre_formules", []):
        brute = row["formulation_brute"].replace("|", "\\|")
        norm = row["formulation_normalisee"].replace("|", "\\|")
        imp = row["implique"].replace("|", "\\|")
        nimp = row["n_implique_pas"].replace("|", "\\|")
        yaml_rel = row["fiche_yaml"].removeprefix("docs/constitution/")
        lines.append(
            f"| `{row['id']}` | **{row['nom']}** | `{row['famille_math']}` | `{row['objet']}` | "
            f"`{brute}` | {norm} (`{row['statut_probatoire']}`) | `{row['etat_4d']}` | "
            f"{imp} | {nimp} | [{Path(yaml_rel).name}]({yaml_rel}) |"
        )

    lines.extend(
        [
            "",
            "## 4. Manques Ouverts & Mises en Garde Vérifiées (`M3`)",
            "",
            "- **Recherche fichiers M365 vide :** Aucune prétention d'exhaustivité sur les fichiers locaux ou M365 non extraits.",
            "- **`MAT-00-ZERO-INT` (`Théorème du Zéro-Intégration`) et `MAT-03-RESET-STAR` (`RESET*`, `R*`, `VR-22`) :** Maintenus au statut `INCONNU` / état `LATENT` sans reconstruction spéculative.",
            "- **`MAT-06-CHAINE-TRANSFO` (Section H) :** La chaîne brute est retournée littéralement `undefined` ; la suite `Demande → Interprétation → Transformation → Résultat` est explicitement qualifiée de *proposition dérivée non sourcée*.",
            "- **`MAT-01-REFLPROB` (Réflexivité probatoire) :** Maintenue au statut `HYPOTHÉTIQUE` (présence historique dans Supela ≠ théorème démontré).",
            f"- **Contradictions & Échecs conservés (`{len(contr.get('contradictions', []))}` entrées) :** Voir [REGISTRE_CONTRADICTIONS.md](REGISTRE_CONTRADICTIONS.md) et [INDEX_FICHES.md](fiches/INDEX_FICHES.md).",
            "",
        ]
    )
    return "\n".join(lines)


def render_contradictions_markdown(contradictions_doc: dict[str, Any]) -> str:
    """Génère REGISTRE_CONTRADICTIONS.md depuis REGISTRE_CONTRADICTIONS.json."""
    lines: list[str] = [
        "# Registre des Contradictions & Échecs Conservés · Supela Ω-ZERO",
        "",
        (
            f"> **Schéma :** `{contradictions_doc.get('schema', 'supela-contradictions/1')}` · "
            f"**Version :** `{contradictions_doc.get('version', '1.0.0')}` · "
            f"**Effacement interdit :** `{contradictions_doc.get('effacement_interdit', True)}`"
        ),
        "",
        f"> {contradictions_doc.get('principe_non_effacement', '')}",
        "",
        "| ID | Titre | Objet | Statut Contradiction | État 4D | Invariants impactés | Conditions de réouverture |",
        "|---|---|---|---|---|---|---|",
    ]
    for item in contradictions_doc.get("contradictions", []):
        titre = str(item["titre"]).replace("|", "\\|")
        obj = str(item["objet_concerne"]).replace("|", "\\|")
        invs = ", ".join(f"`{i}`" for i in item.get("invariants_impactes", []))
        reouv = str(item["conditions_reouverture"]).replace("|", "\\|")
        lines.append(
            f"| `{item['id']}` | **{titre}** | `{obj}` | `{item['statut_contradiction']}` | "
            f"`{item['etat_4d']}` | {invs} | {reouv} |"
        )
    lines.append("")
    for item in contradictions_doc.get("contradictions", []):
        lines.extend(
            [
                f"## {item['id']} — {item['titre']}",
                "",
                f"- **Objet concerné :** `{item['objet_concerne']}`",
                f"- **Statut contradiction :** `{item['statut_contradiction']}` · **État 4D :** `{item['etat_4d']}`",
                f"- **Constat / FAIL historique :** {item['constat_fail_historique']}",
                f"- **État ultérieur :** {item['etat_ulterieur']}",
                f"- **Justification du non-effacement :** {item['justification_conservation']}",
                f"- **Conditions de réouverture :** {item['conditions_reouverture']}",
                f"- **Source / Provenance :** {item['source_provenance']}",
                "",
            ]
        )
    return "\n".join(lines)


def render_markdown(doc: dict[str, Any]) -> str:
    """Génère la vue Markdown lisible et vérifiable de l'Encyclopédie & du Dictionnaire."""
    stats = doc["statistiques"]
    perim = doc["perimetre"]
    lines: list[str] = [
        "# Dictionnaire & Encyclopédie Universelle · Supela Ω-ZERO",
        "",
        f"> **Schéma :** `{doc['schema']}` · **Version :** `{doc['version']}` · **Date :** `{doc['date']}`  ",
        f"> **Statut global :** `{perim['statut_global']}` · **Scan local C:/D: :** `{doc['local_pc_scan']}` · **Verdict :** `{doc['verdict_couverture']}`",
        "",
        "Ce document répertorie de manière strictement vérifiable (règles `M3` : *Manque ≠ permission d'inventer* et `Autorité ≤ Preuve`) :",
        "1. Le **Dictionnaire canonique** des concepts, symboles, invariants, statuts et outils IA ;",
        "2. L'**Encyclopédie GitHub** (les 15 dépôts de `gadboisjean1000-arch` et l'arborescence complète de `omega-zero-4d`) ;",
        "3. Les **Discussions IA, Google Docs, Markdown et Notebooks Colab** archivés dans Google Drive ;",
        "4. La **Matrice des Plateformes IA & Navigateurs** (Copilot, Gemini, Arc, Brave, Opera, Antigravity, Cursor, KiloCode, Cline, ChatGPT, Claude) ;",
        "5. Les **Disques Locaux Windows (`C:\\` et `D:\\`)** avec leur statut d'accessibilité et le collecteur PowerShell dédié ;",
        "6. La **Taxonomie `MATH/00..08`, l'Architecture XIII Domaines, le Registre des Formules, les 20 Fiches YAML et le Registre des Contradictions**.",
        "",
        "## 1. Synthèse & Périmètre d'Accessibilité",
        "",
        "| Source / Périmètre | Statut | Justification / Preuve |",
        "|---|---|---|",
    ]
    for src in perim["sources_statuts"]:
        lines.append(f"| **{src['nom']}** | `{src['statut']}` | {src['raison_ou_preuve']} |")

    lines.extend(
        [
            "",
            f"- **Termes au dictionnaire :** `{stats['termes_dictionnaire']}`",
            f"- **Formules normalisées & Fiches YAML :** `{stats.get('formules_normalisees', len(doc.get('registre_formules', [])))}`",
            f"- **Contradictions & Échecs conservés :** `{stats.get('contradictions_conservees', doc.get('registre_contradictions_ref', {}).get('nombre_contradictions', 0))}`",
            f"- **Dépôts GitHub :** `{stats['depots_github_total']}` (`{stats['depots_github_originaux']}` originaux + `{stats['depots_github_forks']}` forks)",
            f"- **Discussions IA / Docs / Notebooks répertoriés :** `{stats['discussions_ia_google_docs']}`",
            f"- **Plateformes IA & Navigateurs suivis :** `{stats['plateformes_ia_navigateurs']}`",
            f"- **Fichiers réels dans `omega-zero-4d` :** `{stats['fichiers_omega_zero_4d']}`",
            f"- **Entrées locales `C:\\` / `D:\\` importées :** `{stats['entrees_locales_c_d']}`",
            "",
            "## 2. Dictionnaire Terminologique & Conceptuel",
            "",
            "| ID | Terme | Catégorie | Notation / Symbole | Statut épistémique | Définition |",
            "|---|---|---|---|---|---|",
        ]
    )
    for item in doc["dictionnaire"]:
        defn = item["definition"].replace("|", "\\|")
        nota = item["notation"].replace("|", "\\|")
        lines.append(
            f"| `{item['id']}` | **{item['terme']}** | `{item['categorie']}` | `{nota}` | `{item['statut_epistemique']}` | {defn} |"
        )

    lines.extend(
        [
            "",
            "## 3. Encyclopédie GitHub (`gadboisjean1000-arch`)",
            "",
            "| Dépôt | Type | Langage | Branche | Taille (KB) | Rôle dans l'écosystème |",
            "|---|---|---|---|---|---|",
        ]
    )
    for repo in doc["encyclopedie"]["github_depots"]:
        role = repo["role_ecosysteme"].replace("|", "\\|")
        lines.append(
            f"| [{repo['name_with_owner']}]({repo['url']}) | `{repo['type']}` | `{repo['primary_language']}` | `{repo['default_branch']}` | {repo['disk_usage_kb']} | {role} |"
        )

    lines.extend(
        [
            "",
            "## 4. Discussions IA, Google Docs & Notebooks Colab (Google Drive)",
            "",
            "| Date | Titre | Type | Domaine | Outils IA | Résumé vérifié |",
            "|---|---|---|---|---|---|",
        ]
    )
    for disc in doc["encyclopedie"]["discussions_ia_google_docs"]:
        titre = disc["titre"].replace("|", "\\|")
        resume = disc["resume_verifie"].replace("|", "\\|")
        outils = ", ".join(disc["outils_ia_associes"])
        lines.append(
            f"| `{disc['date_modif'][:10]}` | [{titre}]({disc['url']}) | `{disc['type_artefact']}` | {disc['domaine']} | {outils} | {resume} |"
        )

    lines.extend(
        [
            "",
            "## 5. Plateformes IA & Navigateurs (Copilot, Gemini, Arc, Brave, Opera, IDE)",
            "",
            "| Plateforme / Navigateur | Catégorie | Statut | Emplacement Windows | Trace Cloud Vérifiée |",
            "|---|---|---|---|---|",
        ]
    )
    for plat in doc["encyclopedie"]["plateformes_ia_et_navigateurs"]:
        trace = plat["trace_accessible_cloud"].replace("|", "\\|")
        loc = plat["emplacement_local_windows"].replace("|", "\\|")
        lines.append(
            f"| **{plat['nom']}** | `{plat['categorie']}` | `{plat['perimetre_statut']}` | `{loc}` | {trace} |"
        )

    drive_inv = doc["encyclopedie"]["google_drive_inventaire"]
    pc_sync = drive_inv["pc_synchronise_dossier"]
    lines.extend(
        [
            "",
            "## 6. Inventaire Google Drive & Dossiers PC Synchronisés",
            "",
            f"- **Quota Drive :** `{drive_inv['quota_utilise_gb']} GB` utilisés sur `{drive_inv['quota_limite_gb']} GB`",
            f"- **Dossier PC synchronisé (`{pc_sync['nom']}`) :** Desktop (`{pc_sync['desktop_items']}`), Documents (`{pc_sync['documents_items']}`), Downloads (`{pc_sync['downloads_items']}`) — statut `{pc_sync['statut']}`",
            f"- **Note de pagination :** {drive_inv['note_pagination']}",
            "",
            "## 7. Disques Locaux Windows (`C:\\` et `D:\\`) & Collecte Locale",
            "",
            "| Lecteur | Statut | Raison / État | Cibles connues |",
            "|---|---|---|---|",
        ]
    )
    for disk in doc["encyclopedie"]["disques_locaux_windows"]:
        cibles = ", ".join(f"`{c}`" for c in disk["cibles_connues"][:4])
        lines.append(
            f"| `{disk['lecteur']}` | `{disk['perimetre_statut']}` | {disk['raison']} | {cibles} |"
        )

    col = doc["collecteur_local"]
    lines.extend(
        [
            "",
            "### Procédure locale sur Windows (`C:\\` et `D:\\`)",
            "",
            "```powershell",
            col["commande_windows"],
            col["commande_fusion"],
            "```",
            "",
        ]
    )

    if doc.get("taxonomie_math"):
        lines.extend(
            [
                "## 8. Taxonomie `MATH/00..08` & Architecture XIII Domaines",
                "",
                "| Famille `MATH/` | Intitulé | Sous-modules |",
                "|---|---|---|",
            ]
        )
        for fam in doc["taxonomie_math"]:
            mods = ", ".join(f"`{m}`" for m in fam["sous_modules"])
            lines.append(f"| `{fam['famille']}` | **{fam['titre']}** | {mods} |")
        lines.append("")

    if doc.get("registre_formules"):
        lines.extend(
            [
                "## 9. Registre Normalisé des Formules Supela & Fiches YAML",
                "",
                "Voir le registre détaillé [REGISTRE_FORMULES_SUPELA.md](REGISTRE_FORMULES_SUPELA.md) et l'index [fiches/INDEX_FICHES.md](fiches/INDEX_FICHES.md).",
                "",
                "| ID | Nom | Famille | Objet | Statut | État 4D | Formulation brute |",
                "|---|---|---|---|---|---|---|",
            ]
        )
        for row in doc["registre_formules"]:
            brute = row["formulation_brute"].replace("|", "\\|")
            lines.append(
                f"| `{row['id']}` | **{row['nom']}** | `{row['famille_math']}` | `{row['objet']}` | "
                f"`{row['statut_probatoire']}` | `{row['etat_4d']}` | `{brute}` |"
            )
        lines.append("")

    if doc.get("registre_contradictions_ref"):
        cref = doc["registre_contradictions_ref"]
        lines.extend(
            [
                "## 10. Registre des Contradictions & Conservation des Échecs (`T11`)",
                "",
                f"- **JSON canonique contradictions :** [{Path(cref['fichier_json']).name}]({Path(cref['fichier_json']).name}) (`effacement_interdit: {cref['effacement_interdit']}`, `{cref['nombre_contradictions']}` entrées conservées).",
                f"- **Vue Markdown contradictions :** [{Path(cref['fichier_md']).name}]({Path(cref['fichier_md']).name}).",
                "- **Artefact HTML statique dérivé :** [ENCYCLOPEDIE_DICTIONNAIRE.html](ENCYCLOPEDIE_DICTIONNAIRE.html).",
                "",
            ]
        )

    lines.extend(
        [
            f"> **Conclusion :** {doc['conclusion']}",
            "",
        ]
    )
    return "\n".join(lines)


def _safe_json_for_html_script(data: Any) -> str:
    """Sérialise JSON de manière sûre pour intégration directe dans <script type='application/json'>."""
    raw = json.dumps(data, ensure_ascii=False)
    return (
        raw.replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


_HTML_CSS = r"""
:root {
  color-scheme: light dark;
  --bg: #f8fafc;
  --card: #ffffff;
  --content: #f1f5f9;
  --border: #cbd5e1;
  --fg: #0f172a;
  --muted: #475569;
  --primary: #1d4ed8;
  --primary-fg: #ffffff;
  --ok-bg: #dcfce7;
  --ok-fg: #166534;
  --warn-bg: #fef3c7;
  --warn-fg: #92400e;
  --err-bg: #fee2e2;
  --err-fg: #991b1b;
  --info-bg: #dbeafe;
  --info-fg: #1e40af;
  --mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  --sans: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #0b1120;
    --card: #111827;
    --content: #1e293b;
    --border: #334155;
    --fg: #f1f5f9;
    --muted: #94a3b8;
    --primary: #60a5fa;
    --primary-fg: #0b1120;
    --ok-bg: #052e16;
    --ok-fg: #86efac;
    --warn-bg: #451a03;
    --warn-fg: #fcd34d;
    --err-bg: #450a0a;
    --err-fg: #fca5a5;
    --info-bg: #172554;
    --info-fg: #93c5fd;
  }
}
:root[data-theme="dark"] {
  --bg: #0b1120;
  --card: #111827;
  --content: #1e293b;
  --border: #334155;
  --fg: #f1f5f9;
  --muted: #94a3b8;
  --primary: #60a5fa;
  --primary-fg: #0b1120;
  --ok-bg: #052e16;
  --ok-fg: #86efac;
  --warn-bg: #451a03;
  --warn-fg: #fcd34d;
  --err-bg: #450a0a;
  --err-fg: #fca5a5;
  --info-bg: #172554;
  --info-fg: #93c5fd;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--fg);
  font-family: var(--sans);
  font-size: 14px;
  line-height: 1.5;
}
a { color: var(--primary); text-decoration: none; }
a:hover { text-decoration: underline; }
code, pre { font-family: var(--mono); }
.wrap { max-width: 1320px; margin: 0 auto; padding: 18px; display: flex; flex-direction: column; gap: 16px; }
.card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 16px; }
.subcard { background: var(--content); border: 1px solid var(--border); border-radius: 10px; padding: 12px; }
.hdr { display: flex; flex-direction: column; gap: 14px; }
.hdr-top { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: flex-start; gap: 12px; }
.badges { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.badge {
  display: inline-flex; align-items: center; padding: 2px 9px; border-radius: 999px;
  font-size: 11px; font-weight: 600; font-family: var(--mono); border: 1px solid var(--border);
  background: var(--content); color: var(--fg);
}
.badge-primary { background: var(--primary); color: var(--primary-fg); border-color: var(--primary); }
.badge-ok { background: var(--ok-bg); color: var(--ok-fg); border-color: transparent; }
.badge-warn { background: var(--warn-bg); color: var(--warn-fg); border-color: transparent; }
.badge-err { background: var(--err-bg); color: var(--err-fg); border-color: transparent; }
.badge-info { background: var(--info-bg); color: var(--info-fg); border-color: transparent; }
h1 { margin: 4px 0; font-size: 20px; }
h2 { margin: 0 0 10px 0; font-size: 15px; border-bottom: 1px solid var(--border); padding-bottom: 6px; }
h3 { margin: 0 0 6px 0; font-size: 13px; }
.muted { color: var(--muted); font-size: 12px; }
.kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(128px, 1fr)); gap: 8px; }
.kpi { background: var(--content); border: 1px solid var(--border); border-radius: 9px; padding: 9px 11px; }
.kpi-val { font-size: 18px; font-weight: 700; font-family: var(--mono); }
.kpi-lbl { font-size: 11px; color: var(--muted); }
.tabs { display: flex; flex-wrap: wrap; gap: 6px; border-bottom: 1px solid var(--border); padding-bottom: 10px; }
.btn {
  cursor: pointer; padding: 7px 12px; border-radius: 8px; border: 1px solid var(--border);
  background: var(--card); color: var(--fg); font-size: 12px; font-weight: 600;
}
.btn:hover { border-color: var(--primary); }
.btn-active { background: var(--primary); color: var(--primary-fg); border-color: var(--primary); }
.btn-sm { padding: 4px 8px; font-size: 11px; }
.controls { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-bottom: 12px; }
input[type="search"], select {
  padding: 7px 10px; border-radius: 8px; border: 1px solid var(--border);
  background: var(--content); color: var(--fg); font-size: 12px;
}
input[type="search"] { flex: 1; min-width: 220px; }
.grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 12px; }
.grid-3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 10px; }
.tbl-wrap { overflow-x: auto; border: 1px solid var(--border); border-radius: 10px; }
table { width: 100%; border-collapse: collapse; font-size: 12px; text-align: left; }
th, td { padding: 8px 10px; border-bottom: 1px solid var(--border); vertical-align: top; }
th { background: var(--content); font-weight: 600; color: var(--muted); white-space: nowrap; }
tr:hover td { background: rgba(100, 116, 139, 0.06); }
pre { margin: 0; padding: 10px; border-radius: 8px; background: var(--content); border: 1px solid var(--border); overflow-x: auto; font-size: 11.5px; }
.hidden { display: none !important; }
.scroll-box { max-height: 380px; overflow-y: auto; border: 1px solid var(--border); border-radius: 8px; }
.list-row { padding: 7px 10px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; gap: 8px; font-size: 12px; }
.list-row:last-child { border-bottom: none; }
.drawer { border: 2px solid var(--primary); border-radius: 12px; padding: 14px; background: var(--card); margin-top: 12px; }
.mono-wrap { font-family: var(--mono); word-break: break-word; font-size: 11.5px; }
.notice { padding: 10px 12px; border-radius: 8px; border-left: 4px solid var(--primary); background: var(--content); font-size: 12px; }
"""

_HTML_JS = r"""
(function () {
  "use strict";

  function escHtml(v) {
    return String(v == null ? "" : v)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function statusClass(st) {
    var s = String(st || "").toUpperCase();
    if (s.indexOf("PROUV") === 0 || s.indexOf("VERIFIE") >= 0 || s.indexOf("INDEXE_LOCAL") === 0 || s.indexOf("COMPLET") >= 0 || s === "ACTIF" || s === "ORIGINAL" || s === "HISTORIQUE_CORRIGEE_CONSERVEE") {
      return "badge badge-ok";
    }
    if (s.indexOf("INACCESSIBLE") >= 0 || s.indexOf("CONSERVEE") >= 0 || s === "CONTRADICTOIRE" || s === "RÉFUTÉ" || s === "RÉOUVERT" || s === "INCONNUE_SOURCE_INCOMPLETE") {
      return "badge badge-err";
    }
    if (s.indexOf("PARTIEL") >= 0 || s.indexOf("HYBRIDE") >= 0 || s.indexOf("OUVERT") >= 0 || s === "LATENT" || s === "INCONNU" || s === "HYPOTHÉTIQUE") {
      return "badge badge-warn";
    }
    return "badge badge-info";
  }

  var baseData = JSON.parse(document.getElementById("encyclopedia-data").textContent);
  var contradictionsData = JSON.parse(document.getElementById("contradictions-data").textContent);
  var fichesList = JSON.parse(document.getElementById("fiches-yaml-data").textContent);
  var fichesById = {};
  fichesList.forEach(function (f) { fichesById[f.id] = f; });

  var canonicalSha = (document.querySelector('meta[name="supela-canonical-sha256"]') || {}).content || "";
  document.getElementById("hdr-sha").textContent = "SHA-256 : " + canonicalSha.slice(0, 16) + "...";

  var currentDoc = JSON.parse(JSON.stringify(baseData));
  var activeTab = "all";
  var activeDictCat = "ALL";
  var selectedFicheId = null;

  var themeBtn = document.getElementById("theme-toggle");
  themeBtn.addEventListener("click", function () {
    var root = document.documentElement;
    var curr = root.getAttribute("data-theme");
    var next = curr === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    themeBtn.textContent = next === "dark" ? "Mode clair" : "Mode sombre";
  });

  function renderAll() {
    renderHeader();
    renderPerimetre();
    renderDictionary();
    renderFormulas();
    renderContradictionsAndXIII();
    renderDiscussions();
    renderGithubDrive();
    renderLocalCollector();
    applyTabVisibility();
  }

  function renderHeader() {
    var st = currentDoc.statistiques || {};
    var pe = currentDoc.perimetre || {};
    document.getElementById("hdr-global").textContent = pe.statut_global || "";
    document.getElementById("hdr-global").className = statusClass(pe.statut_global);
    document.getElementById("hdr-verdict").textContent = currentDoc.verdict_couverture || "";
    document.getElementById("hdr-verdict").className = statusClass(currentDoc.verdict_couverture);
    document.getElementById("hdr-scan").textContent = "PC: " + (currentDoc.local_pc_scan || "");

    var kpis = [
      { v: st.termes_dictionnaire || 0, l: "Termes Dictionnaire" },
      { v: st.formules_normalisees || (currentDoc.registre_formules || []).length, l: "Formules MATH/" },
      { v: st.fiches_yaml_initiales || fichesList.length, l: "Fiches YAML (29 clés)" },
      { v: st.contradictions_conservees || (contradictionsData.contradictions || []).length, l: "Contradictions" },
      { v: st.depots_github_total || 0, l: "Dépôts GitHub" },
      { v: st.discussions_ia_google_docs || 0, l: "Docs & Colab Drive" },
      { v: st.fichiers_omega_zero_4d || 0, l: "Fichiers A12" },
      { v: st.entrees_locales_c_d || 0, l: "Entrées C:/D:" }
    ];
    document.getElementById("kpi-strip").innerHTML = kpis.map(function (k) {
      return '<div class="kpi"><div class="kpi-val">' + escHtml(k.v) + '</div><div class="kpi-lbl">' + escHtml(k.l) + '</div></div>';
    }).join("");
  }

  function renderPerimetre() {
    var pe = currentDoc.perimetre || {};
    document.getElementById("perim-platform").textContent = pe.plateforme_execution || "";
    document.getElementById("sources-grid").innerHTML = (pe.sources_statuts || []).map(function (s) {
      return '<div class="subcard">' +
        '<div style="display:flex;justify-content:space-between;gap:6px;align-items:center;margin-bottom:4px;">' +
        '<strong>' + escHtml(s.nom) + '</strong><span class="' + statusClass(s.statut) + '">' + escHtml(s.statut) + '</span></div>' +
        '<div class="muted">' + escHtml(s.raison_ou_preuve) + '</div></div>';
    }).join("");

    document.getElementById("epistemic-rules").innerHTML = (pe.regles_epistemiques || []).map(function (r) {
      return '<li>' + escHtml(r) + '</li>';
    }).join("");

    var pFilter = document.getElementById("platform-cat-filter").value;
    var plats = ((currentDoc.encyclopedie || {}).plateformes_ia_et_navigateurs || []).filter(function (p) {
      return pFilter === "ALL" || p.categorie === pFilter;
    });
    document.getElementById("platforms-grid").innerHTML = plats.map(function (p) {
      var tracesHtml = (p.elements_locaux_detectes && p.elements_locaux_detectes.length)
        ? '<details style="margin-top:6px;"><summary class="muted" style="cursor:pointer;">Traces locales (' + p.elements_locaux_detectes.length + ')</summary>' +
          '<ul style="margin:4px 0 0 14px;padding:0;font-size:11px;">' +
          p.elements_locaux_detectes.slice(0, 15).map(function (t) { return '<li class="mono-wrap">' + escHtml(t) + '</li>'; }).join("") +
          '</ul></details>'
        : "";
      return '<div class="subcard">' +
        '<div style="display:flex;justify-content:space-between;gap:6px;align-items:flex-start;margin-bottom:4px;">' +
        '<div><strong>' + escHtml(p.nom) + '</strong><div class="muted">' + escHtml(p.categorie) + '</div></div>' +
        '<span class="' + statusClass(p.perimetre_statut) + '">' + escHtml(p.perimetre_statut) + '</span></div>' +
        '<div style="font-size:12px;margin-bottom:4px;">' + escHtml(p.trace_accessible_cloud) + '</div>' +
        '<div class="mono-wrap muted">' + escHtml(p.emplacement_local_windows) + '</div>' +
        '<div class="muted" style="margin-top:4px;">' + escHtml(p.notes) + '</div>' +
        tracesHtml + '</div>';
    }).join("");
  }

  function renderDictionary() {
    var dict = currentDoc.dictionnaire || [];
    var cats = ["ALL"];
    dict.forEach(function (d) { if (cats.indexOf(d.categorie) === -1) cats.push(d.categorie); });
    document.getElementById("dict-cat-pills").innerHTML = cats.map(function (c) {
      var cls = activeDictCat === c ? "btn btn-sm btn-active" : "btn btn-sm";
      return '<button type="button" data-dict-cat="' + escHtml(c) + '" class="' + cls + '">' + escHtml(c) + '</button>';
    }).join("");
    document.querySelectorAll("[data-dict-cat]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        activeDictCat = btn.getAttribute("data-dict-cat");
        renderDictionary();
      });
    });

    var q = (document.getElementById("dict-search").value || "").toLowerCase().trim();
    var stFilter = document.getElementById("dict-status-filter").value;
    var filtered = dict.filter(function (d) {
      if (activeDictCat !== "ALL" && d.categorie !== activeDictCat) return false;
      if (stFilter !== "ALL" && d.statut_epistemique !== stFilter) return false;
      if (!q) return true;
      return (d.id + " " + d.terme + " " + d.notation + " " + d.definition + " " + (d.sources || []).join(" ")).toLowerCase().indexOf(q) !== -1;
    });
    document.getElementById("dict-count").textContent = filtered.length + " / " + dict.length;
    document.getElementById("dict-grid").innerHTML = filtered.map(function (d) {
      return '<div class="subcard">' +
        '<div style="display:flex;justify-content:space-between;gap:6px;align-items:center;margin-bottom:4px;">' +
        '<span class="badge">' + escHtml(d.id) + '</span>' +
        '<span class="' + statusClass(d.statut_epistemique) + '">' + escHtml(d.statut_epistemique) + '</span></div>' +
        '<div><strong>' + escHtml(d.terme) + '</strong> <span class="muted">(' + escHtml(d.categorie) + ')</span></div>' +
        '<div class="mono-wrap" style="margin:4px 0;color:var(--primary);">' + escHtml(d.notation) + '</div>' +
        '<div style="font-size:12px;">' + escHtml(d.definition) + '</div>' +
        '<div class="muted" style="margin-top:4px;">Sources: ' + escHtml((d.sources || []).join(" · ")) + '</div></div>';
    }).join("");
  }

  function yamlTextFromFiche(f) {
    var out = ["# Fiche " + f.id + " (29 clés universelles)"];
    Object.keys(f).forEach(function (k) {
      var val = f[k];
      if (Array.isArray(val)) {
        if (!val.length) {
          out.push(k + ": []");
        } else {
          out.push(k + ":");
          val.forEach(function (it) {
            if (it && typeof it === "object") {
              var ks = Object.keys(it);
              out.push("  - " + ks[0] + ": " + JSON.stringify(String(it[ks[0]])));
              for (var i = 1; i < ks.length; i++) {
                out.push("    " + ks[i] + ": " + JSON.stringify(String(it[ks[i]])));
              }
            } else {
              out.push("  - " + JSON.stringify(String(it)));
            }
          });
        }
      } else {
        out.push(k + ": " + JSON.stringify(val));
      }
    });
    return out.join("\n");
  }

  function renderFormulas() {
    var tax = currentDoc.taxonomie_math || [];
    document.getElementById("math-taxonomy-grid").innerHTML = tax.map(function (t) {
      return '<div class="subcard">' +
        '<div class="mono-wrap" style="font-weight:700;color:var(--primary);">' + escHtml(t.famille) + '</div>' +
        '<div style="font-weight:600;margin:2px 0;">' + escHtml(t.titre) + '</div>' +
        '<ul style="margin:4px 0 0 16px;padding:0;font-size:11.5px;" class="muted">' +
        (t.sous_modules || []).map(function (m) { return '<li>' + escHtml(m) + '</li>'; }).join("") +
        '</ul></div>';
    }).join("");

    var rows = currentDoc.registre_formules || [];
    var q = (document.getElementById("formula-search").value || "").toLowerCase().trim();
    var famF = document.getElementById("formula-family-filter").value;
    var objF = document.getElementById("formula-obj-filter").value;
    var stF = document.getElementById("formula-status-filter").value;
    var edF = document.getElementById("formula-4d-filter").value;

    var filtered = rows.filter(function (r) {
      if (famF !== "ALL" && r.famille_math !== famF) return false;
      if (objF !== "ALL" && r.objet !== objF) return false;
      if (stF !== "ALL" && r.statut_probatoire !== stF) return false;
      if (edF !== "ALL" && r.etat_4d !== edF) return false;
      if (!q) return true;
      return (r.id + " " + r.nom + " " + r.formulation_brute + " " + r.formulation_normalisee + " " + r.origine + " " + r.implique + " " + r.n_implique_pas).toLowerCase().indexOf(q) !== -1;
    });

    document.getElementById("formula-count").textContent = filtered.length + " / " + rows.length;
    document.getElementById("formula-tbody").innerHTML = filtered.map(function (r) {
      return '<tr>' +
        '<td class="mono-wrap"><strong>' + escHtml(r.id) + '</strong><br><span class="muted">' + escHtml(r.famille_math) + '</span></td>' +
        '<td><strong>' + escHtml(r.nom) + '</strong><br><span class="badge">' + escHtml(r.objet) + '</span> <span class="badge">' + escHtml(r.source_type) + '</span></td>' +
        '<td><div class="mono-wrap">' + escHtml(r.formulation_brute) + '</div><div class="muted" style="margin-top:4px;">Norm.: ' + escHtml(r.formulation_normalisee) + '</div></td>' +
        '<td><span class="' + statusClass(r.statut_probatoire) + '">' + escHtml(r.statut_probatoire) + '</span><br><br><span class="' + statusClass(r.etat_4d) + '">' + escHtml(r.etat_4d) + '</span></td>' +
        '<td><div><strong>Implique:</strong> ' + escHtml(r.implique) + '</div><div class="muted" style="margin-top:4px;"><strong>N\'implique pas:</strong> ' + escHtml(r.n_implique_pas) + '</div></td>' +
        '<td><button type="button" class="btn btn-sm inspect-fiche-btn" data-fiche-id="' + escHtml(r.id) + '">Voir Fiche YAML</button></td>' +
        '</tr>';
    }).join("");

    document.querySelectorAll(".inspect-fiche-btn").forEach(function (b) {
      b.addEventListener("click", function () {
        selectedFicheId = b.getAttribute("data-fiche-id");
        renderFicheInspector();
      });
    });
    renderFicheInspector();
  }

  function renderFicheInspector() {
    var box = document.getElementById("fiche-inspector");
    if (!selectedFicheId || !fichesById[selectedFicheId]) {
      box.classList.add("hidden");
      return;
    }
    var f = fichesById[selectedFicheId];
    box.classList.remove("hidden");
    document.getElementById("fiche-title").textContent = f.id + " — " + f.nom + " (29 clés universelles)";
    document.getElementById("fiche-badges").innerHTML =
      '<span class="badge">' + escHtml(f.type) + '</span>' +
      '<span class="' + statusClass(f.statut_epistemique) + '">' + escHtml(f.statut_epistemique) + '</span>' +
      '<span class="' + statusClass(f.etat_4d) + '">' + escHtml(f.etat_4d) + '</span>';
    document.getElementById("fiche-meta").innerHTML =
      '<div class="subcard"><strong>Formulation brute</strong><div class="mono-wrap">' + escHtml(f.formulation_brute) + '</div></div>' +
      '<div class="subcard"><strong>Formulation normalisée</strong><div>' + escHtml(f.formulation_normalisee) + '</div></div>' +
      '<div class="subcard"><strong>Implique vs N\'implique pas</strong><div><strong>+:</strong> ' + escHtml(f.implique) + '<br><strong>-:</strong> ' + escHtml(f.n_implique_pas) + '</div></div>' +
      '<div class="subcard"><strong>Conditions de réouverture</strong><div>' + escHtml(f.conditions_reouverture) + '</div><div class="muted" style="margin-top:4px;">' + escHtml(f.notes) + '</div></div>';
    document.getElementById("fiche-yaml-raw").textContent = yamlTextFromFiche(f);
  }

  document.getElementById("fiche-close-btn").addEventListener("click", function () {
    selectedFicheId = null;
    renderFicheInspector();
  });

  function renderContradictionsAndXIII() {
    var contrs = contradictionsData.contradictions || [];
    document.getElementById("contr-principle").textContent =
      (contradictionsData.principe_non_effacement || "") + " (effacement_interdit = " + String(contradictionsData.effacement_interdit) + ")";
    document.getElementById("contr-grid").innerHTML = contrs.map(function (c) {
      var lnk = c.url_source ? '<div style="margin-top:4px;"><a target="_blank" rel="noopener" href="' + escHtml(c.url_source) + '">Lien source</a></div>' : "";
      return '<div class="subcard">' +
        '<div style="display:flex;justify-content:space-between;gap:6px;flex-wrap:wrap;margin-bottom:4px;">' +
        '<strong>' + escHtml(c.id) + ' · ' + escHtml(c.objet_concerne) + '</strong>' +
        '<span class="' + statusClass(c.statut_contradiction) + '">' + escHtml(c.statut_contradiction) + '</span></div>' +
        '<div style="font-weight:600;margin-bottom:4px;">' + escHtml(c.titre) + '</div>' +
        '<div style="font-size:12px;"><strong>Constat / FAIL :</strong> ' + escHtml(c.constat_fail_historique) + '</div>' +
        '<div style="font-size:12px;margin-top:4px;"><strong>État ultérieur :</strong> ' + escHtml(c.etat_ulterieur) + '</div>' +
        '<div class="muted" style="margin-top:4px;"><strong>Réouverture :</strong> ' + escHtml(c.conditions_reouverture) + '</div>' +
        '<div class="muted" style="margin-top:4px;">Source : ' + escHtml(c.source_provenance) + '</div>' +
        lnk + '</div>';
    }).join("");

    var xiii = currentDoc.architecture_xiii_sections || [];
    document.getElementById("xiii-tbody").innerHTML = xiii.map(function (s) {
      return '<tr><td><strong>' + escHtml(s.roman) + '</strong></td>' +
        '<td><strong>' + escHtml(s.titre) + '</strong></td>' +
        '<td><span class="' + statusClass(s.statut_couverture) + '">' + escHtml(s.statut_couverture) + '</span></td>' +
        '<td>' + escHtml(s.description) + '</td></tr>';
    }).join("");
  }

  function renderDiscussions() {
    var discs = ((currentDoc.encyclopedie || {}).discussions_ia_google_docs || []);
    var q = (document.getElementById("disc-search").value || "").toLowerCase().trim();
    var tFilter = document.getElementById("disc-type-filter").value;
    var filtered = discs.filter(function (d) {
      if (tFilter !== "ALL" && d.type_artefact !== tFilter) return false;
      if (!q) return true;
      return (d.titre + " " + d.domaine + " " + d.resume_verifie + " " + (d.outils_ia_associes || []).join(" ")).toLowerCase().indexOf(q) !== -1;
    });
    document.getElementById("disc-count").textContent = filtered.length + " / " + discs.length;
    document.getElementById("disc-tbody").innerHTML = filtered.map(function (d) {
      var meta = d.lignes != null ? (d.lignes + " lig. / " + d.caracteres + " car.") : "-";
      return '<tr>' +
        '<td class="mono-wrap">' + escHtml(String(d.date_modif || "").slice(0, 10)) + '</td>' +
        '<td><a target="_blank" rel="noopener" href="' + escHtml(d.url) + '"><strong>' + escHtml(d.titre) + '</strong></a></td>' +
        '<td><span class="badge">' + escHtml(d.type_artefact) + '</span><br><span class="muted">' + escHtml(meta) + '</span></td>' +
        '<td>' + escHtml(d.domaine) + '<br><span class="muted">' + escHtml((d.outils_ia_associes || []).join(", ")) + '</span></td>' +
        '<td>' + escHtml(d.resume_verifie) + '</td></tr>';
    }).join("");
  }

  function renderGithubDrive() {
    var enc = currentDoc.encyclopedie || {};
    var ghFilter = document.getElementById("gh-type-filter").value;
    var repos = (enc.github_depots || []).filter(function (r) {
      return ghFilter === "ALL" || r.type === ghFilter;
    });
    document.getElementById("gh-grid").innerHTML = repos.map(function (r) {
      return '<div class="subcard">' +
        '<div style="display:flex;justify-content:space-between;gap:6px;margin-bottom:4px;">' +
        '<a target="_blank" rel="noopener" href="' + escHtml(r.url) + '"><strong>' + escHtml(r.name_with_owner) + '</strong></a>' +
        '<span class="' + statusClass(r.type) + '">' + escHtml(r.type) + '</span></div>' +
        '<div class="muted">' + escHtml(r.primary_language) + ' · ' + escHtml(r.default_branch) + ' · ' + escHtml(r.disk_usage_kb) + ' KB</div>' +
        '<div style="font-size:12px;margin-top:4px;">' + escHtml(r.role_ecosysteme) + '</div></div>';
    }).join("");

    var treeQ = (document.getElementById("tree-search").value || "").toLowerCase().trim();
    var tree = (enc.omega_zero_4d_arborescence || []).filter(function (f) {
      return !treeQ || (f.chemin + " " + f.categorie).toLowerCase().indexOf(treeQ) !== -1;
    });
    document.getElementById("tree-list").innerHTML = tree.map(function (f) {
      return '<div class="list-row"><span class="mono-wrap">' + escHtml(f.chemin) + '</span>' +
        '<span class="muted">' + escHtml(f.taille_octets) + ' o</span></div>';
    }).join("");

    var di = enc.google_drive_inventaire || {};
    var pc = di.pc_synchronise_dossier || {};
    document.getElementById("drive-quota-line").textContent =
      "Quota : " + di.quota_utilise_gb + " Go / " + di.quota_limite_gb + " Go · PC sync Desktop(" +
      pc.desktop_items + "), Documents(" + pc.documents_items + "), Downloads(" + pc.downloads_items + ")";

    var cpc = di.comptes_par_categorie || {};
    document.getElementById("drive-counts").innerHTML = Object.keys(cpc).map(function (k) {
      return '<span class="badge">' + escHtml(k) + ': ' + escHtml(cpc[k]) + '</span>';
    }).join("");

    var dCat = document.getElementById("drive-cat-filter").value;
    var samples = (di.echantillons_documents_cles || []).filter(function (s) {
      return dCat === "ALL" || s.categorie === dCat;
    });
    document.getElementById("drive-samples").innerHTML = samples.map(function (s) {
      return '<div class="list-row"><span><strong>' + escHtml(s.nom) + '</strong> <span class="badge">' + escHtml(s.categorie) + '</span></span>' +
        '<span class="muted">' + escHtml(String(s.date_modif || "").slice(0, 10)) + '</span></div>';
    }).join("");
  }

  function renderLocalCollector() {
    var col = currentDoc.collecteur_local || {};
    document.getElementById("cmd-win").textContent = col.commande_windows || "";
    document.getElementById("cmd-fusion").textContent = col.commande_fusion || "";
    var disks = ((currentDoc.encyclopedie || {}).disques_locaux_windows || []);
    document.getElementById("disks-grid").innerHTML = disks.map(function (d) {
      var els = d.elements_indexes || [];
      var elsHtml = els.length
        ? '<details style="margin-top:6px;" open><summary class="muted" style="cursor:pointer;">Éléments indexés (' + els.length + ')</summary>' +
          '<div class="scroll-box" style="max-height:200px;margin-top:4px;">' +
          els.slice(0, 100).map(function (e) {
            return '<div class="list-row"><span class="mono-wrap">' + escHtml(e.chemin || e.nom || "") + '</span><span class="badge">' + escHtml(e.type || "") + '</span></div>';
          }).join("") + '</div></details>'
        : '<ul style="margin:6px 0 0 16px;padding:0;font-size:11.5px;" class="muted">' +
          (d.cibles_connues || []).map(function (c) { return '<li class="mono-wrap">' + escHtml(c) + '</li>'; }).join("") + '</ul>';
      return '<div class="subcard">' +
        '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">' +
        '<strong class="mono-wrap" style="font-size:14px;">Lecteur ' + escHtml(d.lecteur) + '</strong>' +
        '<span class="' + statusClass(d.perimetre_statut) + '">' + escHtml(d.perimetre_statut) + '</span></div>' +
        '<div style="font-size:12px;">' + escHtml(d.raison) + '</div>' +
        elsHtml + '</div>';
    }).join("");
  }

  function applyTabVisibility() {
    document.querySelectorAll(".tab-btn").forEach(function (b) {
      var isAct = b.getAttribute("data-tab") === activeTab;
      b.className = isAct ? "tab-btn btn btn-active" : "tab-btn btn";
    });
    document.querySelectorAll(".tab-panel").forEach(function (sec) {
      var id = sec.getAttribute("id");
      if (activeTab === "all" || id === "tab-" + activeTab) {
        sec.classList.remove("hidden");
      } else {
        sec.classList.add("hidden");
      }
    });
  }

  document.querySelectorAll(".tab-btn").forEach(function (b) {
    b.addEventListener("click", function () {
      activeTab = b.getAttribute("data-tab");
      applyTabVisibility();
    });
  });

  [
    ["dict-search", "input", renderDictionary],
    ["dict-status-filter", "change", renderDictionary],
    ["platform-cat-filter", "change", renderPerimetre],
    ["formula-search", "input", renderFormulas],
    ["formula-family-filter", "change", renderFormulas],
    ["formula-obj-filter", "change", renderFormulas],
    ["formula-status-filter", "change", renderFormulas],
    ["formula-4d-filter", "change", renderFormulas],
    ["disc-search", "input", renderDiscussions],
    ["disc-type-filter", "change", renderDiscussions],
    ["gh-type-filter", "change", renderGithubDrive],
    ["tree-search", "input", renderGithubDrive],
    ["drive-cat-filter", "change", renderGithubDrive]
  ].forEach(function (cfg) {
    var el = document.getElementById(cfg[0]);
    if (el) el.addEventListener(cfg[1], cfg[2]);
  });

  document.querySelectorAll(".copy-btn").forEach(function (b) {
    b.addEventListener("click", function () {
      var tgt = document.getElementById(b.getAttribute("data-copy-target"));
      if (tgt && navigator.clipboard) {
        navigator.clipboard.writeText(tgt.textContent || "");
        var old = b.textContent;
        b.textContent = "Copié";
        setTimeout(function () { b.textContent = old; }, 1200);
      }
    });
  });

  // Chargement en mémoire locale d'un export local_pc_inventory.json (lecture seule)
  document.getElementById("local-json-input").addEventListener("change", function (ev) {
    var file = ev.target.files && ev.target.files[0];
    if (!file) return;
    var reader = new FileReader();
    reader.onload = function () {
      try {
        var inv = JSON.parse(String(reader.result || "{}"));
        if (inv.schema !== "supela-local-pc-inventory/1") {
          throw new Error("Schéma attendu : supela-local-pc-inventory/1");
        }
        var preview = JSON.parse(JSON.stringify(baseData));
        var drivesByLetter = {};
        (inv.drives || []).forEach(function (d) { drivesByLetter[String(d.lecteur || "").toUpperCase()] = d; });
        var gitRepos = inv.git_repos || [];
        var notableFiles = inv.notable_files || [];
        var skipHist = Boolean(inv.skip_browser_history);
        (preview.encyclopedie.disques_locaux_windows || []).forEach(function (disk) {
          var l = String(disk.lecteur || "").toUpperCase();
          var f = drivesByLetter[l];
          if (f && (f.statut === "INDEXE_LOCAL" || f.statut === "PARTIELLEMENT_INDEXE")) {
            var dg = gitRepos.filter(function (g) { return String(g.lecteur || "").toUpperCase() === l; });
            var df = notableFiles.filter(function (x) { return String(x.lecteur || "").toUpperCase() === l; });
            var els = [];
            (f.dossiers_racine || []).slice(0, 100).forEach(function (x) { els.push(Object.assign({ type: "DOSSIER_RACINE" }, x)); });
            dg.slice(0, 100).forEach(function (x) { els.push(Object.assign({ type: "DEPOT_GIT_LOCAL" }, x)); });
            df.slice(0, 200).forEach(function (x) { els.push(Object.assign({ type: "FICHIER_NOTABLE" }, x)); });
            disk.perimetre_statut = (f.scan_tronque || (f.dossiers_inaccessibles || 0) > 0) ? "PARTIELLEMENT_INDEXE" : f.statut;
            disk.elements_indexes = els;
            disk.raison = "Aperçu navigateur (" + (inv.machine_name || "PC") + ") : " + dg.length + " dépôts Git, " + df.length + " fichiers notables.";
          }
        });
        var aiCount = 0;
        var hasAi = false;
        var localAi = {};
        (inv.ai_platforms || []).forEach(function (p) { localAi[p.id] = p; });
        var aliasMap = {
          copilot_edge: "copilot_edge",
          gemini_google: "gemini_chrome",
          arc_browser: "arc_browser",
          brave_leo: "brave_leo",
          opera_aria: "opera_aria",
          antigravity_agent: "antigravity",
          cursor_ide: "cursor",
          kilocode_cline_vscode: "vscode_agents"
        };
        (preview.encyclopedie.plateformes_ia_et_navigateurs || []).forEach(function (pl) {
          var loc = localAi[aliasMap[pl.id] || pl.id];
          if (loc && loc.present) {
            hasAi = true;
            pl.perimetre_statut = "INDEXE_LOCAL";
            pl.elements_locaux_detectes = (loc.traces_echantillon || []).map(function (t) {
              return (t.type || "TRACE") + ": " + (t.titre || "") + (t.url ? " — " + t.url : "");
            });
            aiCount += Number(loc.total_traces_ia || 0);
          }
        });
        var allDisksOk = (preview.encyclopedie.disques_locaux_windows || []).every(function (d) { return d.perimetre_statut === "INDEXE_LOCAL"; });
        if (allDisksOk && hasAi && !skipHist) {
          preview.local_pc_scan = "EXECUTEE";
          preview.verdict_couverture = "COMPLETE_SOUS_PREUVE";
          preview.perimetre.statut_global = "COMPLET_SOUS_PREUVE";
        } else {
          preview.local_pc_scan = "PARTIELLE";
          preview.verdict_couverture = "PARTIELLE_AVEC_EXPORT_LOCAL";
          preview.perimetre.statut_global = "HYBRIDE_LOCAL_DISTANT";
        }
        preview.statistiques.entrees_locales_c_d = gitRepos.length + notableFiles.length + aiCount;
        currentDoc = preview;
        var b = document.getElementById("local-merge-banner");
        b.classList.remove("hidden");
        b.textContent = "Aperçu local chargé en mémoire navigateur uniquement (" + (inv.machine_name || "PC") + "). Le JSON canonique versionné n'est pas modifié.";
        document.getElementById("reset-local-btn").classList.remove("hidden");
        renderAll();
      } catch (err) {
        alert("Erreur lecture inventaire local : " + err.message);
      }
    };
    reader.readAsText(file, "utf-8");
  });

  document.getElementById("reset-local-btn").addEventListener("click", function () {
    currentDoc = JSON.parse(JSON.stringify(baseData));
    document.getElementById("local-merge-banner").classList.add("hidden");
    document.getElementById("reset-local-btn").classList.add("hidden");
    renderAll();
  });

  renderAll();
})();
"""


class _EncyclopediaHtmlParser(HTMLParser):
    """Analyseur HTML strict vérifiant absence de CDN, empreinte SHA-256 et bloc JSON."""

    def __init__(self) -> None:
        super().__init__()
        self.external_assets: list[str] = []
        self.meta_sha256: str | None = None
        self.json_script_chunks: list[str] = []
        self.ui_js_blocks: list[str] = []
        self._capture_target: str | None = None
        self._current_chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {k.lower(): (v or "") for k, v in attrs}
        if tag.lower() == "script":
            src = attr_map.get("src", "").strip()
            if src:
                self.external_assets.append(f"script src={src}")
            sid = attr_map.get("id", "")
            stype = attr_map.get("type", "").lower()
            if sid == "encyclopedia-data":
                self._capture_target = "json_main"
                self._current_chunks = []
            elif stype != "application/json":
                self._capture_target = "ui_js"
                self._current_chunks = []
        elif tag.lower() == "link":
            href = attr_map.get("href", "").strip()
            rel = attr_map.get("rel", "").lower()
            if href and href.startswith(("http://", "https://", "//")) and ("stylesheet" in rel or "preload" in rel):
                self.external_assets.append(f"link href={href}")
        elif tag.lower() == "meta" and attr_map.get("name", "").lower() == "supela-canonical-sha256":
            self.meta_sha256 = attr_map.get("content", "").strip()

    def handle_data(self, data: str) -> None:
        if self._capture_target is not None:
            self._current_chunks.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._capture_target is not None:
            joined = "".join(self._current_chunks)
            if self._capture_target == "json_main":
                self.json_script_chunks.append(joined)
            elif self._capture_target == "ui_js" and joined.strip():
                self.ui_js_blocks.append(joined)
            self._capture_target = None
            self._current_chunks = []


def render_html(
    doc: dict[str, Any],
    contradictions_doc: dict[str, Any] | None = None,
    cards: list[dict[str, Any]] | None = None,
) -> str:
    """Génère la vue HTML statique autonome (zéro CDN) avec parité SHA-256 stricte."""
    contr = contradictions_doc if contradictions_doc is not None else load_contradictions_registry()
    card_list = cards if cards is not None else build_formula_cards()
    fiches_public = [extract_yaml_payload(c) for c in card_list]
    canonical_hash = _canonical_sha256(doc)

    fam_options = "".join(
        f'<option value="{html_escape(f["famille"])}">{html_escape(f["famille"])}</option>'
        for f in doc.get("taxonomie_math", [])
    )
    return "\n".join(
        [
            "<!DOCTYPE html>",
            '<html lang="fr">',
            "<head>",
            '  <meta charset="UTF-8" />',
            '  <meta name="viewport" content="width=device-width, initial-scale=1.0" />',
            f'  <meta name="supela-canonical-sha256" content="{canonical_hash}" />',
            "  <title>Dictionnaire &amp; Encyclopédie Universelle · Supela Ω-ZERO</title>",
            "  <style>",
            _HTML_CSS.strip(),
            "  </style>",
            "</head>",
            "<body>",
            '  <div class="wrap">',
            '    <header class="card hdr">',
            '      <div class="hdr-top">',
            "        <div>",
            '          <div class="badges">',
            f'            <span class="badge badge-primary">{html_escape(doc["schema"])}</span>',
            '            <span id="hdr-global" class="badge"></span>',
            '            <span id="hdr-verdict" class="badge"></span>',
            '            <span id="hdr-scan" class="badge"></span>',
            '            <span id="hdr-sha" class="badge"></span>',
            "          </div>",
            "          <h1>Dictionnaire, Formules MATH/ &amp; Encyclopédie Universelle · Supela Ω-ZERO</h1>",
            '          <div class="muted">Chaîne : JSON canonique → Artefact HTML dérivé → Contrôle de parité &amp; syntaxe → Publication éventuelle. Interface strictement consultative sans modification silencieuse du canon (Source ≠ Autorité · M3).</div>',
            "        </div>",
            '        <button id="theme-toggle" type="button" class="btn btn-sm">Mode sombre</button>',
            "      </div>",
            '      <div id="kpi-strip" class="kpis"></div>',
            "    </header>",
            '    <nav class="tabs" role="tablist" aria-label="Vues Encyclopédie">',
            '      <button type="button" data-tab="all" class="tab-btn btn btn-active">0. Tout voir (Vue complète)</button>',
            '      <button type="button" data-tab="perimetre" class="tab-btn btn">1. Périmètre &amp; IA</button>',
            '      <button type="button" data-tab="dictionnaire" class="tab-btn btn">2. Dictionnaire</button>',
            '      <button type="button" data-tab="formules" class="tab-btn btn">3. Formules MATH/ &amp; Fiches YAML</button>',
            '      <button type="button" data-tab="contradictions" class="tab-btn btn">4. Contradictions &amp; XIII Domaines</button>',
            '      <button type="button" data-tab="discussions" class="tab-btn btn">5. Discussions IA, Docs &amp; Colab</button>',
            '      <button type="button" data-tab="github-drive" class="tab-btn btn">6. GitHub &amp; Drive</button>',
            '      <button type="button" data-tab="local-collector" class="tab-btn btn">7. Collecteur Windows C:\\ &amp; D:\\</button>',
            "    </nav>",
            '    <section id="tab-perimetre" class="tab-panel card">',
            '      <h2>1. Périmètre d\'Accessibilité Vérifié &amp; Matrice Plateformes IA</h2>',
            '      <div id="perim-platform" class="muted" style="margin-bottom:10px;"></div>',
            '      <div id="sources-grid" class="grid-3" style="margin-bottom:12px;"></div>',
            '      <div class="notice" style="margin-bottom:12px;"><strong>Règles épistémiques actives :</strong><ul id="epistemic-rules" style="margin:4px 0 0 18px;padding:0;"></ul></div>',
            '      <div class="controls">',
            '        <strong>Plateformes IA, Navigateurs &amp; IDE :</strong>',
            '        <select id="platform-cat-filter"><option value="ALL">Toutes catégories</option><option value="ASSISTANT_IA">Assistants IA</option><option value="NAVIGATEUR_IA">Navigateurs IA</option><option value="IDE_AGENT_IA">IDE &amp; Agents de code</option></select>',
            "      </div>",
            '      <div id="platforms-grid" class="grid-3"></div>',
            "    </section>",
            '    <section id="tab-dictionnaire" class="tab-panel card">',
            "      <h2>2. Dictionnaire Terminologique &amp; Conceptuel Supela Ω-ZERO</h2>",
            '      <div class="controls">',
            '        <input id="dict-search" type="search" placeholder="Filtrer terme, symbole (Π₀, GDS, T11, GRPO...), source ou définition..." />',
            '        <select id="dict-status-filter"><option value="ALL">Tous statuts</option><option value="VERIFIE_EXECUTEE">VERIFIE_EXECUTEE</option><option value="DOCUMENTE_NORMATIF">DOCUMENTE_NORMATIF</option><option value="CANDIDAT_OUVERT">CANDIDAT_OUVERT</option><option value="INACCESSIBLE_DANS_LE_PÉRIMÈTRE">INACCESSIBLE_DANS_LE_PÉRIMÈTRE</option></select>',
            '        <span id="dict-count" class="badge"></span>',
            "      </div>",
            '      <div id="dict-cat-pills" class="controls"></div>',
            '      <div id="dict-grid" class="grid-2"></div>',
            "    </section>",
            '    <section id="tab-formules" class="tab-panel card">',
            "      <h2>3. Formules Retrouvées (Taxonomie MATH/00..08) &amp; Fiches YAML Initiales</h2>",
            '      <div id="math-taxonomy-grid" class="grid-3" style="margin-bottom:14px;"></div>',
            '      <div class="controls">',
            '        <input id="formula-search" type="search" placeholder="Rechercher formule brute, normalisation, ID (MAT-01-TREILLIS, T11, undefined)..." />',
            f'        <select id="formula-family-filter"><option value="ALL">Toutes familles MATH/</option>{fam_options}</select>',
            '        <select id="formula-obj-filter"><option value="ALL">Tous objets</option><option value="Théorème">Théorème</option><option value="Axiome">Axiome</option><option value="Invariant">Invariant</option><option value="Formule">Formule</option><option value="Opérateur">Opérateur</option><option value="Règle">Règle</option><option value="Distinction">Distinction</option><option value="Métrique">Métrique</option><option value="Test">Test</option><option value="Contre-exemple">Contre-exemple</option></select>',
            '        <select id="formula-status-filter"><option value="ALL">Tous statuts</option><option value="PROUVÉ">PROUVÉ</option><option value="SUPPORTÉ">SUPPORTÉ</option><option value="INFÉRÉ">INFÉRÉ</option><option value="HYPOTHÉTIQUE">HYPOTHÉTIQUE</option><option value="INCONNU">INCONNU</option><option value="CONTRADICTOIRE">CONTRADICTOIRE</option></select>',
            '        <select id="formula-4d-filter"><option value="ALL">Tous états 4D</option><option value="ACTIF">ACTIF</option><option value="LATENT">LATENT</option><option value="RÉOUVERT">RÉOUVERT</option></select>',
            '        <span id="formula-count" class="badge"></span>',
            "      </div>",
            '      <div class="tbl-wrap"><table><thead><tr><th>ID &amp; Famille</th><th>Nom &amp; Classification</th><th>Brute vs Normalisée</th><th>Statut &amp; État 4D</th><th>Implique / N\'implique pas</th><th>Fiche YAML</th></tr></thead><tbody id="formula-tbody"></tbody></table></div>',
            '      <div id="fiche-inspector" class="drawer hidden">',
            '        <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;margin-bottom:8px;">',
            '          <h3 id="fiche-title"></h3>',
            '          <div style="display:flex;gap:6px;align-items:center;"><span id="fiche-badges" class="badges"></span><button id="fiche-close-btn" type="button" class="btn btn-sm">Fermer</button></div>',
            "        </div>",
            '        <div id="fiche-meta" class="grid-2" style="margin-bottom:10px;"></div>',
            '        <pre id="fiche-yaml-raw"></pre>',
            "      </div>",
            "    </section>",
            '    <section id="tab-contradictions" class="tab-panel card">',
            "      <h2>4. Registre des Contradictions (Non-Effacement T11) &amp; Architecture XIII Domaines</h2>",
            '      <div id="contr-principle" class="notice" style="margin-bottom:12px;"></div>',
            '      <div id="contr-grid" class="grid-2" style="margin-bottom:14px;"></div>',
            "      <h3>Architecture Encyclopédique en XIII Domaines</h3>",
            '      <div class="tbl-wrap"><table><thead><tr><th>Domaine</th><th>Intitulé</th><th>Couverture</th><th>Contenu &amp; Périmètre</th></tr></thead><tbody id="xiii-tbody"></tbody></table></div>',
            "    </section>",
            '    <section id="tab-discussions" class="tab-panel card">',
            "      <h2>5. Discussions IA, Google Docs &amp; Notebooks Colab (Google Drive)</h2>",
            '      <div class="controls">',
            '        <input id="disc-search" type="search" placeholder="Filtrer par titre, domaine, outil ou résumé vérifié..." />',
            '        <select id="disc-type-filter"><option value="ALL">Tous types</option><option value="GOOGLE_DOC">GOOGLE_DOC</option><option value="GOOGLE_DOC_COPIE">GOOGLE_DOC_COPIE</option><option value="MARKDOWN_DRIVE">MARKDOWN_DRIVE</option><option value="COLAB_NOTEBOOK">COLAB_NOTEBOOK</option></select>',
            '        <span id="disc-count" class="badge"></span>',
            "      </div>",
            '      <div class="tbl-wrap"><table><thead><tr><th>Date</th><th>Titre</th><th>Type &amp; Taille</th><th>Domaine &amp; Outils</th><th>Résumé vérifié</th></tr></thead><tbody id="disc-tbody"></tbody></table></div>',
            "    </section>",
            '    <section id="tab-github-drive" class="tab-panel card">',
            "      <h2>6. Dépôts GitHub (gadboisjean1000-arch), Arborescence A12 &amp; Google Drive</h2>",
            '      <div class="controls">',
            '        <strong>Dépôts GitHub :</strong>',
            '        <select id="gh-type-filter"><option value="ALL">Tous (15)</option><option value="ORIGINAL">ORIGINAL (4)</option><option value="FORK">FORK (11)</option></select>',
            "      </div>",
            '      <div id="gh-grid" class="grid-3" style="margin-bottom:14px;"></div>',
            '      <div class="grid-2">',
            "        <div>",
            '          <div class="controls"><strong>Arborescence omega-zero-4d (A12)</strong><input id="tree-search" type="search" placeholder="Filtrer chemin..." /></div>',
            '          <div id="tree-list" class="scroll-box"></div>',
            "        </div>",
            "        <div>",
            '          <div class="controls"><strong>Inventaire Google Drive</strong><select id="drive-cat-filter"><option value="ALL">Toutes catégories</option><option value="COLAB_NOTEBOOK">COLAB_NOTEBOOK</option><option value="GOOGLE_SLIDES">GOOGLE_SLIDES</option><option value="GOOGLE_SHEETS">GOOGLE_SHEETS</option><option value="PDF_DRIVE">PDF_DRIVE</option><option value="DOCX_DOCUMENTS">DOCX_DOCUMENTS</option></select></div>',
            '          <div id="drive-quota-line" class="muted" style="margin-bottom:6px;"></div>',
            '          <div id="drive-counts" class="badges" style="margin-bottom:8px;"></div>',
            '          <div id="drive-samples" class="scroll-box"></div>',
            "        </div>",
            "      </div>",
            "    </section>",
            '    <section id="tab-local-collector" class="tab-panel card">',
            "      <h2>7. Disques Locaux Windows (C:\\ &amp; D:\\) &amp; Collecteur Lecture-Seule</h2>",
            '      <div class="controls">',
            '        <label class="btn btn-active" style="display:inline-block;">Charger local_pc_inventory.json<input id="local-json-input" type="file" accept=".json,application/json" style="display:none;" /></label>',
            '        <button id="reset-local-btn" type="button" class="btn hidden">Revenir à l\'état cloud vérifié</button>',
            "      </div>",
            '      <div id="local-merge-banner" class="notice hidden" style="margin-bottom:12px;"></div>',
            '      <div class="grid-2" style="margin-bottom:12px;">',
            '        <div class="subcard"><div style="display:flex;justify-content:space-between;margin-bottom:6px;"><strong>1. Commande Windows PowerShell</strong><button type="button" data-copy-target="cmd-win" class="btn btn-sm copy-btn">Copier</button></div><pre id="cmd-win"></pre></div>',
            '        <div class="subcard"><div style="display:flex;justify-content:space-between;margin-bottom:6px;"><strong>2. Fusion Python &amp; Validation Draft 2020-12</strong><button type="button" data-copy-target="cmd-fusion" class="btn btn-sm copy-btn">Copier</button></div><pre id="cmd-fusion"></pre></div>',
            "      </div>",
            '      <div id="disks-grid" class="grid-2"></div>',
            "    </section>",
            "  </div>",
            f'  <script id="encyclopedia-data" type="application/json">{_safe_json_for_html_script(doc)}</script>',
            f'  <script id="contradictions-data" type="application/json">{_safe_json_for_html_script(contr)}</script>',
            f'  <script id="fiches-yaml-data" type="application/json">{_safe_json_for_html_script(fiches_public)}</script>',
            "  <script>",
            _HTML_JS.strip(),
            "  </script>",
            "</body>",
            "</html>",
            "",
        ]
    )


def verify_html_parity(doc: dict[str, Any], html_text: str) -> str:
    """Vérifie zéro CDN externe, parité JSON stricte et empreinte SHA-256 du HTML généré."""
    parser = _EncyclopediaHtmlParser()
    parser.feed(html_text)
    parser.close()

    if parser.external_assets:
        raise ValueError(f"Dépendance externe interdite détectée dans HTML : {parser.external_assets}")
    expected_sha = _canonical_sha256(doc)
    if parser.meta_sha256 != expected_sha:
        raise ValueError(
            f"Divergence SHA-256 HTML ({parser.meta_sha256}) != JSON canonique ({expected_sha})."
        )
    if len(parser.json_script_chunks) != 1:
        raise ValueError(
            f"Nombre invalide de blocs #encyclopedia-data ({len(parser.json_script_chunks)})."
        )
    recovered = json.loads(parser.json_script_chunks[0])
    if recovered != doc:
        raise ValueError("Le JSON embarqué dans ENCYCLOPEDIE_DICTIONNAIRE.html diverge du canon.")
    if not parser.ui_js_blocks:
        raise ValueError("Aucun bloc JavaScript UI trouvé dans HTML.")
    return "\n".join(parser.ui_js_blocks)


def verify_html_js_syntax(html_text: str) -> dict[str, Any]:
    """Vérifie la syntaxe du JavaScript embarqué via `node --check` sans exécution."""
    parser = _EncyclopediaHtmlParser()
    parser.feed(html_text)
    parser.close()
    js_code = "\n".join(parser.ui_js_blocks)
    if not js_code.strip():
        return {"ok": False, "checked_with": None, "stderr": "Bloc JS vide", "script_bytes": 0}
    node_bin = shutil.which("node")
    if node_bin is None:
        return {
            "ok": False,
            "checked_with": None,
            "stderr": "Exécutable node introuvable dans PATH",
            "script_bytes": len(js_code),
        }
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".js", encoding="utf-8", delete=True
    ) as tmp:
        tmp.write(js_code)
        tmp.flush()
        proc = subprocess.run(
            [node_bin, "--check", tmp.name],
            capture_output=True,
            text=True,
            check=False,
        )
    return {
        "ok": proc.returncode == 0,
        "checked_with": node_bin,
        "stderr": proc.stderr.strip(),
        "script_bytes": len(js_code),
    }


def main() -> int:
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Construit ou fusionne le Dictionnaire, Fiches YAML & Encyclopédie HTML/MD Supela Ω-ZERO."
    )
    parser.add_argument("--root", type=Path, default=ROOT_DIR)
    parser.add_argument("--sources-dir", type=Path, default=None)
    parser.add_argument("--base-registry", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--local-inventory", type=Path, default=None)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_MD_OUT)
    parser.add_argument("--out-html", type=Path, default=None)
    parser.add_argument("--out-formulas-md", type=Path, default=None)
    parser.add_argument("--out-contradictions-json", type=Path, default=DEFAULT_CONTRADICTIONS_JSON)
    parser.add_argument("--out-contradictions-md", type=Path, default=None)
    parser.add_argument("--out-fiches-dir", type=Path, default=None)
    parser.add_argument("--skip-html", action="store_true")
    parser.add_argument("--skip-fiches", action="store_true")
    args = parser.parse_args()

    contradictions_doc = load_contradictions_registry(args.out_contradictions_json)
    cards = build_formula_cards()
    is_canonical_run = (
        args.out_json.resolve() == (args.root / "docs" / "constitution" / "supela-dictionnaire-encyclopedie-1.json").resolve()
    )

    if args.sources_dir is not None:
        doc = build_from_sources(args.sources_dir, args.root, contradictions_doc=contradictions_doc)
    else:
        doc = json.loads(args.base_registry.read_text(encoding="utf-8"))
        doc = enrich_structural_knowledge(doc, cards, contradictions_doc)

    if not args.skip_fiches:
        fiches_dir = args.out_fiches_dir if args.out_fiches_dir is not None else (
            DEFAULT_FICHES_DIR if is_canonical_run else None
        )
        if fiches_dir is not None:
            sync_yaml_fiches(fiches_dir, cards)

    formulas_md_out = args.out_formulas_md if args.out_formulas_md is not None else (
        DEFAULT_FORMULAS_MD_OUT if is_canonical_run else None
    )
    contradictions_md_out = args.out_contradictions_md if args.out_contradictions_md is not None else (
        DEFAULT_CONTRADICTIONS_MD if is_canonical_run else None
    )
    if formulas_md_out is not None:
        _atomic_write_text(formulas_md_out, render_formulas_markdown(doc, contradictions_doc))
    if contradictions_md_out is not None:
        _atomic_write_text(contradictions_md_out, render_contradictions_markdown(contradictions_doc))

    doc["encyclopedie"]["omega_zero_4d_arborescence"] = scan_repo_tree(args.root)
    doc["statistiques"]["fichiers_omega_zero_4d"] = len(
        doc["encyclopedie"]["omega_zero_4d_arborescence"]
    )

    if args.local_inventory is not None:
        local_inv = json.loads(args.local_inventory.read_text(encoding="utf-8"))
        doc = merge_local_inventory(doc, local_inv, args.root)

    schema = json.loads(args.schema.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(doc)

    out_html = (
        args.out_html
        if args.out_html is not None
        else (DEFAULT_HTML_OUT if args.out_md.resolve() == DEFAULT_MD_OUT.resolve() else args.out_md.with_suffix(".html"))
    )

    html_verified = False
    for _ in range(4):
        json_text = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
        md_text = render_markdown(doc)
        html_text = "" if args.skip_html else render_html(doc, contradictions_doc, cards)

        prev_json = args.out_json.read_text(encoding="utf-8") if args.out_json.exists() else ""
        prev_md = args.out_md.read_text(encoding="utf-8") if args.out_md.exists() else ""
        prev_html = out_html.read_text(encoding="utf-8") if (not args.skip_html and out_html.exists()) else ""

        _atomic_write_text(args.out_json, json_text)
        _atomic_write_text(args.out_md, md_text)
        if not args.skip_html:
            _atomic_write_text(out_html, html_text)
            verify_html_parity(doc, html_text)
            if shutil.which("node") is not None:
                js_res = verify_html_js_syntax(html_text)
                if not js_res["ok"]:
                    raise RuntimeError(f"Erreur syntaxe JS HTML : {js_res['stderr']}")
            html_verified = True

        updated_tree = scan_repo_tree(args.root)
        if (
            json_text == prev_json
            and md_text == prev_md
            and (args.skip_html or html_text == prev_html)
            and updated_tree == doc["encyclopedie"]["omega_zero_4d_arborescence"]
        ):
            break
        if updated_tree != doc["encyclopedie"]["omega_zero_4d_arborescence"]:
            doc["encyclopedie"]["omega_zero_4d_arborescence"] = updated_tree
            doc["statistiques"]["fichiers_omega_zero_4d"] = len(updated_tree)
            Draft202012Validator(schema).validate(doc)

    print(
        json.dumps(
            {
                "status": "OK",
                "out_json": str(args.out_json),
                "out_md": str(args.out_md),
                "out_html": None if args.skip_html else str(out_html),
                "html_parity_verified": html_verified,
                "canonical_sha256": _canonical_sha256(doc),
                "verdict_couverture": doc["verdict_couverture"],
                "statistiques": doc["statistiques"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

