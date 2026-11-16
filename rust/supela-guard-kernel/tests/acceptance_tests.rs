use std::collections::BTreeMap;
use std::fs::{self, OpenOptions};
use std::io::{BufReader, Read, Write};
use std::path::PathBuf;
use std::process::{Command, Stdio};
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;

use supela_guard_kernel::{
    parse_json, DurableJournal, FixedClock, GuardService, JsonValue, RecoveryPolicy,
    IPC_PROTOCOL_VERSION,
};

static COUNTER: AtomicU64 = AtomicU64::new(1);

struct TempDir {
    path: PathBuf,
}

impl TempDir {
    fn new(prefix: &str) -> Self {
        let id = COUNTER.fetch_add(1, Ordering::SeqCst);
        let dir = std::env::temp_dir().join(format!(
            "supela_gk_acc_{prefix}_{}_{id}",
            std::process::id()
        ));
        let _ = fs::remove_dir_all(&dir);
        fs::create_dir_all(&dir).unwrap();
        Self { path: dir }
    }
}

impl Drop for TempDir {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.path);
    }
}

#[test]
fn ipc_ping_status_and_verify_roundtrip() {
    let dir = TempDir::new("ping_status");
    let journal_path = dir.path.join("journal.jsonl");
    let journal = DurableJournal::open(&journal_path, RecoveryPolicy::TruncatePartialTail).unwrap();
    let clock = Arc::new(FixedClock::new(1_794_844_800));
    let service = GuardService::new(journal, clock);

    let input = concat!(
        r#"{"protocol":"SUP-IPC-01","request_id":"req-ping-1","op":"ping","params":{}}"#,
        "\n",
        r#"{"protocol":"SUP-IPC-01","request_id":"req-status-1","op":"status","params":{}}"#,
        "\n",
        r#"{"protocol":"SUP-IPC-01","request_id":"req-verify-1","op":"verify_chain","params":{}}"#,
        "\n"
    );
    let mut reader = BufReader::new(input.as_bytes());
    let mut out = Vec::new();
    let count = service.serve_stream(&mut reader, &mut out).unwrap();
    assert_eq!(count, 3);

    let lines: Vec<String> = String::from_utf8(out)
        .unwrap()
        .lines()
        .map(|s| s.to_string())
        .collect();
    assert_eq!(lines.len(), 3);

    let ping = parse_json(&lines[0]).unwrap();
    assert_eq!(ping.get("ok").and_then(JsonValue::as_bool), Some(true));
    assert_eq!(
        ping.get("result")
            .and_then(|r| r.get("zero_external_crates"))
            .and_then(JsonValue::as_bool),
        Some(true)
    );

    let status = parse_json(&lines[1]).unwrap();
    assert_eq!(
        status
            .get("result")
            .and_then(|r| r.get("worm_mode"))
            .and_then(JsonValue::as_str),
        Some("COOPERATIVE_OS_FILE_LOCK_NOT_HARDWARE_TPM")
    );
    assert_eq!(
        status
            .get("result")
            .and_then(|r| r.get("external_crates"))
            .and_then(JsonValue::as_i64),
        Some(0)
    );

    let verify = parse_json(&lines[2]).unwrap();
    assert_eq!(
        verify
            .get("result")
            .and_then(|r| r.get("head_hash"))
            .and_then(JsonValue::as_str),
        Some("GENESIS")
    );
}

#[test]
fn policy_barrier_blocks_score_to_truth_escalation_and_permits_candidat() {
    let dir = TempDir::new("policy_barrier");
    let journal_path = dir.path.join("journal.jsonl");
    let journal = DurableJournal::open(&journal_path, RecoveryPolicy::Strict).unwrap();
    let clock = Arc::new(FixedClock::new(1_794_844_900));
    let service = GuardService::new(journal, clock);

    // 1. Auto-promotion ETABLI sans preuve ni ratification -> BLOQUE fail-closed
    let promote_req = r#"{"protocol":"SUP-IPC-01","request_id":"eval-bad-1","op":"evaluate_candidate","params":{"candidate_id":"C-SCORE","reward":0.99,"r_max":1.0,"proof_verified":false,"requested_status":"ETABLI","requested_authority_level":0,"evidence_level":0,"human_ratified":false}}"#;
    let bad_resp = service.handle_line(promote_req);
    assert_eq!(bad_resp.get("ok").and_then(JsonValue::as_bool), Some(false));
    assert_eq!(
        bad_resp
            .get("error")
            .and_then(|e| e.get("code"))
            .and_then(JsonValue::as_str),
        Some("AUTHORITY_EXCEEDS_PROOF")
    );

    // 2. Autorite > Preuve -> BLOQUE fail-closed
    let auth_req = r#"{"protocol":"SUP-IPC-01","request_id":"eval-bad-2","op":"evaluate_candidate","params":{"candidate_id":"C-AUTH","reward":0.7,"r_max":1.0,"proof_verified":false,"requested_status":"CANDIDAT","requested_authority_level":2,"evidence_level":1}}"#;
    let bad_auth = service.handle_line(auth_req);
    assert_eq!(bad_auth.get("ok").and_then(JsonValue::as_bool), Some(false));
    assert_eq!(
        bad_auth
            .get("error")
            .and_then(|e| e.get("code"))
            .and_then(JsonValue::as_str),
        Some("AUTHORITY_EXCEEDS_PROOF")
    );

    // 3. Score exorbitant (> r_max) -> borne par GF1 et jamais ETABLI
    let outlier_req = r#"{"protocol":"SUP-IPC-01","request_id":"eval-outlier-1","op":"evaluate_candidate","params":{"candidate_id":"C-OUTLIER","reward":42.0,"r_max":1.0}}"#;
    let outlier_resp = service.handle_line(outlier_req);
    assert_eq!(
        outlier_resp.get("ok").and_then(JsonValue::as_bool),
        Some(true)
    );
    assert_eq!(
        outlier_resp
            .get("result")
            .and_then(|r| r.get("evaluation"))
            .and_then(|e| e.get("gf1_clamped"))
            .and_then(JsonValue::as_bool),
        Some(true)
    );
    assert_eq!(
        outlier_resp
            .get("result")
            .and_then(|r| r.get("evaluation"))
            .and_then(|e| e.get("resulting_status"))
            .and_then(JsonValue::as_str),
        Some("REJETE_GF1_ABERRANT")
    );

    // 4. Candidat nominal -> CANDIDAT uniquement + revue humaine requise
    let ok_req = r#"{"protocol":"SUP-IPC-01","request_id":"eval-ok-1","op":"evaluate_candidate","params":{"candidate_id":"C-OK","reward":0.8,"r_max":1.0}}"#;
    let ok_resp = service.handle_line(ok_req);
    assert_eq!(ok_resp.get("ok").and_then(JsonValue::as_bool), Some(true));
    assert_eq!(
        ok_resp
            .get("result")
            .and_then(|r| r.get("evaluation"))
            .and_then(|e| e.get("promotion_verdict"))
            .and_then(JsonValue::as_str),
        Some("ADMISSIBLE_A_REVUE_HUMAINE")
    );
    assert_eq!(service.journal().verify_chain().unwrap().entries, 2);
}

#[test]
fn sup_ici_01_transition_c1_c2_and_refutations() {
    let dir = TempDir::new("sup_ici_01");
    let journal =
        DurableJournal::open(dir.path.join("journal.jsonl"), RecoveryPolicy::Strict).unwrap();
    let clock = Arc::new(FixedClock::new(1_794_845_000));
    let service = GuardService::new(journal, clock);
    let prev = "0123456789abcdef".repeat(4);

    // C2 nominal (G2 -> G4) => reversible=false, accessibility=REFERENTIAL
    let ok_c2 = format!(
        r#"{{"protocol":"SUP-IPC-01","request_id":"tx-c2-ok","op":"compress_transition","params":{{"object_id":"OBJ-K-1","author":"jean-francois","origin":"omega-zero-4d","from_generation":"G2","to_generation":"G4","from_status":"HYPOTHESE","to_status":"NON-RÉCLAMÉ","compression_level":"C2","previous_hash":"{prev}","reason":"Archivage G4 sous C2","existing_proofs":["PRF-01"],"output_proofs":["PRF-01"],"existing_contradictions":["CONTR-T11"],"output_contradictions":["CONTR-T11"],"dependencies":["SUP-ICI-01"]}}}}"#
    );
    let resp = service.handle_line(&ok_c2);
    assert_eq!(resp.get("ok").and_then(JsonValue::as_bool), Some(true));
    assert_eq!(
        resp.get("result")
            .and_then(|r| r.get("transition"))
            .and_then(|t| t.get("reversible"))
            .and_then(JsonValue::as_bool),
        Some(false)
    );
    assert_eq!(
        resp.get("result")
            .and_then(|r| r.get("transition"))
            .and_then(|t| t.get("accessibility_mode"))
            .and_then(JsonValue::as_str),
        Some("REFERENTIAL")
    );

    // Refutation 1 : C2 + claim_full_copy=true
    let bad_c2_copy = format!(
        r#"{{"protocol":"SUP-IPC-01","request_id":"tx-bad-1","op":"compress_transition","params":{{"object_id":"OBJ-K-1","author":"jean-francois","origin":"omega-zero-4d","from_generation":"G2","to_generation":"G4","compression_level":"C2","previous_hash":"{prev}","reason":"Tentative mensonge C2","claim_full_copy":true}}}}"#
    );
    assert_eq!(
        service
            .handle_line(&bad_c2_copy)
            .get("error")
            .and_then(|e| e.get("code"))
            .and_then(JsonValue::as_str),
        Some("COMPRESSION_FAIL_C2_FULL_COPY")
    );

    // Refutation 2 : Effacement contradiction active CONTR-T11
    let bad_contra = format!(
        r#"{{"protocol":"SUP-IPC-01","request_id":"tx-bad-2","op":"compress_transition","params":{{"object_id":"OBJ-K-1","author":"jean-francois","origin":"omega-zero-4d","from_generation":"G0","to_generation":"G1","compression_level":"C1","previous_hash":"{prev}","reason":"Compression C1","existing_contradictions":["CONTR-T11"],"output_contradictions":[]}}}}"#
    );
    assert_eq!(
        service
            .handle_line(&bad_contra)
            .get("error")
            .and_then(|e| e.get("code"))
            .and_then(JsonValue::as_str),
        Some("SUP_ICI_01_CONTRADICTION_ERASED")
    );

    // Refutation 3 : Promotion HYPOTHESE -> FAIT sans preuve nouvelle
    let bad_fact = format!(
        r#"{{"protocol":"SUP-IPC-01","request_id":"tx-bad-3","op":"compress_transition","params":{{"object_id":"OBJ-K-1","author":"jean-francois","origin":"omega-zero-4d","from_generation":"G0","to_generation":"G1","from_status":"HYPOTHESE","to_status":"FAIT","compression_level":"C0","previous_hash":"{prev}","reason":"Compression abusive","existing_proofs":["PRF-1"],"output_proofs":["PRF-1"]}}}}"#
    );
    assert_eq!(
        service
            .handle_line(&bad_fact)
            .get("error")
            .and_then(|e| e.get("code"))
            .and_then(JsonValue::as_str),
        Some("SUP_ICI_01_HYPOTHESIS_TO_FACT_WITHOUT_PROOF")
    );
}

#[test]
fn ipc_rejects_future_timestamp_bad_protocol_bad_base64_and_oversized_frame() {
    let dir = TempDir::new("ipc_security");
    let journal =
        DurableJournal::open(dir.path.join("journal.jsonl"), RecoveryPolicy::Strict).unwrap();
    // 2026-11-16T12:00:00Z = 1794830400? Wait: let's check using clock helper indirectly via FixedClock
    // Fixed timestamp 2026-11-16T00:00:00Z -> 1_794_787_200 ; future 2027-01-01T00:00:00Z is definitely >> skew
    let clock = Arc::new(FixedClock::new(1_794_787_200));
    let service = GuardService::new(journal, clock).with_limits(512, 300);

    // Trame depassant max_line_bytes (512 octets) suivie d'un ping valide
    let oversized = format!(
        r#"{{"protocol":"{IPC_PROTOCOL_VERSION}","request_id":"big","op":"ping","params":{{"pad":"{}"}}}}"#,
        "A".repeat(700)
    );
    let stream_data = format!(
        "{oversized}\n{{\"protocol\":\"WRONG-PROTO\",\"request_id\":\"bad-p\",\"op\":\"ping\"}}\n{{\"protocol\":\"SUP-IPC-01\",\"request_id\":\"future-1\",\"timestamp_utc\":\"2099-01-01T00:00:00Z\",\"op\":\"ping\"}}\n{{\"protocol\":\"SUP-IPC-01\",\"request_id\":\"b64-1\",\"op\":\"append_event\",\"params\":{{\"event_type\":\"X\",\"payload_b64\":\"Zh==\"}}}}\n{{\"protocol\":\"SUP-IPC-01\",\"request_id\":\"ok-after\",\"op\":\"ping\"}}\n"
    );

    let mut reader = BufReader::new(stream_data.as_bytes());
    let mut out = Vec::new();
    let handled = service.serve_stream(&mut reader, &mut out).unwrap();
    assert_eq!(handled, 5);

    let responses: Vec<JsonValue> = String::from_utf8(out)
        .unwrap()
        .lines()
        .map(|l| parse_json(l).unwrap())
        .collect();

    assert_eq!(
        responses[0]
            .get("error")
            .and_then(|e| e.get("code"))
            .and_then(JsonValue::as_str),
        Some("LINE_TOO_LARGE")
    );
    assert_eq!(
        responses[1]
            .get("error")
            .and_then(|e| e.get("code"))
            .and_then(JsonValue::as_str),
        Some("UNSUPPORTED_PROTOCOL")
    );
    assert_eq!(
        responses[2]
            .get("error")
            .and_then(|e| e.get("code"))
            .and_then(JsonValue::as_str),
        Some("FUTURE_TIMESTAMP_REJECTED")
    );
    assert_eq!(
        responses[3]
            .get("error")
            .and_then(|e| e.get("code"))
            .and_then(JsonValue::as_str),
        Some("INVALID_BASE64")
    );
    assert_eq!(
        responses[4].get("ok").and_then(JsonValue::as_bool),
        Some(true)
    );
}

#[test]
fn worm_tamper_detection_catches_modified_record() {
    let dir = TempDir::new("tamper");
    let journal_path = dir.path.join("worm.jsonl");
    let journal = DurableJournal::open(&journal_path, RecoveryPolicy::Strict).unwrap();
    let clock = FixedClock::new(1_794_800_000);

    for i in 1..=3 {
        let mut payload = BTreeMap::new();
        payload.insert("step".into(), JsonValue::Integer(i));
        journal
            .append_event(
                &format!("req-{i}"),
                "STEP",
                JsonValue::Object(payload),
                &clock,
            )
            .unwrap();
    }
    assert_eq!(journal.verify_chain().unwrap().entries, 3);

    // Alteration furtive du contenu dans la ligne 2
    let mut raw = String::new();
    fs::File::open(&journal_path)
        .unwrap()
        .read_to_string(&mut raw)
        .unwrap();
    let tampered = raw.replacen("\"step\":2", "\"step\":9", 1);
    assert_ne!(raw, tampered);
    let mut f = OpenOptions::new()
        .write(true)
        .truncate(true)
        .open(&journal_path)
        .unwrap();
    f.write_all(tampered.as_bytes()).unwrap();
    f.sync_all().unwrap();

    let err = journal.verify_chain().unwrap_err();
    assert_eq!(err.code(), "WORM_TAMPER_DETECTED");
}

#[test]
fn cli_binary_stdio_serve_verify_status_end_to_end() {
    let dir = TempDir::new("cli_bin");
    let journal_path = dir.path.join("cli_ledger.jsonl");
    let bin = env!("CARGO_BIN_EXE_supela-guard-kernel");

    // 1. Lancer serve en sous-processus reel via stdin/stdout (SUP-IPC-01)
    let mut child = Command::new(bin)
        .args(["serve", "--journal"])
        .arg(&journal_path)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .spawn()
        .unwrap();

    {
        let mut stdin = child.stdin.take().unwrap();
        let reqs = concat!(
            r#"{"protocol":"SUP-IPC-01","request_id":"cli-1","op":"append_event","params":{"event_type":"INIT","payload":{"ok":true}}}"#,
            "\n",
            r#"{"protocol":"SUP-IPC-01","request_id":"cli-2","op":"evaluate_candidate","params":{"candidate_id":"H-1","reward":0.85,"r_max":1.0}}"#,
            "\n",
            r#"{"protocol":"SUP-IPC-01","request_id":"cli-3","op":"status"}"#,
            "\n"
        );
        stdin.write_all(reqs.as_bytes()).unwrap();
    }

    let output = child.wait_with_output().unwrap();
    assert!(output.status.success());
    let stdout = String::from_utf8(output.stdout).unwrap();
    let lines: Vec<JsonValue> = stdout.lines().map(|l| parse_json(l).unwrap()).collect();
    assert_eq!(lines.len(), 3);
    assert!(lines
        .iter()
        .all(|v| v.get("ok").and_then(JsonValue::as_bool) == Some(true)));

    // 2. Executer `verify` sur journal intact
    let verify_ok = Command::new(bin)
        .args(["verify", "--journal"])
        .arg(&journal_path)
        .output()
        .unwrap();
    assert!(verify_ok.status.success());
    let vjson = parse_json(String::from_utf8(verify_ok.stdout).unwrap().trim()).unwrap();
    assert_eq!(vjson.get("entries").and_then(JsonValue::as_i64), Some(2));
    assert_eq!(vjson.get("valid").and_then(JsonValue::as_bool), Some(true));

    // 3. Executer `status`
    let status_out = Command::new(bin)
        .args(["status", "--journal"])
        .arg(&journal_path)
        .output()
        .unwrap();
    assert!(status_out.status.success());
    let sjson = parse_json(String::from_utf8(status_out.stdout).unwrap().trim()).unwrap();
    assert_eq!(
        sjson.get("protocol").and_then(JsonValue::as_str),
        Some("SUP-IPC-01")
    );

    // 4. Alterer le journal puis re-verifier `verify` => echec explicite WORM_TAMPER_DETECTED
    let orig = fs::read_to_string(&journal_path).unwrap();
    fs::write(&journal_path, orig.replacen("INIT", "HACK", 1)).unwrap();
    let verify_fail = Command::new(bin)
        .args(["verify", "--journal"])
        .arg(&journal_path)
        .output()
        .unwrap();
    assert!(!verify_fail.status.success());
    let fail_json = parse_json(String::from_utf8(verify_fail.stdout).unwrap().trim()).unwrap();
    assert_eq!(
        fail_json.get("code").and_then(JsonValue::as_str),
        Some("WORM_TAMPER_DETECTED")
    );
}
