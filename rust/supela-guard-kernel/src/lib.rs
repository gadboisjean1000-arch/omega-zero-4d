#![forbid(unsafe_code)]

pub mod base64;
pub mod clock;
pub mod ipc;
pub mod journal;
pub mod json;
pub mod kernel;
pub mod sha256;

pub use clock::{Clock, FixedClock, SystemClock};
pub use ipc::{
    build_status_json, read_bounded_line, GuardService, IpcError, DEFAULT_MAX_FUTURE_SKEW_SECS,
    DEFAULT_MAX_LINE_BYTES, IPC_PROTOCOL_VERSION,
};
pub use journal::{AppendReceipt, ChainVerification, DurableJournal, JournalError, RecoveryPolicy};
pub use json::{parse_json, JsonError, JsonValue};
pub use kernel::{
    evaluate_candidate_policy, evaluate_transition, AccessibilityMode, CandidatePolicyOutcome,
    CandidatePolicyRequest, CompressionLevel, GenerationStage, KernelError, KernelObjectStatus,
    TransitionDecision, TransitionRequest,
};
pub use sha256::{domain_separated_sha256, sha256_hex, worm_entry_hash, Sha256, WORM_DOMAIN_TAG};
