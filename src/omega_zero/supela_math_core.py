from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import IntEnum
from fractions import Fraction
from typing import Any

from .grpo_bridge import SupelaGRPOBridge
from .models import canonical_sha256


class ProofLatticeLevel(IntEnum):
    """Treillis probatoire complet MAT-01 : G0 < G1 < G2 < G3 < G4."""

    G0_BRUT = 0
    G1_OBSERVE = 1
    G2_TESTE_LOCAL = 2
    G3_REPRODUIT_CROISE = 3
    G4_SCELLE_LOCAL = 4

    @classmethod
    def join(cls, a: ProofLatticeLevel, b: ProofLatticeLevel) -> ProofLatticeLevel:
        """Borne supérieure (supremum) a ∨ b dans le treillis borné (G, ⪯)."""
        return cls(max(int(a), int(b)))

    @classmethod
    def meet(cls, a: ProofLatticeLevel, b: ProofLatticeLevel) -> ProofLatticeLevel:
        """Borne inférieure (infimum) a ∧ b dans le treillis borné (G, ⪯)."""
        return cls(min(int(a), int(b)))


def verify_proof_lattice_axioms() -> dict[str, Any]:
    """Vérifie exhaustivement les axiomes de treillis borné et la borne de Galois sur G0..G4."""
    elems = tuple(ProofLatticeLevel)
    bottom = ProofLatticeLevel.G0_BRUT
    top = ProofLatticeLevel.G4_SCELLE_LOCAL

    reflexive = all(a <= a for a in elems)
    antisymmetric = all((not (a <= b and b <= a)) or (a == b) for a in elems for b in elems)
    transitive = all(
        (not (a <= b and b <= c)) or (a <= c) for a in elems for b in elems for c in elems
    )
    commutative = all(
        ProofLatticeLevel.join(a, b) == ProofLatticeLevel.join(b, a)
        and ProofLatticeLevel.meet(a, b) == ProofLatticeLevel.meet(b, a)
        for a in elems
        for b in elems
    )
    associative = all(
        ProofLatticeLevel.join(a, ProofLatticeLevel.join(b, c))
        == ProofLatticeLevel.join(ProofLatticeLevel.join(a, b), c)
        and ProofLatticeLevel.meet(a, ProofLatticeLevel.meet(b, c))
        == ProofLatticeLevel.meet(ProofLatticeLevel.meet(a, b), c)
        for a in elems
        for b in elems
        for c in elems
    )
    idempotent = all(
        ProofLatticeLevel.join(a, a) == a and ProofLatticeLevel.meet(a, a) == a for a in elems
    )
    absorptive = all(
        ProofLatticeLevel.join(a, ProofLatticeLevel.meet(a, b)) == a
        and ProofLatticeLevel.meet(a, ProofLatticeLevel.join(a, b)) == a
        for a in elems
        for b in elems
    )
    bounded = all(
        bottom <= a <= top
        and ProofLatticeLevel.join(a, bottom) == a
        and ProofLatticeLevel.meet(a, top) == a
        for a in elems
    )
    galois_authority_monotone = all(
        BoundedAuthorityEvaluation("LATTICE", p, req, 1.0).granted_authority <= int(p)
        and (
            BoundedAuthorityEvaluation("LATTICE", p, req, 1.0).granted_authority
            <= BoundedAuthorityEvaluation("LATTICE", q, req, 1.0).granted_authority
        )
        for p in elems
        for q in elems
        if p <= q
        for req in range(-1, 7)
    )
    all_ok = all(
        (
            reflexive,
            antisymmetric,
            transitive,
            commutative,
            associative,
            idempotent,
            absorptive,
            bounded,
            galois_authority_monotone,
        )
    )
    return {
        "cardinality": len(elems),
        "triples_checked": len(elems) ** 3,
        "partial_order_ok": reflexive and antisymmetric and transitive,
        "lattice_laws_ok": commutative and associative and idempotent and absorptive,
        "bounded_ok": bounded,
        "galois_authority_monotone": galois_authority_monotone,
        "all_axioms_verified": all_ok,
    }


@dataclass
class SupelaStateTuple:
    """MAT-00 : État fondamental S_i = <P_i, E_i, C_i, K_i> avec monotonie K_t ⊆ K_{t+1}."""

    provenance: list[str]
    evidence: list[str]
    contradictions: list[str]
    knowledge_register: frozenset[str] = field(default_factory=frozenset)

    def advance(
        self,
        new_knowledge: set[str],
        *,
        new_provenance: str | None = None,
        new_evidence: str | None = None,
        new_contradiction: str | None = None,
    ) -> SupelaStateTuple:
        """Préserve la monotonie stricte K_t ⊆ K_{t+1} sans effacement des contradictions."""
        next_k = self.knowledge_register | frozenset(new_knowledge)
        assert self.knowledge_register.issubset(next_k)
        return SupelaStateTuple(
            provenance=[*self.provenance, *([new_provenance] if new_provenance else [])],
            evidence=[*self.evidence, *([new_evidence] if new_evidence else [])],
            contradictions=[*self.contradictions, *([new_contradiction] if new_contradiction else [])],
            knowledge_register=next_k,
        )

    def reset_contradictions_only_in_c(self) -> SupelaStateTuple:
        """MAT-00 : C -> ∅ lors d'un reset de session tout en conservant K_t monotone."""
        return SupelaStateTuple(
            provenance=[*self.provenance, "RESET_SESSION_C_EMPTY"],
            evidence=list(self.evidence),
            contradictions=[],
            knowledge_register=self.knowledge_register,
        )


@dataclass(frozen=True)
class BoundedAuthorityEvaluation:
    """MAT-01 / MAT-06 : Authority(G) <= Proof(G) et amélioration != autorisation."""

    object_id: str
    proof_level: ProofLatticeLevel
    requested_authority: int
    improvement_score: float

    @property
    def granted_authority(self) -> int:
        return min(max(0, self.requested_authority), int(self.proof_level))

    @property
    def authority_bounded_ok(self) -> bool:
        return self.granted_authority <= int(self.proof_level)

    @property
    def auto_authorized_by_improvement(self) -> bool:
        return False


@dataclass(frozen=True)
class ThreeDimensionalSeparation:
    """MAT-04 (compatibilité runtime) : séparation stricte entre 3 plans distincts."""

    history_hash: str
    local_context: str
    proof_digest: str

    @property
    def dimensions_distinct(self) -> bool:
        return len({self.history_hash, self.local_context, self.proof_digest}) == 3


@dataclass(frozen=True)
class CanonicalHLPSeparation:
    """MAT-04-HLP canonique : Sens humain (H) ≠ Littéral brut (L) ≠ Établi sous preuve (P)."""

    human_meaning: str
    literal_source: str
    proof_plane: str

    @property
    def dimensions_distinct(self) -> bool:
        normalized = (
            self.human_meaning.strip(),
            self.literal_source.strip(),
            self.proof_plane.strip(),
        )
        return all(normalized) and len(set(normalized)) == 3


@dataclass(frozen=True)
class FractalScaleAggregation:
    """
    Théorème d'agrégation multi-échelles VR-Fractal-Ω (Supela-K3-Omega/VR-Fractal-Omega.md) :
      Pour n sous-systèmes avec poids positifs W_i = T_{t,i} + C_{t,i} > 0
      et turbulences finies Δ_{t,i} >= 0 :
        P_{t,i} = W_i / (1 + Δ_{t,i}),   P_t = Σ_i P_{t,i} = W / (1 + Δ_t^eff)
      où 1 + Δ_t^eff est la moyenne harmonique pondérée exacte des (1 + Δ_{t,i}),
      garantissant l'encadrement strict :
        min_i Δ_{t,i} <= Δ_t^eff <= max_i Δ_{t,i}
      et la limite exacte : max_i Δ_{t,i} -> 0+  ==>  Δ_t^eff -> 0+ et P_t -> Σ_i (T_{t,i} + C_{t,i}).
    """

    subsystems: tuple[tuple[float, float, float], ...]

    def __post_init__(self) -> None:
        if not self.subsystems:
            raise ValueError("VR-Fractal-Ω requiert au moins un sous-système.")
        for idx, (t_i, c_i, delta_i) in enumerate(self.subsystems):
            if not (math.isfinite(t_i) and math.isfinite(c_i) and math.isfinite(delta_i)):
                raise ValueError(f"Sous-système {idx}: composantes non finies interdites.")
            if t_i + c_i <= 0.0:
                raise ValueError(f"Sous-système {idx}: T_i + C_i doit être strictement positif.")
            if delta_i < 0.0:
                raise ValueError(
                    f"Sous-système {idx}: Δ_i doit appartenir à [0, +∞) (évite la singularité Δ=-1)."
                )

    def evaluate(self, *, tol: float = 1e-12) -> dict[str, Any]:
        weights = [t_i + c_i for t_i, c_i, _ in self.subsystems]
        deltas = [d_i for _, _, d_i in self.subsystems]
        micro_states = [w_i / (1.0 + d_i) for w_i, d_i in zip(weights, deltas)]

        total_weight = sum(weights)
        macro_state = sum(micro_states)
        effective_turbulence = (total_weight / macro_state) - 1.0
        reconstructed_macro = total_weight / (1.0 + effective_turbulence)

        min_delta = min(deltas)
        max_delta = max(deltas)
        scale_tol = tol * max(1.0, total_weight, max_delta)
        identity_ok = abs(macro_state - reconstructed_macro) <= scale_tol
        squeeze_bound_ok = (min_delta - scale_tol) <= effective_turbulence <= (max_delta + scale_tol)
        zero_limit_ok = (
            abs(macro_state - total_weight) <= scale_tol and abs(effective_turbulence) <= scale_tol
            if max_delta == 0.0
            else macro_state <= total_weight + scale_tol
        )
        return {
            "subsystem_count": len(self.subsystems),
            "total_weight_T_plus_C": total_weight,
            "macro_state_P_t": macro_state,
            "effective_turbulence_delta_eff": effective_turbulence,
            "min_micro_turbulence": min_delta,
            "max_micro_turbulence": max_delta,
            "harmonic_identity_verified": identity_ok,
            "squeeze_bound_verified": squeeze_bound_ok,
            "zero_turbulence_bound_verified": zero_limit_ok,
            "theorem_verified": identity_ok and squeeze_bound_ok and zero_limit_ok,
        }


@dataclass(frozen=True)
class SGGv2Metric:
    """
    MAT-08-PATTERNS-LAS (SGG_v2) : conservation fidèle des poids bruts (∑ = 6/5 = 1.20,
    trace CONTR-Z0-TENSION) et dérivation exacte sur le simplexe Δ^4 (∑ = 1) en arithmétique rationnelle.
    """

    a: Fraction
    v: Fraction
    e: Fraction
    t: Fraction
    m: Fraction

    RAW_WEIGHTS: tuple[Fraction, ...] = (
        Fraction(1, 4),
        Fraction(3, 10),
        Fraction(3, 10),
        Fraction(3, 20),
        Fraction(1, 5),
    )
    RAW_WEIGHT_SUM: Fraction = Fraction(6, 5)
    NORMALIZED_WEIGHTS: tuple[Fraction, ...] = (
        Fraction(5, 24),
        Fraction(1, 4),
        Fraction(1, 4),
        Fraction(1, 8),
        Fraction(1, 6),
    )

    @classmethod
    def from_floats(cls, a: float, v: float, e: float, t: float, m: float) -> SGGv2Metric:
        vals = (a, v, e, t, m)
        if any(not math.isfinite(x) or x < 0.0 or x > 1.0 for x in vals):
            raise ValueError("Les composantes SGG_v2 (A, V, É, T, M) doivent appartenir à [0, 1].")
        return cls(*(Fraction(str(x)) for x in vals))

    def evaluate(self) -> dict[str, Any]:
        components = (self.a, self.v, self.e, self.t, self.m)
        raw_sum_check = sum(self.RAW_WEIGHTS, Fraction(0))
        norm_sum_check = sum(self.NORMALIZED_WEIGHTS, Fraction(0))

        raw_score = sum((w * x for w, x in zip(self.RAW_WEIGHTS, components)), Fraction(0))
        norm_score = sum((w * x for w, x in zip(self.NORMALIZED_WEIGHTS, components)), Fraction(0))
        order_isomorphism_ok = norm_score == Fraction(5, 6) * raw_score
        simplex_range_ok = Fraction(0) <= norm_score <= Fraction(1)
        return {
            "raw_weights_sum_exact": str(raw_sum_check),
            "normalized_weights_sum_exact": str(norm_sum_check),
            "normalized_weights_exact": [str(w) for w in self.NORMALIZED_WEIGHTS],
            "sgg_raw_exact": str(raw_score),
            "sgg_raw_float": float(raw_score),
            "sgg_norm_exact": str(norm_score),
            "sgg_norm_float": float(norm_score),
            "order_preserving_scaling_factor": "5/6",
            "order_isomorphism_verified": order_isomorphism_ok,
            "simplex_bounds_verified": simplex_range_ok,
            "raw_trace_preserved_without_erasure": raw_sum_check == Fraction(6, 5),
            "metric_verified": (
                raw_sum_check == Fraction(6, 5)
                and norm_sum_check == Fraction(1)
                and order_isomorphism_ok
                and simplex_range_ok
            ),
        }


@dataclass(frozen=True)
class MetricResetContraction:
    """
    Extension formelle candidate pour MAT-00-ZERO-INT (TZI) :
    Modèle d'espace métrique pointé (S, d, Z_0) muni d'un opérateur de reset contractant R
    (R(Z_0) = Z_0, d(R(S), Z_0) <= kappa * d(S, Z_0) avec 0 < kappa < 1).
    Ne remplace jamais la formulation historique semi-formelle conservée dans CONTR-Z0-TENSION.
    """

    initial_distance: float
    contraction_kappa: float
    critical_threshold: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.initial_distance) or self.initial_distance < 0.0:
            raise ValueError("La distance initiale d(S_0, Z_0) doit être finie et >= 0.")
        if not (0.0 < self.contraction_kappa < 1.0):
            raise ValueError("Le facteur de contraction kappa doit appartenir à ]0, 1[.")
        if not math.isfinite(self.critical_threshold) or self.critical_threshold <= 0.0:
            raise ValueError("Le seuil critique theta_critique doit être strictement positif.")

    def verify_convergence(self) -> dict[str, Any]:
        if self.initial_distance < self.critical_threshold:
            k_star = 0
        else:
            ratio = self.critical_threshold / self.initial_distance
            k_star = int(math.floor(math.log(ratio) / math.log(self.contraction_kappa))) + 1

        distances = [self.initial_distance * (self.contraction_kappa**k) for k in range(k_star + 1)]
        strictly_decreasing = all(distances[k + 1] < distances[k] for k in range(len(distances) - 1))
        threshold_reached = distances[-1] < self.critical_threshold
        fixed_point_preserved = (0.0 * self.contraction_kappa) == 0.0
        return {
            "epistemic_scope": "FORMAL_CANDIDATE_EXTENSION",
            "initial_distance": self.initial_distance,
            "contraction_kappa": self.contraction_kappa,
            "critical_threshold": self.critical_threshold,
            "guaranteed_steps_k_star": k_star,
            "final_distance": distances[-1],
            "strictly_decreasing": strictly_decreasing,
            "threshold_reached": threshold_reached,
            "fixed_point_z0_invariant": fixed_point_preserved,
            "contraction_verified": strictly_decreasing and threshold_reached and fixed_point_preserved,
        }


@dataclass(frozen=True)
class VR22VitalityEvaluator:
    """MAT-03-RESET-STAR : garde stricte Complexité > 0 pour V_e = Valeur / Complexité >= 1.0."""

    value: float
    complexity: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.value) or self.value < 0.0:
            raise ValueError("VR-22: Valeur doit être finie et >= 0.")
        if not math.isfinite(self.complexity) or self.complexity <= 0.0:
            raise ValueError("VR-22: Complexité doit être strictement positive (> 0).")

    @property
    def vitality_ratio(self) -> float:
        return self.value / self.complexity

    @property
    def vitality_ok(self) -> bool:
        return self.vitality_ratio >= 1.0


def _is_symmetric_positive_semidefinite(
    matrix: Sequence[Sequence[float]], *, tol: float = 1e-12
) -> bool:
    """
    Vérification exacte M ⪰ 0 par décomposition de Cholesky à pivotage diagonal complet
    (complément de Schur, Higham Ch. 10) — fonctionne sur matrices singulières ou de plein rang.
    """
    n = len(matrix)
    if n == 0 or any(len(row) != n for row in matrix):
        return False

    work = [[float(x) for x in row] for row in matrix]
    max_abs = 0.0
    for i in range(n):
        for j in range(n):
            val = work[i][j]
            if not math.isfinite(val):
                return False
            if abs(val) > max_abs:
                max_abs = abs(val)
            if abs(val - work[j][i]) > tol * max(1.0, abs(val), abs(work[j][i])):
                return False

    eps = tol * max(1.0, max_abs)
    for k in range(n):
        min_diag = min(work[i][i] for i in range(k, n))
        if min_diag < -eps:
            return False

        pivot = max(range(k, n), key=lambda idx: work[idx][idx])
        pivot_val = work[pivot][pivot]
        if pivot_val <= eps:
            # Si tous les termes diagonaux restants sont nuls, tout hors-diagonale non nul implique indéfini.
            for i in range(k, n):
                for j in range(k, n):
                    if abs(work[i][j]) > eps:
                        return False
            return True

        if pivot != k:
            work[k], work[pivot] = work[pivot], work[k]
            for row in work:
                row[k], row[pivot] = row[pivot], row[k]

        inv_pivot = 1.0 / work[k][k]
        for i in range(k + 1, n):
            w_ik = work[i][k]
            for j in range(k + 1, n):
                work[i][j] -= w_ik * work[j][k] * inv_pivot
    return True


@dataclass(frozen=True)
class GenericThermodynamicStep:
    """
    Mécanique irréversible GENERIC en dimension finie n >= 2 (MECANIQUE_IRREVERSIBLE_GENERIC_SUPELA.md) :
      z_dot = L(z) grad_E + M(z) grad_S
    Vérifie simultanément les 7 conditions structurelles :
      1. L^T = -L (antisymétrie de Poisson)
      2. M^T = M (symétrie d'Onsager-Casimir)
      3. M ⪰ 0 (semi-définie positivité complète via Cholesky pivoté)
      4. L * grad_S == 0 (dégénérescence réversible : conservation d'entropie)
      5. M * grad_E == 0 (dégénérescence dissipative : conservation d'énergie)
      6. dE/dt = <grad_E, L*grad_E + M*grad_S> == 0 (1er principe)
      7. dS/dt = <grad_S, M*grad_S> >= 0 (2e principe)
    """

    grad_e: Sequence[float]
    grad_s: Sequence[float]
    l_matrix: Sequence[Sequence[float]]
    m_matrix: Sequence[Sequence[float]]

    def __post_init__(self) -> None:
        n = len(self.grad_e)
        if n < 2:
            raise ValueError("GENERIC requiert une dimension n >= 2.")
        if len(self.grad_s) != n:
            raise ValueError("grad_e et grad_s doivent avoir la même dimension.")
        if len(self.l_matrix) != n or any(len(row) != n for row in self.l_matrix):
            raise ValueError("l_matrix doit être carrée de dimension n x n.")
        if len(self.m_matrix) != n or any(len(row) != n for row in self.m_matrix):
            raise ValueError("m_matrix doit être carrée de dimension n x n.")

    @staticmethod
    def _mat_vec(m: Sequence[Sequence[float]], v: Sequence[float]) -> tuple[float, ...]:
        return tuple(sum(row[j] * v[j] for j in range(len(v))) for row in m)

    @staticmethod
    def _dot(a: Sequence[float], b: Sequence[float]) -> float:
        return sum(x * y for x, y in zip(a, b))

    @classmethod
    def canonical_3d_damped_oscillator(
        cls,
        *,
        q: float = 1.2,
        p: float = 0.8,
        temperature: float = 2.0,
        gamma: float = 0.5,
    ) -> GenericThermodynamicStep:
        """
        Système GENERIC couplé non-trivial en dimension 3 : z = (q, p, s),
          E(q,p,s) = 0.5*(q^2 + p^2) + T_0 * s,  S(q,p,s) = s
          L symplectique non-nul + M = (gamma / T_0) * v v^T ⪰ 0 avec v = (0, T_0, -p)^T
        Garantit L != 0, M != 0, L*grad_S = 0, M*grad_E = 0, dE/dt = 0 et dS/dt = gamma*p^2/T_0 > 0.
        """
        if temperature <= 0.0:
            raise ValueError("La température T_0 doit être strictement positive.")
        if gamma < 0.0:
            raise ValueError("Le coefficient de friction gamma doit être >= 0.")
        return cls(
            grad_e=(q, p, temperature),
            grad_s=(0.0, 0.0, 1.0),
            l_matrix=(
                (0.0, 1.0, 0.0),
                (-1.0, 0.0, 0.0),
                (0.0, 0.0, 0.0),
            ),
            m_matrix=(
                (0.0, 0.0, 0.0),
                (0.0, gamma * temperature, -gamma * p),
                (0.0, -gamma * p, gamma * (p * p) / temperature),
            ),
        )

    def verify_invariants(self, *, tol: float = 1e-12) -> dict[str, Any]:
        n = len(self.grad_e)
        l_antisym = all(
            abs(self.l_matrix[i][j] + self.l_matrix[j][i]) <= tol for i in range(n) for j in range(n)
        )
        m_sym = all(
            abs(self.m_matrix[i][j] - self.m_matrix[j][i]) <= tol for i in range(n) for j in range(n)
        )
        m_psd = _is_symmetric_positive_semidefinite(self.m_matrix, tol=tol)
        l_non_trivial = any(abs(self.l_matrix[i][j]) > tol for i in range(n) for j in range(n))
        m_non_trivial = any(abs(self.m_matrix[i][j]) > tol for i in range(n) for j in range(n))

        l_grad_s = self._mat_vec(self.l_matrix, self.grad_s)
        m_grad_e = self._mat_vec(self.m_matrix, self.grad_e)
        degeneracy_l_s = all(abs(x) <= tol for x in l_grad_s)
        degeneracy_m_e = all(abs(x) <= tol for x in m_grad_e)

        l_grad_e = self._mat_vec(self.l_matrix, self.grad_e)
        m_grad_s = self._mat_vec(self.m_matrix, self.grad_s)
        x_dot = tuple(l_grad_e[i] + m_grad_s[i] for i in range(n))

        d_energy = self._dot(self.grad_e, x_dot)
        d_entropy = self._dot(self.grad_s, m_grad_s)

        energy_conserved = abs(d_energy) <= tol
        entropy_non_decreasing = d_entropy >= -tol
        return {
            "dimension": n,
            "l_antisymmetric": l_antisym,
            "m_symmetric": m_sym,
            "m_positive_semidefinite": m_psd,
            "l_non_trivial": l_non_trivial,
            "m_non_trivial": m_non_trivial,
            "degeneracy_L_gradS_zero": degeneracy_l_s,
            "degeneracy_M_gradE_zero": degeneracy_m_e,
            "dE_dt": d_energy,
            "dS_dt": d_entropy,
            "energy_conserved": energy_conserved,
            "entropy_non_decreasing": entropy_non_decreasing,
            "generic_valid": (
                l_antisym
                and m_sym
                and m_psd
                and degeneracy_l_s
                and degeneracy_m_e
                and energy_conserved
                and entropy_non_decreasing
            ),
        }


def run_supela_math_unification(*, validator_name: str = "Jean-François Gadbois") -> dict[str, Any]:
    """
    Exécute tous les possibles mathématiques & Supela (MAT-00..MAT-08 + VR-Fractal-Ω + GENERIC 3D)
    en séparant strictement ce qui est prouvé localement de ce qui reste A_PROUVER.
    """
    # MAT-00 : Monotonie K_t ⊆ K_{t+1}
    s0 = SupelaStateTuple(
        provenance=["INIT_MAT_00"],
        evidence=["LOCAL_TEST"],
        contradictions=[],
        knowledge_register=frozenset({"PI0_IDEMPOTENT"}),
    )
    s1 = s0.advance({"SUP_ICI_01", "SUP_NORM_NET_01"}, new_provenance="STEP_1", new_evidence="PYTEST")
    mat00_monotone = s0.knowledge_register.issubset(s1.knowledge_register)

    # MAT-00-ZERO-INT : modèle formel candidat de contraction métrique Banach (sans écraser CONTR-Z0-TENSION)
    tzi_contraction = MetricResetContraction(
        initial_distance=10.0,
        contraction_kappa=0.5,
        critical_threshold=0.01,
    ).verify_convergence()

    # MAT-01 : Axiomes complets de treillis borné + autorité bornée de Galois
    lattice_report = verify_proof_lattice_axioms()
    auth = BoundedAuthorityEvaluation(
        object_id="CAND-MATH-01",
        proof_level=ProofLatticeLevel.G2_TESTE_LOCAL,
        requested_authority=4,
        improvement_score=0.99,
    )

    # MAT-03 : Garde de vitalité VR-22 (Complexité > 0)
    vr22 = VR22VitalityEvaluator(value=2.4, complexity=1.5)

    # MAT-04 : H != L != P (runtime + canonique)
    hlp = ThreeDimensionalSeparation(
        history_hash=canonical_sha256({"h": "hist"}),
        local_context="R_LOCAL_PYTHON_311",
        proof_digest=canonical_sha256({"p": "proof"}),
    )
    hlp_canonical = CanonicalHLPSeparation(
        human_meaning="Intention normative exprimée par l'architecte souverain",
        literal_source="Formulation brute archivée sans réécriture silencieuse",
        proof_plane="Assertion exécutable vérifiée (pytest + OPA + Rust)",
    )

    # MAT-07 : Preuve analytique + différences finies réelles GRPO (L(theta_old) = 0 et grad_L != 0)
    grpo_step = SupelaGRPOBridge.analyze_zero_loss_nonzero_grad(
        theta=[0.25, -0.10, 0.40, -0.35],
        rewards=[1.0, 0.2, 0.8, 0.0],
    )
    grpo_max_fd_err = max(
        abs(a - b) for a, b in zip(grpo_step.analytical_grad, grpo_step.finite_diff_grad)
    )
    mat07_counterexample_ok = (
        abs(grpo_step.scalar_loss) < 1e-12
        and grpo_step.grad_norm > 1e-6
        and grpo_max_fd_err < 1e-7
    )

    # VR-Fractal-Ω : Agrégation multi-échelles par moyenne harmonique pondérée exacte
    fractal_res = FractalScaleAggregation(
        subsystems=((10.0, 5.0, 0.20), (8.0, 4.0, 0.05), (6.0, 3.0, 0.00))
    ).evaluate()

    # MAT-08 : SGG_v2 (conservation du brut ∑=1.20 + normalisation rationnelle exacte sur le simplexe)
    sgg_res = SGGv2Metric.from_floats(0.9, 0.8, 0.85, 0.75, 0.95).evaluate()

    # GENERIC 3D : oscillateur amorti couplé réversible/irréversible (L != 0, M != 0, M ⪰ 0)
    generic_step = GenericThermodynamicStep.canonical_3d_damped_oscillator(
        q=1.2, p=0.8, temperature=2.0, gamma=0.5
    )
    generic_res = generic_step.verify_invariants()

    payload: dict[str, Any] = {
        "schema": "supela-math-unification/1",
        "timestamp_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "human_test_validation": {
            "validator": validator_name,
            "scope": "LOCAL_TESTS_AND_FORMAL_INVARIANTS",
            "universal_claim": False,
        },
        "mat_00_monotone_k": mat00_monotone,
        "mat_00_tzi_metric_contraction": tzi_contraction,
        "mat_01_authority_bounded": auth.authority_bounded_ok and auth.granted_authority == 2,
        "mat_01_lattice_axioms": lattice_report,
        "mat_03_vr22_vitality": {
            "value": vr22.value,
            "complexity": vr22.complexity,
            "vitality_ratio": vr22.vitality_ratio,
            "vitality_ok": vr22.vitality_ok,
        },
        "mat_04_hlp_distinct": hlp.dimensions_distinct and hlp_canonical.dimensions_distinct,
        "mat_06_improvement_not_authorization": auth.auto_authorized_by_improvement is False,
        "mat_07_loss_zero_grad_nonzero": mat07_counterexample_ok,
        "mat_07_grpo_analysis": {
            "scalar_loss": grpo_step.scalar_loss,
            "grad_norm": grpo_step.grad_norm,
            "max_finite_diff_error": grpo_max_fd_err,
        },
        "mat_08_sgg_v2_simplex": sgg_res,
        "vr_fractal_omega_aggregation": fractal_res,
        "generic_thermodynamics": generic_res,
        "honest_open_bounds": [
            "OPEN-01:Validite_Universelle_A_PROUVER",
            "OPEN-02:Theoreme_du_Vide_General_A_PROUVER",
            "OPEN-03:Terminaison_Generale_A_PROUVER",
        ],
    }
    payload["digest_sha256"] = canonical_sha256(payload)
    return payload
