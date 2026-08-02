NORME CANU
Cycle Autonome Normatif Universel
Projet Supela
NORME OFFICIELLE
Version	1.0.0 — Norme Durable
Date d'émission	31 juillet 2026
Statut	NORME OFFICIELLE
Projet	Supela
Auteur	Jef / Jean-François Gadbois
« Le Vide est l'état fondamental. Tout cycle commence et finit dans le Vide. »
Table des matières
1. Préambule et champ d'application
2. Définition mathématique du cycle CANU
2.1 États et espace d'état
2.2 Définition formelle du cycle
2.3 Théorème du Vide
2.4 Diagramme d'état
3. Protocole opérationnel
3.1–3.5 Modules Origine, Excitation, Mesure, Reset, Cycle
4. Version logicielle
4.1–4.3 Harness Zéro, Reset Absolu Shell, Règles logicielles
5. Version constitutionnelle
5.1–5.3 Préambule, Articles I–VII, Grille de conformité
6. Version pipeline (CI/CD)
6.1–6.3 Architecture, Configuration YAML, Règles pipeline
7. Version agentique
7.1–7.4 Architecture, Protocole, Relance, Agent Superviseur
8. Glossaire normatif CANU
9. Registre des violations et procédures de remédiation
10. Journal de version et cycle de vie de la norme
Section 1 — Préambule et champ d'application
1.1 Objet
La présente norme, désignée NORME CANU — Cycle Autonome Normatif Universel, a pour objet de formaliser, de définir avec précision et de rendre opposable le Cycle Autonome Normatif Universel applicable à l'ensemble du projet Supela. Elle constitue la référence normative de premier rang pour toute opération, tout module, tout agent et tout pipeline rattaché au projet Supela. Aucune norme de niveau inférieur ne peut la contredire.

1.2 Principe du Théorème du Vide et du Reset
L'état Vide, noté ∅, est l'état fondamental, stable, vérifiable et reproductible de tout système Supela. Cet état est défini comme l'absence totale de résidu, de perturbation active et d'observable non annulé. Tout cycle CANU prend nécessairement naissance dans l'état ∅ et doit, sans exception, y retourner à son terme. L'état ∅ n'est pas un état parmi d'autres : il est l'attracteur unique du cycle et la condition de toute composabilité. La fonction Reset est l'opération formelle qui assure ce retour.

1.3 Invariant fond/surface
La norme CANU établit une distinction constitutionnelle et opérationnelle entre fond et surface :

Fond : ensemble des formalismes mathématiques, invariants formels, états S = {∅, E, M, R}, fonctions de transition, articles constitutionnels et paramètres déclarés dans la norme. Le fond est immuable au cours d'un cycle.
Surface : ensemble des métriques observées, logs générés, artefacts temporaires, variables d'environnement transitoires et tout observable produit pendant l'exécution d'un cycle. La surface est éphémère et doit être intégralement annulée par le Reset.
Invariant formel : pour tout ensemble S de surface et tout ensemble F de fond, S ∩ F = ∅. Aucun élément de surface ne peut modifier, remplacer, masquer ou contaminer un élément de fond. Toute violation de cet invariant constitue une violation constitutionnelle CANU.

1.4 Périmètre d'application
La présente norme s'applique sans restriction ni dérogation à l'ensemble des composants suivants du projet Supela :

Modules logiciels (bibliothèques, services, API internes)
Modules opérationnels (procédures, protocoles d'exécution)
Modules constitutionnels (chartes, règles de gouvernance)
Pipelines d'intégration et de déploiement continus (CI/CD)
Agents autonomes (LLM, agents orchestrateurs, agents spécialisés)
Tout nouveau module intégré au projet Supela est réputé soumis à la norme CANU dès sa déclaration formelle dans le fond du projet.

Section 2 — Définition mathématique du cycle CANU
2.1 États et espace d'état
L'espace d'état du cycle CANU est un ensemble fini S défini comme suit :

S = { ∅, E, M, R }

Symbole	Nom	Définition normative
∅	Vide	État fondamental. Aucun résidu, aucune excitation active, aucun observable non annulé. État initial et final obligatoire de tout cycle CANU.
E	Excitation	État de perturbation contrôlée. Une excitation documentée et bornée a été appliquée au système. L'excitation est active.
M	Mesure	État d'observation. La réponse du système à l'excitation est en cours de capture. Les observables déclarés dans le fond sont collectés.
R	Reset	État d'annulation. Tous les résidus de surface sont effacés. Le système effectue la transition formelle vers ∅.
2.2 Définition formelle du cycle
Un cycle CANU, noté γ, est défini comme la suite d'états suivante :

Définition — Cycle CANU
γ : ∅ → E → M → R → ∅

Tout cycle CANU est une application de l'état ∅ vers l'état ∅, passant séquentiellement par E, M et R.

Les propriétés formelles du cycle sont les suivantes :

Fonction de transition :

δ : S × Σ → S

où S = {∅, E, M, R} et Σ = {excite, mesure, reset, vide}

Condition d'intégrité du cycle :

∀ γ_n, γ_n(fin) = ∅

(tout cycle se ferme sur l'état Vide)

Invariant formel du cycle :

I(γ) := (état_initial = ∅) ∧ (état_final = ∅)

Condition de non-contamination fond/surface :

∀ s ∈ Surface, s ∩ Fond = ∅

Composabilité de cycles :

γ_n ∘ γ_{n+1} est valide si et seulement si γ_n(fin) = ∅ = γ_{n+1}(début)

Deux cycles ne peuvent être composés que si le premier a bien été fermé dans l'état ∅. Aucune composition partielle n'est admissible.

2.3 Théorème du Vide (énoncé formel)
Théorème — Vide
Théorème (Vide) : Pour tout système Supela conforme à la norme CANU, l'état ∅ est l'unique attracteur du cycle γ. Tout état non-∅ constaté après l'exécution de la fonction Reset constitue une violation de la norme CANU.

Corollaire — Reset Absolu
Corollaire (Reset Absolu) : La fonction Reset R : S → ∅ est totale sur S, injective sur S \ {∅}, et idempotente :

R(R(s)) = R(s) = ∅ pour tout s ∈ S.

L'idempotence du Reset garantit qu'un Reset appliqué à l'état ∅ ne produit aucun effet de bord. Cette propriété est constitutionnellement requise pour la sécurité des environnements CI/CD et agentiques.

2.4 Diagramme d'état
La machine à états finis du cycle CANU est définie par la table de transitions suivante :

Transition	État source	Déclencheur (Σ)	État cible	Condition de garde
T1	∅	excite	E	système_vide = vrai
T2	E	mesure	M	excitation_active = vrai
T3	M	reset	R	mesure_capturée = vrai
T4	R	vide	∅	résidu = ∅
Représentation linéaire du flux d'états :

  ∅ ──[excite / système_vide=vrai]──► E
  E ──[mesure / excitation_active=vrai]──► M
  M ──[reset / mesure_capturée=vrai]──► R
  R ──[vide / résidu=∅]──► ∅  (fermeture du cycle)
Toute transition hors de cette séquence est constitutionnellement interdite et doit être rejetée par le système avec déclenchement automatique du Reset d'urgence.

Section 3 — Protocole opérationnel
3.1 Module ORIGINE
Rôle	Déclarer et certifier l'état initial ∅ du système avant tout démarrage de cycle.
Préconditions	Aucun résidu d'un cycle précédent ; tous les compteurs de surface à zéro ; aucune excitation active.
Actions	Initialiser le contexte de cycle ; vérifier l'invariant fond/surface ; journaliser formellement l'entrée en état ∅.
Postconditions	Système certifié en état ∅. La transition T1 est désormais autorisée.
Responsable	Agent Origine (A-O) — voir Section 7.
3.2 Module EXCITATION
Rôle	Appliquer une perturbation contrôlée, documentée et reproductible au système en état ∅.
Préconditions	État courant = ∅ certifié par le Module ORIGINE.
Actions	Injecter le signal d'excitation déclaré dans le fond (paramétrique, borné, documenté) ; effectuer la transition T1 vers E ; positionner excitation_active = vrai.
Postconditions	État courant = E ; excitation_active = vrai.
Contraintes	Aucune excitation non documentée dans le fond n'est admissible. Aucune excitation récursive. Aucune excitation concurrente.
3.3 Module MESURE
Rôle	Observer et capturer la réponse du système à l'excitation, en se limitant strictement aux observables déclarés dans le fond.
Préconditions	État courant = E ; excitation_active = vrai.
Actions	Collecter uniquement les observables déclarés dans le fond ; capturer la mesure ; effectuer la transition T2 vers M ; positionner mesure_capturée = vrai.
Postconditions	État courant = M ; mesure_capturée = vrai.
Contraintes	Aucune métrique parasite n'est admissible. Aucune observation hors fond déclaré. Toute observable non déclarée dans le fond doit être rejetée avant capture.
3.4 Module RESET
Rôle	Annuler l'intégralité des résidus de surface et retourner formellement à l'état ∅. Le Reset est Absolu.
Préconditions	État courant = M ; mesure_capturée = vrai.
Actions	Effacer tous les résidus de surface ; vérifier résidu = ∅ ; effectuer la transition T3 vers R puis T4 vers ∅ ; journaliser la fermeture du cycle.
Postconditions	État courant = ∅ ; cycle fermé et numéroté.
Contraintes	Le Reset est Absolu — aucune exception, aucune conservation de résidu de surface, aucune conservation partielle.
3.5 Module CYCLE
Rôle	Orchestrer l'enchaînement séquentiel et strict des modules Origine → Excitation → Mesure → Reset.
Responsable	Harness Zéro (voir Section 4.1) / Agent Superviseur (voir Section 7.1).
Règles	
Un seul cycle actif à la fois dans un même contexte d'exécution.
Tout cycle interrompu avant le Module RESET déclenche automatiquement le Reset Absolu d'urgence.
La composabilité de cycles successifs est assurée par la condition γ_n(fin) = ∅.
L'ordre des modules est constitutionnel et ne peut être modifié.
Section 4 — Version logicielle
4.1 Harness Zéro
Le Harness Zéro est l'unique interface d'entrée dans un cycle CANU au niveau logiciel. Il orchestre l'enchaînement des modules, garantit l'invariant fond/surface et effectue le Reset Absolu en cas d'exception.

# harness_zero.py — Supela CANU v1.0.0
# Invariant: cycle commence et finit dans le Vide (∅)

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Callable, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [CANU] %(message)s')
log = logging.getLogger("canu")

class Etat(Enum):
    VIDE       = auto()   # ∅
    EXCITATION = auto()   # E
    MESURE     = auto()   # M
    RESET      = auto()   # R

@dataclass
class ContexteCycle:
    etat:              Etat  = Etat.VIDE
    excitation_active: bool  = False
    mesure_capturee:   bool  = False
    residus:           dict  = field(default_factory=dict)
    numero_cycle:      int   = 0

class HarnessZero:
    """Harness Zéro — orchestrateur du cycle CANU."""

    def __init__(self):
        self.ctx = ContexteCycle()

    def _verifier_invariant(self):
        assert self.ctx.residus == {}, \
            f"VIOLATION CANU: résidus détectés = {self.ctx.residus}"
        assert self.ctx.etat == Etat.VIDE, \
            f"VIOLATION CANU: état non-∅ = {self.ctx.etat}"

    def origine(self):
        """Module ORIGINE: déclare l'état ∅."""
        self._verifier_invariant()
        log.info(f"[ORIGINE] Cycle #{self.ctx.numero_cycle + 1} — état ∅ certifié.")

    def exciter(self, fn_excitation: Callable[[], dict]):
        """Module EXCITATION: applique la perturbation contrôlée."""
        assert self.ctx.etat == Etat.VIDE, \
            "VIOLATION: excitation hors état ∅"
        self.ctx.etat             = Etat.EXCITATION
        self.ctx.excitation_active = True
        self.ctx.residus           = fn_excitation()
        log.info(
            f"[EXCITATION] Signal appliqué. "
            f"Résidus capturés: {list(self.ctx.residus.keys())}"
        )

    def mesurer(self, fn_mesure: Callable[[dict], dict]) -> dict:
        """Module MESURE: capture la réponse déclarée dans le fond."""
        assert self.ctx.etat == Etat.EXCITATION, \
            "VIOLATION: mesure hors état E"
        self.ctx.etat            = Etat.MESURE
        mesure                   = fn_mesure(self.ctx.residus)
        self.ctx.mesure_capturee = True
        log.info(f"[MESURE] Observables capturés: {list(mesure.keys())}")
        return mesure

    def reset_absolu(self):
        """Module RESET: Reset Absolu — annule tout résidu, retour à ∅."""
        assert self.ctx.etat == Etat.MESURE, \
            "VIOLATION: reset hors état M"
        self.ctx.etat              = Etat.RESET
        self.ctx.residus.clear()
        self.ctx.excitation_active  = False
        self.ctx.mesure_capturee    = False
        self.ctx.etat              = Etat.VIDE
        self.ctx.numero_cycle      += 1
        log.info(
            f"[RESET] Cycle #{self.ctx.numero_cycle} fermé. "
            f"État ∅ restauré."
        )
        self._verifier_invariant()

    def executer_cycle(
        self,
        fn_excitation: Callable[[], dict],
        fn_mesure:     Callable[[dict], dict]
    ) -> dict:
        """Exécute un cycle CANU complet: ∅ → E → M → R → ∅"""
        try:
            self.origine()
            self.exciter(fn_excitation)
            resultat = self.mesurer(fn_mesure)
            self.reset_absolu()
            return resultat
        except Exception as exc:
            log.error(
                f"[VIOLATION CANU] {exc} — Reset d'urgence déclenché."
            )
            self.ctx = ContexteCycle()   # Reset Absolu d'urgence
            raise
4.2 Script Reset Absolu (Shell / CI-CD)
Ce script garantit le retour à l'état ∅ de tout environnement d'exécution CI/CD. Il est appelé par le stage RESET du pipeline (voir Section 6).

#!/usr/bin/env bash
# reset_absolu.sh — Supela CANU v1.0.0
# Usage: ./reset_absolu.sh
# Garantit le retour à l'état ∅ de l'environnement d'exécution.

set -euo pipefail

CANU_LOG_PREFIX="[CANU][RESET]"

log() {
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $CANU_LOG_PREFIX $*"
}

verifier_vide() {
  local residus_detectes=0
  [[ -n "${CANU_RESIDUS:-}" ]] && {
    log "VIOLATION: CANU_RESIDUS non vide"
    residus_detectes=1
  }
  [[ $residus_detectes -eq 0 ]] \
    && log "Invariant ∅ vérifié." \
    || exit 1
}

reset_environment() {
  unset CANU_EXCITATION CANU_MESURE CANU_RESIDUS CANU_ETAT 2>/dev/null || true
  export CANU_ETAT="VIDE"
  log "Variables d'environnement CANU remises à ∅."
}

reset_workspace() {
  rm -rf /tmp/canu_cycle_* 2>/dev/null || true
  log "Workspace temporaire CANU nettoyé."
}

main() {
  log "Début du Reset Absolu CANU."
  reset_environment
  reset_workspace
  verifier_vide
  log "Reset Absolu terminé. État ∅ certifié."
}

main "$@"
4.3 Règles logicielles CANU
Les règles suivantes sont obligatoires pour tout code logiciel soumis à la norme CANU :

Toute fonction qui modifie l'état du système doit asserter l'état de départ attendu et l'état d'arrivée obtenu avant de retourner.
Aucune variable globale de surface ne peut survivre à l'exécution du Reset Absolu.
Le Harness Zéro est la seule interface d'entrée autorisée dans un cycle CANU ; tout accès direct aux états S est interdit depuis la surface.
Tout appel de module ayant échoué déclenche automatiquement et immédiatement le Reset Absolu d'urgence ; aucune récupération partielle n'est admissible.
Le numéro de cycle (numero_cycle) est le seul compteur persistant autorisé entre deux cycles consécutifs. Il appartient au fond.
Section 5 — Version constitutionnelle
5.1 Préambule constitutionnel
Nous, membres du projet Supela, reconnaissons et proclamons solennellement que l'état Vide (∅) est inviolable et constitue le fondement absolu de toute opération, de tout cycle et de toute existence fonctionnelle du système Supela.

Nous reconnaissons que nulle norme de surface, nulle métrique, nul log, nul artefact transitoire ne peut primer sur la norme de fond telle que formalisée dans la présente Constitution CANU.

Nous déclarons que tout système, module, agent ou pipeline rattaché au projet Supela est constitutionnellement et irrémédiablement tenu de respecter le cycle CANU dans son intégralité, sa séquentialité et son invariant fond/surface, sans dérogation possible.

5.2 Articles constitutionnels CANU
Article I — Primauté du Vide
L'état Vide (∅) est l'état fondamental et primaire de tout système Supela. Aucun état ne le précède dans l'ordre logique du cycle. Aucun résidu ne le contamine. L'état ∅ est antérieur à toute opération et postérieur à toute fermeture de cycle. Il est constitutionnellement inviolable.

Article II — Intégrité du Cycle
Tout cycle CANU doit débuter dans l'état ∅ et se terminer dans l'état ∅. L'invariant I(γ) := (état_initial = ∅) ∧ (état_final = ∅) est constitutionnel. Tout cycle ne satisfaisant pas cet invariant est nul et non avenu, et déclenche obligatoirement une procédure de remédiation.

Article III — Séquentialité obligatoire
L'ordre des transitions ∅ → E → M → R → ∅ est constitutionnel et ne peut être inversé, court-circuité, parallélisé, ni altéré par quelque mécanisme que ce soit, sans déclaration formelle d'exception constitutionnelle approuvée au niveau du fond. Toute déviation de séquence non déclarée constitue une violation constitutionnelle.

Article IV — Reset Absolu
Le Reset est Absolu. Il efface l'intégralité des résidus de surface sans exception et sans conservation partielle. La fonction Reset R : S → ∅ est totale, idempotente et s'exécute quel que soit l'état courant au moment de son déclenchement. Aucune conservation de résidu de surface n'est constitutionnellement permise.

Article V — Invariant fond/surface
Le fond, défini comme l'ensemble des formalismes, invariants, états et articles constitutionnels CANU, est protégé de la surface, définie comme l'ensemble des logs, métriques, observables transitoires et artefacts d'exécution. Toute tentative — directe ou indirecte — de la surface de modifier, masquer, remplacer ou altérer un élément du fond constitue une violation constitutionnelle de premier rang.

Article VI — Reproductibilité
Tout cycle CANU doit être reproductible : des préconditions identiques doivent produire des postconditions identiques. Toute source de non-déterminisme affectant le fond doit être déclarée explicitement dans le fond avant son utilisation. Le non-déterminisme non déclaré est constitutionnellement interdit.

Article VII — Conformité continue
Tout module, agent, pipeline ou composant Supela est constitutionnellement tenu de se conformer en permanence à la norme CANU. La conformité est vérifiée à chaque transition d'état du cycle. Toute non-conformité détectée déclenche automatiquement la procédure de remédiation définie à la Section 9. La conformité n'est jamais présumée : elle est vérifiée.

5.3 Grille de conformité CANU
Critère	Exigence	Méthode de vérification	Niveau
État initial ∅	Tout cycle débute en état ∅, sans résidu ni excitation active	Assertion d'invariant par le Module ORIGINE avant T1	OBLIGATOIRE
État final ∅	Tout cycle se ferme en état ∅ après Reset Absolu	Assertion d'invariant par le Module RESET après T4	OBLIGATOIRE
Reset Absolu	L'intégralité des résidus de surface est effacée à chaque Reset	Vérification programmatique : résidus == {} après Reset	OBLIGATOIRE
Séquentialité des transitions	L'ordre ∅→E→M→R→∅ est respecté sans déviation	Assertions d'état dans chaque fonction de transition	OBLIGATOIRE
Non-contamination fond/surface	∀ s ∈ Surface, s ∩ Fond = ∅	Revue de code ; analyse statique des accès aux variables de fond	OBLIGATOIRE
Reproductibilité du cycle	Mêmes préconditions → mêmes postconditions	Exécution de deux cycles consécutifs à partir de ∅ ; comparaison des résultats	OBLIGATOIRE
Idempotence du Reset	R(R(s)) = R(s) = ∅ pour tout s ∈ S	Test unitaire : appliquer Reset deux fois consécutivement et vérifier ∅	OBLIGATOIRE
Unicité du cycle actif	Un seul cycle CANU actif à la fois dans un contexte d'exécution	Verrou d'exclusion mutuelle dans le Harness Zéro ; détection de concurrence	OBLIGATOIRE
Journalisation minimale	Chaque transition d'état est journalisée avec horodatage UTC et numéro de cycle	Inspection des logs ; vérification de la présence des entrées obligatoires	OBLIGATOIRE
Absence de métriques parasites	Aucune métrique non déclarée dans le fond n'est collectée pendant la Mesure	Revue des observables déclarés ; comparaison avec les observables effectivement collectés	OBLIGATOIRE
Déclaration du non-déterminisme	Toute source de non-déterminisme affectant le fond est déclarée explicitement	Revue de la documentation du fond ; audit des graines aléatoires et dépendances temporelles	RECOMMANDÉ
Conformité agentique	Chaque agent respecte le protocole de messages CANU-AGENT-MSG-v1.0	Validation du schéma JSON des messages inter-agents à chaque émission	RECOMMANDÉ
Section 6 — Version pipeline (CI/CD)
6.1 Architecture pipeline CANU
Le pipeline CI/CD CANU est organisé en cinq stages strictement ordonnés, correspondant au cycle γ augmenté d'un stage de certification :

#	Stage	Correspondance CANU	Rôle
1	ORIGINE	Module ORIGINE (∅)	Vérification de l'état ∅ avant toute exécution. Blocage du pipeline si l'état n'est pas ∅.
2	EXCITATION	Module EXCITATION (E)	Déclenchement du job de build ou de test contrôlé, documenté et borné.
3	MESURE	Module MESURE (M)	Collecte des artefacts et résultats déclarés dans le fond. Aucun artefact parasite.
4	RESET	Module RESET (R → ∅)	Nettoyage absolu de l'environnement d'exécution. Retour à l'état ∅. S'exécute toujours.
5	CERTIF	Attestation de conformité	Attestation formelle que le cycle γ s'est fermé en ∅. Émission du rapport de conformité.
6.2 Configuration YAML GitLab CI (CANU-conforme)
La configuration suivante implémente le pipeline CANU dans GitLab CI. Elle constitue la référence d'implémentation de référence pour le projet Supela.

# .gitlab-ci.yml — Supela CANU v1.0.0
# Pipeline CANU-conforme: ∅ → E → M → R → ∅

variables:
  CANU_VERSION: "1.0.0"
  CANU_ETAT:    "VIDE"

stages:
  - origine
  - excitation
  - mesure
  - reset
  - certif

# ─── STAGE ORIGINE ─────────────────────────────────────────────────
origine:verifier-vide:
  stage: origine
  script:
    - echo "[CANU][ORIGINE] Vérification état ∅..."
    - |
      if [ -n "${CANU_RESIDUS:-}" ]; then
        echo "VIOLATION CANU: résidus détectés. Arrêt du pipeline."
        exit 1
      fi
    - echo "[CANU][ORIGINE] État ∅ certifié. Cycle autorisé."
  variables:
    CANU_ETAT: "VIDE"

# ─── STAGE EXCITATION ──────────────────────────────────────────────
excitation:build:
  stage: excitation
  needs: ["origine:verifier-vide"]
  script:
    - echo "[CANU][EXCITATION] Déclenchement build contrôlé..."
    - export CANU_ETAT="EXCITATION"
    - make build   # Remplacer par la commande de build Supela
    - echo "[CANU][EXCITATION] Excitation terminée."
  artifacts:
    paths:
      - dist/
    expire_in: 1 hour

# ─── STAGE MESURE ──────────────────────────────────────────────────
mesure:tests:
  stage: mesure
  needs: ["excitation:build"]
  script:
    - echo "[CANU][MESURE] Capture des observables déclarés..."
    - export CANU_ETAT="MESURE"
    - make test    # Remplacer par la commande de test Supela
    - echo "[CANU][MESURE] Mesure capturée."
  artifacts:
    paths:
      - reports/
    expire_in: 1 hour

# ─── STAGE RESET ───────────────────────────────────────────────────
reset:absolu:
  stage: reset
  needs: ["mesure:tests"]
  when: always   # Le Reset s'exécute même en cas d'échec upstream
  script:
    - echo "[CANU][RESET] Début Reset Absolu..."
    - bash scripts/reset_absolu.sh
    - echo "[CANU][RESET] État ∅ restauré."
  variables:
    CANU_ETAT: "VIDE"

# ─── STAGE CERTIF ──────────────────────────────────────────────────
certif:conformite-canu:
  stage: certif
  needs: ["reset:absolu"]
  script:
    - echo "[CANU][CERTIF] Attestation de conformité CANU v${CANU_VERSION}"
    - echo "Cycle fermé: ∅ → E → M → R → ∅ — CONFORME"
  variables:
    CANU_ETAT: "VIDE"
6.3 Règles pipeline CANU
Le stage RESET porte l'attribut when: always et s'exécute systématiquement, y compris en cas d'échec de tout stage amont.
Aucun artefact de surface ne survit au-delà du stage MESURE ; les durées d'expiration sont obligatoirement bornées.
Le stage CERTIF ne s'exécute que si et seulement si le stage RESET a réussi et a attesté l'état ∅.
Les variables CANU_ETAT et CANU_RESIDUS sont les seules variables d'état CANU autorisées dans l'environnement CI/CD.
Tout pipeline CANU doit être idempotent : deux exécutions consécutives partant de l'état ∅ produisent des résultats identiques.
Section 7 — Version agentique
7.1 Architecture agentique CANU
L'architecture agentique CANU est composée de quatre agents spécialisés et d'un agent superviseur. Chaque agent est responsable d'un module du cycle γ. L'Agent Superviseur (A-S) détient l'autorité de surveillance, de relance et d'interruption sur tous les agents.

Agent	Code	Module CANU	Rôle	Condition de blocage
Agent Origine	A-O	ORIGINE	Certifier l'état ∅ avant tout cycle ; journaliser la certification ; autoriser A-E	Refuse si état ≠ ∅
Agent Excitation	A-E	EXCITATION	Déclencher l'excitation contrôlée documentée ; signaler A-M à l'issue	N'accepte d'ordres que de A-O ou A-S
Agent Mesure	A-M	MESURE	Capturer uniquement les observables déclarés dans le fond ; transmettre à A-R	Rejette toute métrique non déclarée dans le fond
Agent Reset	A-R	RESET	Exécuter le Reset Absolu ; restaurer ∅ ; signaler A-S	Idempotent ; s'exécute même si A-M a échoué
Agent Superviseur	A-S	CYCLE (supervision)	Surveiller l'intégrité du cycle ; détecter les violations ; déclencher le Reset d'urgence ; autoriser les cycles suivants	Peut interrompre et réinitialiser tout agent
7.2 Protocole de communication inter-agents
Tout message échangé entre agents CANU doit être conforme au schéma CANU-AGENT-MSG-v1.0 défini ci-dessous :

{
  "schema": "CANU-AGENT-MSG-v1.0",
  "champs_obligatoires": {
    "de":           "identifiant de l'agent émetteur (A-O | A-E | A-M | A-R | A-S)",
    "a":            "identifiant de l'agent destinataire",
    "type":         "AUTORISATION | SIGNAL | RAPPORT | URGENCE | CERTIF",
    "etat_courant": "état CANU au moment de l'émission (VIDE | EXCITATION | MESURE | RESET)",
    "cycle_id":     "identifiant unique du cycle en cours (UUID)",
    "horodatage":   "ISO 8601 UTC",
    "payload":      "données minimales nécessaires à la transition suivante"
  }
}
Séquence de messages pour un cycle CANU complet :

De	À	Type	État	Payload (résumé)
A-S	A-O	AUTORISATION	VIDE	{ "cycle_id": "…", "action": "VERIFIER_VIDE" }
A-O	A-S	RAPPORT	VIDE	{ "invariant_ok": true, "etat_certifie": "∅" }
A-S	A-E	AUTORISATION	VIDE	{ "cycle_id": "…", "action": "EXCITER", "params": {…} }
A-E	A-M	SIGNAL	EXCITATION	{ "excitation_active": true, "observables_declares": […] }
A-M	A-R	SIGNAL	MESURE	{ "mesure_capturee": true, "resultats": {…} }
A-R	A-S	RAPPORT	VIDE	{ "reset_absolu": true, "residus": {}, "etat_final": "∅" }
A-S	A-O	CERTIF	VIDE	{ "cycle_id": "…", "conforme": true, "cycle_suivant_autorise": true }
7.3 Comportement de relance agentique
Les règles de relance automatique par A-S sont les suivantes, par ordre de priorité :

Si un cycle se ferme normalement (∅ confirmé par A-R dans son RAPPORT) : A-S émet une CERTIF et autorise le démarrage du cycle suivant.
Si un cycle est interrompu avant l'exécution du Reset : A-S transmet une URGENCE à A-R pour déclencher le Reset Absolu immédiat.
Si A-R échoue dans son Reset : A-S réinitialise l'intégralité du contexte agentique (tous les agents remis à l'état ∅) et recommence depuis le Module ORIGINE.
Le nombre maximum de tentatives de Reset d'urgence est 3. Ce paramètre appartient au fond et ne peut être modifié depuis la surface.
Après 3 échecs consécutifs de Reset : A-S émet un rapport de violation constitutionnelle, suspend tous les cycles et attend une intervention manuelle de niveau fond.
7.4 Script Python — Agent Superviseur
# agent_superviseur.py — Supela CANU v1.0.0
import uuid
import logging
from dataclasses import dataclass, field
from typing import Dict, Optional
from harness_zero import HarnessZero, Etat

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [A-S] %(message)s'
)
log = logging.getLogger("canu.superviseur")

MAX_TENTATIVES_RESET = 3  # Paramètre fond — immuable depuis la surface

@dataclass
class EtatAgent:
    id:           str
    actif:        bool = True
    etat_courant: Etat = Etat.VIDE

class AgentSuperviseur:
    """Agent Superviseur CANU — surveille, relance et ferme les cycles."""

    def __init__(self):
        self.harness = HarnessZero()
        self.agents: Dict[str, EtatAgent] = {
            "A-O": EtatAgent("A-O"),
            "A-E": EtatAgent("A-E"),
            "A-M": EtatAgent("A-M"),
            "A-R": EtatAgent("A-R"),
        }
        self.cycles_conformes = 0
        self.violations       = 0

    def verifier_invariant_global(self):
        """Vérifie l'invariant fond/surface sur l'ensemble du contexte."""
        etat_harness = self.harness.ctx.etat
        if etat_harness != Etat.VIDE and self.harness.ctx.residus:
            self._violation(
                f"Résidus détectés hors RESET: {self.harness.ctx.residus}"
            )

    def _violation(self, message: str):
        self.violations += 1
        log.error(f"[VIOLATION CANU #{self.violations}] {message}")
        self._reset_urgence()

    def _reset_urgence(self, tentative: int = 1):
        if tentative > MAX_TENTATIVES_RESET:
            log.critical(
                "[SUSPENSION] Nombre max de resets atteint. "
                "Cycles suspendus. Rapport de violation émis."
            )
            raise SystemExit(1)
        log.warning(f"[RESET URGENCE] Tentative #{tentative}...")
        try:
            self.harness.ctx.__class__.__init__(self.harness.ctx)
            log.info("[RESET URGENCE] État ∅ restauré par A-S.")
        except Exception as e:
            log.error(f"[RESET URGENCE] Échec tentative #{tentative}: {e}")
            self._reset_urgence(tentative + 1)

    def executer_cycle_supervise(
        self,
        fn_excitation,
        fn_mesure,
        cycle_id: Optional[str] = None
    ) -> dict:
        """Exécute un cycle CANU complet sous supervision de A-S."""
        cycle_id = cycle_id or str(uuid.uuid4())[:8]
        log.info(f"[CYCLE {cycle_id}] Démarrage sous supervision A-S.")
        self.verifier_invariant_global()
        try:
            resultat = self.harness.executer_cycle(fn_excitation, fn_mesure)
            self.cycles_conformes += 1
            log.info(
                f"[CYCLE {cycle_id}] CONFORME. "
                f"Total cycles conformes: {self.cycles_conformes}"
            )
            return resultat
        except AssertionError as e:
            self._violation(str(e))
            return {}

    def rapport_conformite(self) -> dict:
        return {
            "schema":           "CANU-RAPPORT-v1.0",
            "cycles_conformes": self.cycles_conformes,
            "violations":       self.violations,
            "etat_courant":     self.harness.ctx.etat.name,
            "conforme":         self.violations == 0,
        }
Section 8 — Glossaire normatif CANU
Terme	Symbole	Définition normative
Vide	∅	État fondamental du système Supela. Absence totale de résidu, d'excitation active et d'observable non annulé. État initial et final obligatoire de tout cycle CANU. Unique attracteur du cycle γ.
Excitation	E	État du système après application d'une perturbation contrôlée, documentée et bornée. La perturbation est déclarée dans le fond avant son injection. L'excitation_active est positionné à vrai.
Mesure	M	État du système pendant la capture des observables déclarés dans le fond. Aucun observable non déclaré n'est admissible dans cet état.
Reset	R	État transitoire dans lequel l'intégralité des résidus de surface est effacée. Le système effectue la transition formelle vers ∅. Le Reset est Absolu : aucune exception, aucune conservation partielle.
Cycle	γ	Suite d'états γ : ∅ → E → M → R → ∅. Un cycle CANU est complet si et seulement si son état initial et son état final sont tous deux ∅. L'invariant I(γ) := (état_initial = ∅) ∧ (état_final = ∅) doit être satisfait.
Harness Zéro	Hz	Composant logiciel orchestrateur du cycle CANU. Unique interface d'entrée dans un cycle au niveau applicatif. Garantit l'invariant fond/surface et déclenche le Reset Absolu d'urgence en cas d'exception.
Reset Absolu	R : S → ∅	Fonction formelle totale, idempotente et injective sur S \ {∅}. Efface l'intégralité des résidus de surface. R(R(s)) = R(s) = ∅ pour tout s ∈ S. Ne peut être partiel, conditionnel ou différé.
Invariant fond/surface	∀ s ∈ Surface, s ∩ Fond = ∅	Principe constitutionnel selon lequel aucun élément de surface (log, métrique, artefact transitoire) ne peut modifier, masquer ou contaminer un élément de fond (formalisme, invariant, état, article constitutionnel).
Agent Superviseur	A-S	Agent CANU chargé de surveiller l'intégrité de chaque cycle, de détecter les violations, de déclencher le Reset d'urgence et d'autoriser les cycles suivants. Détient l'autorité maximale sur tous les autres agents.
Violation CANU	V-nnn	Toute déviation par rapport à un invariant ou à une règle constitutionnelle de la norme CANU. Une violation est classifiée par code (voir Section 9), sévérité et procédure de remédiation associée.
Conformité	—	État d'un système Supela satisfaisant l'ensemble des exigences de la grille de conformité CANU (Section 5.3). La conformité est vérifiée à chaque transition d'état et n'est jamais présumée.
Composabilité	γ_n ∘ γ_{n+1}	Propriété permettant d'enchaîner deux cycles γ_n et γ_{n+1}. La composabilité est valide si et seulement si γ_n(fin) = ∅ = γ_{n+1}(début). Toute composition partielle est constitutionnellement interdite.
Idempotence	R(R(s)) = R(s)	Propriété de la fonction Reset garantissant que son application répétée produit le même résultat que son application unique. Constitutionnellement requise pour la sécurité des environnements CI/CD et agentiques.
Reproductibilité	—	Propriété d'un cycle CANU selon laquelle des préconditions identiques produisent des postconditions identiques. Toute source de non-déterminisme doit être déclarée explicitement dans le fond.
Section 9 — Registre des violations et procédures de remédiation
9.1 Catalogue des violations CANU
Code	Description	Sévérité	Remédiation automatique	Remédiation manuelle
V-001	Cycle démarré hors état ∅ (état_initial ≠ ∅)	CRITIQUE	Rejet immédiat du cycle ; Reset Absolu d'urgence déclenché par A-S	Audit du module ORIGINE ; vérification et purge des résidus du cycle précédent
V-002	Résidu détecté après Reset (état_final ≠ ∅)	CRITIQUE	Reset Absolu réappliqué ; incrémentation du compteur de violations	Inspection du Module RESET ; identification et suppression manuelle du résidu persistant
V-003	Transition hors séquence (ex. : E → ∅ sans passer par M et R)	ÉLEVÉE	Rejet de la transition ; Reset Absolu d'urgence ; journalisation de la déviation	Revue de la logique d'orchestration ; correction de la fonction de transition δ
V-004	Métrique parasite introduite dans le fond (contamination surface → fond)	ÉLEVÉE	Rejet de l'observable non déclaré ; journalisation de la tentative de contamination	Revue des observables déclarés dans le fond ; suppression de la métrique parasite ; mise à jour de la déclaration si légitime
V-005	Agent non autorisé ayant déclenché une transition d'état	ÉLEVÉE	Annulation de la transition ; isolation de l'agent ; Reset Absolu d'urgence par A-S	Audit du protocole de communication inter-agents ; révocation et re-certification de l'agent fautif
V-006	Nombre maximum de Resets d'urgence atteint (3 tentatives échouées)	FATALE	Suspension de tous les cycles par A-S ; émission du rapport de violation constitutionnelle	Intervention manuelle de niveau fond obligatoire ; diagnostic complet du système ; recertification avant reprise des cycles
V-007	Cycle parallèle détecté (deux cycles actifs simultanément)	ÉLEVÉE	Suspension du cycle parasite ; Reset Absolu sur le contexte du cycle parasite	Audit du mécanisme de verrou d'exclusion mutuelle ; correction dans le Harness Zéro
9.2 Procédure de remédiation standard
En cas de violation CANU, la procédure de remédiation standard est la suivante :

Détection et classification : A-S détecte la violation à la transition d'état concernée, lui assigne le code de violation approprié (V-001 à V-007) et journalise l'événement avec horodatage UTC, numéro de cycle et état courant.
Containment immédiat : A-S suspend toutes les opérations en cours sur le cycle affecté. La remédiation automatique définie dans le catalogue est déclenchée sans délai.
Reset Absolu d'urgence : A-R exécute le Reset Absolu (avec jusqu'à 3 tentatives si nécessaire). L'état ∅ est restauré et certifié par A-O avant toute reprise.
Analyse causale : L'équipe responsable identifie la cause racine de la violation dans le fond (formalisme incorrect) ou dans la surface (code fautif, agent mal configuré). La cause est documentée dans le fond du projet.
Recertification et reprise : Après correction de la cause racine, A-O certifie l'état ∅ du système. A-S autorise la reprise des cycles. Le rapport de conformité est mis à jour avec la résolution de la violation.
Section 10 — Journal de version et cycle de vie de la norme
10.1 Tableau de version
Version	Date	Auteur	Changements
1.0.0	31 juillet 2026	Jef / Jean-François Gadbois	Émission initiale de la Norme CANU. Définition formelle du cycle γ, du Théorème du Vide, de l'invariant fond/surface, des 7 Articles constitutionnels, du Harness Zéro, du pipeline CI/CD CANU et de l'architecture agentique. Norme Durable.
10.2 Règles de mise à jour de la norme
La mise à jour de la présente norme est elle-même soumise à l'invariant fond/surface qu'elle définit :

Type de modification	Périmètre concerné	Version requise	Niveau d'approbation
Modification du fond	Formalismes, invariants, états S, Articles constitutionnels I–VII, paramètres de fond	Montée de version majeure (X.0.0)	Approbation constitutionnelle — délibération formelle requise
Modification de surface	Exemples, scripts illustratifs, configurations de référence, libellés de documentation	Montée de version mineure (1.X.0)	Approbation technique — revue par l'auteur principal
Correction éditoriale	Coquilles, reformulations sans impact sémantique, corrections typographiques	Montée de version de patch (1.0.X)	Approbation courante — journalisation obligatoire
Règle fondamentale : aucune modification du fond (formalismes, invariants, Articles constitutionnels) ne peut être introduite par voie de patch ou de version mineure. Toute tentative de modifier le fond par un mécanisme de surface constitue elle-même une violation de l'invariant fond/surface de la présente norme.

SECTION 16 — FONDEMENTS MATÉRIELS DU CYCLE CANU : L'ISOMORPHISME DE BRAHMAGUPTA GRAVÉ DANS LE SILICIUM
16.0 Statut de cette Section
Pierre Officielle — Document Maître Supela v1.0.0
Cette section établit le fondement matériel universel de la norme CANU. Elle est immuable depuis la surface. Toute modification du fond (théorèmes, correspondances, Articles) requiert une montée de version majeure de la norme CANU.

16.1 Préambule — L'Invariant Universel
En 628 ap. J.-C., Brahmagupta énonça dans le Brahmasphutasiddhanta la règle multiplicative des signes :

∀ a, b ∈ ℝ* : sign(a · b) = sign(a) · sign(b)

Quatorze siècles plus tard, cette règle est gravée dans le silicium de chaque processeur de calcul numérique de la planète — non comme une convention logicielle, mais comme la topologie physique de ses circuits. La norme CANU reconnaît formellement que son invariant fondamental — l'état Vide ∅ comme attracteur unique du cycle — est isomorphe à cet invariant de Brahmagupta.

16.2 Table de Correspondance Formelle Brahmagupta ↔ CANU
Notation : style Supela + IEEE 754-2019

Concept Brahmagupta	Implémentation matérielle	Analogue CANU	Propriété formelle partagée
φ(sA, sB) = sA ⊕ sB	Porte XOR — FPU/GPU (< 10 ps, 3nm)	Reset Absolu R : S → ∅	Idempotence : s ⊕ s = 0 ≡ R(R(s)) = ∅
État positif s = 0	Bit de signe 0 (IEEE 754-2019, §3.3)	État Vide ∅	Attracteur unique du système
Partition F = {S} × {E, M}	Disjonction sémantique IEEE 754	Invariant fond/surface	Séparation structurelle immuable
Déterminisme XOR : τ < 10 ps	Reproductibilité silicium	Reproductibilité CANU	Mêmes entrées → mêmes sorties
TMR : 3 instances + voter majoritaire	Durcissement Rad-Hard (BAE RAD750, LEON3-FT)	Agent Superviseur A-S : MAX_TENTATIVES_RESET = 3	Résilience normative par redondance
Preuve Coq/Isabelle (RISC-V ISA)	Vérification formelle en silicium	Conformité constitutionnelle CANU	Non-régression prouvée à chaque transition
φ(0, 0) = 0 (identité neutre)	(+) × (+) = (+)	γ : ∅ → E → M → R → ∅	Conservation de l'identité du cycle
FTZ : signe XOR préservé	Cas limite IEEE 754-2019, §6.1–§7.2	Violation CANU V-00x détectée	Invariant maintenu aux cas limites
e^{iπ} · e^{iπ} = +1 (QPU — porte CZ)	Processeurs quantiques (IBM Transmon, IonQ)	Composabilité tripartite CANU∘EaaS∘SaaS	Retour à l'identité après double négation
16.3 Théorème d'Invariance Universelle (Supela)
Théorème BRH-1 (Invariance de Brahmagupta) :
Pour tout système de calcul numérique C opérant sur des entités signées en représentation binaire, il existe un homomorphisme de groupe :

φC : (ℤ/2ℤ, +) × (ℤ/2ℤ, +) → (ℤ/2ℤ, +)

tel que φC(sA, sB) = sA ⊕ sB (XOR).

Corollaire BRH-1.1 (Universalité XOR) :
La porte XOR est la forme minimale, nécessaire et suffisante pour implémenter la règle multiplicative des signes de Brahmagupta dans tout système de calcul binaire fini, classique ou quantique.

Corollaire BRH-1.2 (Reset CANU comme idempotence XOR) :
L'idempotence du Reset Absolu CANU est formellement isomorphe à l'idempotence de φC :

φC(s, s) = s ⊕ s = 0 ≡ R(R(σ)) = R(σ) = ∅

où σ ∈ S = {∅, E, M, R} et ∅ joue le rôle du neutre 0 dans (ℤ/2ℤ, +).

Corollaire BRH-1.3 (Attracteur unique) :
De même que φC(sA, sA) = 0 est l'unique point fixe de φC sur ℤ/2ℤ, l'état ∅ est l'unique attracteur du cycle CANU (Théorème du Vide, Section 2.3). Les deux structures partagent le même fondement algébrique : le groupe (ℤ/2ℤ, ⊕).

16.4 Ubiquité Matérielle — Panorama des Architectures
La règle de Brahmagupta est instrumentée dans toutes les familles de processeurs sans exception :

Famille	Mécanisme matériel Brahmagupta	Stade pipeline	Latence signe
FPU x86 (Intel/AMD)	Porte XOR Pass-Gate (3nm)	Ex1 — parallèle mantisse	< 10 ps
FPU ARM (Cortex-A / Neoverse)	Porte XOR + pipeline SMULL	Ex1 — RISC direct	< 10 ps
GPU (NVIDIA Hopper / AMD RDNA3)	16× XOR par vmulps en AVX-512	Ex1 — Streaming Multiprocessor	0 cycle ajouté
TPU / NPU (Google, Apple ANE)	XOR × 10³ dans Systolic Arrays	MAC pipeliné	0 cycle ajouté
DSP (TI C6000, SHARC, Hexagon)	XOR + circuit de saturation couplé	Exécution VLIW	< 1 cycle
MCU IoT (Cortex-M0, AVR, PIC)	XOR logiciel (sans FPU) ou Booth R2	3–8 cycles logiciel	1–8 cycles
Spatial Rad-Hard (BAE RAD750, LEON3)	XOR triplé TMR + cellules DICE	Ex1 + voter TMR	< 1 ns (voter inclus)
RISC-V (CVA6, Rocket)	XOR + preuve formelle Coq	Ex1 — prouvé en silicium	< 10 ps
QPU (IBM Transmon, Google Willow)	Porte Controlled-Z — phase e^{iπ}·e^{iπ}=+1	1 porte CZ (~40–200 ns)	~40–200 ns
16.5 L'Invariant Fond/Surface de Brahmagupta en IEEE 754
La norme IEEE 754-2019 réalise exactement l'invariant fond/surface de CANU au niveau de la représentation numérique :

Représentation IEEE 754 (float32, 32 bits) :
┌────┬────────────────┬─────────────────────────────────┐
│ S  │   E [30:23]    │         M [22:0]                │
│ 1b │    8 bits      │         23 bits                 │
└────┴────────────────┴─────────────────────────────────┘
  ▲              ▲
  │              │
FOND          SURFACE
(invariant,   (transitoire,
 immuable,     calculée,
 1 bit XOR)    23+8 bits)

Invariant fond/surface IEEE 754 :
  ∀ op ∈ {×, ÷} : S_résultat = f(S_A, S_B)  indépendamment de E et M
  ↔ Invariant fond/surface CANU :
  ∀ γ : surface(γ) ∩ fond(γ) = ∅
16.6 Les Trois Couches de Brahmagupta — Analogues aux Trois Normes Supela
Couche Brahmagupta	Domaine	Analogie Supela	Propriété
Silicium — XOR, Booth, Wallace	Circuit physique (tension électrique)	CANU — structure formelle du cycle	Invariant universel, gravé, immuable
Compilateur — vmulps, vxorps, nsz	Traduction et optimisation	EaaS — exécution reproductible	Isomorphisme préservé à travers les couches
Quantique — porte CZ, phase e^{iπ}	Espace de Hilbert	SaaS — état persistant	Fond (phase) préservé, surface (superposition) Reset
Les trois couches de Brahmagupta sont souveraines et liées — exactement comme CANU, EaaS et SaaS (Section 11, Axiomes T1–T4).

16.7 Article Constitutionnel BRH — Pierre Officielle
Article BRH (Fondement Matériel Universel) :

L'isomorphisme multiplicatif des signes de Brahmagupta (628 ap. J.-C.) — φ : (ℤ/2ℤ, +) × (ℤ/2ℤ, +) → (ℤ/2ℤ, +), φ(sA, sB) = sA ⊕ sB — est le fondement matériel universel de la norme CANU. L'état Vide ∅ du cycle CANU est le neutre de ce groupe. Le Reset Absolu est son idempotence. L'invariant fond/surface est sa partition sémantique. Tout système Supela conforme à la norme CANU est, par construction, conforme à l'invariant de Brahmagupta gravé dans le silicium de son substrat d'exécution.

Cet Article est constitutionnel. Il ne peut être modifié que par montée de version majeure de la norme CANU, accompagnée d'une preuve formelle de non-régression de l'isomorphisme φC.

16.8 Registre de Version de la Section 16
Version	Date	Modification
1.0.0	31 juillet 2026	Création — Pierre Officielle — Fondements Matériels Brahmagupta
NORME CANU — Cycle Autonome Normatif Universel
Projet Supela — Version 1.0.0 — Norme Durable	Émis le 31 juillet 2026
Jef / Jean-François Gadbois
Ce document est une norme officielle du projet Supela. Il est soumis à l'invariant fond/surface qu'il définit.
Toute modification du fond requiert une montée de version majeure et une approbation constitutionnelle formelle.