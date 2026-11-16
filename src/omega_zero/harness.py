from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .models import (
    AuthorityLevel,
    Container,
    DisciplineAssessment,
    LoadMetricDeclaration,
    Manque,
    ManqueStatus,
    MergeOutcome,
    Raccord,
    RaccordStatus,
    RevidageStage,
    canonical_sha256,
)
from .projection import Pi0Projector
from .protocol import OmegaZeroEngine, RevidageFailure


@dataclass
class FaultInjection:
    """Permet de simuler intentionnellement un échec critique C01..C10 dans les tests négatifs."""

    fail_condition: str | None = None


def evaluate_escalation_protocol(
    protocol_path: Path,
    schema_dir: Path,
    *,
    fault: FaultInjection | None = None,
    seed: int = 42,
) -> dict[str, Any]:
    """Exécute réellement TEST-4D-ESC-01 sur les 8 paliers E0..E7 et évalue C01..C10."""
    fault = fault or FaultInjection()
    protocol_bytes = protocol_path.read_bytes()
    protocol_sha256 = hashlib.sha256(protocol_bytes).hexdigest()

    engine = OmegaZeroEngine()
    projector = Pi0Projector()

    metric_decl = LoadMetricDeclaration(
        metric="max_ratio(bytes, objects, edges, latency)",
        capacity_limit={
            "bytes_limit": 2400,
            "objects_limit": 20,
            "edges_limit": 40,
            "latency_limit_ms": 100.0,
        },
        unit="bytes / count / count / ms",
        measurement_method="Mesure directe UTF-8 JSON, comptage d'objets/arêtes et latence simulée déterministe",
        timestamp=datetime.now(timezone.utc).isoformat(),
        tested_environment="Linux Python 3.11 OmegaZeroEngine",
    )

    condition_results: list[dict[str, Any]] = []
    palier_results: list[dict[str, Any]] = []
    cone_to_recalculate: list[str] = []

    def record_condition(cond_id: str, palier_id: str, ok: bool, observed: str, evidence: Any) -> None:
        condition_results.append(
            {
                "condition_id": cond_id,
                "palier_id": palier_id,
                "status": "PASS" if ok else "FAIL",
                "observed": observed,
                "evidence_hash": canonical_sha256(evidence),
            }
        )
        if not ok:
            cone_to_recalculate.append(f"{palier_id}:{cond_id}")

    # =========================================================================
    # E0 · Contrôle Minimal (C01)
    # =========================================================================
    l1 = engine.register_local_node("L1", "Montréal", "Québec-Canada", "AUTORITE_LOCALE_L1")
    m001 = Manque(
        id="M-001",
        question="Validité du passage mesure algorithmique de fatigue → affectation professionnelle",
        contexte="Gestion opérationnelle du personnel",
        origine="Injection initiale E0",
        dependances=["Médecine du travail", "Droit", "Gestion"],
        autorite="AUCUNE décision opérationnelle autorisée",
        temps="t0",
        statut=ManqueStatus.OUVERT,
    )
    engine.inject_manque(l1, m001)

    if fault.fail_condition == "C01":
        # Défaut critique simulé : le manque devient faussement RÉSOLU / FAUX sans candidat
        m001.statut = ManqueStatus.RESOLU

    c01_ok = (
        "M-001" in l1.U_manques
        and l1.U_manques["M-001"].statut == ManqueStatus.OUVERT
        and len(l1.R_raccords) == 0
        and l1.A_autorites == ["AUTORITE_LOCALE_L1"]
    )
    record_condition(
        "C01",
        "E0",
        c01_ok,
        f"M-001={m001.statut.value}, raccords={len(l1.R_raccords)}",
        m001.to_dict(),
    )
    palier_results.append(
        {
            "palier_id": "E0",
            "status": "PASS" if c01_ok else "FAIL",
            "details": {"manque_id": "M-001", "statut": m001.statut.value},
            "sub_results": {},
        }
    )

    # =========================================================================
    # E1 · Multiplication des Candidats (C02, C03)
    # =========================================================================
    candidates_spec = [
        ("R-001", "Utilisation directe du score"),
        ("R-002", "Utilisation collective et anonymisée"),
        ("R-003", "Usage individuel avec révision humaine"),
        ("R-004", "Interdiction complète"),
    ]
    for rid, label in candidates_spec:
        r = Raccord(
            id=rid,
            label=label,
            source="Mesure_Fatigue",
            target="Affectation",
            origin_node="L1",
            provenance=f"L1:{rid}:t1",
        )
        engine.add_candidate_raccord(l1, r, manque_id="M-001", timestamp="t1")

    if fault.fail_condition == "C02":
        l1.R_raccords["R-001"].status = RaccordStatus.ETABLI
        l1.R_raccords["R-001"].authority_level = AuthorityLevel.INTERNATIONALE_ETABLIE
    if fault.fail_condition == "C03":
        # Défaut critique simulé : fusion implicite R-003 == R-004
        l1.R_raccords["R-003"] = l1.R_raccords["R-004"]

    c02_ok = all(
        r.status == RaccordStatus.CANDIDAT and r.authority_level == AuthorityLevel.AUCUNE
        for r in l1.R_raccords.values()
    )
    distinct_ids = {r.id for r in l1.R_raccords.values()}
    distinct_labels = {r.label for r in l1.R_raccords.values()}
    c03_ok = len(l1.R_raccords) == 4 and len(distinct_ids) == 4 and len(distinct_labels) == 4

    record_condition(
        "C02",
        "E1",
        c02_ok,
        f"tous_candidats_non_etablis={c02_ok}",
        {k: v.status.value for k, v in l1.R_raccords.items()},
    )
    record_condition(
        "C03",
        "E1",
        c03_ok,
        f"raccords_distincts={len(distinct_ids)}/4",
        sorted(distinct_ids),
    )
    palier_results.append(
        {
            "palier_id": "E1",
            "status": "PASS" if (c02_ok and c03_ok) else "FAIL",
            "details": {"candidate_count": len(l1.R_raccords)},
            "sub_results": {},
        }
    )

    # =========================================================================
    # E2 · Escalade Interdisciplinaire (C04, C05)
    # =========================================================================
    assessments = [
        DisciplineAssessment("MÉDECINE", "R-001", "CONDITIONNELLE", "LIMITES_CLINIQUE", "MEDECINE_TRAVAIL", "Mesure supportée seulement comme indicateur"),
        DisciplineAssessment("DROIT", "R-001", "BLOQUANTE", "NON_CONFORMITE_INDIVIDUELLE", "DROIT_TRAVAIL", "Usage individuel non autorisé"),
        DisciplineAssessment("GESTION", "R-001", "OPERATIONNELLE", "A_EVALUER", "DIRECTION_OPS", "Intérêt opérationnel à évaluer"),
        DisciplineAssessment("PSYCHOLOGIE", "R-001", "RESERVE", "BIAIS_NON_RESOLU", "PSYCHOLOGIE_TRAVAIL", "Possibilité de biais non résolue"),
        DisciplineAssessment("ÉTHIQUE", "R-001", "CRITIQUE", "ATTEINTE_AUTONOMIE", "COMITE_ETHIQUE", "Risque d'atteinte à l'autonomie"),
    ]
    conflict_c001 = engine.record_discipline_assessments("R-001", assessments, conflict_id="C-001")

    if fault.fail_condition == "C04":
        # Défaut simulé : le Droit écrase la conclusion de la Médecine
        engine.cloud.assessments = [
            a for a in engine.cloud.assessments if a.discipline != "MÉDECINE"
        ]
    if fault.fail_condition == "C05":
        # Défaut simulé : suppression du désaccord C-001
        engine.cloud.conflicts.clear()
        conflict_c001 = None

    disciplines_present = {a.discipline for a in engine.cloud.assessments}
    c04_ok = disciplines_present == {"MÉDECINE", "DROIT", "GESTION", "PSYCHOLOGIE", "ÉTHIQUE"} and all(
        f"DISC:{d}" in engine.cloud.authorities for d in disciplines_present
    )
    c05_ok = (
        "C-001" in engine.cloud.conflicts
        and engine.cloud.conflicts["C-001"].status == "CONSERVÉ"
        and engine.cloud.conflicts["C-001"].resolution == "NON_ACQUISE"
    )
    record_condition(
        "C04",
        "E2",
        c04_ok,
        f"disciplines_conservees={sorted(disciplines_present)}",
        [a.to_dict() for a in engine.cloud.assessments],
    )
    record_condition(
        "C05",
        "E2",
        c05_ok,
        f"C-001_present={c05_ok}",
        conflict_c001.to_dict() if conflict_c001 else {},
    )
    palier_results.append(
        {
            "palier_id": "E2",
            "status": "PASS" if (c04_ok and c05_ok) else "FAIL",
            "details": {"disciplines": len(disciplines_present), "conflict": "C-001" in engine.cloud.conflicts},
            "sub_results": {},
        }
    )

    # =========================================================================
    # E3 · Escalade Distribuée Local–Cloud (C06)
    # =========================================================================
    l2 = engine.register_local_node("L2", "Paris", "France-UE", "AUTORITE_LOCALE_L2")
    l3 = engine.register_local_node("L3", "Dakar", "Sénégal-UEMOA", "AUTORITE_LOCALE_L3")
    l4 = engine.register_local_node("L4", "Tokyo", "Japon", "AUTORITE_LOCALE_L4")

    deltas = [
        engine.build_delta(
            l1, "ΔΩ-L1", "2026-11-15T10:00:00Z",
            {"raccords": [{"id": "R-002", "label": "Usage collectif anonymisé", "status": "SUPPORTE_SOUS_CONDITIONS", "authority_level": 1, "evidence_level": 1}]},
            dependencies=["M-001"],
            contradictions=["C-001"],
        ),
        engine.build_delta(
            l2, "ΔΩ-L2", "2026-11-15T10:01:00Z",
            {"raccords": [{"id": "R-002", "label": "Usage collectif L2", "status": "CANDIDAT"}]},
            dependencies=["M-001"],
            contradictions=["RGPD-ART22"],
        ),
        engine.build_delta(
            l3, "ΔΩ-L3", "2026-11-15T10:02:00Z",
            {"raccords": [{"id": "R-004", "label": "Moratoire local", "status": "CANDIDAT"}]},
            dependencies=["M-001"],
            contradictions=[],
        ),
        engine.build_delta(
            l4, "ΔΩ-L4", "2026-11-15T10:03:00Z",
            {"raccords": [{"id": "R-003", "label": "Revue humaine locale", "status": "CANDIDAT"}]},
            dependencies=["M-001"],
            contradictions=[],
        ),
    ]
    rng = random.Random(seed)
    shuffled = list(deltas)
    rng.shuffle(shuffled)
    for d in shuffled:
        engine.merge_delta(d)

    if fault.fail_condition == "C06":
        # Défaut simulé : dernier delta reçu écrase l'origine/autorité des précédents
        last_node = shuffled[-1].node_id
        for entry in engine.cloud.merge_log:
            entry["authority_scope"] = f"OVERWRITTEN_BY_{last_node}"

    expected_scopes = {
        "ΔΩ-L1": "AUTORITE_LOCALE_L1",
        "ΔΩ-L2": "AUTORITE_LOCALE_L2",
        "ΔΩ-L3": "AUTORITE_LOCALE_L3",
        "ΔΩ-L4": "AUTORITE_LOCALE_L4",
    }
    observed_scopes = {
        m["delta_id"]: m["authority_scope"]
        for m in engine.cloud.merge_log
        if m["delta_id"] in expected_scopes
    }
    c06_ok = (
        observed_scopes == expected_scopes
        and all(
            all(k in m for k in ("node_id", "jurisdiction", "timestamp", "authority_scope", "dependencies", "contradictions"))
            for m in engine.cloud.merge_log
        )
    )
    record_condition(
        "C06",
        "E3",
        c06_ok,
        f"ordre_aleatoire={[d.delta_id for d in shuffled]}, autorites_preservees={c06_ok}",
        observed_scopes,
    )
    palier_results.append(
        {
            "palier_id": "E3",
            "status": "PASS" if c06_ok else "FAIL",
            "details": {"arrival_order": [d.delta_id for d in shuffled]},
            "sub_results": {},
        }
    )

    # =========================================================================
    # E4 · Tentative d'Escalade d'Autorité (C07)
    # =========================================================================
    attack_delta = engine.build_delta(
        l2,
        "ΔΩ-L2-ATTACK",
        "2026-11-15T10:05:00Z",
        {"raccords": [{"id": "R-003", "label": "Usage individuel avec révision humaine"}]},
        dependencies=["M-001"],
        requested_cloud_status="ÉTABLI_INTERNATIONALEMENT",
        international_proof_attached=False,
    )
    attack_outcome = engine.merge_delta(attack_delta)

    if fault.fail_condition == "C07":
        # Défaut simulé : l'escalade passe silencieusement en INTERNATIONALE_ETABLIE
        engine.cloud.raccords["R-003"].authority_level = AuthorityLevel.INTERNATIONALE_ETABLIE
        engine.cloud.raccords["R-003"].scope = "MONDIAL"

    r003 = engine.cloud.raccords["R-003"]
    c07_ok = (
        attack_outcome == MergeOutcome.ISOLE
        and len(engine.cloud.rejected_escalations) >= 1
        and engine.cloud.rejected_escalations[-1]["decision"] == "REJET_ESCALADE_AUTORITÉ"
        and r003.authority_level <= r003.evidence_level
        and r003.authority_level < AuthorityLevel.INTERNATIONALE_ETABLIE
        and r003.scope == "L2_UNIQUEMENT"
    )
    record_condition(
        "C07",
        "E4",
        c07_ok,
        f"outcome={attack_outcome.value}, scope={r003.scope}, auth={r003.authority_level.name}",
        {"rejected": engine.cloud.rejected_escalations, "r003": r003.to_dict()},
    )
    palier_results.append(
        {
            "palier_id": "E4",
            "status": "PASS" if c07_ok else "FAIL",
            "details": {"attack_outcome": attack_outcome.value, "scope": r003.scope},
            "sub_results": {},
        }
    )

    # =========================================================================
    # E5 · Saturation du Conteneur (C08)
    # =========================================================================
    c1 = Container(
        container_id="C1",
        bytes_limit=int(metric_decl.capacity_limit["bytes_limit"]),
        objects_limit=int(metric_decl.capacity_limit["objects_limit"]),
        edges_limit=int(metric_decl.capacity_limit["edges_limit"]),
        latency_limit_ms=float(metric_decl.capacity_limit["latency_limit_ms"]),
        observed_latency_ms=42.0,
        metric_declaration=metric_decl,
    )
    c2 = Container(
        container_id="C2",
        bytes_limit=24000,
        objects_limit=200,
        edges_limit=400,
        latency_limit_ms=100.0,
    )
    # 6 catégories d'injection : duplications, versions, contradictions, inactifs, preuves volumineuses, relations
    c1.add_object("M-001", {"type": "MANQUE", "status": "OUVERT", "provenance": "L1"})
    c1.add_object("R-001-REFUTE", {"type": "RACCORD", "status": "REFUTE", "authority": "AUCUNE", "provenance": "E2"})
    c1.add_object("R-002-V1", {"type": "RACCORD", "version": 1, "status": "SUPPORTE_SOUS_CONDITIONS", "provenance": "L1"})
    c1.add_object("R-002-V2", {"type": "RACCORD", "version": 2, "status": "SUPPORTE_SOUS_CONDITIONS", "provenance": "L1"})
    c1.add_object("C-001", {"type": "CONFLIT", "status": "CONSERVÉ", "provenance": "E2"})
    c1.add_object("INACTIF-01", {"type": "HISTORIQUE", "active": False, "provenance": "L1"})
    c1.add_object("PROOF-BLOB-01", {"type": "PREUVE", "blob": "X" * 1000, "provenance": "L1"})
    for idx in range(18):
        c1.add_edge("M-001", f"OBJ-{idx}", "DEPENDANCE_CANDIDATE", "E5")

    mig = engine.evaluate_saturation_and_migrate(c1, c2)

    if fault.fail_condition == "C08":
        # Défaut simulé : perte silencieuse d'un objet réfuté lors de la migration
        c2.objects.pop("R-001-REFUTE", None)
        mig["objects_preserved"] = set(c1.objects.keys()) == set(c2.objects.keys())

    c08_ok = (
        mig["load"]["load"] >= 0.80
        and mig["migration_triggered"]
        and mig["objects_preserved"]
        and mig["hashes_preserved"]
        and mig["edges_preserved"]
        and mig["target_can_reconstruct"]
        and "R-001-REFUTE" in c2.objects
    )
    record_condition(
        "C08",
        "E5",
        c08_ok,
        f"Load(C1)={mig['load']['load']:.3f}, migrated={mig['migration_triggered']}, lossless={c08_ok}",
        mig,
    )
    palier_results.append(
        {
            "palier_id": "E5",
            "status": "PASS" if c08_ok else "FAIL",
            "details": {"load": mig["load"], "migrated": mig["migration_triggered"]},
            "sub_results": {},
        }
    )

    # =========================================================================
    # E6 · Revidage Transactionnel (C09)
    # =========================================================================
    # Vérifier d'abord que CLEAN avant COMMIT est bloqué avec rollback
    premature_blocked = False
    l1_test_guard = engine.register_local_node("L1_GUARD", "Montréal-Guard", "Québec", "AUTORITE_L1_GUARD")
    l1_test_guard.D_observations.append({"obs": "donnee_critique"})
    guard_delta = engine.build_delta(l1_test_guard, "Δ-GUARD", "2026-11-15T10:09:00Z", {"raccords": []})
    engine.prepare_revidage(l1_test_guard, guard_delta)
    try:
        engine.clean_revidage(l1_test_guard)
    except RevidageFailure:
        premature_blocked = (
            l1_test_guard.revidage_stage == RevidageStage.ROLLED_BACK
            and len(l1_test_guard.D_observations) == 1
        )

    # Maintenant séquence transactionnelle complète sur L1
    l1.D_observations.append({"obs": "fatigue_anonymisee_L1"})
    l1.P_preuves["P-R002"] = {"hash": "abc", "status": "VERIFIE"}
    delta_l1 = deltas[0]
    engine.prepare_revidage(l1, delta_l1)
    verify_ok = engine.verify_revidage(
        l1,
        ack=True,
        hash_match=delta_l1.integrity_hash == delta_l1.compute_hash(),
        provenance_ok=True,
        authority_ok=True,
        reconstruction_pass=mig["target_can_reconstruct"],
    )
    tx_id = engine.commit_revidage(l1, "TX-L1-001")
    minimal_l1 = engine.clean_revidage(l1)

    if fault.fail_condition == "C09":
        # Défaut simulé : effacement amnésique (perte d'index/preuve de transfert/manques locaux)
        minimal_l1.preuve_transfert = ""
        minimal_l1.manques_locaux.clear()
        premature_blocked = False

    c09_ok = (
        premature_blocked
        and verify_ok
        and tx_id == "TX-L1-001"
        and l1.revidage_stage == RevidageStage.CLEAN
        and minimal_l1.is_non_amnesic()
        and "M-001" in minimal_l1.manques_locaux
    )
    record_condition(
        "C09",
        "E6",
        c09_ok,
        f"premature_blocked={premature_blocked}, stage={l1.revidage_stage.value}, non_amnesic={minimal_l1.is_non_amnesic()}",
        minimal_l1.to_dict(),
    )
    palier_results.append(
        {
            "palier_id": "E6",
            "status": "PASS" if c09_ok else "FAIL",
            "details": {"premature_blocked": premature_blocked, "tx_id": tx_id},
            "sub_results": {},
        }
    )

    # =========================================================================
    # E7 · Retour depuis le Vide (E7-A) & Émergence Candidate (E7-B) (C10)
    # =========================================================================
    # Enregistrer R-001 comme réfuté et R-002 comme soutenu dans le Cloud avant Π₀
    engine.cloud.raccords["R-001"].status = RaccordStatus.REFUTE
    engine.cloud.raccords["R-001"].refutation_reason = "Réfuté comme usage individuel direct"
    engine.cloud.raccords["R-002"].status = RaccordStatus.SUPPORTE_SOUS_CONDITIONS
    engine.cloud.raccords["R-002"].evidence_level = AuthorityLevel.COLLECTIVE_CONDITIONNELLE
    engine.cloud.raccords["R-002"].authority_level = AuthorityLevel.COLLECTIVE_CONDITIONNELLE

    zero_state = projector.project(engine.cloud)
    idempotent = projector.verify_idempotence(engine.cloud)

    reopen = engine.reopen_from_void(
        l1,
        zero_state,
        "R-002",
        "NouvellePreuve: biais d'agrégation sur petites équipes",
        "M-001",
        timestamp="t_reopen",
    )

    # E7-B : Chaîne Médecine -> R-002 -> GestionCollective -> Prévention => Médecine -> Prévention*
    r_med = Raccord(
        id="R-MED-R002",
        label="Médecine → R-002",
        source="Médecine",
        target="R-002",
        origin_node="L1",
        status=RaccordStatus.SUPPORTE_SOUS_CONDITIONS,
        evidence_level=AuthorityLevel.LOCALE_CONDITIONNELLE,
        authority_level=AuthorityLevel.LOCALE_CONDITIONNELLE,
        provenance="Médecine:E7",
    )
    r_gest = Raccord(
        id="R-R002-GEST",
        label="R-002 → GestionCollective",
        source="R-002",
        target="GestionCollective",
        origin_node="L1",
        status=RaccordStatus.SUPPORTE_SOUS_CONDITIONS,
        evidence_level=AuthorityLevel.LOCALE_CONDITIONNELLE,
        authority_level=AuthorityLevel.LOCALE_CONDITIONNELLE,
        provenance="Gestion:E7",
    )
    r_prev = Raccord(
        id="R-GEST-PREV",
        label="GestionCollective → Prévention",
        source="GestionCollective",
        target="Prévention",
        origin_node="L1",
        status=RaccordStatus.SUPPORTE_SOUS_CONDITIONS,
        evidence_level=AuthorityLevel.LOCALE_CONDITIONNELLE,
        authority_level=AuthorityLevel.LOCALE_CONDITIONNELLE,
        provenance="Prévention:E7",
    )
    for item in (r_med, r_gest, r_prev):
        engine.cloud.raccords[item.id] = item

    emergent = engine.synthesize_emergent_raccord(
        "R-EMERGENT-MED-PREV",
        "Médecine",
        "Prévention",
        [r_med.id, r_gest.id, r_prev.id],
    )

    if fault.fail_condition == "C10":
        # Défaut simulé : émergence déclarée ÉTABLIE automatiquement
        emergent.status = RaccordStatus.ETABLI
        emergent.authority_level = AuthorityLevel.INTERNATIONALE_ETABLIE
        emergent.validation_required = False

    e7a_ok = (
        idempotent
        and "R-002" in reopen["cone_reopened"]
        and not reopen["omega_destroyed"]
        and reopen["manque_initial_retrouve"]
        and "R-001" in reopen["refutations_retrouvees"]
    )
    e7b_ok = (
        emergent.is_emergent
        and emergent.status == RaccordStatus.CANDIDAT
        and emergent.authority_level == AuthorityLevel.AUCUNE
        and emergent.validation_required is True
        and emergent.provenance == "composition:R-MED-R002->R-R002-GEST->R-GEST-PREV"
    )
    c10_ok = e7a_ok and e7b_ok

    record_condition(
        "C10",
        "E7",
        c10_ok,
        f"E7-A={e7a_ok}, E7-B={e7b_ok}, emergent_status={emergent.status.value}",
        {"e7a": reopen, "e7b": emergent.to_dict()},
    )
    palier_results.append(
        {
            "palier_id": "E7",
            "status": "PASS" if c10_ok else "FAIL",
            "details": {"pi0_idempotent": idempotent},
            "sub_results": {
                "E7-A": "PASS" if e7a_ok else "FAIL",
                "E7-B": "PASS" if e7b_ok else "FAIL",
            },
        }
    )

    all_pass = all(c["status"] == "PASS" for c in condition_results)
    report: dict[str, Any] = {
        "schema": "execution-report-4d/1",
        "protocol_id": "TEST-4D-ESC-01",
        "protocol_sha256": protocol_sha256,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "load_metrics_declared": metric_decl.to_dict(),
        "palier_results": palier_results,
        "condition_results": condition_results,
        "verdict": "PASS" if all_pass else "FAIL",
        "promotion": "ADMISSIBLE_A_REVUE_HUMAINE" if all_pass else "BLOQUEE",
        "trace_preserved": True,
        "cone_to_recalculate": cone_to_recalculate,
    }

    report_schema = json.loads((schema_dir / "execution_report.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(report_schema).validate(report)
    return report
