"""
MetaOrchestrator + DissonanceResolver — SCDH v1.0
Encapsulation agnostique d'un ensemble de boîtes noires {M1, M2, … Mn}.
IS ≤ 3 — Architecture Safety OS déterministe.

Auteur : Jean-François Gadbois (Jef)
Référence : Document Maître SCDH §8 — Méta-Orchestrateur RAIM
"""

from __future__ import annotations
import statistics
from dataclasses import dataclass, field
from typing import Sequence

from orchestrator import AutoLevel, GovernanceOrchestrator

THRESHOLD_CONSENSUS  = 0.05
THRESHOLD_MODERATE   = 0.15
THRESHOLD_ELEVATED   = 0.30


@dataclass
class ModelPrediction:
    model_id: str
    score: float
    confidence: float = 1.0
    reliability_weight: float = 1.0


@dataclass
class ArbitrationResult:
    sigma_squared: float
    regime: str
    weighted_score: float
    target_level: AutoLevel
    gate_triggered: str
    log_entry: str = field(default="")


class DissonanceResolver:
    """Calcule la variance inter-modèles et détermine le régime d'arbitrage."""

    def resolve(self, predictions: Sequence[ModelPrediction]) -> ArbitrationResult:
        scores  = [p.score for p in predictions]
        sigma2  = statistics.variance(scores) if len(scores) > 1 else 0.0
        w_score = self._weighted_score(predictions)
        regime, gate, level = self._classify(sigma2)
        log = f"ARB σ²={sigma2:.4f} → {regime} | weighted_score={w_score:.3f} | gate={gate} | level={level.value}"
        return ArbitrationResult(sigma2, regime, w_score, level, gate, log)

    @staticmethod
    def _weighted_score(predictions: Sequence[ModelPrediction]) -> float:
        total_w = sum(p.reliability_weight * p.confidence for p in predictions)
        if total_w == 0:
            return 0.0
        return sum(p.score * p.reliability_weight * p.confidence for p in predictions) / total_w

    @staticmethod
    def _classify(sigma2: float) -> tuple[str, str, AutoLevel]:
        if sigma2 < THRESHOLD_CONSENSUS:
            return "CONSENSUS",  "V1", AutoLevel.N3_HIGH
        if sigma2 < THRESHOLD_MODERATE:
            return "MODERATE",   "V2", AutoLevel.N2_PARTIAL
        if sigma2 < THRESHOLD_ELEVATED:
            return "ELEVATED",   "V3", AutoLevel.N1_ASSISTED
        return     "CRITICAL",   "V4", AutoLevel.N0_MANUAL


class MetaOrchestrator:
    """Enveloppe déterministe et agnostique pour un ensemble de modèles IA."""

    def __init__(self) -> None:
        self._orchestrator  = GovernanceOrchestrator()
        self._resolver      = DissonanceResolver()
        self._history: list[ArbitrationResult] = []

    def arbitrate(self, predictions: Sequence[ModelPrediction]) -> ArbitrationResult:
        result = self._resolver.resolve(predictions)
        self._history.append(result)
        if result.gate_triggered == "V4":
            self._orchestrator.trigger_v4_kill_switch()
        return result

    @property
    def current_level(self) -> AutoLevel:
        return self._orchestrator.current_level

    @property
    def history(self) -> list[ArbitrationResult]:
        return list(self._history)
