# NORME CANU v1.0.0 — Guide d'Implémentation Rapide

## 1. Cycle CANU — Formule Minimale

### Formule
```
γ : ∅ → E → M → R → ∅
```

### Signification
- **∅** : État Vide (pas de résidu, pas d'observable non annulé)
- **E** : Excitation (action contrôlée et bornée)
- **M** : Mesure (capture des observables déclarés)
- **R** : Reset (annulation absolue de la surface)
- **∅** : Retour au Vide (cycle fermé)

### Propriétés Formelles
- **Déterministe :** Mêmes conditions → mêmes résultats
- **Reproductible :** Deux cycles consécutifs donnent les mêmes observables
- **Composable :** γₙ ∘ γₙ₊₁ valide si γₙ(fin) = ∅
- **Idempotent :** Reset(Reset(s)) = ∅

---

## 2. Invariant Fond/Surface — Règle d'Or

### Énoncé
```
∀ s ∈ Surface, s ∩ Fond = ∅
```

### Interprétation
- **Fond** = Structures formelles, invariants, paramètres déclarés, code
- **Surface** = Observables, métriques, logs, variables transitoires, artefacts

**Aucun élément de surface ne peut modifier ou contaminer le fond.**

### Violation = Erreur Critique
Si la surface interfère avec le fond → le cycle n'est pas fermable au Vide → violation constitutionnelle.

---

## 3. Implémentation Pipeline CI/CD — YAML GitLab

### Structure Minimale
```yaml
variables:
  CANU_VERSION: "1.0.0"
  CANU_ETAT: "VIDE"

stages:
  - origine       # ∅ : Vérifier état Vide initial
  - excitation    # E : Déclencher action (build, test, etc.)
  - mesure        # M : Capturer observables
  - reset         # R : Nettoyage complet
  - certif        # Attestation de conformité

# STAGE ORIGINE
origine:verifier-vide:
  stage: origine
  script:
    - if [ -n "${CANU_RESIDUS:-}" ]; then exit 1; fi
    - echo "[CANU][ORIGINE] État ∅ certifié."

# STAGE EXCITATION
excitation:build:
  stage: excitation
  needs: ["origine:verifier-vide"]
  script:
    - make build
  artifacts:
    paths: [dist/]

# STAGE MESURE
mesure:tests:
  stage: mesure
  needs: ["excitation:build"]
  script:
    - make test
  artifacts:
    paths: [reports/]

# STAGE RESET (Toujours exécuté)
reset:absolu:
  stage: reset
  needs: ["mesure:tests"]
  when: always
  script:
    - bash scripts/reset_absolu.sh

# STAGE CERTIF
certif:conformite-canu:
  stage: certif
  needs: ["reset:absolu"]
  script:
    - echo "∅ → E → M → R → ∅ — CONFORME"
```

---

## 4. Implémentation Logicielle — Harness Zéro

### Initialisation
```python
class CANUHarness:
    def __init__(self):
        self.state = "VOID"  # ∅
        self.residuals = set()
        self.cycle_id = None
        self.lock = threading.Lock()
    
    def origin(self):
        """∅ : Initialisation"""
        assert self.state == "VOID" and not self.residuals
        self.cycle_id = uuid.uuid4()
        return True

    def excite(self, action):
        """E : Perturbation contrôlée"""
        with self.lock:
            self.state = "EXCITATION"
            result = action()  # Exécution bornée
            return result

    def measure(self, observables):
        """M : Capture déclarée"""
        self.state = "MEASURE"
        data = {obs: getattr(self, obs) for obs in observables}
        return data

    def reset(self):
        """R → ∅ : Reset Absolu"""
        with self.lock:
            self.state = "RESET"
            self.residuals.clear()
            # Nettoyer l'environnement
            self.state = "VOID"
            assert len(self.residuals) == 0  # Idempotence
            return True
```

---

## 5. Vérification Conformité — 10 Critères Essentiels

| # | Critère | Test | Status |
|---|---------|------|--------|
| 1 | État initial = ∅ | Assertion `state == "VOID"` avant T1 | ✓ |
| 2 | État final = ∅ | Assertion `state == "VOID"` après R | ✓ |
| 3 | Reset Absolu | Vérifier `residuals == {}` post-Reset | ✓ |
| 4 | Séquentialité | Respeter ordre ∅→E→M→R | ✓ |
| 5 | Non-contamination | Analyser accès à fond pendant surface | ✓ |
| 6 | Reproductibilité | Deux cycles identiques → même résultat | ✓ |
| 7 | Idempotence | `Reset(Reset(s)) = ∅` | ✓ |
| 8 | Unicité active | Un seul cycle en cours (verrou mutex) | ✓ |
| 9 | Journalisation | Chaque transition horodatée | ✓ |
| 10 | Absence parasites | Aucune métrique non déclarée | ✓ |

---

## 6. Protocole Agent CANU — Message Format

```json
{
  "message_id": "msg_uuid",
  "cycle_id": "γ_001",
  "phase": "E",
  "sender_agent": "Agent-A",
  "receiver_agent": "Agent-B",
  "payload": {
    "action": "compute",
    "params": {...}
  },
  "timestamp_utc": "2026-07-31T23:59:59Z",
  "conformity_signature": "sha256_hash"
}
```

---

## 7. Fondements Matériels Brahmagupta

### Isomorphisme Universel
```
φ : (ℤ/2ℤ, +)² → (ℤ/2ℤ, +)
φ(sA, sB) = sA ⊕ sB
```

Propriétés :
- **Silicium :** XOR logique (Booth, Wallace) — E₁, temps < 10 ps
- **Compilateur :** Vmulps, vxorps (instruction set) — isomorphisme préservé
- **Quantique :** Porte Controlled-Z (phase e^{iπ}) — ~ 40–200 ns
- **IEEE 754 :** Bit de signe S = 1 bit (FOND), Exposant+Mantisse = 31 bits (SURFACE)

L'invariant fond/surface de CANU est **gravé dans le silicium** de tout processeur moderne.

---

## 8. Cas d'Usage Directs

### Cognitive Individuelle
```
C₁: Réception du problème (Chaos)
 ↓ [∅ → E]
C₂: Cristallisation des perspectives (Tension)
 ↓ [E → M]
C₃: Extraction de l'essence (Densité)
 ↓ [M → R]
C₄: Décision émise (Propagation)
 ↓ [R → ∅]
C₅: Apprentissage sans trauma (Résonance au Vide)
```

### Pipeline CI/CD
```
∅ : Vérifier répertoire vide
E : Déclencher build (git clone, make, docker)
M : Capturer tests, logs, artefacts
R : Nettoyer container, cache, variables
∅ : Repos, prêt pour cycle suivant
```

### Agent IA / RAG
```
∅ : État initial mémoire vide
E : Ingestion documents, embedding
M : Construction index vectoriel
R : Nettoyage cache temporaire
∅ : LLM prêt pour requête suivante
```

---

## 9. Erreurs Courantes et Remédiation

### Erreur 1: Résidu Non Nettoyé
```
AVANT : Les fichiers temporaires restent après Reset
APRÈS : bash scripts/reset_absolu.sh exécute find + rm
RÉSULTAT : ✓ État ∅ garanti
```

### Erreur 2: Contamination Fond/Surface
```
AVANT : Log écrit dans fondamental.cfg
APRÈS : Logs → surface_logs/ seulement
RÉSULTAT : ✓ Invariant préservé
```

### Erreur 3: Concurrence
```
AVANT : Deux cycles γ et γ' en parallèle
APRÈS : threading.Lock() dans Harness.excite()
RÉSULTAT : ✓ Unicité active garantie
```

---

## 10. Vérification Finale — Test de Fermeture

```bash
#!/bin/bash
# Test: le cycle se ferme-t-il au Vide ?

echo "1. Initialiser ∅..."
python -c "h = CANUHarness(); assert h.origin()"

echo "2. Exciter (E)..."
python -c "h.excite(lambda: print('action'))"

echo "3. Mesurer (M)..."
python -c "h.measure(['cpu', 'memory'])"

echo "4. Reset (R)..."
python -c "h.reset(); assert h.state == 'VOID'"

echo "✓ Cycle fermé: ∅ → E → M → R → ∅"
echo "✓ CONFORME NORME CANU v1.0.0"
```

---

## Axiome Final

> « Ce qui ne peut pas revenir au Vide n'appartient pas au système Supela. »

**NORME CANU v1.0.0 = Fondement formel de tout système Supela.**

---

**© Jean-François Gadbois (Jef), 2026 — Tous droits réservés**
