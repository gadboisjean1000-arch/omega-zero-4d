#![forbid(unsafe_code)]

use std::env;
use std::io::{self, BufReader, BufWriter};
use std::path::PathBuf;
use std::process::ExitCode;
use std::sync::Arc;

use supela_guard_kernel::{
    build_status_json, DurableJournal, GuardService, RecoveryPolicy, SystemClock,
    DEFAULT_MAX_FUTURE_SKEW_SECS, DEFAULT_MAX_LINE_BYTES,
};

const DEFAULT_JOURNAL_PATH: &str = ".omega_vault/rust_guard_journal.jsonl";

fn print_usage() {
    eprintln!(
        "Usage: supela-guard-kernel <serve|verify|status> [--journal <PATH>] [--max-line-bytes <N>]"
    );
}

fn parse_args(args: &[String]) -> Result<(String, PathBuf, usize), String> {
    if args.is_empty() || matches!(args[0].as_str(), "-h" | "--help") {
        return Err("help".into());
    }

    let cmd = args[0].clone();
    if !matches!(cmd.as_str(), "serve" | "verify" | "status") {
        return Err(format!("commande inconnue : {cmd}"));
    }

    let mut journal = PathBuf::from(DEFAULT_JOURNAL_PATH);
    let mut max_line_bytes = DEFAULT_MAX_LINE_BYTES;

    let mut i = 1usize;
    while i < args.len() {
        match args[i].as_str() {
            "--journal" => {
                i += 1;
                if i >= args.len() {
                    return Err("--journal exige un chemin".into());
                }
                journal = PathBuf::from(&args[i]);
            }
            "--max-line-bytes" => {
                i += 1;
                if i >= args.len() {
                    return Err("--max-line-bytes exige un entier".into());
                }
                max_line_bytes = args[i]
                    .parse::<usize>()
                    .map_err(|_| "--max-line-bytes invalide".to_string())?;
                if max_line_bytes == 0 {
                    return Err("--max-line-bytes doit etre > 0".into());
                }
            }
            "--stdio" => {}
            other => return Err(format!("option inconnue : {other}")),
        }
        i += 1;
    }

    Ok((cmd, journal, max_line_bytes))
}

fn main() -> ExitCode {
    let args: Vec<String> = env::args().skip(1).collect();
    let (cmd, journal_path, max_line_bytes) = match parse_args(&args) {
        Ok(parsed) => parsed,
        Err(msg) if msg == "help" => {
            print_usage();
            return ExitCode::SUCCESS;
        }
        Err(msg) => {
            eprintln!("Erreur arguments : {msg}");
            print_usage();
            return ExitCode::from(2);
        }
    };

    match cmd.as_str() {
        "serve" => {
            let journal =
                match DurableJournal::open(&journal_path, RecoveryPolicy::TruncatePartialTail) {
                    Ok(j) => j,
                    Err(e) => {
                        eprintln!("Erreur ouverture journal : {e}");
                        return ExitCode::FAILURE;
                    }
                };
            let service = GuardService::new(journal, Arc::new(SystemClock))
                .with_limits(max_line_bytes, DEFAULT_MAX_FUTURE_SKEW_SECS);
            let stdin = io::stdin();
            let stdout = io::stdout();
            let mut reader = BufReader::new(stdin.lock());
            let mut writer = BufWriter::new(stdout.lock());
            if let Err(e) = service.serve_stream(&mut reader, &mut writer) {
                eprintln!("Erreur service SUP-IPC-01 : {e}");
                return ExitCode::FAILURE;
            }
            ExitCode::SUCCESS
        }
        "verify" => {
            let journal = match DurableJournal::open(&journal_path, RecoveryPolicy::Strict) {
                Ok(j) => j,
                Err(e) => {
                    println!("{}", serde_error_json(e.code(), &e.to_string()));
                    return ExitCode::FAILURE;
                }
            };
            match journal.verify_chain() {
                Ok(ver) => {
                    println!("{}", ver.to_json().to_canonical_string());
                    ExitCode::SUCCESS
                }
                Err(e) => {
                    println!("{}", serde_error_json(e.code(), &e.to_string()));
                    ExitCode::FAILURE
                }
            }
        }
        "status" => {
            let journal =
                match DurableJournal::open(&journal_path, RecoveryPolicy::TruncatePartialTail) {
                    Ok(j) => j,
                    Err(e) => {
                        println!("{}", serde_error_json(e.code(), &e.to_string()));
                        return ExitCode::FAILURE;
                    }
                };
            match journal.verify_chain() {
                Ok(ver) => {
                    let status = build_status_json(
                        &ver,
                        journal.recovered_truncated_bytes(),
                        max_line_bytes,
                    );
                    println!("{}", status.to_canonical_string());
                    ExitCode::SUCCESS
                }
                Err(e) => {
                    println!("{}", serde_error_json(e.code(), &e.to_string()));
                    ExitCode::FAILURE
                }
            }
        }
        _ => ExitCode::from(2),
    }
}

fn serde_error_json(code: &str, message: &str) -> String {
    use std::collections::BTreeMap;
    use supela_guard_kernel::JsonValue;

    let mut map = BTreeMap::new();
    map.insert("ok".into(), JsonValue::Bool(false));
    map.insert("code".into(), JsonValue::String(code.into()));
    map.insert("message".into(), JsonValue::String(message.into()));
    JsonValue::Object(map).to_canonical_string()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_serve_verify_status_and_rejects_invalid_args() {
        let parsed = parse_args(&[
            "serve".into(),
            "--journal".into(),
            "/tmp/j.jsonl".into(),
            "--max-line-bytes".into(),
            "4096".into(),
            "--stdio".into(),
        ])
        .unwrap();
        assert_eq!(parsed.0, "serve");
        assert_eq!(parsed.1, PathBuf::from("/tmp/j.jsonl"));
        assert_eq!(parsed.2, 4096);

        assert!(parse_args(&["verify".into()]).is_ok());
        assert!(parse_args(&["status".into()]).is_ok());
        assert_eq!(parse_args(&["--help".into()]).unwrap_err(), "help");
        assert!(parse_args(&["serve".into(), "--max-line-bytes".into(), "0".into()]).is_err());
        assert!(parse_args(&["unknown".into()]).is_err());
    }
}
