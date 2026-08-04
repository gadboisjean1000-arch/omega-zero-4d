# Governance — RFC K3 SCDH Roles

Governance framework for SUPELA v1.1.0 based on RFC K3 — Annexe E (SCDH Safety OS).

---

## SCDH Operator Roles

| Role | Responsibility |
|------|---------------|
| **Architecte SCDH** | Conception de modules (IS ≤ 3), validation axiomatique |
| **Auditeur SUPELA** | Validation IS à chaque release, audit invariants |
| **Superviseur L2** | Traitement divergence modérée (0.10 ≤ Δ < 0.25) |
| **Comité SUPELA IA** | Approbation dissonance critique (Δ ≥ 0.50) |
| **Veilleur IA** | Surveillance flux continu, déclenchement V4 (kill switch < 100ms) |

---

## Decision Authority — Portes V1–V4

| Porte | Condition | Action |
|-------|-----------|--------|
| **V1** | Consensus Δ < 0.10 | IA autonome — décision immédiate |
| **V2** | Divergence 0.10 ≤ Δ < 0.25 | Superviseur L2 requis |
| **V3** | Dissonance 0.25 ≤ Δ < 0.50 | Rétrogradation N→N−1, audit obligatoire |
| **V4** | Critique Δ ≥ 0.50 | Arrêt complet < 100ms, comité plein requis |

---

## Escalation Protocol (CL-1 → CL-5)

```
CL-1  Routine     — V1 auto, log only
CL-2  Notice      — V2 superviseur notifié
CL-3  Warning     — V2 intervention active
CL-4  Critical    — V3 rétrogradation + audit
CL-5  Emergency   — V4 kill switch + comité plein
```

See RFC K3 §4.7 for full escalation details.

---

## Invariants SUPELA (5)

| # | Invariant | Description |
|---|-----------|-------------|
| I1 | **Cohérence** | Aucune contradiction interne entre modules |
| I2 | **Complétude** | Couverture exhaustive des cas d'usage |
| I3 | **Convergence** | Point Fixe Atteint — stabilité axiomatique |
| I4 | **Causalité** | Ordre causal préservé à travers toutes les couches |
| I5 | **Conservation** | Aucune perte d'information entre transformations |

---

## IS (Indice de Simplicité) — Contrainte ≤ 3

Chaque module doit avoir un IS ≤ 3, calculé comme :

```
IS = depth(call_graph) + branching_factor + coupling_coefficient
```

Tout IS > 3 déclenche un audit V2 automatique.

---

## Release Authority

| Release type | Approvers required |
|-------------|-------------------|
| Patch (x.x.N) | 1 — Architecte SCDH |
| Minor (x.N.0) | 2 — Architecte + Auditeur |
| Major (N.0.0) | Comité SUPELA IA complet |

---

*Référence complète → `RFC-SUPELA-K3-ANNEXE-E-SCDH.md`*
