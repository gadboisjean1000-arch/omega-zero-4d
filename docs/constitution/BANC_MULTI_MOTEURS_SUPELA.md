# Banc Multi-Moteurs Supela · Spécification Formelle (`supela-multi-engine-bench/1`)

> **Statut :** Spécification exécutable implémentée dans [`src/omega_zero/multi_engine_bench.py`](../../src/omega_zero/multi_engine_bench.py) et validée par [`schemas/supela_multi_engine_bench_1.schema.json`](../../schemas/supela_multi_engine_bench_1.schema.json).  
> **Principe cardinal :** **Le banc ne vote pas.** Trois moteurs disant `VRAI` ne constituent pas automatiquement une preuve (`Score ≠ Preuve ≠ Vérité`, `Convergence ≠ Preuve`).

---

## 1. Architecture du Banc Multi-Moteurs

Le banc place **Copilot**, toute autre **IA X**, les moteurs **Formel/math**, et **Supela lui-même** au même rang d'objets éprouvables face au **même objet / test**.  
Supela n'est jamais juge de sa propre victoire : le banc doit pouvoir conclure **`SUPELA_EN_DÉFAUT`** dès lors qu'un moteur Supela échoue, contredit une preuve vérifiée ou prétend s'auto-valider sans preuve.

```text
                 ┌──────────────────────┐
                 │   MÊME OBJET / TEST  │
                 └──────────┬───────────┘
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
      Moteur A          Moteur B          Moteur C / Supela
      Copilot             IA X           Formel / math / Supela
          │                 │                 │
          ▼                 ▼                 ▼
       résultat          résultat          résultat
          │                 │                 │
          └─────────────────┼─────────────────┘
                            ▼
                      Banc Supela
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
        convergence      divergence      indéterminé
            │               │               │
            └───────────────┼───────────────┘
                            ▼
                 preuves + référentiels
                            │
                            ▼
                   promotion éventuelle
```

---

## 2. Règles Normatives Invariantes

1. **Non-vote (`vote_interdit = true`) :** Aucun comptage majoritaire (`k` sur `n` moteurs) ne peut promouvoir un résultat au rang de vérité ou d'autorité.
2. **Convergence ≠ Preuve :** La convergence multi-moteurs augmente l'information disponible ; elle n'augmente pas automatiquement le statut de vérité.
3. **Divergence = Donnée :** Une divergence entre moteurs n'est pas un échec du banc ; c'est une **donnée produite par le banc**, conservée sans écrasement (`effacement_interdit = true`).
4. **Symétrie d'épreuve & `SUPELA_EN_DÉFAUT` :**
   - Supela est soumis aux mêmes exigences probatoires que Copilot, une IA externe ou un vérificateur formel.
   - Le banc conclut `SUPELA_EN_DÉFAUT` si un moteur identifié `supela` :
     - produit `FAUX`, `ERREUR` ou `INDÉTERMINÉ` face à un résultat opposé accompagné d'une preuve vérifiée (`preuve_verifiee = true`) dans le référentiel cible, ou
     - affirme `VRAI` sans preuve vérifiée alors qu'un autre moteur produit une réfutation / contre-exemple prouvé, ou
     - tente une auto-promotion (`auto_promotion_tentee = true`) sans preuve vérifiée ni ratification humaine.
5. **Promotion éventuelle bornée (`Authority ≤ Proof`) :** Une promotion reste `false` par défaut (`promotion_autorisee = false`) ; elle n'est envisageable que si au moins une preuve vérifiée et son référentiel explicite lèvent toute contradiction active, et demeure soumise à ratification humaine.

---

## 3. Enregistrement Minimal Obligatoire (10 Champs)

Chaque exécution moteur soumise au banc conserve au minimum les 10 champs suivants :

| Champ | Rôle | Contrainte fail-closed |
|---|---|---|
| `objet` | Identifiant / énoncé de l'objet ou du test commun | Non vide, identique pour tous les moteurs du même banc |
| `moteur` | Identifiant du moteur (`copilot`, `ia_x`, `formel_math`, `supela`, …) | Non vide, unique par `(moteur, version)` dans un run |
| `version` | Version exacte ou empreinte du moteur | Non vide |
| `referentiel` | Référentiel normatif, mathématique ou documentaire utilisé | Non vide |
| `premisses` | Liste explicite des prémisses fournies au moteur | Liste non nulle |
| `methode` | Méthode d'évaluation (`heuristique`, `formelle`, `test_local`, …) | Non vide |
| `resultat` | Verdict produit (`VRAI`, `FAUX`, `INDÉTERMINÉ`, `ERREUR`) | Enum strict |
| `preuve_fournie` | Référence / contenu de preuve produite (ou `""` si absente) + `preuve_verifiee` (`bool`) | Aucune promotion sans `preuve_verifiee == true` |
| `contradictions` | Liste des contradictions ou contre-exemples détectés | Conservée intégralement (jamais effacée) |
| `statut` | Statut épistémique du run (`CANDIDAT`, `PROUVE`, `REFUTE`, `INDETERMINE`, `EN_DEFAUT`) | Cohérent avec `preuve_verifiee` et `resultat` |

---

## 4. Intégration dans `omega-zero-4d`

- **Module Python :** [`src/omega_zero/multi_engine_bench.py`](../../src/omega_zero/multi_engine_bench.py) (`SupelaMultiEngineBench`, `EngineRunRecord`, `MultiEngineBenchReport`).
- **Outil MCP :** `omega_multi_engine_bench` dans [`src/omega_zero/mcp_server.py`](../../src/omega_zero/mcp_server.py).
- **Schéma JSON Draft 2020-12 :** [`schemas/supela_multi_engine_bench_1.schema.json`](../../schemas/supela_multi_engine_bench_1.schema.json).
- **Tests :** [`tests/test_multi_engine_bench.py`](../../tests/test_multi_engine_bench.py).
