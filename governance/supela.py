"""
Supela — couche de gouvernance EIR pour SUPELA.

Supela orchestre les dimensions:
- E: Energie / compute / ressources
- I: Information / RAG / connaissances
- R: Relation / routing / coordination

Le Vide intact sert de baseline neutre.
Le Zero absolu sert de circuit-breaker de reset.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class EIRState:
    energie: float
    information: float
    relation: float

    def as_dict(self) -> dict[str, float]:
        return {
            "E": self.energie,
            "I": self.information,
            "R": self.relation,
        }


class VideIntact:
    """Etat de reference neutre du systeme."""

    def __init__(self, baseline: EIRState | None = None) -> None:
        self.baseline = baseline or EIRState(0.5, 0.5, 0.5)

    def assess(self, state: Mapping[str, float]) -> dict[str, Any]:
        deviation = {
            "E": abs(state["E"] - self.baseline.energie),
            "I": abs(state["I"] - self.baseline.information),
            "R": abs(state["R"] - self.baseline.relation),
        }
        ok = all(value <= 0.3 for value in deviation.values())
        return {"ok": ok, "deviation": deviation, "baseline": self.baseline.as_dict()}


class ZeroAbsolu:
    """Reset controle du systeme en cas de desequilibre critique."""

    def trigger(self) -> dict[str, str]:
        return {"status": "reset", "mode": "zero_absolu"}


class EIRMonitor:
    """Lecture des metriques EIR depuis le contexte d'execution."""

    def snapshot(self) -> EIRState:
        return EIRState(0.5, 0.5, 0.5)


class SupelaCore:
    """Orchestrateur central Supela."""

    def __init__(self) -> None:
        self.vide_intact = VideIntact()
        self.zero_absolu = ZeroAbsolu()
        self.monitor = EIRMonitor()

    def cycle(self) -> dict[str, Any]:
        state = self.monitor.snapshot()
        coherence = self.vide_intact.assess(state.as_dict())
        if not coherence["ok"]:
            return {
                "eir": state.as_dict(),
                "coherence": coherence,
                "action": self.zero_absolu.trigger(),
            }
        return {
            "eir": state.as_dict(),
            "coherence": coherence,
            "action": {"status": "stable"},
        }

