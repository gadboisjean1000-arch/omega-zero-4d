# Supela-Guard-Kernel · Spécification Exécutable (`SUP-ICI-01`)

> **Statut :** Spécification intégrée et exécutable dans [`src/omega_zero/guard_kernel.py`](../../src/omega_zero/guard_kernel.py) et validée par [`schemas/supela_guard_kernel_1.schema.json`](../../schemas/supela_guard_kernel_1.schema.json).  
> **Principe directeur :** $\Omega$ traverse les générations en réduisant le poids de ce qu'il transporte, jamais en effaçant silencieusement ce qui permet d'en comprendre le sens.

---

## 1. Invariant Intercycle (`SUP-ICI-01`)

Pour toute génération $G_n$ transformée en $G_{n+1} = T_n(G_n)$, le noyau de continuité :

$$K_n = \{ \text{identité},\ \text{provenance},\ \text{décisions},\ \text{preuves},\ \text{limites},\ \text{dépendances},\ \text{transformation} \}$$

doit satisfaire :

$$\forall n,\quad K_n \subseteq \operatorname{Accessible}(G_{n+1})$$

selon l'un des trois modes vérifiables : `DIRECT`, `REFERENTIAL` (empreinte + localisation) ou `RECONSTRUCTIBLE` (transformation documentée et restituable).

### Interdictions mécanisées
1. Promouvoir une hypothèse (`HYPOTHESE`) en fait (`FAIT`) par simple compression sans nouvelle preuve.
2. Effacer une contradiction active lors d'une transition.
3. Perdre l'auteur ou l'origine d'un objet.
4. Hériter silencieusement de l'autorité normative précédente (`authority = PENDING_HUMAN_RATIFICATION` par défaut).
5. Déclarer `RECONSTRUCTIBLE` sans localisation, empreinte et historique de transformation vérifiables.
6. Remplacer une preuve par un simple résumé sans conserver la référence de preuve.

---

## 2. Compression Sans Perte de Sens (`C0` / `C1` / `C2`)

| Niveau | Mécanisme | Restitution | Règle d'honnêteté |
|---|---|---|---|
| **C0** | Conservation intégrale | Bit-à-bit exacte | Usage actif ou preuve critique |
| **C1** | Compression `zlib` vérifiée par aller-retour | Exacte (`decompress(c) == raw`) | Aucune information retirée |
| **C2** | Résidu sémantique minimal $R_{\min}(O)$ | Référentielle + réouvrable (`NON-RÉCLAMÉ`) | `C2` ne doit **jamais** être présenté comme copie complète (`reversible = false`) |

Le résidu $R_{\min}(O)$ exige les 10 champs : `identity`, `provenance`, `original_hash`, `status`, `scope`, `dependencies`, `transformation`, `reason`, `reopening_conditions`, `location`.  
Les 8 questions critiques du test de perte de sens sont évaluées avant validation ; tout manquement déclenche `COMPRESSION-FAIL` ([`CompressionFailureError`](../../src/omega_zero/guard_kernel.py)).

---

## 3. Cycle des générations (`G0..G5`)

- `G0` (`SOURCE`) $\to$ `G1` (`TRAVAIL`) $\to$ `G2` (`VALIDATION`) $\to$ `G3` (`CONSOLIDATION`) $\to$ `G4` (`NON-RÉCLAMÉ`) $\to$ `G5` (`DERNIER PASSAGE`).
- **Réclamation (`G4 → G1/G2`) :** toute nouvelle dépendance, contradiction ou question rouvre le cycle actif sous statut `RÉCLAMÉ`.
- **Dernier passage (`G5`) :** exige vérification des dépendances (`dependencies_checked = true`), motif explicite et autorité humaine pour `REJET_JUSTIFIE`, tout en conservant le registre historique ($\operatorname{RejetDuContenu} \neq \operatorname{EffacementDeLExistenceHistorique}$).
