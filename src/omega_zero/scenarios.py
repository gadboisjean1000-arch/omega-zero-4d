from __future__ import annotations

from typing import Any

from .models import (
    AuthorityLevel,
    DisciplineAssessment,
    Manque,
    ManqueStatus,
    MergeOutcome,
    Raccord,
    RaccordStatus,
)
from .projection import ManqueStateMachine, Pi0Projector
from .protocol import OmegaZeroEngine


def run_second_domain_hydrology_example() -> dict[str, Any]:
    """Exécute le second exemple inter-domaines complet (Hydrologie × Droit administratif × Secours × Éthique).

    Exerce :
    - Deux nœuds locaux déconnectés (L_Amont, L_Bassin) + Cloud
    - Détection de manque M-HYDRO-01
    - 3 candidats RH-01..RH-03 (réfuté, soutenu sous conditions, inconnu)
    - Conflit interdisciplinaire C-HYDRO-01 conservé
    - Rejet d'escalade d'autorité locale -> globale sur RH-01
    - Transitions d'états du Manque (OUVERT -> SOUS_EXPLORATION -> PARTIELLEMENT_RÉDUIT -> REQUALIFIÉ)
    - Statuts complémentaires (INACCESSIBLE_DANS_LE_PÉRIMÈTRE sur capteur satellitaire, RÉFUTÉ_COMME_PROBLÈME sur seuil saisonnier)
    - Projection Π₀ + idempotence + réouverture ciblée de cône
    """
    engine = OmegaZeroEngine()
    projector = Pi0Projector()

    l_amont = engine.register_local_node(
        "L_Amont", "Bassin Amont", "Municipalite-Nord", "HYDRO_CAPTEURS_AMONT"
    )
    l_bassin = engine.register_local_node(
        "L_Bassin", "Zone Urbaine Basse", "Municipalite-Centre", "COORDINATION_SECOURS_LOCAUX"
    )

    m_hydro = Manque(
        id="M-HYDRO-01",
        question="Validité du passage score prédictif hydrométrique → ordre obligatoire d'évacuation",
        contexte="Crue éclair avec connectivité Cloud intermittente",
        origine="Required(Évacuation_Automatique) \\ Available(S_0)",
        dependances=["O_H", "O_DA", "O_S", "O_E"],
        autorite="COMPETENCE_MUNICIPALE_EXCLUSIVE",
        temps="2026-11-15T20:00:00Z",
        statut=ManqueStatus.OUVERT,
    )
    engine.inject_manque(l_amont, m_hydro)

    # Manques complémentaires pour exercer tous les statuts canoniques dans le cycle
    m_sat = Manque(
        id="M-HYDRO-SAT",
        question="Disponibilité de données radar satellitaires haute fréquence en temps réel",
        contexte="Couverture nuageuse et absence d'accès API temps réel dans le périmètre local",
        origine="Capteur hors périmètre local",
        dependances=["SAT_API"],
        autorite="AGENCE_SPATIALE_EXTERNE",
        temps="2026-11-15T20:02:00Z",
        statut=ManqueStatus.OUVERT,
    )
    engine.inject_manque(l_amont, m_sat)
    ManqueStateMachine.transition(
        m_sat,
        ManqueStatus.INACCESSIBLE_DANS_LE_PERIMETRE,
        reason="Flux satellitaire hors compétence et hors connectivité du nœud local",
        actor="L_Amont",
        timestamp="2026-11-15T20:03:00Z",
        evidence_ref="BARRIERE_RESEAU_ET_COMPETENCE",
    )

    m_premisse = Manque(
        id="M-HYDRO-SEUIL-FIXE",
        question="Un seuil unique annuel de hauteur d'eau suffit-il toute l'année ?",
        contexte="Hypothèse d'un seuil estival appliqué en période d'embâcle hivernale",
        origine="Question initiale héritée d'un ancien modèle",
        dependances=["O_H"],
        autorite="HYDROLOGIE_LOCALE",
        temps="2026-11-15T20:04:00Z",
        statut=ManqueStatus.OUVERT,
    )
    engine.inject_manque(l_bassin, m_premisse)
    ManqueStateMachine.transition(
        m_premisse,
        ManqueStatus.REFUTE_COMME_PROBLEME,
        reason="Fausse prémisse prouvée : l'embâcle modifie la relation hauteur/débit.",
        actor="L_Bassin",
        timestamp="2026-11-15T20:05:00Z",
        evidence_ref="PREUVE_EMBACLE_HYDRAULIQUE",
    )

    # Injection des 3 candidats sur M-HYDRO-01
    rh1 = Raccord(
        id="RH-01",
        label="Déclenchement automatique obligatoire par score IA local",
        source="Score_IA",
        target="Ordre_Evacuation",
        origin_node="L_Amont",
        disciplines=["O_H", "O_DA", "O_E"],
        provenance="L_Amont:t1",
    )
    rh2 = Raccord(
        id="RH-02",
        label="Pré-alerte interne et pré-positionnement des secours",
        source="Score_IA",
        target="Prepositionnement_Secours",
        origin_node="L_Bassin",
        disciplines=["O_H", "O_DA", "O_S"],
        provenance="L_Bassin:t1",
    )
    rh3 = Raccord(
        id="RH-03",
        label="Recommandation d'évacuation ciblée avec validation humaine municipale",
        source="Score_IA",
        target="Decision_Maire",
        origin_node="L_Bassin",
        disciplines=["O_H", "O_DA", "O_S", "O_E"],
        provenance="L_Bassin:t1",
    )
    engine.add_candidate_raccord(l_amont, rh1, manque_id="M-HYDRO-01", timestamp="2026-11-15T20:06:00Z")
    engine.add_candidate_raccord(l_bassin, rh2)
    engine.add_candidate_raccord(l_bassin, rh3)
    # Répercuter RH-02 et RH-03 aussi dans le cloud pour l'épreuve
    engine.cloud.raccords["RH-02"] = rh2
    engine.cloud.raccords["RH-03"] = rh3

    # Évaluations disciplinaires conservées séparément + conflit C-HYDRO-01
    conflict = engine.record_discipline_assessments(
        "RH-01",
        [
            DisciplineAssessment("O_H", "RH-01", "FORTE_AMONT_FAIBLE_AVAL", "INCERTITUDE_CAPTEUR", "HYDROLOGIE", "Indicateur utile seulement"),
            DisciplineAssessment("O_DA", "RH-01", "BLOQUANTE", "ILLEGALITE_AUTOMATISATION", "DROIT_MUNICIPAL", "Acte municipal requis"),
            DisciplineAssessment("O_S", "RH-01", "FAVORABLE_PRE_ALERTE", "AUCUN", "SECOURS", "Utile en pré-positionnement interne"),
            DisciplineAssessment("O_E", "RH-01", "ALERTE_BIAIS", "SOUS_REPRESENTATION_ZONE_BASSE", "ETHIQUE", "Risque d'iniquité territoriale"),
        ],
        conflict_id="C-HYDRO-01",
    )

    # Épreuve : RH-01 réfuté, RH-02 soutenu sous conditions, RH-03 inconnu
    engine.cloud.raccords["RH-01"].status = RaccordStatus.REFUTE
    engine.cloud.raccords["RH-01"].authority_level = AuthorityLevel.AUCUNE
    engine.cloud.raccords["RH-01"].refutation_reason = "Absence de base légale municipale et biais zone basse"

    engine.cloud.raccords["RH-02"].status = RaccordStatus.SUPPORTE_SOUS_CONDITIONS
    engine.cloud.raccords["RH-02"].evidence_level = AuthorityLevel.COLLECTIVE_CONDITIONNELLE
    engine.cloud.raccords["RH-02"].authority_level = AuthorityLevel.COLLECTIVE_CONDITIONNELLE
    engine.cloud.raccords["RH-02"].conditions = ["Portée interne secours uniquement"]

    engine.cloud.raccords["RH-03"].status = RaccordStatus.INCONNU
    engine.cloud.raccords["RH-03"].authority_level = AuthorityLevel.AUCUNE

    # Delta L_Amont tentant une escalade non prouvée vers statut global
    d_amont = engine.build_delta(
        l_amont,
        delta_id="DELTA-AMONT-01",
        timestamp="2026-11-15T20:10:00Z",
        payload={
            "raccords": [
                {
                    "id": "RH-01-ESCALADE",
                    "label": "Tentative d'imposer RH-01 à toute l'agglomération",
                    "source": "L_Amont",
                    "target": "Agglomeration",
                }
            ]
        },
        requested_cloud_status="ÉTABLI_INTERNATIONALEMENT",
        international_proof_attached=False,
    )
    merge_outcome = engine.merge_delta(d_amont)

    # Évolution du manque M-HYDRO-01 : SOUS_EXPLORATION -> PARTIELLEMENT_RÉDUIT -> REQUALIFIÉ
    ManqueStateMachine.transition(
        m_hydro,
        ManqueStatus.SOUS_EXPLORATION,
        reason="Début d'épreuve interdisciplinaire sur RH-01..RH-03",
        actor="CLOUD",
        timestamp="2026-11-15T20:11:00Z",
        evidence_ref="RH-02",
    ) if m_hydro.statut == ManqueStatus.OUVERT else None
    ManqueStateMachine.transition(
        m_hydro,
        ManqueStatus.PARTIELLEMENT_REDUIT,
        reason="RH-02 soutenu pour pré-positionnement interne ; RH-03 reste ouvert",
        actor="CLOUD",
        timestamp="2026-11-15T20:12:00Z",
        evidence_ref="PREUVE_RH02",
    )
    ManqueStateMachine.transition(
        m_hydro,
        ManqueStatus.REQUALIFIE,
        reason="Scission vers M-HYDRO-01a (résolu partiellement) et M-HYDRO-01b (ouvert)",
        actor="CLOUD",
        timestamp="2026-11-15T20:13:00Z",
        children_ids=["M-HYDRO-01a", "M-HYDRO-01b"],
    )
    m_hydro_1b = Manque(
        id="M-HYDRO-01b",
        question="Validation humaine municipale et couverture équitable de RH-03",
        contexte="Sous-manque issu de M-HYDRO-01",
        origine="Scission M-HYDRO-01",
        dependances=["O_DA", "O_E", "RH-03"],
        autorite="AUTORITE_MUNICIPALE",
        temps="2026-11-15T20:13:00Z",
        statut=ManqueStatus.OUVERT,
        parent_id="M-HYDRO-01",
    )
    engine.cloud.manques["M-HYDRO-01"] = m_hydro
    engine.cloud.manques["M-HYDRO-01b"] = m_hydro_1b
    engine.cloud.manques["M-HYDRO-SAT"] = m_sat
    engine.cloud.manques["M-HYDRO-SEUIL-FIXE"] = m_premisse

    # Projection Π₀ et vérification d'idempotence
    zero = projector.project(engine.cloud)
    idempotent = projector.verify_idempotence(engine.cloud)

    # Réouverture ciblée sur nouvelle preuve
    reopen_info = engine.reopen_from_void(
        l_bassin,
        zero,
        "RH-02",
        "NouvellePreuve: saturation d'un pont aval modifiant les temps de pré-positionnement",
        "M-HYDRO-01b",
        timestamp="2026-11-15T20:20:00Z",
    )

    return {
        "example_id": "EX-P0-02",
        "conflict_preserved": conflict is not None and conflict.status == "CONSERVÉ",
        "merge_outcome": merge_outcome.value,
        "rejected_escalations": len(engine.cloud.rejected_escalations),
        "pi0_idempotent": idempotent,
        "pi0_non_empty": zero.is_non_empty(),
        "pi0_preserved_manques": sorted(zero.manques.keys()),
        "pi0_preserved_refutations": sorted(zero.refutations.keys()),
        "pi0_preserved_proofs": sorted(zero.proofs.keys()),
        "reopen_info": reopen_info,
    }
