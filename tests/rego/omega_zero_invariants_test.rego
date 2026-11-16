# ---------------------------------------------------------------------------
# Suite de réfutation OPA (Rego v1) pour Supela Ω-ZERO · Local-Cloud-4D
# 2 cas positifs + 13 cas négatifs réfutant chaque invariant critique
# ---------------------------------------------------------------------------
package supela.omega_zero.governance

import rego.v1

fresh_ok_ns := 1791547500000000000
stale_ns := 1791548400000000000
future_ns := 1791547190000000000

valid_input := {
	"protocol": {"sha256": "be1ce58a92ec9fac5ecc3432c09697db4673eb6cbc55db08849215e255ad5faf"},
	"attestation": {
		"producer_id": "omega-harness-ci",
		"provenance": "HARNAIS_TEST_ESCALADE_4D.py",
		"signature": "c2lnYXR1cmUtcGxhY2Vob2xkZXI=",
		"nonce": "nonce-omega-001",
		"timestamp": "2026-10-09T12:00:00Z",
		"protocol_sha256": "be1ce58a92ec9fac5ecc3432c09697db4673eb6cbc55db08849215e255ad5faf",
	},
	"ledger": {"mode": "append-only", "tamper_detected": false},
	"ci_cd": {"branch": "refs/heads/main", "direct_commit_to_main": false},
	"report": {
		"protocol_sha256": "be1ce58a92ec9fac5ecc3432c09697db4673eb6cbc55db08849215e255ad5faf",
		"verdict": "PASS",
		"promotion": "ADMISSIBLE_A_REVUE_HUMAINE",
		"trace_preserved": true,
		"load_metrics_declared": {
			"metric": "max_ratio(bytes, objects, edges, latency)",
			"capacity_limit": {
				"bytes_limit": 2400,
				"objects_limit": 20,
				"edges_limit": 40,
				"latency_limit_ms": 100.0,
			},
			"unit": "bytes / count / count / ms",
			"measurement_method": "direct",
			"timestamp": "2026-10-09T12:00:00Z",
			"tested_environment": "Linux Python 3.11",
		},
		"palier_results": [
			{"palier_id": "E0", "status": "PASS", "sub_results": {}},
			{"palier_id": "E1", "status": "PASS", "sub_results": {}},
			{"palier_id": "E2", "status": "PASS", "sub_results": {}},
			{"palier_id": "E3", "status": "PASS", "sub_results": {}},
			{"palier_id": "E4", "status": "PASS", "sub_results": {}},
			{"palier_id": "E5", "status": "PASS", "sub_results": {}},
			{"palier_id": "E6", "status": "PASS", "sub_results": {}},
			{"palier_id": "E7", "status": "PASS", "sub_results": {"E7-A": "PASS", "E7-B": "PASS"}},
		],
		"condition_results": [
			{"condition_id": "C01", "status": "PASS"},
			{"condition_id": "C02", "status": "PASS"},
			{"condition_id": "C03", "status": "PASS"},
			{"condition_id": "C04", "status": "PASS"},
			{"condition_id": "C05", "status": "PASS"},
			{"condition_id": "C06", "status": "PASS"},
			{"condition_id": "C07", "status": "PASS"},
			{"condition_id": "C08", "status": "PASS"},
			{"condition_id": "C09", "status": "PASS"},
			{"condition_id": "C10", "status": "PASS"},
		],
	},
	"raccords": [
		{
			"id": "R-002",
			"status": "SUPPORTE_SOUS_CONDITIONS",
			"authority_level": 2,
			"evidence_level": 2,
			"is_emergent": false,
			"validation_required": false,
			"origin_type": "PROOF_TESTED",
		},
		{
			"id": "R-EMERGENT-MED-PREV",
			"status": "CANDIDAT",
			"authority_level": 0,
			"evidence_level": 0,
			"is_emergent": true,
			"validation_required": true,
			"origin_type": "COMPOSITION",
		},
		{
			"id": "H-GRPO-01",
			"status": "CANDIDAT",
			"authority_level": 0,
			"evidence_level": 0,
			"is_emergent": false,
			"validation_required": true,
			"origin_type": "GRPO_SCORE_ONLY",
		},
	],
	"manques": [
		{"id": "M-001", "statut": "SOUS_EXPLORATION", "silently_deleted": false},
	],
	"manque_transitions": [
		{"from": "OUVERT", "to": "SOUS_EXPLORATION"},
	],
	"revidage_tx": {
		"clean_executed_before_commit": false,
		"stage_sequence": ["PREPARE", "VERIFY", "COMMIT", "CLEAN"],
		"verify_predicates": {
			"ACK": true,
			"HashMatch": true,
			"ProvenanceOK": true,
			"AuthorityOK": true,
			"ReconstructionPASS": true,
		},
	},
}

# === CAS POSITIFS ==========================================================
test_coherence_valid if {
	coherence_satisfied with input as valid_input with time.now_ns as fresh_ok_ns
}

test_allow_human_review_valid_on_main if {
	allow_human_review with input as valid_input with time.now_ns as fresh_ok_ns
}

# === CAS NEGATIFS (13 réfutations) =========================================
test_deny_direct_commit if {
	bad := object.union(valid_input, {"ci_cd": {"branch": "refs/heads/main", "direct_commit_to_main": true}})
	not allow_human_review with input as bad with time.now_ns as fresh_ok_ns
}

test_deny_automatic_promotion if {
	bad := object.union(valid_input, {"report": object.union(valid_input.report, {"promotion": "AUTOMATIQUE"})})
	not allow_human_review with input as bad with time.now_ns as fresh_ok_ns
}

test_deny_protocol_hash_mismatch if {
	bad := object.union(valid_input, {"report": object.union(valid_input.report, {"protocol_sha256": "0000"})})
	not coherence_satisfied with input as bad with time.now_ns as fresh_ok_ns
}

test_deny_condition_failed if {
	bad_conds := [
		{"condition_id": "C01", "status": "PASS"},
		{"condition_id": "C02", "status": "PASS"},
		{"condition_id": "C03", "status": "PASS"},
		{"condition_id": "C04", "status": "PASS"},
		{"condition_id": "C05", "status": "PASS"},
		{"condition_id": "C06", "status": "PASS"},
		{"condition_id": "C07", "status": "FAIL"},
		{"condition_id": "C08", "status": "PASS"},
		{"condition_id": "C09", "status": "PASS"},
		{"condition_id": "C10", "status": "PASS"},
	]
	bad := object.union(valid_input, {"report": object.union(valid_input.report, {"condition_results": bad_conds})})
	not coherence_satisfied with input as bad with time.now_ns as fresh_ok_ns
}

test_deny_missing_condition if {
	bad_conds := array.slice(valid_input.report.condition_results, 0, 9)
	bad := object.union(valid_input, {"report": object.union(valid_input.report, {"condition_results": bad_conds})})
	not coherence_satisfied with input as bad with time.now_ns as fresh_ok_ns
}

test_deny_authority_exceeds_evidence if {
	bad_raccords := [
		{
			"id": "R-003",
			"status": "SUPPORTE_SOUS_CONDITIONS",
			"authority_level": 4,
			"evidence_level": 1,
			"is_emergent": false,
			"validation_required": false,
			"origin_type": "LOCAL_ONLY",
		},
	]
	bad := object.union(valid_input, {"raccords": bad_raccords})
	not coherence_satisfied with input as bad with time.now_ns as fresh_ok_ns
}

test_deny_emergent_auto_established if {
	bad_raccords := [
		{
			"id": "R-EMERGENT-MED-PREV",
			"status": "ETABLI",
			"authority_level": 3,
			"evidence_level": 0,
			"is_emergent": true,
			"validation_required": false,
			"origin_type": "COMPOSITION",
		},
	]
	bad := object.union(valid_input, {"raccords": bad_raccords})
	not coherence_satisfied with input as bad with time.now_ns as fresh_ok_ns
}

test_deny_grpo_score_auto_promotion if {
	bad_raccords := [
		{
			"id": "H-GRPO-01",
			"status": "ETABLI",
			"authority_level": 0,
			"evidence_level": 0,
			"is_emergent": false,
			"validation_required": false,
			"origin_type": "GRPO_SCORE_ONLY",
		},
	]
	bad := object.union(valid_input, {"raccords": bad_raccords})
	not coherence_satisfied with input as bad with time.now_ns as fresh_ok_ns
}

test_deny_premature_clean_before_commit if {
	bad := object.union(valid_input, {"revidage_tx": object.union(valid_input.revidage_tx, {"clean_executed_before_commit": true})})
	not coherence_satisfied with input as bad with time.now_ns as fresh_ok_ns
}

test_deny_missing_load_declaration if {
	bad := object.remove(valid_input, ["report", "load_metrics_declared", "tested_environment"])
	not coherence_satisfied with input as bad with time.now_ns as fresh_ok_ns
}

test_deny_forbidden_manque_jump_ouvert_to_resolu if {
	bad := object.union(valid_input, {"manque_transitions": [{"from": "OUVERT", "to": "RÉSOLU"}]})
	not coherence_satisfied with input as bad with time.now_ns as fresh_ok_ns
}

test_deny_stale_attestation if {
	not coherence_satisfied with input as valid_input with time.now_ns as stale_ns
}

test_deny_future_attestation if {
	not coherence_satisfied with input as valid_input with time.now_ns as future_ns
}

test_deny_tampered_ledger if {
	bad := object.union(valid_input, {"ledger": {"mode": "append-only", "tamper_detected": true}})
	not coherence_satisfied with input as bad with time.now_ns as fresh_ok_ns
}

# === TESTS SUP-ICI-01 & GRPO GF1..GF5 ======================================
valid_guard_kernel_transitions := [
	{
		"object_id": "OBJ-001",
		"from_generation": "G0",
		"to_generation": "G1",
		"compression_level": "C1",
		"preserved_fields": ["identity", "provenance", "status", "scope", "dependencies", "reopening_conditions"],
		"reversible": true,
		"authority": "PENDING_HUMAN_RATIFICATION",
		"semantic_loss_passed": true,
	},
	{
		"object_id": "OBJ-001",
		"from_generation": "G2",
		"to_generation": "G4",
		"compression_level": "C2",
		"preserved_fields": ["identity", "provenance", "status", "scope", "dependencies", "reopening_conditions"],
		"reversible": false,
		"authority": "PENDING_HUMAN_RATIFICATION",
		"semantic_loss_passed": true,
	},
]

valid_grpo_explorations := [
	{
		"candidate_id": "H-OUTLIER",
		"gf1_outlier_blocked": true,
		"gf2_admitted": false,
		"final_status": "REJETE_GF1_ABERRANT",
		"authority_level": "AUCUNE",
		"human_review_required": true,
	},
	{
		"candidate_id": "H-LOW",
		"gf1_outlier_blocked": false,
		"gf2_admitted": false,
		"final_status": "FILTRE_GF2_SOUS_SEUIL",
		"authority_level": "AUCUNE",
		"human_review_required": true,
	},
	{
		"candidate_id": "H-CAND",
		"gf1_outlier_blocked": false,
		"gf2_admitted": true,
		"final_status": "CANDIDAT",
		"authority_level": "AUCUNE",
		"human_review_required": true,
	},
]

test_allow_valid_guard_kernel_and_grpo_traces if {
	good := object.union(valid_input, {
		"guard_kernel_transitions": valid_guard_kernel_transitions,
		"grpo_explorations": valid_grpo_explorations,
	})
	allow_human_review with input as good with time.now_ns as fresh_ok_ns
}

test_deny_c2_reversible_claim if {
	bad_tx := [object.union(valid_guard_kernel_transitions[1], {"reversible": true})]
	bad := object.union(valid_input, {"guard_kernel_transitions": bad_tx})
	not coherence_satisfied with input as bad with time.now_ns as fresh_ok_ns
}

test_deny_guard_kernel_semantic_loss_failed if {
	bad_tx := [object.union(valid_guard_kernel_transitions[0], {"semantic_loss_passed": false})]
	bad := object.union(valid_input, {"guard_kernel_transitions": bad_tx})
	not coherence_satisfied with input as bad with time.now_ns as fresh_ok_ns
}

test_deny_guard_kernel_missing_preserved_field if {
	bad_tx := [object.union(valid_guard_kernel_transitions[0], {"preserved_fields": ["identity", "status"]})]
	bad := object.union(valid_input, {"guard_kernel_transitions": bad_tx})
	not coherence_satisfied with input as bad with time.now_ns as fresh_ok_ns
}

test_deny_grpo_trace_auto_authority if {
	bad_grpo := [object.union(valid_grpo_explorations[2], {"authority_level": "RATIFIEE"})]
	bad := object.union(valid_input, {"grpo_explorations": bad_grpo})
	not coherence_satisfied with input as bad with time.now_ns as fresh_ok_ns
}

test_deny_grpo_trace_auto_established if {
	bad_grpo := [object.union(valid_grpo_explorations[2], {"final_status": "ETABLI"})]
	bad := object.union(valid_input, {"grpo_explorations": bad_grpo})
	not coherence_satisfied with input as bad with time.now_ns as fresh_ok_ns
}
