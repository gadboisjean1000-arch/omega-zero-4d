"""
Supela — Cadre de co-organisation EIR (Énergie · Information · Relation)
Auteur : Jean-François Gadbois | Cadre Supela, Montréal QC

Orchestrateur central de gouvernance : lit l'état EIR, détecte les déséquilibres,
rééquilibre via les modules existants, et teste la cohérence au Vide intact.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class EIRState:
    """État de la triade Énergie-Information-Relation."""
    energie: float
    information: float
    relation: float

    def as_dict(self) -> dict[str, float]:
        return {
            "E": self.energie,
            "I": self.information,
            "R": self.relation,
        }

    @property
    def is_balanced(self) -> bool:
        """Vrai si les trois dimensions sont proches de l'équilibre."""
        return all(0.3 < v < 0.7 for v in [self.energie, self.information, self.relation])


class VideIntact:
    """
    Le Vide intact : état de référence neutre du système.
    Aucune excitation ne doit le consommer ou le détruire.
    Chaque cycle EIR est testé contre cette baseline.
    """
    BASELINE = {"E": 0.5, "I": 0.5, "R": 0.5}
    TOLERANCE = 0.3

    def test(self, eir_state: dict[str, float]) -> dict[str, Any]:
        """Teste la cohérence d'un état EIR contre le Vide intact."""
        deviation = {k: abs(eir_state[k] - self.BASELINE[k]) for k in "EIR"}
        ok = all(d <= self.TOLERANCE for d in deviation.values())
        return {
            "ok": ok,
            "deviation": deviation,
            "baseline": self.BASELINE,
        }


class ZeroAbsolu:
    """
    Le Zéro absolu : limite asymptotique irréductible.
    Inatteignable (comme 0 K en physique), mais point de reset
    vers lequel le système revient en cas de déséquilibre critique.
    """
    def trigger(self) -> dict[str, str]:
        """Reset contrôlé : retour à l'état Vide intact sans destruction."""
        import logging
        logging.warning("[SUPELA] Zéro absolu déclenché — reset système")
        return {"status": "reset", "mode": "zero_absolu", "target": "vide_intact"}


class EIRMonitor:
    """
    Surveillance en temps réel des métriques EIR.
    Lit l'état de santé de chaque dimension.
    """
    def __init__(self, baseline: EIRState | None = None) -> None:
        self.baseline = baseline or EIRState(0.5, 0.5, 0.5)
        self.history: list[EIRState] = []

    def snapshot(self) -> EIRState:
        """Capture l'état courant des trois dimensions."""
        # À connecter aux métriques réelles du système
        state = EIRState(0.5, 0.5, 0.5)
        self.history.append(state)
        return state

    def get_trend(self, window: int = 10) -> dict[str, float]:
        """Tendance récente pour déterminer la dérive."""
        if not self.history or len(self.history) < 2:
            return {}
        recent = self.history[-window:]
        return {
            "E_trend": recent[-1].energie - recent[0].energie,
            "I_trend": recent[-1].information - recent[0].information,
            "R_trend": recent[-1].relation - recent[0].relation,
        }


class SupelaCore:
    """
    Gouverneur central Supela.
    Orchestre la Triade EIR selon les principes de co-organisation.
    """

    def __init__(self) -> None:
        self.vide = VideIntact()
        self.zero = ZeroAbsolu()
        self.monitor = EIRMonitor()
        self.reset_count = 0

    def cycle(self) -> dict[str, Any]:
        """
        Un cycle Supela complet :
        1. Mesurer l'état EIR
        2. Tester la cohérence au Vide intact
        3. Rééquilibrer si nécessaire
        4. Déclencher reset si critique
        """
        eir_state = self.monitor.snapshot()
        coherence = self.vide.test(eir_state.as_dict())

        result = {
            "eir": eir_state.as_dict(),
            "coherence": coherence,
            "action": {"status": "stable"},
        }

        if not coherence["ok"]:
            action = self._rebalance(eir_state)
            result["action"] = action
            if action.get("mode") == "reset":
                self.reset_count += 1

        return result

    def _rebalance(self, state: EIRState) -> dict[str, Any]:
        """
        Détecte la dimension déficiente et déclenche le rééquilibrage.
        """
        deviations = {
            "E": abs(state.energie - self.vide.BASELINE["E"]),
            "I": abs(state.information - self.vide.BASELINE["I"]),
            "R": abs(state.relation - self.vide.BASELINE["R"]),
        }

        max_dim = max(deviations, key=deviations.get)

        if deviations[max_dim] > 0.5:
            # Déséquilibre critique → reset
            return self.zero.trigger()

        # Rééquilibrage léger
        if max_dim == "E":
            return {"status": "rebalance", "target": "energie"}
        elif max_dim == "I":
            return {"status": "rebalance", "target": "information"}
        else:
            return {"status": "rebalance", "target": "relation"}

    def get_status(self) -> dict[str, Any]:
        """Retourne l'état courant du système Supela."""
        return {
            "resets_triggered": self.reset_count,
            "vide_baseline": self.vide.BASELINE,
            "monitor_history_len": len(self.monitor.history),
        }
