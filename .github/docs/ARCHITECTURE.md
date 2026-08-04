# Architecture — SUPELA v1.1.0

Hiérarchie en 5 couches de l'écosystème SUPELA.

---

## Vue d'ensemble

```
┌─────────────────────────────────────────────────────────┐
│  Layer 4 — Security & Surveillance (SCDH / RFC K3)      │
├─────────────────────────────────────────────────────────┤
│  Layer 3 — Implementations (Silicon · Quantum · Rad)    │
├─────────────────────────────────────────────────────────┤
│  Layer 2 — Integration Hub (Document Maître)            │
├─────────────────────────────────────────────────────────┤
│  Layer 1 — Frameworks (LCI · NORME CANU · MoteurRAIM)   │
├─────────────────────────────────────────────────────────┤
│  Layer 0 — Meta-Architecture Fondatrice (SUPELA core)   │
└─────────────────────────────────────────────────────────┘
```

---

## Layer 0 — Meta-Architecture Fondatrice

| Composant | Description |
|-----------|-------------|
| **SUPELA v1.0.0 axioms** | Fondation axiomatique — 5 invariants |
| **Point Fixe Atteint** | Cohérence = 100%, stabilité prouvée |
| **Hypercube 3×3** | Matrice de gouvernance 9-cellules |
| **Corpus SUPELA v1.0.0** | Archive primaire — 4 dépôts |

**Fichiers:** `SYNTHESE-FINALE-SUPELA-v1.1.0.md`, `supela-corpus-v1.0.0/`

---

## Layer 1 — Frameworks

| Framework | Description |
|-----------|-------------|
| **LCI** | Loi Contradiction Interne — preuve Lyapunov |
| **NORME CANU** | Cycle autonome 19 étapes normalisées |
| **RFC K3 – Annexe E** | SCDH Safety OS — portes V1–V4 |
| **MoteurRAIM v2.2.0** | Arbitrage dissonance, 19/19 tests |

**Fichiers:** `RFC-SUPELA-K3-ANNEXE-E-SCDH.md`, `ANNEXES-A-D-NORMES-OPERATIONNELLES.md`, `norme-canu/`

---

## Layer 2 — Integration Hub

| Composant | Description |
|-----------|-------------|
| **Document Maître** | 9 Parties + 4 extensions — référence centrale |
| **CATALOGUE-COMPLET** | Navigation inter-archives |
| **Deployment Roadmap** | Phases 1–4, gates, livrables |
| **Dashboard SGG v2** | KPIs temps réel interactifs |

**Fichiers:** `MASTER-FORMALIZATION.md`, `DEPLOYMENT-ROADMAP.md`, `DASHBOARD-SGG-v2-INTERACTIVE.html`, `document-maitre/`

---

## Layer 3 — Implementations

### Silicon
| Module | Spec |
|--------|------|
| **AVX-512 kernel** | RAIM O(1), cible 267M ops/sec |
| **GPU FP32** | Vectorisation 16× float32 |
| **Booth R-4** | Multiplicateur matériel optimisé |

### Quantum
| Module | Spec |
|--------|------|
| **Qiskit CZ gate** | Encodage de phase `|11⟩ → −|11⟩` |
| **NISQ backends** | IonQ / IBMQ / Honeywell |

### Rad-Hard
| Module | Spec |
|--------|------|
| **TMR** | Triple Modular Redundancy |
| **DICE layout** | Dual Interlocked storage Cell |
| **MTTF target** | > 10 ans en environnement radiatif |

**Fichiers:** `PROFILING-MEMORY-CPU-SILICON-QUANTUM.md`, `PERFORMANCE-BENCHMARKS-SUPELA-v1.1.0.md`

---

## Layer 4 — Security & Surveillance

| Composant | Spec |
|-----------|------|
| **RFC K3 SCDH** | Agnostic multi-model safety OS |
| **Portes V1–V4** | Escalade déterministe par seuil Δ |
| **KPIs temps réel** | Cohérence, IS, MTTF, divergence |
| **Kill switch V4** | Arrêt complet < 100ms si Δ ≥ 0.50 |

**Fichiers:** `RFC-SUPELA-K3-ANNEXE-E-SCDH.md`, `governance/`, `DASHBOARD-SGG-v2-INTERACTIVE.html`

---

## Governance Python Modules

```
governance/
├── orchestrator.py          # Orchestrateur principal SCDH
├── supela.py                # Module d'exposition Supela EIR
├── supela_core.py           # Orchestration EIR : SupelaCore, VideIntact, ZeroAbsolu, EIRMonitor
├── meta_orchestrator.py     # Meta-orchestration multi-modèle
└── test_governance_rules.py # Suite de tests 17/17
```

### Supela EIR Architecture
- **Triade EIR** : Énergie (compute), Information (RAG/AI), Relation (routing)
- **VideIntact** : État de référence neutre — baseline de cohérence
- **ZeroAbsolu** : Limite asymptotique — circuit-breaker et reset
- **EIRMonitor** : Surveillance temps réel des 3 dimensions
- **SupelaCore** : Gouverneur central — orchestre le cycle EIR

---

*Référence complète → `MASTER-FORMALIZATION.md`*  
*Gouvernance détaillée → `RFC-SUPELA-K3-ANNEXE-E-SCDH.md`*
