# Contributing — SUPELA v1.1.0

Thank you for contributing to the SUPELA ecosystem. This project follows rigorous industrial and academic standards. Please read carefully before submitting changes.

---

## Code of Conduct

All contributions must respect:
- The **5 Invariants SUPELA** (Cohérence, Complétude, Convergence, Causalité, Conservation)
- The **IS ≤ 3** architectural complexity constraint (RFC K3 §3.4)
- The **SCDH Gating Protocol** (V1–V4 escalade)

---

## Development Setup

```bash
# 1. Clone
git clone https://github.com/groupnatupro/multi-branches.git
cd multi-branches

# 2. Install Python dependencies (governance modules)
cd governance
pip install -r requirements.txt  # if present

# 3. Run tests
python3 test_governance_rules.py -v
```

---

## Contribution Workflow

1. **Fork** the repository
2. **Branch** from `main`: `git checkout -b feat/your-feature`
3. **Implement** your changes respecting IS ≤ 3
4. **Test** all governance invariants: `python3 governance/test_governance_rules.py -v`
5. **Validate** formalization: all CI workflows must pass
6. **Commit** using Conventional Commits (see below)
7. **Open PR** with the standard PR template

---

## Commit Convention

Use [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix | Usage |
|--------|-------|
| `feat:` | New feature or module |
| `fix:` | Bug fix |
| `docs:` | Documentation only |
| `chore:` | Maintenance, deps, tooling |
| `ci:` | CI/CD pipeline changes |
| `perf:` | Performance improvement |
| `refactor:` | Code refactor (no feature/fix) |
| `test:` | Adding or fixing tests |

Example: `feat: add MoteurRAIM v2.3.0 test block T-20`

---

## PR Review Criteria

All PRs must satisfy:

- [ ] All CI workflows **PASS** (test-raim, validate-formalization, silicon-benchmark, quantum-integration, supela-ci)
- [ ] `governance/test_governance_rules.py` — **17/17 PASS**
- [ ] `RFC-SUPELA-K3-ANNEXE-E-SCDH.md` — **19/19 PASS** marker maintained
- [ ] Documentation updated if behaviour changes
- [ ] No archive deletion (corpus-supela, norme-canu, document-maitre, supela-corpus-v1.0.0)
- [ ] IS ≤ 3 constraint respected in all new modules

---

## Questions

Refer to `MASTER-FORMALIZATION.md` Part VIII for navigational guidance.
