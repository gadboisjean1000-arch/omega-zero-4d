#!/usr/bin/env python3
"""Constructeur et fusionneur du Dictionnaire & Encyclopédie Universelle Supela Ω-ZERO."""

from __future__ import annotations

import argparse
import copy
import io
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT_DIR / "schemas" / "supela_encyclopedie_1.schema.json"
DEFAULT_JSON_OUT = ROOT_DIR / "docs" / "constitution" / "supela-dictionnaire-encyclopedie-1.json"
DEFAULT_MD_OUT = ROOT_DIR / "docs" / "constitution" / "ENCYCLOPEDIE_DICTIONNAIRE.md"

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


def scan_repo_tree(root: Path) -> list[dict[str, Any]]:
    """Liste tous les fichiers réels de omega-zero-4d soumis à A12."""
    items: list[dict[str, Any]] = []
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel_parts = p.relative_to(root).parts
        if any(part in EXCLUDED_REPO_DIRS or part.endswith(".egg-info") for part in rel_parts):
            continue
        if p.suffix in {".bundle", ".pyc", ".pyo"} or p.name == ".DS_Store":
            continue
        rel_posix = p.relative_to(root).as_posix()
        category = rel_parts[0] if len(rel_parts) > 1 else "root"
        items.append(
            {
                "chemin": rel_posix,
                "categorie": category,
                "taille_octets": int(p.stat().st_size),
            }
        )
    return items


def build_from_sources(sources_dir: Path, root: Path) -> dict[str, Any]:
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
    native_docs = [d for d in gdocs_raw if d.get("mimeType") == "application/vnd.google-apps.document"]
    seen_copy_titles = 0
    for d in native_docs:
        did = str(d["id"])
        title = str(d.get("name") or "Sans titre").replace("\n", " ").strip()
        mod_time = str(d.get("modifiedTime") or "")
        preview_info = doc_previews.get(did, {})
        lines = int(preview_info.get("line_count", 0))
        chars = int(preview_info.get("char_count", 0))

        is_copy = False
        if title == "toutes les chapitre un coups":
            seen_copy_titles += 1
            is_copy = seen_copy_titles > 1

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
            "trace_accessible_cloud": "Aucune API Copilot connectée ; matrice Zero-Trust Microsoft AZ-500/CA-01/PIM-02 documentée dans Google Docs.",
            "emplacement_local_windows": "%LOCALAPPDATA%\\Microsoft\\Edge\\User Data\\",
            "perimetre_statut": "INACCESSIBLE_DANS_LE_PÉRIMÈTRE",
            "methode_collecte_locale": "scripts/collect_local_encyclopedie.ps1 (Bookmarks + URLs History SQLite Copilot/Bing)",
            "notes": "Requiert l'exécution locale sur Windows pour inventorier les discussions Copilot et favoris Edge.",
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
    return doc


def merge_local_inventory(base_doc: dict[str, Any], local_inv: dict[str, Any], root: Path) -> dict[str, Any]:
    """Fusionne un export local_pc_inventory.json dans le registre canonique."""
    merged = copy.deepcopy(base_doc)
    merged["encyclopedie"]["omega_zero_4d_arborescence"] = scan_repo_tree(root)

    drives_by_letter = {
        str(d.get("lecteur", "")).upper(): d for d in local_inv.get("drives", [])
    }
    git_repos = list(local_inv.get("git_repos", []))
    notable_files = list(local_inv.get("notable_files", []))

    total_local_entries = len(git_repos) + len(notable_files)
    scanned_drives_count = 0

    new_disk_entries: list[dict[str, Any]] = []
    for disk in merged["encyclopedie"]["disques_locaux_windows"]:
        letter = str(disk["lecteur"]).upper()
        found = drives_by_letter.get(letter)
        if found and found.get("statut") == "INDEXE_LOCAL":
            scanned_drives_count += 1
            disk_git = [g for g in git_repos if str(g.get("lecteur", "")).upper() == letter]
            disk_files = [f for f in notable_files if str(f.get("lecteur", "")).upper() == letter]
            elements: list[dict[str, Any]] = []
            for ddir in found.get("dossiers_racine", [])[:100]:
                elements.append({"type": "DOSSIER_RACINE", **ddir})
            for grepo in disk_git[:100]:
                elements.append({"type": "DEPOT_GIT_LOCAL", **grepo})
            for nf in disk_files[:200]:
                elements.append({"type": "FICHIER_NOTABLE", **nf})

            disk["perimetre_statut"] = "INDEXE_LOCAL"
            disk["raison"] = (
                f"Indexé localement sur {local_inv.get('machine_name', 'poste Windows')} "
                f"({len(disk_git)} dépôts Git, {len(disk_files)} fichiers notables)."
            )
            disk["elements_indexes"] = elements
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
        if loc and loc.get("present"):
            traces = [
                f"{t.get('type', 'TRACE')}: {t.get('titre') or t.get('url', '')}"
                for t in loc.get("traces_echantillon", [])[:50]
            ]
            plat["perimetre_statut"] = "INDEXE_LOCAL"
            plat["elements_locaux_detectes"] = traces
            plat["notes"] = (
                f"Détecté localement ({loc.get('total_traces_ia', 0)} traces IA/favoris) dans {loc.get('chemin_detecte', '')}."
            )
            total_local_entries += int(loc.get("total_traces_ia", 0))

    # Mettre à jour les statuts de périmètre
    drive_source_map = {"windows_drive_C": "C:\\", "windows_drive_D": "D:\\"}
    for src in merged["perimetre"]["sources_statuts"]:
        sid = src["source_id"]
        target_letter = drive_source_map.get(sid)
        if target_letter and drives_by_letter.get(target_letter, {}).get("statut") == "INDEXE_LOCAL":
            src["statut"] = "INDEXE_LOCAL"
            src["raison_ou_preuve"] = (
                f"Importé depuis local_pc_inventory.json ({local_inv.get('generated_utc', '')})."
            )
        elif sid == "historiques_ia_locaux" and local_ai_by_id:
            src["statut"] = "INDEXE_LOCAL"
            src["raison_ou_preuve"] = (
                "Traces navigateurs et agents IA locaux importées depuis collect_local_encyclopedie.ps1."
            )

    all_disks_indexed = scanned_drives_count >= len(merged["encyclopedie"]["disques_locaux_windows"])
    merged["local_pc_scan"] = "EXECUTEE" if all_disks_indexed else "PARTIELLE"
    merged["verdict_couverture"] = (
        "COMPLETE_SOUS_PREUVE" if all_disks_indexed else "PARTIELLE_AVEC_EXPORT_LOCAL"
    )
    merged["perimetre"]["statut_global"] = (
        "COMPLET_SOUS_PREUVE" if all_disks_indexed else "HYBRIDE_LOCAL_DISTANT"
    )
    merged["statistiques"]["fichiers_omega_zero_4d"] = len(
        merged["encyclopedie"]["omega_zero_4d_arborescence"]
    )
    merged["statistiques"]["entrees_locales_c_d"] = total_local_entries
    merged["collecteur_local"]["dernier_import_local"] = {
        "machine_name": local_inv.get("machine_name", ""),
        "generated_utc": local_inv.get("generated_utc", ""),
        "drives_count": len(local_inv.get("drives", [])),
        "git_repos_count": len(git_repos),
        "notable_files_count": len(notable_files),
    }
    merged["conclusion"] = (
        f"Encyclopédie fusionnée avec l'inventaire local ({local_inv.get('machine_name', 'PC')}) : "
        f"{total_local_entries} entrées locales ajoutées aux ressources GitHub et Google Drive/Docs."
    )
    return merged


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
        "5. Les **Disques Locaux Windows (`C:\\` et `D:\\`)** avec leur statut d'accessibilité et le collecteur PowerShell dédié.",
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
            f"> **Conclusion :** {doc['conclusion']}",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Construit ou fusionne le Dictionnaire & Encyclopédie Supela Ω-ZERO.")
    parser.add_argument("--root", type=Path, default=ROOT_DIR)
    parser.add_argument("--sources-dir", type=Path, default=None)
    parser.add_argument("--base-registry", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--local-inventory", type=Path, default=None)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_MD_OUT)
    args = parser.parse_args()

    if args.sources_dir is not None:
        doc = build_from_sources(args.sources_dir, args.root)
    else:
        doc = json.loads(args.base_registry.read_text(encoding="utf-8"))
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

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    for _ in range(3):
        json_text = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
        md_text = render_markdown(doc)
        prev_json = args.out_json.read_text(encoding="utf-8") if args.out_json.exists() else ""
        prev_md = args.out_md.read_text(encoding="utf-8") if args.out_md.exists() else ""
        args.out_json.write_text(json_text, encoding="utf-8")
        args.out_md.write_text(md_text, encoding="utf-8")
        if json_text == prev_json and md_text == prev_md:
            break
        updated_tree = scan_repo_tree(args.root)
        if updated_tree == doc["encyclopedie"]["omega_zero_4d_arborescence"]:
            break
        doc["encyclopedie"]["omega_zero_4d_arborescence"] = updated_tree
        doc["statistiques"]["fichiers_omega_zero_4d"] = len(updated_tree)
        Draft202012Validator(schema).validate(doc)

    print(
        json.dumps(
            {
                "status": "OK",
                "out_json": str(args.out_json),
                "out_md": str(args.out_md),
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
