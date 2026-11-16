use std::collections::BTreeMap;
use std::io::{BufRead, Write};
use std::sync::Arc;

use crate::base64;
use crate::clock::{parse_rfc3339_unix_secs, Clock};
use crate::journal::{DurableJournal, JournalError};
use crate::json::{parse_json, JsonValue};
use crate::kernel::{
    evaluate_candidate_policy, evaluate_transition, CandidatePolicyRequest, CompressionLevel,
    GenerationStage, KernelError, KernelObjectStatus, TransitionRequest,
};

pub const IPC_PROTOCOL_VERSION: &str = "SUP-IPC-01";
pub const DEFAULT_MAX_LINE_BYTES: usize = 1_048_576;
pub const DEFAULT_MAX_FUTURE_SKEW_SECS: u64 = 300;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum IpcError {
    InvalidConfig(String),
    Io(String),
    LineTooLarge {
        max_bytes: usize,
        observed_bytes: usize,
    },
    InvalidUtf8(String),
}

impl std::fmt::Display for IpcError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::InvalidConfig(msg) => write!(f, "configuration IPC invalide : {msg}"),
            Self::Io(msg) => write!(f, "erreur E/S IPC : {msg}"),
            Self::LineTooLarge {
                max_bytes,
                observed_bytes,
            } => write!(
                f,
                "ligne IPC hors borne memoire ({observed_bytes} octets > limite {max_bytes})"
            ),
            Self::InvalidUtf8(msg) => write!(f, "UTF-8 IPC invalide : {msg}"),
        }
    }
}

impl std::error::Error for IpcError {}

impl From<std::io::Error> for IpcError {
    fn from(err: std::io::Error) -> Self {
        Self::Io(err.to_string())
    }
}

/// Reads a single newline-delimited frame using strictly O(1) bounded memory
/// capped at `max_bytes`. Excess bytes up to the next `\n` (or EOF) are drained
/// chunk-by-chunk without buffering them into heap memory.
pub fn read_bounded_line<R: BufRead>(
    reader: &mut R,
    max_bytes: usize,
) -> Result<Option<String>, IpcError> {
    if max_bytes == 0 {
        return Err(IpcError::InvalidConfig(
            "max_bytes doit etre superieur a 0".into(),
        ));
    }

    let mut buf: Vec<u8> = Vec::new();
    loop {
        let avail = reader.fill_buf()?;
        if avail.is_empty() {
            if buf.is_empty() {
                return Ok(None);
            }
            if buf.last() == Some(&b'\r') {
                buf.pop();
            }
            let s = String::from_utf8(buf).map_err(|e| IpcError::InvalidUtf8(e.to_string()))?;
            return Ok(Some(s));
        }

        if let Some(nl_pos) = avail.iter().position(|&b| b == b'\n') {
            let new_len = buf.len().saturating_add(nl_pos);
            if new_len > max_bytes {
                reader.consume(nl_pos + 1);
                return Err(IpcError::LineTooLarge {
                    max_bytes,
                    observed_bytes: new_len,
                });
            }
            buf.extend_from_slice(&avail[..nl_pos]);
            reader.consume(nl_pos + 1);
            if buf.last() == Some(&b'\r') {
                buf.pop();
            }
            let s = String::from_utf8(buf).map_err(|e| IpcError::InvalidUtf8(e.to_string()))?;
            return Ok(Some(s));
        }

        let new_len = buf.len().saturating_add(avail.len());
        if new_len > max_bytes {
            let mut total = buf.len().saturating_add(avail.len());
            drop(buf);
            let avail_len = avail.len();
            reader.consume(avail_len);
            loop {
                let chunk = reader.fill_buf()?;
                if chunk.is_empty() {
                    break;
                }
                if let Some(nl_pos) = chunk.iter().position(|&b| b == b'\n') {
                    total = total.saturating_add(nl_pos);
                    reader.consume(nl_pos + 1);
                    break;
                }
                let chunk_len = chunk.len();
                total = total.saturating_add(chunk_len);
                reader.consume(chunk_len);
            }
            return Err(IpcError::LineTooLarge {
                max_bytes,
                observed_bytes: total,
            });
        }

        buf.extend_from_slice(avail);
        let avail_len = avail.len();
        reader.consume(avail_len);
    }
}

pub struct GuardService {
    journal: DurableJournal,
    clock: Arc<dyn Clock>,
    max_future_skew_secs: u64,
    max_line_bytes: usize,
}

impl GuardService {
    pub fn new(journal: DurableJournal, clock: Arc<dyn Clock>) -> Self {
        Self {
            journal,
            clock,
            max_future_skew_secs: DEFAULT_MAX_FUTURE_SKEW_SECS,
            max_line_bytes: DEFAULT_MAX_LINE_BYTES,
        }
    }

    pub fn with_limits(mut self, max_line_bytes: usize, max_future_skew_secs: u64) -> Self {
        self.max_line_bytes = max_line_bytes;
        self.max_future_skew_secs = max_future_skew_secs;
        self
    }

    pub fn journal(&self) -> &DurableJournal {
        &self.journal
    }

    pub fn serve_stream<R: BufRead, W: Write>(
        &self,
        reader: &mut R,
        writer: &mut W,
    ) -> Result<usize, IpcError> {
        let mut handled = 0usize;
        loop {
            match read_bounded_line(reader, self.max_line_bytes) {
                Ok(None) => break,
                Ok(Some(line)) => {
                    if line.trim().is_empty() {
                        continue;
                    }
                    let resp = self.handle_line(&line);
                    let encoded = resp.to_canonical_string();
                    writer.write_all(encoded.as_bytes())?;
                    writer.write_all(b"\n")?;
                    writer.flush()?;
                    handled += 1;
                }
                Err(IpcError::LineTooLarge {
                    max_bytes,
                    observed_bytes,
                }) => {
                    let resp = error_response(
                        None,
                        "LINE_TOO_LARGE",
                        &format!(
                            "trame IPC depassant la borne memoire ({observed_bytes} > {max_bytes} octets)"
                        ),
                    );
                    let encoded = resp.to_canonical_string();
                    writer.write_all(encoded.as_bytes())?;
                    writer.write_all(b"\n")?;
                    writer.flush()?;
                    handled += 1;
                }
                Err(IpcError::InvalidUtf8(msg)) => {
                    let resp = error_response(None, "INVALID_UTF8", &msg);
                    let encoded = resp.to_canonical_string();
                    writer.write_all(encoded.as_bytes())?;
                    writer.write_all(b"\n")?;
                    writer.flush()?;
                    handled += 1;
                }
                Err(err) => return Err(err),
            }
        }
        Ok(handled)
    }

    pub fn handle_line(&self, raw_line: &str) -> JsonValue {
        let parsed = match parse_json(raw_line) {
            Ok(v) => v,
            Err(e) => return error_response(None, "INVALID_JSON", &e.to_string()),
        };

        let request_id = parsed.get("request_id").and_then(JsonValue::as_str);

        let protocol = match parsed.get("protocol").and_then(JsonValue::as_str) {
            Some(p) => p,
            None => {
                return error_response(
                    request_id,
                    "UNSUPPORTED_PROTOCOL",
                    "champ obligatoire 'protocol' manquant (attendu SUP-IPC-01)",
                );
            }
        };
        if protocol != IPC_PROTOCOL_VERSION {
            return error_response(
                request_id,
                "UNSUPPORTED_PROTOCOL",
                &format!("protocole non supporte : '{protocol}' (attendu {IPC_PROTOCOL_VERSION})"),
            );
        }

        let req_id = match request_id {
            Some(id) if !id.trim().is_empty() => id,
            _ => {
                return error_response(
                    None,
                    "INVALID_REQUEST_ID",
                    "champ 'request_id' obligatoire et non vide",
                );
            }
        };

        if let Some(ts_val) = parsed.get("timestamp_utc") {
            let ts_str = match ts_val.as_str() {
                Some(s) => s,
                None => {
                    return error_response(
                        Some(req_id),
                        "INVALID_TIMESTAMP",
                        "timestamp_utc doit etre une chaine RFC 3339",
                    );
                }
            };
            let parsed_ts = match parse_rfc3339_unix_secs(ts_str) {
                Ok(t) => t,
                Err(e) => {
                    return error_response(Some(req_id), "INVALID_TIMESTAMP", &e.message);
                }
            };
            let max_allowed = self
                .clock
                .now_unix_secs()
                .saturating_add(self.max_future_skew_secs);
            if parsed_ts > max_allowed {
                return error_response(
                    Some(req_id),
                    "FUTURE_TIMESTAMP_REJECTED",
                    &format!("horodatage futur rejete ({parsed_ts} > max autorise {max_allowed})"),
                );
            }
        }

        let op = match parsed.get("op").and_then(JsonValue::as_str) {
            Some(o) if !o.trim().is_empty() => o,
            _ => {
                return error_response(
                    Some(req_id),
                    "INVALID_OPERATION",
                    "champ 'op' obligatoire et non vide",
                );
            }
        };

        let empty_params = JsonValue::Object(BTreeMap::new());
        let params = parsed.get("params").unwrap_or(&empty_params);
        if params.as_object().is_none() {
            return error_response(
                Some(req_id),
                "INVALID_PARAMS",
                "champ 'params' doit etre un objet JSON",
            );
        }

        match op {
            "ping" => self.op_ping(req_id),
            "status" => self.op_status(req_id),
            "verify_chain" => self.op_verify_chain(req_id),
            "append_event" => self.op_append_event(req_id, params),
            "evaluate_candidate" => self.op_evaluate_candidate(req_id, params),
            "compress_transition" => self.op_compress_transition(req_id, params),
            other => error_response(
                Some(req_id),
                "UNKNOWN_OPERATION",
                &format!("operation inconnue : {other}"),
            ),
        }
    }

    fn op_ping(&self, req_id: &str) -> JsonValue {
        match self.journal.verify_chain() {
            Ok(ver) => {
                let mut map = BTreeMap::new();
                map.insert("status".into(), JsonValue::String("OK".into()));
                map.insert(
                    "protocol".into(),
                    JsonValue::String(IPC_PROTOCOL_VERSION.into()),
                );
                map.insert("zero_external_crates".into(), JsonValue::Bool(true));
                map.insert("entries".into(), JsonValue::Integer(ver.entries as i64));
                ok_response(req_id, JsonValue::Object(map))
            }
            Err(e) => error_response(Some(req_id), e.code(), &e.to_string()),
        }
    }

    fn op_status(&self, req_id: &str) -> JsonValue {
        match self.journal.verify_chain() {
            Ok(ver) => ok_response(
                req_id,
                build_status_json(
                    &ver,
                    self.journal.recovered_truncated_bytes(),
                    self.max_line_bytes,
                ),
            ),
            Err(e) => error_response(Some(req_id), e.code(), &e.to_string()),
        }
    }

    fn op_verify_chain(&self, req_id: &str) -> JsonValue {
        match self.journal.verify_chain() {
            Ok(ver) => ok_response(req_id, ver.to_json()),
            Err(e) => error_response(Some(req_id), e.code(), &e.to_string()),
        }
    }

    fn op_append_event(&self, req_id: &str, params: &JsonValue) -> JsonValue {
        let event_type = match params.get("event_type").and_then(JsonValue::as_str) {
            Some(s) if !s.trim().is_empty() => s,
            _ => {
                return error_response(
                    Some(req_id),
                    "INVALID_PARAMS",
                    "params.event_type obligatoire",
                );
            }
        };

        if let Some(b64_val) = params.get("payload_b64") {
            let b64_str = match b64_val.as_str() {
                Some(s) => s,
                None => {
                    return error_response(
                        Some(req_id),
                        "INVALID_BASE64",
                        "params.payload_b64 doit etre une chaine Base64",
                    );
                }
            };
            if let Err(e) = base64::decode(b64_str) {
                return error_response(Some(req_id), "INVALID_BASE64", &e.to_string());
            }
        }

        let payload = match params.get("payload") {
            Some(p) => p.clone(),
            None => JsonValue::Object(BTreeMap::new()),
        };

        match self
            .journal
            .append_event(req_id, event_type, payload, self.clock.as_ref())
        {
            Ok(receipt) => ok_response(req_id, receipt.to_json()),
            Err(e) => error_response(Some(req_id), e.code(), &e.to_string()),
        }
    }

    fn op_evaluate_candidate(&self, req_id: &str, params: &JsonValue) -> JsonValue {
        let candidate_id = match params.get("candidate_id").and_then(JsonValue::as_str) {
            Some(s) if !s.trim().is_empty() => s.to_string(),
            _ => {
                return error_response(
                    Some(req_id),
                    "INVALID_PARAMS",
                    "params.candidate_id obligatoire",
                );
            }
        };

        let reward = match params.get("reward").and_then(JsonValue::as_f64) {
            Some(v) => v,
            None => {
                return error_response(
                    Some(req_id),
                    "GF1_NON_FINITE_REWARD",
                    "params.reward numerique fini obligatoire",
                );
            }
        };

        let r_max = params
            .get("r_max")
            .and_then(JsonValue::as_f64)
            .unwrap_or(1.0);
        let proof_verified = params
            .get("proof_verified")
            .and_then(JsonValue::as_bool)
            .unwrap_or(false);
        let requested_status = params
            .get("requested_status")
            .and_then(JsonValue::as_str)
            .unwrap_or("CANDIDAT")
            .to_string();
        let requested_authority_level = params
            .get("requested_authority_level")
            .and_then(JsonValue::as_i64)
            .unwrap_or(0);
        let evidence_level = params
            .get("evidence_level")
            .and_then(JsonValue::as_i64)
            .unwrap_or(0);
        let human_ratified = params
            .get("human_ratified")
            .and_then(JsonValue::as_bool)
            .unwrap_or(false);

        let eval_req = CandidatePolicyRequest {
            candidate_id,
            reward,
            r_max,
            proof_verified,
            requested_status,
            requested_authority_level,
            evidence_level,
            human_ratified,
        };

        let outcome = match evaluate_candidate_policy(&eval_req) {
            Ok(out) => out,
            Err(e) => return error_response(Some(req_id), e.code(), &e.to_string()),
        };

        let receipt = match self.journal.append_event(
            req_id,
            "CANDIDATE_EVALUATION",
            outcome.to_json(),
            self.clock.as_ref(),
        ) {
            Ok(r) => r,
            Err(e) => return error_response(Some(req_id), e.code(), &e.to_string()),
        };

        let mut res = BTreeMap::new();
        res.insert("evaluation".into(), outcome.to_json());
        res.insert("receipt".into(), receipt.to_json());
        ok_response(req_id, JsonValue::Object(res))
    }

    fn op_compress_transition(&self, req_id: &str, params: &JsonValue) -> JsonValue {
        if let Some(b64_val) = params.get("content_b64") {
            let b64_str = match b64_val.as_str() {
                Some(s) => s,
                None => {
                    return error_response(
                        Some(req_id),
                        "INVALID_BASE64",
                        "params.content_b64 doit etre une chaine Base64",
                    );
                }
            };
            if let Err(e) = base64::decode(b64_str) {
                return error_response(Some(req_id), "INVALID_BASE64", &e.to_string());
            }
        }

        let req = match parse_transition_params(params) {
            Ok(r) => r,
            Err(e) => return error_response(Some(req_id), e.code(), &e.to_string()),
        };

        let decision = match evaluate_transition(&req) {
            Ok(d) => d,
            Err(e) => return error_response(Some(req_id), e.code(), &e.to_string()),
        };

        let receipt = match self.journal.append_event(
            req_id,
            "GUARD_KERNEL_TRANSITION",
            decision.to_json(),
            self.clock.as_ref(),
        ) {
            Ok(r) => r,
            Err(e) => return error_response(Some(req_id), e.code(), &e.to_string()),
        };

        let mut res = BTreeMap::new();
        res.insert("transition".into(), decision.to_json());
        res.insert("receipt".into(), receipt.to_json());
        ok_response(req_id, JsonValue::Object(res))
    }
}

pub fn build_status_json(
    ver: &crate::journal::ChainVerification,
    recovered_truncated_bytes: usize,
    max_line_bytes: usize,
) -> JsonValue {
    let mut map = BTreeMap::new();
    map.insert(
        "protocol".into(),
        JsonValue::String(IPC_PROTOCOL_VERSION.into()),
    );
    map.insert(
        "worm_mode".into(),
        JsonValue::String("COOPERATIVE_OS_FILE_LOCK_NOT_HARDWARE_TPM".into()),
    );
    map.insert(
        "crypto_audit_status".into(),
        JsonValue::String("PENDING_INDEPENDENT_AUDIT".into()),
    );
    map.insert("external_crates".into(), JsonValue::Integer(0));
    map.insert(
        "max_line_bytes".into(),
        JsonValue::Integer(max_line_bytes as i64),
    );
    map.insert(
        "recovered_truncated_bytes".into(),
        JsonValue::Integer(recovered_truncated_bytes as i64),
    );
    map.insert("chain".into(), ver.to_json());
    JsonValue::Object(map)
}

fn parse_transition_params(params: &JsonValue) -> Result<TransitionRequest, KernelError> {
    let req_str = |k: &str| -> Result<String, KernelError> {
        params
            .get(k)
            .and_then(JsonValue::as_str)
            .map(|s| s.to_string())
            .ok_or_else(|| KernelError::InvalidInput(format!("params.{k} manquant ou invalide")))
    };
    let opt_vec = |k: &str| -> Result<Vec<String>, KernelError> {
        match params.get(k) {
            None => Ok(Vec::new()),
            Some(val) => {
                let arr = val.as_array().ok_or_else(|| {
                    KernelError::InvalidInput(format!("params.{k} doit etre un tableau"))
                })?;
                let mut out = Vec::with_capacity(arr.len());
                for item in arr {
                    let s = item.as_str().ok_or_else(|| {
                        KernelError::InvalidInput(format!(
                            "element de params.{k} doit etre une chaine"
                        ))
                    })?;
                    out.push(s.to_string());
                }
                Ok(out)
            }
        }
    };

    let from_gen = GenerationStage::parse(&req_str("from_generation")?)?;
    let to_gen = GenerationStage::parse(&req_str("to_generation")?)?;
    let from_status = KernelObjectStatus::parse(
        params
            .get("from_status")
            .and_then(JsonValue::as_str)
            .unwrap_or("HYPOTHESE"),
    )?;
    let to_status = KernelObjectStatus::parse(
        params
            .get("to_status")
            .and_then(JsonValue::as_str)
            .unwrap_or("HYPOTHESE"),
    )?;
    let compression_level = CompressionLevel::parse(&req_str("compression_level")?)?;

    Ok(TransitionRequest {
        object_id: req_str("object_id")?,
        object_type: params
            .get("object_type")
            .and_then(JsonValue::as_str)
            .unwrap_or("kernel_artifact")
            .to_string(),
        author: req_str("author")?,
        origin: req_str("origin")?,
        scope: params
            .get("scope")
            .and_then(JsonValue::as_str)
            .unwrap_or("LOCAL")
            .to_string(),
        from_generation: from_gen,
        to_generation: to_gen,
        from_status,
        to_status,
        compression_level,
        previous_hash: req_str("previous_hash")?,
        reason: req_str("reason")?,
        transformation: params
            .get("transformation")
            .and_then(JsonValue::as_str)
            .unwrap_or("sup_ici_01_transition")
            .to_string(),
        existing_proofs: opt_vec("existing_proofs")?,
        output_proofs: opt_vec("output_proofs")?,
        existing_contradictions: opt_vec("existing_contradictions")?,
        output_contradictions: opt_vec("output_contradictions")?,
        dependencies: opt_vec("dependencies")?,
        reopening_conditions: match opt_vec("reopening_conditions")? {
            v if v.is_empty() => vec!["Nouvelle preuve ou contradiction".into()],
            v => v,
        },
        location: params
            .get("location")
            .and_then(JsonValue::as_str)
            .unwrap_or("inline://journal")
            .to_string(),
        claim_full_copy: params
            .get("claim_full_copy")
            .and_then(JsonValue::as_bool)
            .unwrap_or(false),
        inherit_authority_silently: params
            .get("inherit_authority_silently")
            .and_then(JsonValue::as_bool)
            .unwrap_or(false),
        human_ratified: params
            .get("human_ratified")
            .and_then(JsonValue::as_bool)
            .unwrap_or(false),
    })
}

fn ok_response(request_id: &str, result: JsonValue) -> JsonValue {
    let mut map = BTreeMap::new();
    map.insert(
        "protocol".into(),
        JsonValue::String(IPC_PROTOCOL_VERSION.into()),
    );
    map.insert("request_id".into(), JsonValue::String(request_id.into()));
    map.insert("ok".into(), JsonValue::Bool(true));
    map.insert("result".into(), result);
    JsonValue::Object(map)
}

fn error_response(request_id: Option<&str>, code: &str, message: &str) -> JsonValue {
    let mut err_obj = BTreeMap::new();
    err_obj.insert("code".into(), JsonValue::String(code.into()));
    err_obj.insert("message".into(), JsonValue::String(message.into()));

    let mut map = BTreeMap::new();
    map.insert(
        "protocol".into(),
        JsonValue::String(IPC_PROTOCOL_VERSION.into()),
    );
    map.insert(
        "request_id".into(),
        match request_id {
            Some(id) => JsonValue::String(id.into()),
            None => JsonValue::Null,
        },
    );
    map.insert("ok".into(), JsonValue::Bool(false));
    map.insert("error".into(), JsonValue::Object(err_obj));
    JsonValue::Object(map)
}

pub fn map_journal_err(err: &JournalError) -> (&'static str, String) {
    (err.code(), err.to_string())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::BufReader;

    #[test]
    fn read_bounded_line_rejects_oversized_line_with_o1_memory_and_recovers_stream() {
        let mut payload = b"0123456789abcdef\nsecond\n".to_vec();
        let mut reader = BufReader::with_capacity(4, payload.as_slice());

        let first = read_bounded_line(&mut reader, 8);
        assert!(matches!(
            first,
            Err(IpcError::LineTooLarge {
                max_bytes: 8,
                observed_bytes: 16
            })
        ));
        let second = read_bounded_line(&mut reader, 8).unwrap();
        assert_eq!(second.as_deref(), Some("second"));
        assert_eq!(read_bounded_line(&mut reader, 8).unwrap(), None);

        payload.clear();
    }

    #[test]
    fn read_bounded_line_handles_huge_unterminated_stream_without_oom() {
        let giant = "x".repeat(2_000_000);
        let mut reader = BufReader::with_capacity(4096, giant.as_bytes());
        let res = read_bounded_line(&mut reader, 1024);
        assert!(matches!(
            res,
            Err(IpcError::LineTooLarge {
                max_bytes: 1024,
                observed_bytes: 2_000_000
            })
        ));
    }
}
