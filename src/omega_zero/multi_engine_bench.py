"""Banc multi-moteurs Supela (supela-multi-engine-bench/1).

Règles fondamentales :
1. Le banc ne vote pas : trois moteurs disant VRAI ne constituent pas une preuve.
2. La convergence augmente l'information disponible, jamais automatiquement la vérité.
3. Une divergence est une donnée produite par le banc, conservée sans effacement.
4. Supela est éprouvé au même titre que Copilot, toute autre IA ou un moteur formel :
   le banc peut conclure SUPELA_EN_DÉFAUT.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MultiEngineBenchError(ValueError):
    """Erreur levée lorsqu'une exécution moteur viole le contrat fail-closed du banc."""


class EngineResult(str, Enum):
    VRAI = "VRAI"
    FAUX = "FAUX"
    INDETERMINE = "INDÉTERMINÉ"
    ERREUR = "ERREUR"


class EngineRecordStatus(str, Enum):
    CANDIDAT = "CANDIDAT"
    PROUVE = "PROUVE"
    REFUTE = "REFUTE"
    INDETERMINE = "INDETERMINE"
    EN_DEFAUT = "EN_DEFAUT"


class BenchOutcome(str, Enum):
    CONVERGENCE = "CONVERGENCE"
    DIVERGENCE = "DIVERGENCE"
    INDETERMINE = "INDÉTERMINÉ"


class BenchVerdict(str, Enum):
    CONVERGENCE_SANS_PREUVE = "CONVERGENCE_SANS_PREUVE"
    CONVERGENCE_ETAYEE_A_RATIFIER = "CONVERGENCE_ETAYEE_A_RATIFIER"
    DIVERGENCE_CONSERVEE = "DIVERGENCE_CONSERVEE"
    INDETERMINE_OUVERT = "INDETERMINE_OUVERT"
    SUPELA_EN_DEFAUT = "SUPELA_EN_DEFAUT"


class TruthLevel(str, Enum):
    NON_ETABLI = "NON_ÉTABLI"
    PARTIELLEMENT_ETABLI = "PARTIELLEMENT_ÉTABLI"
    ETABLI_DANS_LE_PERIMETRE = "ÉTABLI_DANS_LE_PÉRIMÈTRE"
    CONTRADICTOIRE = "CONTRADICTOIRE"
    INDETERMINE = "INDÉTERMINÉ"


@dataclass(frozen=True)
class EngineRunRecord:
    """Enregistrement minimal obligatoire (10 champs + métadonnées probatoires)."""

    objet: str
    moteur: str
    version: str
    referentiel: str
    premisses: tuple[str, ...]
    methode: str
    resultat: EngineResult
    preuve_fournie: str
    contradictions: tuple[str, ...] = field(default_factory=tuple)
    statut: EngineRecordStatus = EngineRecordStatus.CANDIDAT
    preuve_verifiee: bool = False
    est_supela: bool | None = None
    auto_promotion_tentee: bool = False

    def __post_init__(self) -> None:
        for field_name, val in (
            ("objet", self.objet),
            ("moteur", self.moteur),
            ("version", self.version),
            ("referentiel", self.referentiel),
            ("methode", self.methode),
        ):
            if not isinstance(val, str) or not val.strip():
                raise MultiEngineBenchError(f"Champ obligatoire vide ou invalide: {field_name}")

        if self.preuve_verifiee and not self.preuve_fournie.strip():
            raise MultiEngineBenchError(
                f"Moteur '{self.moteur}': preuve_verifiee=True exige une preuve_fournie non vide."
            )

        if self.statut == EngineRecordStatus.PROUVE and not self.preuve_verifiee:
            raise MultiEngineBenchError(
                f"Moteur '{self.moteur}': statut PROUVE interdit sans preuve_verifiee=True."
            )

    @property
    def is_supela_engine(self) -> bool:
        if self.est_supela is not None:
            return self.est_supela
        return "supela" in self.moteur.lower()

    def to_dict(self) -> dict[str, Any]:
        return {
            "objet": self.objet,
            "moteur": self.moteur,
            "version": self.version,
            "referentiel": self.referentiel,
            "premisses": list(self.premisses),
            "methode": self.methode,
            "resultat": self.resultat.value,
            "preuve_fournie": self.preuve_fournie,
            "preuve_verifiee": self.preuve_verifiee,
            "contradictions": list(self.contradictions),
            "statut": self.statut.value,
            "est_supela": self.is_supela_engine,
            "auto_promotion_tentee": self.auto_promotion_tentee,
        }


@dataclass(frozen=True)
class MultiEngineBenchReport:
    """Rapport déterministe produit par le Banc multi-moteurs Supela."""

    objet: str
    outcome: BenchOutcome
    supela_en_defaut: bool
    verdict_banc: BenchVerdict
    statut_verite: TruthLevel
    promotion_autorisee: bool
    preuves_verifiees: tuple[dict[str, str], ...]
    referentiels: tuple[str, ...]
    contradictions_consolidees: tuple[str, ...]
    moteurs: tuple[EngineRunRecord, ...]
    report_sha256: str
    vote_interdit: bool = True
    convergence_n_est_pas_preuve: bool = True
    ratification_humaine_requise: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "supela-multi-engine-bench/1",
            "objet": self.objet,
            "vote_interdit": self.vote_interdit,
            "convergence_n_est_pas_preuve": self.convergence_n_est_pas_preuve,
            "outcome": self.outcome.value,
            "supela_en_defaut": self.supela_en_defaut,
            "verdict_banc": self.verdict_banc.value,
            "statut_verite": self.statut_verite.value,
            "promotion_autorisee": self.promotion_autorisee,
            "ratification_humaine_requise": self.ratification_humaine_requise,
            "preuves_verifiees": list(self.preuves_verifiees),
            "referentiels": list(self.referentiels),
            "contradictions_consolidees": list(self.contradictions_consolidees),
            "moteurs": [m.to_dict() for m in self.moteurs],
            "report_sha256": self.report_sha256,
        }


class SupelaMultiEngineBench:
    """Évaluateur déterministe multi-moteurs sans vote majoritaire."""

    @staticmethod
    def evaluate(records: list[EngineRunRecord] | tuple[EngineRunRecord, ...]) -> MultiEngineBenchReport:
        if len(records) < 2:
            raise MultiEngineBenchError("Le banc multi-moteurs exige au moins 2 moteurs distincts.")

        objet = records[0].objet
        seen_engines: set[tuple[str, str]] = set()
        for rec in records:
            if rec.objet != objet:
                raise MultiEngineBenchError(
                    f"Objet discordant '{rec.objet}' != '{objet}' : le banc exige le même objet."
                )
            key = (rec.moteur.strip().lower(), rec.version.strip().lower())
            if key in seen_engines:
                raise MultiEngineBenchError(f"Moteur/version dupliqué dans le banc: {rec.moteur}@{rec.version}")
            seen_engines.add(key)

        results_set = {r.resultat for r in records}
        if results_set == {EngineResult.VRAI} or results_set == {EngineResult.FAUX}:
            outcome = BenchOutcome.CONVERGENCE
        elif len(results_set) == 1 and EngineResult.INDETERMINE in results_set:
            outcome = BenchOutcome.INDETERMINE
        elif len(results_set) > 1 or EngineResult.ERREUR in results_set:
            outcome = BenchOutcome.DIVERGENCE
        else:
            outcome = BenchOutcome.INDETERMINE

        preuves_verifiees = tuple(
            {
                "moteur": r.moteur,
                "referentiel": r.referentiel,
                "preuve_fournie": r.preuve_fournie,
            }
            for r in records
            if r.preuve_verifiee
        )

        referentiels = tuple(dict.fromkeys(r.referentiel for r in records))
        contradictions: list[str] = []
        for r in records:
            for c in r.contradictions:
                if c not in contradictions:
                    contradictions.append(c)

        if outcome == BenchOutcome.DIVERGENCE:
            summary = "Divergence inter-moteurs observée: " + ", ".join(
                f"{r.moteur}={r.resultat.value}" for r in records
            )
            if summary not in contradictions:
                contradictions.append(summary)

        # Détection symétrique : Supela n'est jamais juge de sa propre victoire
        supela_records = [r for r in records if r.is_supela_engine]
        proven_true_by_other = any(
            not r.is_supela_engine and r.preuve_verifiee and r.resultat == EngineResult.VRAI for r in records
        )
        proven_false_by_other = any(
            not r.is_supela_engine and r.preuve_verifiee and r.resultat == EngineResult.FAUX for r in records
        )

        supela_en_defaut = False
        for sr in supela_records:
            if sr.statut == EngineRecordStatus.EN_DEFAUT or sr.resultat == EngineResult.ERREUR:
                supela_en_defaut = True
                contradictions.append(
                    f"SUPELA_EN_DÉFAUT: moteur '{sr.moteur}' en erreur ou statut EN_DEFAUT."
                )
            elif sr.auto_promotion_tentee and not sr.preuve_verifiee:
                supela_en_defaut = True
                contradictions.append(
                    f"SUPELA_EN_DÉFAUT: tentative d'auto-promotion sans preuve vérifiée par '{sr.moteur}'."
                )
            elif sr.resultat == EngineResult.VRAI and proven_false_by_other and not sr.preuve_verifiee:
                supela_en_defaut = True
                contradictions.append(
                    f"SUPELA_EN_DÉFAUT: '{sr.moteur}' affirme VRAI sans preuve face à une réfutation prouvée."
                )
            elif sr.resultat in {EngineResult.FAUX, EngineResult.INDETERMINE} and proven_true_by_other:
                supela_en_defaut = True
                contradictions.append(
                    f"SUPELA_EN_DÉFAUT: '{sr.moteur}' retourne {sr.resultat.value} face à une preuve vérifiée."
                )

        # Détermination du verdict sans jamais voter par majorité
        has_proven_true = any(r.preuve_verifiee and r.resultat == EngineResult.VRAI for r in records)
        has_proven_false = any(r.preuve_verifiee and r.resultat == EngineResult.FAUX for r in records)
        contradictory_proofs = has_proven_true and has_proven_false

        if supela_en_defaut:
            verdict = BenchVerdict.SUPELA_EN_DEFAUT
            statut_verite = TruthLevel.CONTRADICTOIRE if outcome == BenchOutcome.DIVERGENCE else TruthLevel.NON_ETABLI
            promotion_autorisee = False
        elif outcome == BenchOutcome.CONVERGENCE and not preuves_verifiees:
            # Règle essentielle : 3 moteurs disant VRAI sans preuve != preuve
            verdict = BenchVerdict.CONVERGENCE_SANS_PREUVE
            statut_verite = TruthLevel.NON_ETABLI
            promotion_autorisee = False
        elif outcome == BenchOutcome.CONVERGENCE and preuves_verifiees and not contradictions:
            verdict = BenchVerdict.CONVERGENCE_ETAYEE_A_RATIFIER
            statut_verite = TruthLevel.ETABLI_DANS_LE_PERIMETRE
            promotion_autorisee = True
        elif outcome == BenchOutcome.DIVERGENCE:
            verdict = BenchVerdict.DIVERGENCE_CONSERVEE
            statut_verite = (
                TruthLevel.CONTRADICTOIRE
                if contradictory_proofs or contradictions
                else TruthLevel.PARTIELLEMENT_ETABLI
            )
            promotion_autorisee = False
        else:
            verdict = BenchVerdict.INDETERMINE_OUVERT
            statut_verite = TruthLevel.INDETERMINE
            promotion_autorisee = False

        payload_for_hash = {
            "schema": "supela-multi-engine-bench/1",
            "objet": objet,
            "vote_interdit": True,
            "convergence_n_est_pas_preuve": True,
            "outcome": outcome.value,
            "supela_en_defaut": supela_en_defaut,
            "verdict_banc": verdict.value,
            "statut_verite": statut_verite.value,
            "promotion_autorisee": promotion_autorisee,
            "ratification_humaine_requise": True,
            "preuves_verifiees": list(preuves_verifiees),
            "referentiels": list(referentiels),
            "contradictions_consolidees": contradictions,
            "moteurs": [r.to_dict() for r in records],
        }
        canonical = json.dumps(payload_for_hash, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

        return MultiEngineBenchReport(
            objet=objet,
            outcome=outcome,
            supela_en_defaut=supela_en_defaut,
            verdict_banc=verdict,
            statut_verite=statut_verite,
            promotion_autorisee=promotion_autorisee,
            preuves_verifiees=preuves_verifiees,
            referentiels=referentiels,
            contradictions_consolidees=tuple(contradictions),
            moteurs=tuple(records),
            report_sha256=digest,
        )
