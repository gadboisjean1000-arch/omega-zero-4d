from __future__ import annotations

import copy
import json

import pytest

from omega_zero.serverless_laws_handler import handle_supela_http_request
from omega_zero.supela_laws import (
    DiscreteClassBBounds,
    FourBoundaryGate,
    GeoBoundingBox,
    GeoTopologyEngine,
    IntegrityStatus,
    LedgerIntegrityError,
    MultiJurisdictionStructureCheck,
    NormativeLevel,
    ReversibleAppendOnlyLedger,
    SpaceTimeJurisdictionBin,
    ThawConditionGate,
    evaluate_sensor_integrity,
    run_supela_laws_suite,
)
from scripts.build_proven_laws_web import (
    DEFAULT_HTML_OUT,
    DEFAULT_JSON_OUT,
    DEFAULT_MD_OUT,
    render_laws_markdown,
    verify_laws_html_parity,
    verify_laws_js_syntax,
)


def test_law03_two_zeros_separation_and_tri_state_integrity() -> None:
    down = evaluate_sensor_integrity(
        "qwen2.5:7b", expected_digest="sha256:abc", observed_digest=None, sensor_reachable=False
    )
    assert down.status == IntegrityStatus.SONDE_INEXECUTABLE
    assert down.exit_code == 3

    tamper = evaluate_sensor_integrity(
        "qwen2.5:7b", expected_digest="sha256:abc", observed_digest="sha256:xyz", sensor_reachable=True
    )
    assert tamper.status == IntegrityStatus.DIGEST_DIVERGENT
    assert tamper.exit_code == 1

    ok = evaluate_sensor_integrity(
        "qwen2.5:7b", expected_digest="sha256:abc", observed_digest="sha256:abc", sensor_reachable=True
    )
    assert ok.status == IntegrityStatus.DIGEST_CONCORDANT
    assert ok.exit_code == 0


def test_law05_four_boundaries_and_law06_thaw_condition_refutations() -> None:
    # (C ∧ P ∧ V ∧ Signature) ne suffit jamais sans ratification souveraine A
    no_human = FourBoundaryGate(True, True, True, True, human_ratification=False).evaluate()
    assert no_human["promotion_authorized"] is False
    assert no_human["non_transitivity_respected"] is True

    no_proof = FourBoundaryGate(True, True, False, True, human_ratification=True).evaluate()
    assert no_proof["promotion_authorized"] is False

    full = FourBoundaryGate(True, True, True, True, human_ratification=True).evaluate()
    assert full["promotion_authorized"] is True

    # Dégel refusé si H_souverain=False, si capteur muet ou si non-classifiés > 0
    assert (
        ThawConditionGate(True, 50.0, 0, 0, IntegrityStatus.DIGEST_CONCORDANT, 0, False).evaluate()[
            "thaw_allowed"
        ]
        is False
    )
    assert (
        ThawConditionGate(True, 50.0, 0, 0, IntegrityStatus.SONDE_INEXECUTABLE, 1, True).evaluate()[
            "thaw_allowed"
        ]
        is False
    )
    assert (
        ThawConditionGate(True, 50.0, 0, 1, IntegrityStatus.DIGEST_CONCORDANT, 0, True).evaluate()[
            "thaw_allowed"
        ]
        is False
    )
    assert (
        ThawConditionGate(True, 50.0, 0, 0, IntegrityStatus.DIGEST_CONCORDANT, 0, True).evaluate()[
            "thaw_allowed"
        ]
        is True
    )


def test_law07_reversible_append_only_ledger_r_star_and_sqlite_triggers() -> None:
    e1 = ReversibleAppendOnlyLedger.make_event(
        sequence_no=1,
        event_type="INIT",
        payload={"mode": "stable"},
        previous_event_hash="GENESIS",
        actor_id="JFG",
        authority_class="RATIFIED_HUMAN",
    )
    e2 = ReversibleAppendOnlyLedger.make_event(
        sequence_no=2,
        event_type="SET",
        payload={"mode": "divergent"},
        previous_event_hash=e1["event_hash"],
        actor_id="agent",
        authority_class="PROPOSED",
    )
    with_retract = ReversibleAppendOnlyLedger.retract_r_star(
        [e1, e2], target_sequence=1, reason="R*", ratified_by="JFG"
    )
    replayed = ReversibleAppendOnlyLedger.replay(with_retract)
    assert replayed["data"] == {"mode": "stable"}
    assert replayed["sequence_no"] == 3
    assert len(with_retract) == 3

    # Falsification d'un seul bit -> LedgerIntegrityError immédiat
    tampered = copy.deepcopy(with_retract)
    tampered[0]["payload"]["mode"] = "corrupted"
    with pytest.raises(LedgerIntegrityError):
        ReversibleAppendOnlyLedger.replay(tampered)

    # Triggers physiques SQLite interdisent UPDATE et DELETE
    trig = ReversibleAppendOnlyLedger.verify_sqlite_append_only_triggers()
    assert trig["triggers_verified"] is True


def test_normative_pyramid_rejects_shell_and_preserves_conflicts() -> None:
    bad_shell = MultiJurisdictionStructureCheck(
        structure_id="BAD-SHELL",
        corporate_domicile="Offshore sans substance",
        contract_governing_law="Clause opaque",
        arbitration_framework="Aucun",
        ip_treaty_anchor="Aucun",
        osbl_quebec_part_iii=True,
        osbl_non_distribution_enforced=False,
        economic_substance_verified=False,
        crs_tax_transparency_enforced=False,
        mandatory_public_order_respected=False,
    ).evaluate()
    assert bad_shell["compliant_model"] is False
    assert len(bad_shell["violations"]) == 4
    assert bad_shell["verdict"] == "REJET_HIERARCHIE_NORMATIVE"

    conflict = MultiJurisdictionStructureCheck(
        structure_id="CONFLICT-QC-CH",
        corporate_domicile="Québec (OSBL Partie III)",
        contract_governing_law="Droit matériel suisse (CO)",
        arbitration_framework="New York 1958",
        ip_treaty_anchor="Berne",
        osbl_quebec_part_iii=True,
        osbl_non_distribution_enforced=True,
        economic_substance_verified=True,
        crs_tax_transparency_enforced=True,
        mandatory_public_order_respected=True,
        conflicting_jurisdictions=("Québec_Loi_25", "UE_NIS2"),
    ).evaluate()
    assert conflict["compliant_model"] is True
    assert conflict["conflict_4d_conserved"] is True
    assert conflict["legal_counsel_review_required"] is True


def test_geospatial_arcgis_topology_rules_and_branch_conflicts() -> None:
    parent = GeoBoundingBox("P", "Parent", -74.0, 45.0, -70.0, 47.0)
    z1 = GeoBoundingBox("Z1", "Ouest", -74.0, 45.0, -72.0, 47.0)
    z2 = GeoBoundingBox("Z2", "Est", -72.0, 45.0, -70.0, 47.0)
    clean = GeoTopologyEngine.verify_topology(parent, [z1, z2])
    assert clean["topology_valid"] is True

    # Chevauchement interdit (MUST_NOT_OVERLAP)
    z_ov = GeoBoundingBox("Z3", "Overlap", -72.5, 45.0, -71.5, 47.0)
    ov_res = GeoTopologyEngine.verify_topology(parent, [z1, z2, z_ov])
    assert ov_res["rule_must_not_overlap"] is False
    assert ov_res["topology_valid"] is False

    # Trou interdit (MUST_NOT_HAVE_GAPS)
    z_small = GeoBoundingBox("Z2S", "Est partiel", -71.0, 45.0, -70.0, 47.0)
    gap_res = GeoTopologyEngine.verify_topology(parent, [z1, z_small])
    assert gap_res["rule_must_not_have_gaps"] is False

    # Sortie de couverture (MUST_BE_COVERED_BY)
    z_out = GeoBoundingBox("ZOUT", "Hors parent", -75.0, 45.0, -72.0, 47.0)
    out_res = GeoTopologyEngine.verify_topology(parent, [z_out, z2])
    assert out_res["rule_must_be_covered_by"] is False

    # Bornes WGS84 invalides rejetées
    with pytest.raises(ValueError):
        GeoBoundingBox("BAD", "Hors WGS84", -190.0, 0.0, 10.0, 10.0)

    # Branch Versioning 4D détecte le conflit sans écrasement
    br = GeoTopologyEngine.detect_branch_version_conflicts(
        [
            SpaceTimeJurisdictionBin("B1", "Z1", "2026-11-19T00:00:00Z", "main", NormativeLevel.L1_ORDRE_PUBLIC_NATIONAL, "h1"),
            SpaceTimeJurisdictionBin("B2", "Z1", "2026-11-19T00:00:00Z", "feat", NormativeLevel.L1_ORDRE_PUBLIC_NATIONAL, "h2"),
        ]
    )
    assert br["conflicts_detected"] == 1
    assert br["zero_silent_overwrite"] is True


def test_supela_laws_suite_and_web_artifacts_parity() -> None:
    report = run_supela_laws_suite()
    assert report["schema"] == "supela-is-the-laws/1.0"
    assert report["verdict_global"] == "CONFORME_AU_PERIMETRE_FORMALISE"
    assert report["summary"]["laws_verified"] == 12
    assert report["summary"]["laws_total"] == 12
    assert report["clause_honnetete"]["universal_truth_claimed"] is False
    assert report["clause_honnetete"]["legal_counsel_required_for_binding_contracts"] is True
    assert DiscreteClassBBounds.verify_all()["all_bounds_verified"] is True

    # Vérification des artefacts générés sur disque (JSON + MD + HTML 0-CDN + JS valide)
    assert DEFAULT_JSON_OUT.exists()
    assert DEFAULT_MD_OUT.exists()
    assert DEFAULT_HTML_OUT.exists()

    disk_doc = json.loads(DEFAULT_JSON_OUT.read_text(encoding="utf-8"))
    assert disk_doc["verdict_global"] == "CONFORME_AU_PERIMETRE_FORMALISE"
    assert render_laws_markdown(disk_doc) == DEFAULT_MD_OUT.read_text(encoding="utf-8")

    html_text = DEFAULT_HTML_OUT.read_text(encoding="utf-8")
    parity = verify_laws_html_parity(disk_doc, html_text)
    assert parity["parity_ok"] is True
    assert parity["zero_cdn_verified"] is True

    js_res = verify_laws_js_syntax(html_text)
    assert js_res["ok"] is True, js_res.get("stderr", "")


def test_serverless_azure_functions_adapter_read_only_routes() -> None:
    health = handle_supela_http_request("GET", "/api/supela/health")
    assert health.status_code == 200
    health_data = json.loads(health.body)
    assert health_data["verdict_global"] == "CONFORME_AU_PERIMETRE_FORMALISE"
    assert health_data["read_only_edge"] is True
    assert health_data["canonical_ledger_hosted_here"] is False

    laws_res = handle_supela_http_request("GET", "/api/supela/laws")
    assert laws_res.status_code == 200
    assert json.loads(laws_res.body)["summary"]["laws_verified"] == 12

    web_res = handle_supela_http_request("GET", "/api/supela/laws/web")
    assert web_res.status_code == 200
    assert "supela-laws-data" in web_res.body

    # Toute mutation est refusée fail-closed (405) et route inconnue -> 404
    assert handle_supela_http_request("POST", "/api/supela/laws").status_code == 405
    assert handle_supela_http_request("DELETE", "/api/supela/health").status_code == 405
    assert handle_supela_http_request("GET", "/api/supela/unknown").status_code == 404
