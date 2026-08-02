"""
Suite de Tests Unitaires — Invariants de Gouvernance SCDH
17 tests couvrant Annexes A / B / C / D + MetaOrchestrator

Résultats certifiés : 17/17 PASS — Gate G0 Franchie
PV-CVEA-2026-001 — 28 juillet 2026

Auteur : Jean-François Gadbois (Jef)
"""

import ast
import time
import unittest

from orchestrator import AutoLevel, Decision, Gate, GovernanceOrchestrator
from meta_orchestrator import (
    DissonanceResolver, MetaOrchestrator, ModelPrediction,
)


# ── Analyseur IS (AST — Annexe D) ──────────────────────────────────────────

class _ComplexityVisitor(ast.NodeVisitor):
    def __init__(self):
        self.complexity = 1
    def visit_If(self, n):        self.complexity += 1; self.generic_visit(n)
    def visit_For(self, n):       self.complexity += 1; self.generic_visit(n)
    def visit_While(self, n):     self.complexity += 1; self.generic_visit(n)
    def visit_ExceptHandler(self, n): self.complexity += 1; self.generic_visit(n)


def _is_score(source: str) -> int:
    v = _ComplexityVisitor(); v.visit(ast.parse(source))
    cc = v.complexity
    if cc <= 3:  return 0
    if cc <= 5:  return 2
    if cc <= 10: return 3
    if cc <= 15: return 4
    return 5


# ── Annexe A — Autonomie (3 tests) ─────────────────────────────────────────

class TestAnnexeA_Autonomie(unittest.TestCase):

    def test_A01_is4_floors_to_N1(self):
        """IS=4 plafonne à N1 (sur-ingénierie bloquante)."""
        o = GovernanceOrchestrator(AutoLevel.N3_HIGH)
        self.assertEqual(o.evaluate(Decision(AutoLevel.N3_HIGH, Gate.APPROVED, 0.05, 4)), AutoLevel.N1_ASSISTED)

    def test_A02_nominal_path_N3(self):
        """Scénario nominal (IS=2, I_B=0.05, APPROVED) → N3_HIGH."""
        o = GovernanceOrchestrator(AutoLevel.N2_PARTIAL)
        self.assertEqual(o.evaluate(Decision(AutoLevel.N3_HIGH, Gate.APPROVED, 0.05, 2)), AutoLevel.N3_HIGH)

    def test_A03_rejected_gate_floors_to_N1(self):
        """REJECTED gate → N1_ASSISTED peu importe IS."""
        o = GovernanceOrchestrator(AutoLevel.N3_HIGH)
        self.assertEqual(o.evaluate(Decision(AutoLevel.N3_HIGH, Gate.REJECTED, 0.03, 1)), AutoLevel.N1_ASSISTED)


# ── Annexe B — Kill Switch V4 (5 tests) ────────────────────────────────────

class TestAnnexeB_KillSwitch(unittest.TestCase):

    def test_B01_v4_reaches_N0_under_100ms(self):
        """V4 → N0_MANUAL en < 100 ms (SLA contractuel)."""
        o = GovernanceOrchestrator(AutoLevel.N3_HIGH)
        t0 = time.perf_counter()
        o.trigger_v4_kill_switch()
        elapsed = (time.perf_counter() - t0) * 1000
        self.assertEqual(o.current_level, AutoLevel.N0_MANUAL)
        self.assertLess(elapsed, 100.0)

    def test_B02_kill_switch_flag_set(self):
        """Flag kill_switch_active = True après V4."""
        o = GovernanceOrchestrator()
        o.trigger_v4_kill_switch()
        self.assertTrue(o.kill_switch_active)

    def test_B03_reactivation_requires_quorum(self):
        """Réactivation CVEA : 3 votes OK → N1 ; 2 votes → refus."""
        o = GovernanceOrchestrator()
        o.trigger_v4_kill_switch()
        self.assertFalse(o.reactivate(2))
        self.assertTrue(o.reactivate(3))
        self.assertEqual(o.current_level, AutoLevel.N1_ASSISTED)

    def test_B04_emergency_gate_triggers_v4(self):
        """Gate EMERGENCY via evaluate() → N0_MANUAL."""
        o = GovernanceOrchestrator(AutoLevel.N3_HIGH)
        self.assertEqual(o.evaluate(Decision(AutoLevel.N3_HIGH, Gate.EMERGENCY, 0.01, 1)), AutoLevel.N0_MANUAL)

    def test_B05_fail_secure_unknown_bias(self):
        """I_B > 0.25 → N0_MANUAL (fail-secure)."""
        o = GovernanceOrchestrator(AutoLevel.N3_HIGH)
        self.assertEqual(o.evaluate(Decision(AutoLevel.N3_HIGH, Gate.APPROVED, 0.30, 1)), AutoLevel.N0_MANUAL)


# ── Annexe C — Biais (4 tests) ─────────────────────────────────────────────

class TestAnnexeC_Biais(unittest.TestCase):

    def test_C01_high_bias_N0(self):
        o = GovernanceOrchestrator()
        self.assertEqual(o.evaluate(Decision(AutoLevel.N3_HIGH, Gate.APPROVED, 0.26, 2)), AutoLevel.N0_MANUAL)

    def test_C02_moderate_bias_N1(self):
        o = GovernanceOrchestrator()
        self.assertEqual(o.evaluate(Decision(AutoLevel.N3_HIGH, Gate.APPROVED, 0.15, 2)), AutoLevel.N1_ASSISTED)

    def test_C03_nominal_bias_N3(self):
        o = GovernanceOrchestrator()
        self.assertEqual(o.evaluate(Decision(AutoLevel.N3_HIGH, Gate.APPROVED, 0.08, 2)), AutoLevel.N3_HIGH)

    def test_C04_exact_boundary_010(self):
        """Borne exacte I_B=0.10 → N3 (off-by-one absent)."""
        o = GovernanceOrchestrator()
        self.assertEqual(o.evaluate(Decision(AutoLevel.N3_HIGH, Gate.APPROVED, 0.10, 2)), AutoLevel.N3_HIGH)


# ── Annexe D — Indice de Simplicité (3 tests) ──────────────────────────────

class TestAnnexeD_Simplicite(unittest.TestCase):

    def test_D01_simple_code_is_le3(self):
        code = """
def process(data, bias_score):
    if bias_score > 0.25:
        return "REJECT"
    elif bias_score > 0.10:
        return "WARN"
    for item in data:
        if item:
            return "REVIEW"
    return "ACCEPT"
"""
        self.assertLessEqual(_is_score(code), 3)

    def test_D02_overengineered_code_is_ge4(self):
        code = "\n".join(["def f(x):"] + [f"    if x == {i}: pass" for i in range(12)] + ["    return x"])
        self.assertGreaterEqual(_is_score(code), 4)

    def test_D03_orchestrator_self_conformity(self):
        """orchestrator.py auto-évalué : IS = 3 (CC=9, conforme borne sup.)."""
        import pathlib
        src = (pathlib.Path(__file__).parent / "orchestrator.py").read_text(encoding="utf-8")
        self.assertLessEqual(_is_score(src), 3)


# ── MetaOrchestrator — DissonanceResolver (2 tests) ────────────────────────

class TestMetaOrchestrator(unittest.TestCase):

    def _preds(self, scores):
        return [ModelPrediction(f"M{i+1}", s) for i, s in enumerate(scores)]

    def test_M01_consensus(self):
        """σ² < 0.05 → CONSENSUS → V1."""
        r = DissonanceResolver().resolve(self._preds([0.80, 0.82, 0.81]))
        self.assertEqual(r.regime, "CONSENSUS")
        self.assertEqual(r.gate_triggered, "V1")

    def test_M02_critical_triggers_V4(self):
        """σ² ≥ 0.30 → CRITICAL → V4 → N0_MANUAL. ([0.05, 0.95] → σ²=0.405)"""
        meta = MetaOrchestrator()
        r = meta.arbitrate(self._preds([0.05, 0.95]))
        self.assertGreaterEqual(r.sigma_squared, 0.30)
        self.assertEqual(r.gate_triggered, "V4")
        self.assertEqual(meta.current_level, AutoLevel.N0_MANUAL)


if __name__ == "__main__":
    unittest.main(verbosity=2)
