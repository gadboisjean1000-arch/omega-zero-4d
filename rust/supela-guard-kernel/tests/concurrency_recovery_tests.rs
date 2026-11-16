use std::collections::{BTreeMap, HashSet};
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::PathBuf;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;
use std::thread;

use supela_guard_kernel::{parse_json, DurableJournal, FixedClock, JsonValue, RecoveryPolicy};

static COUNTER: AtomicU64 = AtomicU64::new(1);

struct TempDir {
    path: PathBuf,
}

impl TempDir {
    fn new(prefix: &str) -> Self {
        let id = COUNTER.fetch_add(1, Ordering::SeqCst);
        let dir = std::env::temp_dir().join(format!(
            "supela_gk_conc_{prefix}_{}_{id}",
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
fn concurrent_threads_append_serialize_cleanly_with_valid_worm_chain() {
    let dir = TempDir::new("threads");
    let journal_path = dir.path.join("concurrent_journal.jsonl");
    let _init = DurableJournal::open(&journal_path, RecoveryPolicy::TruncatePartialTail).unwrap();

    let thread_count = 8usize;
    let ops_per_thread = 15usize;
    let clock = Arc::new(FixedClock::new(1_794_850_000));

    let mut handles = Vec::new();
    for tid in 0..thread_count {
        let path_clone = journal_path.clone();
        let clock_clone = Arc::clone(&clock);
        handles.push(thread::spawn(move || {
            let j = DurableJournal::open(&path_clone, RecoveryPolicy::TruncatePartialTail).unwrap();
            let mut receipts = Vec::with_capacity(ops_per_thread);
            for step in 0..ops_per_thread {
                let mut payload = BTreeMap::new();
                payload.insert("thread".into(), JsonValue::Integer(tid as i64));
                payload.insert("step".into(), JsonValue::Integer(step as i64));
                let receipt = j
                    .append_event(
                        &format!("req-t{tid}-s{step}"),
                        "CONCURRENT_WRITE",
                        JsonValue::Object(payload),
                        clock_clone.as_ref(),
                    )
                    .unwrap();
                receipts.push(receipt);
            }
            receipts
        }));
    }

    let mut seen_seqs = HashSet::new();
    for h in handles {
        for r in h.join().unwrap() {
            assert!(!r.idempotent_replay);
            assert!(seen_seqs.insert(r.seq));
        }
    }

    let total = (thread_count * ops_per_thread) as u64;
    assert_eq!(seen_seqs.len(), total as usize);
    for seq in 1..=total {
        assert!(seen_seqs.contains(&seq));
    }

    let verifier = DurableJournal::open(&journal_path, RecoveryPolicy::Strict).unwrap();
    let chain = verifier.verify_chain().unwrap();
    assert_eq!(chain.entries, total);
    assert!(chain.valid);
}

#[test]
fn idempotency_replay_returns_cached_receipt_and_conflict_fails_closed() {
    let dir = TempDir::new("idempotency");
    let journal_path = dir.path.join("idempotent.jsonl");
    let journal = DurableJournal::open(&journal_path, RecoveryPolicy::Strict).unwrap();
    let clock = FixedClock::new(1_794_851_000);

    let payload1 = parse_json(r#"{"a":1,"b":"supela"}"#).unwrap();
    let r1 = journal
        .append_event("req-idem-01", "DECISION", payload1, &clock)
        .unwrap();
    assert_eq!(r1.seq, 1);
    assert!(!r1.idempotent_replay);

    // Requete rejouee avec memes valeurs (ordre des cles JSON different -> meme forme canonique)
    let payload_reordered = parse_json(r#"{"b":"supela","a":1}"#).unwrap();
    let r2 = journal
        .append_event("req-idem-01", "DECISION", payload_reordered, &clock)
        .unwrap();
    assert!(r2.idempotent_replay);
    assert_eq!(r2.seq, r1.seq);
    assert_eq!(r2.entry_hash, r1.entry_hash);
    assert_eq!(journal.verify_chain().unwrap().entries, 1);

    // Conflit explicite : meme request_id mais payload different => refuse fail-closed
    let payload_conflict = parse_json(r#"{"a":2,"b":"supela"}"#).unwrap();
    let err = journal
        .append_event("req-idem-01", "DECISION", payload_conflict, &clock)
        .unwrap_err();
    assert_eq!(err.code(), "IDEMPOTENCY_CONFLICT");

    // Memes donnees avec event_type different => refuse aussi
    let payload_same = parse_json(r#"{"a":1,"b":"supela"}"#).unwrap();
    let err2 = journal
        .append_event("req-idem-01", "OTHER_EVENT", payload_same, &clock)
        .unwrap_err();
    assert_eq!(err2.code(), "IDEMPOTENCY_CONFLICT");

    assert_eq!(journal.verify_chain().unwrap().entries, 1);
}

#[test]
fn crash_recovery_truncates_partial_tail_without_losing_committed_chain() {
    let dir = TempDir::new("crash_tail");
    let journal_path = dir.path.join("recovery.jsonl");
    let clock = FixedClock::new(1_794_852_000);

    {
        let journal = DurableJournal::open(&journal_path, RecoveryPolicy::Strict).unwrap();
        for i in 1..=3 {
            let mut p = BTreeMap::new();
            p.insert("k".into(), JsonValue::Integer(i));
            journal
                .append_event(&format!("req-{i}"), "COMMIT", JsonValue::Object(p), &clock)
                .unwrap();
        }
    }

    // Simuler une coupure d'alimentation en milieu d'ecriture sans '\n' final
    let partial_bytes = br#"{"seq":4,"event_type":"UNFLUSHED_HALF_WRITE"#;
    {
        let mut f = OpenOptions::new().append(true).open(&journal_path).unwrap();
        f.write_all(partial_bytes).unwrap();
        f.flush().unwrap();
    }

    // Le mode Strict refuse silencieusement d'ignorer une queue tronquee
    let strict_err = DurableJournal::open(&journal_path, RecoveryPolicy::Strict).unwrap_err();
    assert_eq!(strict_err.code(), "JOURNAL_TRUNCATED_TAIL");

    // Le mode TruncatePartialTail restaure les 3 entrees intactes
    let recovered =
        DurableJournal::open(&journal_path, RecoveryPolicy::TruncatePartialTail).unwrap();
    assert_eq!(recovered.recovered_truncated_bytes(), partial_bytes.len());
    let chain = recovered.verify_chain().unwrap();
    assert_eq!(chain.entries, 3);
    assert!(chain.valid);

    // Ajout post-reprise seq=4 chaine proprement
    let r4 = recovered
        .append_event(
            "req-4",
            "POST_RECOVERY",
            parse_json(r#"{"restored":true}"#).unwrap(),
            &clock,
        )
        .unwrap();
    assert_eq!(r4.seq, 4);
    assert_eq!(r4.prev_hash, chain.head_hash);
    assert_eq!(recovered.verify_chain().unwrap().entries, 4);
}

#[test]
fn crash_recovery_refuses_to_mask_historical_line_corruption() {
    let dir = TempDir::new("tamper_before_tail");
    let journal_path = dir.path.join("corrupt.jsonl");
    let clock = FixedClock::new(1_794_853_000);

    {
        let journal = DurableJournal::open(&journal_path, RecoveryPolicy::Strict).unwrap();
        journal
            .append_event("req-1", "A", parse_json(r#"{"x":1}"#).unwrap(), &clock)
            .unwrap();
        journal
            .append_event("req-2", "B", parse_json(r#"{"x":2}"#).unwrap(), &clock)
            .unwrap();
    }

    // Corrompre l'entree historique 1 ET ajouter une queue partielle en fin de fichier
    let content = fs::read_to_string(&journal_path).unwrap();
    let corrupted = format!(
        "{}{}",
        content.replacen("\"x\":1", "\"x\":9", 1),
        r#"{"seq":3"#
    );
    fs::write(&journal_path, corrupted).unwrap();

    // La reprise NE DOIT JAMAIS masquer l'alteration de la ligne 1
    let err = DurableJournal::open(&journal_path, RecoveryPolicy::TruncatePartialTail).unwrap_err();
    assert_eq!(err.code(), "WORM_TAMPER_DETECTED");
}

#[test]
fn recovery_when_first_record_is_truncated_resets_to_empty_clean_journal() {
    let dir = TempDir::new("first_line_crash");
    let journal_path = dir.path.join("first_crash.jsonl");
    let torn = br#"{"seq":1,"timestamp_utc":"incomplete"#;
    fs::write(&journal_path, torn).unwrap();

    let recovered =
        DurableJournal::open(&journal_path, RecoveryPolicy::TruncatePartialTail).unwrap();
    assert_eq!(recovered.recovered_truncated_bytes(), torn.len());
    let chain = recovered.verify_chain().unwrap();
    assert_eq!(chain.entries, 0);
    assert_eq!(chain.head_hash, "GENESIS");

    let clock = FixedClock::new(1_794_854_000);
    let r1 = recovered
        .append_event(
            "req-first",
            "BOOT",
            parse_json(r#"{"clean":true}"#).unwrap(),
            &clock,
        )
        .unwrap();
    assert_eq!(r1.seq, 1);
    assert_eq!(r1.prev_hash, "GENESIS");
}

#[test]
fn multi_process_subprocesses_serialize_cleanly_on_os_lock() {
    use std::process::{Command, Stdio};

    let dir = TempDir::new("multiproc_lock");
    let journal_path = dir.path.join("multiproc_journal.jsonl");
    let bin = env!("CARGO_BIN_EXE_supela-guard-kernel");

    let proc_count = 4usize;
    let msgs_per_proc = 8usize;
    let mut children = Vec::with_capacity(proc_count);

    for pid in 0..proc_count {
        let mut child = Command::new(bin)
            .args(["serve", "--journal"])
            .arg(&journal_path)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .spawn()
            .unwrap();

        let mut payload = String::new();
        for mid in 0..msgs_per_proc {
            payload.push_str(&format!(
                "{{\"protocol\":\"SUP-IPC-01\",\"request_id\":\"proc-{pid}-msg-{mid}\",\"op\":\"append_event\",\"params\":{{\"event_type\":\"MULTIPROC\",\"payload\":{{\"pid\":{pid},\"mid\":{mid}}}}}}}\n"
            ));
        }
        if let Some(mut stdin) = child.stdin.take() {
            stdin.write_all(payload.as_bytes()).unwrap();
        }
        children.push(child);
    }

    for child in children {
        let out = child.wait_with_output().unwrap();
        assert!(out.status.success());
        let text = String::from_utf8(out.stdout).unwrap();
        let lines: Vec<_> = text.lines().collect();
        assert_eq!(lines.len(), msgs_per_proc);
        for line in lines {
            let v = parse_json(line).unwrap();
            assert_eq!(v.get("ok").and_then(JsonValue::as_bool), Some(true));
        }
    }

    let verifier = DurableJournal::open(&journal_path, RecoveryPolicy::Strict).unwrap();
    let chain = verifier.verify_chain().unwrap();
    assert_eq!(chain.entries, (proc_count * msgs_per_proc) as u64);
    assert!(chain.valid);
}
