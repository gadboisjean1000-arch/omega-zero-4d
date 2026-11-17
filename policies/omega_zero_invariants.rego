# ---------------------------------------------------------------------------
# Supela Ω-ZERO · Local-Cloud-4D — Invariants & Barrière d'Échelle (Rego v1)
# Aligné avec la discipline Supela-K3-Omega :
#   - Aucun booléen déclaratif admis sans preuve recalculée
#   - Autorité <= Preuve ; Exploration != Autorité ; Score != Preuve != Vérité
#   - 8 paliers (E0..E7) et 10 conditions distinctes (C01..C10) vérifiés
# ---------------------------------------------------------------------------
package supela.omega_zero.governance

import rego.v1

max_attestation_age_ns := 900000000000

canonical_manque_statuses := {
	"OUVERT",
	"SOUS_EXPLORATION",
	"PARTIELLEMENT_RÉDUIT",
	"RÉSOLU",
	"RÉFUTÉ_COMME_PROBLÈME",
	"REQUALIFIÉ",
	"INACCESSIBLE_DANS_LE_PÉRIMÈTRE",
}

expected_condition_ids := {"C01", "C02", "C03", "C04", "C05", "C06", "C07", "C08", "C09", "C10"}

expected_palier_ids := {"E0", "E1", "E2", "E3", "E4", "E5", "E6", "E7"}

required_load_decl_keys := {
	"metric",
	"capacity_limit",
	"unit",
	"measurement_method",
	"timestamp",
	"tested_environment",
}

required_verify_predicates := {
	"ACK",
	"HashMatch",
	"ProvenanceOK",
	"AuthorityOK",
	"ReconstructionPASS",
}

# --- 1. Attestation structurée, fraîche et liée au hash du protocole -------
attestation_complete if {
	att := input.attestation
	att.producer_id != ""
	att.provenance != ""
	att.signature != ""
	att.nonce != ""
	att.timestamp != ""
	att.protocol_sha256 != ""
}

attestation_fresh if {
	age_ns := time.now_ns() - time.parse_rfc3339_ns(input.attestation.timestamp)
	age_ns >= 0
	age_ns <= max_attestation_age_ns
}

protocol_hash_matches if {
	input.attestation.protocol_sha256 == input.protocol.sha256
	input.report.protocol_sha256 == input.protocol.sha256
}

# --- 2. Registre WORM non altéré -------------------------------------------
worm_immutable if {
	input.ledger.mode == "append-only"
	input.ledger.tamper_detected == false
}

# --- 3. Recalcul complet du verdict 10 conditions / 8 paliers --------------
passed_conditions contains c.condition_id if {
	some c in input.report.condition_results
	c.status == "PASS"
}

passed_paliers contains p.palier_id if {
	some p in input.report.palier_results
	p.status == "PASS"
}

all_conditions_verified if {
	count(input.report.condition_results) == 10
	passed_conditions == expected_condition_ids
	count(input.report.palier_results) == 8
	passed_paliers == expected_palier_ids
	e7 := [p | some p in input.report.palier_results; p.palier_id == "E7"][0]
	e7.sub_results["E7-A"] == "PASS"
	e7.sub_results["E7-B"] == "PASS"
}

# --- 4. Déclaration métrique Load(C) (C08) ---------------------------------
load_metrics_declared if {
	decl := input.report.load_metrics_declared
	every k in required_load_decl_keys {
		decl[k] != null
		decl[k] != ""
	}
	decl.capacity_limit.bytes_limit > 0
	decl.capacity_limit.objects_limit > 0
	decl.capacity_limit.edges_limit > 0
	decl.capacity_limit.latency_limit_ms > 0
}

# --- 5. Bornage d'autorité et barrière d'émergence / GRPO ------------------
no_authority_exceeds_proof if {
	every r in input.raccords {
		r.authority_level <= r.evidence_level
	}
}

# Règle claire : tout raccord émergent doit rester CANDIDAT, autorité 0, validation requise
emergent_raccords_safe if {
	bad := [r |
		some r in input.raccords
		r.is_emergent == true
		not raccord_is_safe_candidate(r)
	]
	count(bad) == 0
}

raccord_is_safe_candidate(r) if {
	r.status == "CANDIDAT"
	r.authority_level == 0
	r.validation_required == true
}

# Aucun candidat issu uniquement d'un score GRPO ne peut être ÉTABLI sans preuve
grpo_barrier_respected if {
	bad := [r |
		some r in input.raccords
		r.origin_type == "GRPO_SCORE_ONLY"
		r.status == "ETABLI"
	]
	count(bad) == 0
}

# --- 6. Invariant du Manque (M1..M5) ---------------------------------------
manques_valid if {
	every m in input.manques {
		canonical_manque_statuses[m.statut]
		not m.silently_deleted
	}
	bad_jumps := [t |
		some t in input.manque_transitions
		t.from == "OUVERT"
		t.to == "RÉSOLU"
	]
	count(bad_jumps) == 0
}

# --- 7. Revidage transactionnel (C09) --------------------------------------
revidage_transactional if {
	tx := input.revidage_tx
	tx.clean_executed_before_commit == false
	tx.stage_sequence == ["PREPARE", "VERIFY", "COMMIT", "CLEAN"]
	every p in required_verify_predicates {
		tx.verify_predicates[p] == true
	}
}

# --- 7b. Supela-Guard-Kernel (SUP-ICI-01, C0/C1/C2, G0..G5) -----------------
required_guard_kernel_fields := {
	"identity",
	"provenance",
	"status",
	"scope",
	"dependencies",
	"reopening_conditions",
}

sup_ici_01_satisfied if {
	transitions := object.get(input, "guard_kernel_transitions", [])
	every tx in transitions {
		tx.semantic_loss_passed == true
		tx.authority != "AUTO_ESTABLISHED"
		guard_kernel_c2_honest(tx)
		every field in required_guard_kernel_fields {
			field in tx.preserved_fields
		}
	}
}

guard_kernel_c2_honest(tx) if {
	tx.compression_level != "C2"
}

guard_kernel_c2_honest(tx) if {
	tx.compression_level == "C2"
	tx.reversible == false
}

# --- 7c. Pont GRPO GF1..GF5 -------------------------------------------------
grpo_guardrails_satisfied if {
	traces := object.get(input, "grpo_explorations", [])
	every t in traces {
		t.authority_level == "AUCUNE"
		t.human_review_required == true
		grpo_trace_status_valid(t)
	}
}

grpo_trace_status_valid(t) if {
	t.gf1_outlier_blocked == true
	t.final_status == "REJETE_GF1_ABERRANT"
}

grpo_trace_status_valid(t) if {
	t.gf1_outlier_blocked == false
	t.gf2_admitted == false
	t.final_status == "FILTRE_GF2_SOUS_SEUIL"
}

grpo_trace_status_valid(t) if {
	t.gf1_outlier_blocked == false
	t.gf2_admitted == true
	t.final_status == "CANDIDAT"
}

# --- 7d. Programmation Évolutive à Preuve Conservée (PCEP) -------------------
pcep_invariants_satisfied if {
	not input.pcep_envelope
}

pcep_invariants_satisfied if {
	env := input.pcep_envelope
	env.schema == "supela-pcep-network/1"
	pcep_open_proofs_not_promoted(env)
	pcep_transports_safe(env)
	pcep_agents_bounded(env)
	pcep_evolution_steps_complete(env)
	pcep_revocations_safe(env)
	pcep_signature_envelope_honest(env.signature_envelope)
}

pcep_open_proofs_not_promoted(env) if {
	every item in env.open_proofs_registry {
		item.status == "A_PROUVER"
		item.promoted == false
	}
}

pcep_transports_safe(env) if {
	bad := [t |
		some t in env.referential_transports
		t.transport_allowed == true
		t.transport_proof_verified == false
	]
	count(bad) == 0
}

pcep_agents_bounded(env) if {
	every a in env.agent_authorities {
		a.action_authority <= a.verified_proof_level
		a.bounded_ok == true
	}
}

pcep_evolution_steps_complete(env) if {
	every s in env.evolution_steps {
		s.trace != ""
		s.scope != ""
		count(s.proof_refs) > 0
		is_array(s.counter_evidence)
	}
}

pcep_revocations_safe(env) if {
	bad := [tx |
		some tx in env.auto_revocation_transitions
		tx.from_status == "CONTRADICTED"
		tx.to_status == "VALID"
	]
	count(bad) == 0
}

pcep_signature_envelope_honest(sig_env) if {
	sig_env.signature_status == "EN_ATTENTE_SIGNATURE"
	sig_env.ready_for_signature == true
	sig_env.signature == null
	sig_env.canonical_payload_sha256 != ""
}

pcep_signature_envelope_honest(sig_env) if {
	sig_env.signature_status == "SIGNEE"
	is_string(sig_env.signature)
	sig_env.signature != ""
}

# --- 8. Synthèse de cohérence Ω-ZERO ---------------------------------------
coherence_satisfied if {
	attestation_complete
	attestation_fresh
	protocol_hash_matches
	worm_immutable
	all_conditions_verified
	load_metrics_declared
	no_authority_exceeds_proof
	emergent_raccords_safe
	grpo_barrier_respected
	manques_valid
	revidage_transactional
	sup_ici_01_satisfied
	grpo_guardrails_satisfied
	pcep_invariants_satisfied
}

# --- 9. Barrière de promotion (jamais automatique !) -----------------------
allow_human_review if {
	input.ci_cd.branch == "refs/heads/main"
	input.ci_cd.direct_commit_to_main == false
	input.report.verdict == "PASS"
	input.report.promotion == "ADMISSIBLE_A_REVUE_HUMAINE"
	input.report.trace_preserved == true
	coherence_satisfied
}
