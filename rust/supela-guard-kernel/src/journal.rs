use std::collections::BTreeMap;
use std::fs::{self, File, OpenOptions};
use std::io::{Read, Seek, SeekFrom, Write};
use std::path::{Path, PathBuf};

use crate::clock::Clock;
use crate::json::{parse_json, JsonValue};
use crate::sha256::{sha256_hex, worm_entry_hash};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum RecoveryPolicy {
    Strict,
    TruncatePartialTail,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum JournalError {
    Io(String),
    InvalidInput(String),
    TruncatedTail {
        trailing_bytes: usize,
    },
    TamperDetected {
        line: usize,
        reason: String,
    },
    IdempotencyConflict {
        request_id: String,
        existing_hash: String,
        attempted_hash: String,
    },
}

impl JournalError {
    pub fn code(&self) -> &'static str {
        match self {
            Self::Io(_) => "JOURNAL_IO_ERROR",
            Self::InvalidInput(_) => "JOURNAL_INVALID_INPUT",
            Self::TruncatedTail { .. } => "JOURNAL_TRUNCATED_TAIL",
            Self::TamperDetected { .. } => "WORM_TAMPER_DETECTED",
            Self::IdempotencyConflict { .. } => "IDEMPOTENCY_CONFLICT",
        }
    }
}

impl std::fmt::Display for JournalError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Io(msg) => write!(f, "erreur E/S journal : {msg}"),
            Self::InvalidInput(msg) => write!(f, "entree journal invalide : {msg}"),
            Self::TruncatedTail { trailing_bytes } => {
                write!(f, "queue partielle non terminee ({trailing_bytes} octets)")
            }
            Self::TamperDetected { line, reason } => {
                write!(f, "alteration WORM detectee ligne {line} : {reason}")
            }
            Self::IdempotencyConflict {
                request_id,
                existing_hash,
                attempted_hash,
            } => write!(
                f,
                "conflit d'idempotence pour request_id='{request_id}' (existant={existing_hash}, recu={attempted_hash})"
            ),
        }
    }
}

impl std::error::Error for JournalError {}

impl From<std::io::Error> for JournalError {
    fn from(err: std::io::Error) -> Self {
        Self::Io(err.to_string())
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AppendReceipt {
    pub seq: u64,
    pub prev_hash: String,
    pub entry_hash: String,
    pub payload_sha256: String,
    pub timestamp_utc: String,
    pub idempotent_replay: bool,
}

impl AppendReceipt {
    pub fn to_json(&self) -> JsonValue {
        let mut map = BTreeMap::new();
        map.insert("seq".into(), JsonValue::Integer(self.seq as i64));
        map.insert(
            "prev_hash".into(),
            JsonValue::String(self.prev_hash.clone()),
        );
        map.insert(
            "entry_hash".into(),
            JsonValue::String(self.entry_hash.clone()),
        );
        map.insert(
            "payload_sha256".into(),
            JsonValue::String(self.payload_sha256.clone()),
        );
        map.insert(
            "timestamp_utc".into(),
            JsonValue::String(self.timestamp_utc.clone()),
        );
        map.insert(
            "idempotent_replay".into(),
            JsonValue::Bool(self.idempotent_replay),
        );
        JsonValue::Object(map)
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ChainVerification {
    pub entries: u64,
    pub head_hash: String,
    pub valid: bool,
}

impl ChainVerification {
    pub fn to_json(&self) -> JsonValue {
        let mut map = BTreeMap::new();
        map.insert("entries".into(), JsonValue::Integer(self.entries as i64));
        map.insert(
            "head_hash".into(),
            JsonValue::String(self.head_hash.clone()),
        );
        map.insert("valid".into(), JsonValue::Bool(self.valid));
        JsonValue::Object(map)
    }
}

#[derive(Debug, Clone)]
struct ParsedRecord {
    seq: u64,
    timestamp_utc: String,
    request_id: String,
    event_type: String,
    payload_sha256: String,
    prev_hash: String,
    entry_hash: String,
}

#[derive(Debug, Clone)]
pub struct DurableJournal {
    path: PathBuf,
    lock_path: PathBuf,
    recovered_truncated_bytes: usize,
}

struct LockGuard {
    file: File,
}

impl LockGuard {
    fn acquire(lock_path: &Path) -> Result<Self, JournalError> {
        if let Some(parent) = lock_path.parent() {
            if !parent.as_os_str().is_empty() {
                fs::create_dir_all(parent)?;
            }
        }
        let file = OpenOptions::new()
            .create(true)
            .read(true)
            .write(true)
            .truncate(false)
            .open(lock_path)?;
        file.lock()?;
        Ok(Self { file })
    }
}

impl Drop for LockGuard {
    fn drop(&mut self) {
        let _ = self.file.unlock();
    }
}

impl DurableJournal {
    pub fn open(path: impl AsRef<Path>, policy: RecoveryPolicy) -> Result<Self, JournalError> {
        let path_buf = path.as_ref().to_path_buf();
        if path_buf.as_os_str().is_empty() {
            return Err(JournalError::InvalidInput(
                "chemin du journal vide".to_string(),
            ));
        }
        let lock_path = lock_path_for(&path_buf);

        let recovered_truncated_bytes = {
            let _lock = LockGuard::acquire(&lock_path)?;
            if !path_buf.exists() {
                File::create(&path_buf)?.sync_all()?;
                sync_parent_dir(&path_buf)?;
                0
            } else {
                recover_or_verify_raw(&path_buf, policy)?
            }
        };

        Ok(Self {
            path: path_buf,
            lock_path,
            recovered_truncated_bytes,
        })
    }

    pub fn path(&self) -> &Path {
        &self.path
    }

    pub fn recovered_truncated_bytes(&self) -> usize {
        self.recovered_truncated_bytes
    }

    pub fn append_event(
        &self,
        request_id: &str,
        event_type: &str,
        payload: JsonValue,
        clock: &dyn Clock,
    ) -> Result<AppendReceipt, JournalError> {
        if request_id.trim().is_empty() || event_type.trim().is_empty() {
            return Err(JournalError::InvalidInput(
                "request_id et event_type obligatoires et non vides".into(),
            ));
        }

        let payload_canonical = payload.to_canonical_string();
        let payload_sha256 = sha256_hex(payload_canonical.as_bytes());
        let idempotency_digest = idempotency_fingerprint(event_type, &payload_sha256);

        let _lock = LockGuard::acquire(&self.lock_path)?;
        let records = load_and_verify_records(&self.path)?;

        for rec in &records {
            if rec.request_id == request_id {
                let existing_fp = idempotency_fingerprint(&rec.event_type, &rec.payload_sha256);
                if existing_fp == idempotency_digest {
                    return Ok(AppendReceipt {
                        seq: rec.seq,
                        prev_hash: rec.prev_hash.clone(),
                        entry_hash: rec.entry_hash.clone(),
                        payload_sha256: rec.payload_sha256.clone(),
                        timestamp_utc: rec.timestamp_utc.clone(),
                        idempotent_replay: true,
                    });
                }
                return Err(JournalError::IdempotencyConflict {
                    request_id: request_id.to_string(),
                    existing_hash: existing_fp,
                    attempted_hash: idempotency_digest,
                });
            }
        }

        let (seq, prev_hash) = match records.last() {
            Some(last) => (last.seq + 1, last.entry_hash.clone()),
            None => (1, "GENESIS".to_string()),
        };

        let timestamp_unix = clock.now_unix_secs();
        let timestamp_utc = clock.now_rfc3339();

        let mut body = BTreeMap::new();
        body.insert("seq".into(), JsonValue::Integer(seq as i64));
        body.insert(
            "timestamp_utc".into(),
            JsonValue::String(timestamp_utc.clone()),
        );
        body.insert(
            "timestamp_unix".into(),
            JsonValue::Integer(timestamp_unix as i64),
        );
        body.insert("request_id".into(), JsonValue::String(request_id.into()));
        body.insert("event_type".into(), JsonValue::String(event_type.into()));
        body.insert(
            "payload_sha256".into(),
            JsonValue::String(payload_sha256.clone()),
        );
        body.insert("payload".into(), payload);
        body.insert("prev_hash".into(), JsonValue::String(prev_hash.clone()));

        let canonical_body = JsonValue::Object(body.clone()).to_canonical_string();
        let entry_hash = worm_entry_hash(&prev_hash, &canonical_body);

        body.insert("entry_hash".into(), JsonValue::String(entry_hash.clone()));
        let mut line = JsonValue::Object(body).to_canonical_string();
        line.push('\n');

        let mut file = OpenOptions::new()
            .create(true)
            .append(true)
            .open(&self.path)?;
        file.write_all(line.as_bytes())?;
        file.flush()?;
        file.sync_all()?;
        sync_parent_dir(&self.path)?;

        Ok(AppendReceipt {
            seq,
            prev_hash,
            entry_hash,
            payload_sha256,
            timestamp_utc,
            idempotent_replay: false,
        })
    }

    pub fn verify_chain(&self) -> Result<ChainVerification, JournalError> {
        let _lock = LockGuard::acquire(&self.lock_path)?;
        let records = load_and_verify_records(&self.path)?;
        let head_hash = records
            .last()
            .map(|r| r.entry_hash.clone())
            .unwrap_or_else(|| "GENESIS".to_string());
        Ok(ChainVerification {
            entries: records.len() as u64,
            head_hash,
            valid: true,
        })
    }
}

fn lock_path_for(path: &Path) -> PathBuf {
    let mut os = path.as_os_str().to_os_string();
    os.push(".lock");
    PathBuf::from(os)
}

fn sync_parent_dir(path: &Path) -> Result<(), JournalError> {
    #[cfg(unix)]
    {
        if let Some(parent) = path.parent() {
            let dir = if parent.as_os_str().is_empty() {
                Path::new(".")
            } else {
                parent
            };
            if let Ok(handle) = File::open(dir) {
                let _ = handle.sync_all();
            }
        }
    }
    let _ = path;
    Ok(())
}

fn idempotency_fingerprint(event_type: &str, payload_sha256: &str) -> String {
    sha256_hex(format!("{event_type}\0{payload_sha256}").as_bytes())
}

fn recover_or_verify_raw(path: &Path, policy: RecoveryPolicy) -> Result<usize, JournalError> {
    let mut raw = Vec::new();
    {
        let mut f = File::open(path)?;
        f.read_to_end(&mut raw)?;
    }
    if raw.is_empty() {
        return Ok(0);
    }

    let last_nl = raw.iter().rposition(|&b| b == b'\n');
    let has_trailing_partial = match last_nl {
        Some(pos) => pos + 1 < raw.len(),
        None => true,
    };

    if !has_trailing_partial {
        let _ = verify_complete_bytes(&raw)?;
        return Ok(0);
    }

    let (intact_prefix, trailing_bytes) = match last_nl {
        Some(pos) => (&raw[..=pos], raw.len() - (pos + 1)),
        None => (&[][..], raw.len()),
    };

    // Always verify intact prefix first so historical tamper is never masked as tail crash!
    let _ = verify_complete_bytes(intact_prefix)?;

    match policy {
        RecoveryPolicy::Strict => Err(JournalError::TruncatedTail { trailing_bytes }),
        RecoveryPolicy::TruncatePartialTail => {
            let mut file = OpenOptions::new().write(true).open(path)?;
            file.set_len(intact_prefix.len() as u64)?;
            file.seek(SeekFrom::End(0))?;
            file.sync_all()?;
            sync_parent_dir(path)?;
            Ok(trailing_bytes)
        }
    }
}

fn load_and_verify_records(path: &Path) -> Result<Vec<ParsedRecord>, JournalError> {
    if !path.exists() {
        return Ok(Vec::new());
    }
    let mut raw = Vec::new();
    {
        let mut f = File::open(path)?;
        f.read_to_end(&mut raw)?;
    }
    verify_complete_bytes(&raw)
}

fn verify_complete_bytes(raw: &[u8]) -> Result<Vec<ParsedRecord>, JournalError> {
    if raw.is_empty() {
        return Ok(Vec::new());
    }
    if !raw.ends_with(b"\n") {
        let last_nl = raw.iter().rposition(|&b| b == b'\n');
        let trailing_bytes = match last_nl {
            Some(pos) => raw.len() - (pos + 1),
            None => raw.len(),
        };
        return Err(JournalError::TruncatedTail { trailing_bytes });
    }

    let text = std::str::from_utf8(raw).map_err(|e| JournalError::TamperDetected {
        line: 1,
        reason: format!("UTF-8 invalide dans le journal : {e}"),
    })?;

    let mut records = Vec::new();
    let mut expected_prev = "GENESIS".to_string();

    for (idx, line_raw) in text.split_terminator('\n').enumerate() {
        let line_no = idx + 1;
        if line_raw.trim().is_empty() {
            return Err(JournalError::TamperDetected {
                line: line_no,
                reason: "ligne vide inattendue dans le ledger".into(),
            });
        }
        let val = parse_json(line_raw).map_err(|e| JournalError::TamperDetected {
            line: line_no,
            reason: format!("JSON corrompu : {e}"),
        })?;
        let obj = val
            .as_object()
            .ok_or_else(|| JournalError::TamperDetected {
                line: line_no,
                reason: "l'enregistrement doit etre un objet JSON".into(),
            })?;

        let expected_keys = [
            "entry_hash",
            "event_type",
            "payload",
            "payload_sha256",
            "prev_hash",
            "request_id",
            "seq",
            "timestamp_unix",
            "timestamp_utc",
        ];
        if obj.len() != expected_keys.len() || !expected_keys.iter().all(|k| obj.contains_key(*k)) {
            return Err(JournalError::TamperDetected {
                line: line_no,
                reason: "ensemble de champs WORM altere".into(),
            });
        }

        let seq = obj.get("seq").and_then(JsonValue::as_u64).ok_or_else(|| {
            JournalError::TamperDetected {
                line: line_no,
                reason: "seq invalide".into(),
            }
        })?;
        if seq != line_no as u64 {
            return Err(JournalError::TamperDetected {
                line: line_no,
                reason: format!("sequence rompue : attendu {line_no}, recu {seq}"),
            });
        }

        let prev_hash = obj
            .get("prev_hash")
            .and_then(JsonValue::as_str)
            .ok_or_else(|| JournalError::TamperDetected {
                line: line_no,
                reason: "prev_hash manquant".into(),
            })?;
        if prev_hash != expected_prev {
            return Err(JournalError::TamperDetected {
                line: line_no,
                reason: "rupture de chainage prev_hash".into(),
            });
        }

        let payload = obj
            .get("payload")
            .ok_or_else(|| JournalError::TamperDetected {
                line: line_no,
                reason: "payload manquant".into(),
            })?;
        let payload_sha256 = obj
            .get("payload_sha256")
            .and_then(JsonValue::as_str)
            .ok_or_else(|| JournalError::TamperDetected {
                line: line_no,
                reason: "payload_sha256 invalide".into(),
            })?;
        let recomputed_payload_sha = sha256_hex(payload.to_canonical_string().as_bytes());
        if payload_sha256 != recomputed_payload_sha {
            return Err(JournalError::TamperDetected {
                line: line_no,
                reason: "payload_sha256 falsifie".into(),
            });
        }

        let entry_hash = obj
            .get("entry_hash")
            .and_then(JsonValue::as_str)
            .ok_or_else(|| JournalError::TamperDetected {
                line: line_no,
                reason: "entry_hash manquant".into(),
            })?;
        let timestamp_utc = obj
            .get("timestamp_utc")
            .and_then(JsonValue::as_str)
            .ok_or_else(|| JournalError::TamperDetected {
                line: line_no,
                reason: "timestamp_utc invalide".into(),
            })?;
        let request_id = obj
            .get("request_id")
            .and_then(JsonValue::as_str)
            .ok_or_else(|| JournalError::TamperDetected {
                line: line_no,
                reason: "request_id invalide".into(),
            })?;
        let event_type = obj
            .get("event_type")
            .and_then(JsonValue::as_str)
            .ok_or_else(|| JournalError::TamperDetected {
                line: line_no,
                reason: "event_type invalide".into(),
            })?;

        let mut body = obj.clone();
        body.remove("entry_hash");
        let canonical_body = JsonValue::Object(body).to_canonical_string();
        let recomputed_entry_hash = worm_entry_hash(prev_hash, &canonical_body);
        if entry_hash != recomputed_entry_hash {
            return Err(JournalError::TamperDetected {
                line: line_no,
                reason: "empreinte SUPELA-WORM-V1 alteree".into(),
            });
        }

        expected_prev = entry_hash.to_string();
        records.push(ParsedRecord {
            seq,
            timestamp_utc: timestamp_utc.to_string(),
            request_id: request_id.to_string(),
            event_type: event_type.to_string(),
            payload_sha256: payload_sha256.to_string(),
            prev_hash: prev_hash.to_string(),
            entry_hash: entry_hash.to_string(),
        });
    }

    Ok(records)
}
