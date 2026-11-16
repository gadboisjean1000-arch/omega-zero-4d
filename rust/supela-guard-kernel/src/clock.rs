use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ClockError {
    pub message: String,
}

impl std::fmt::Display for ClockError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "ClockError: {}", self.message)
    }
}

impl std::error::Error for ClockError {}

pub trait Clock: Send + Sync {
    fn now_unix_secs(&self) -> u64;

    fn now_rfc3339(&self) -> String {
        format_unix_rfc3339(self.now_unix_secs())
    }
}

#[derive(Debug, Default, Clone, Copy)]
pub struct SystemClock;

impl Clock for SystemClock {
    fn now_unix_secs(&self) -> u64 {
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0)
    }
}

#[derive(Debug)]
pub struct FixedClock {
    epoch_secs: AtomicU64,
}

impl FixedClock {
    pub fn new(epoch_secs: u64) -> Self {
        Self {
            epoch_secs: AtomicU64::new(epoch_secs),
        }
    }

    pub fn set(&self, epoch_secs: u64) {
        self.epoch_secs.store(epoch_secs, Ordering::SeqCst);
    }

    pub fn advance(&self, delta_secs: u64) -> u64 {
        self.epoch_secs.fetch_add(delta_secs, Ordering::SeqCst) + delta_secs
    }
}

impl Clock for FixedClock {
    fn now_unix_secs(&self) -> u64 {
        self.epoch_secs.load(Ordering::SeqCst)
    }
}

/// Formats UNIX seconds (UTC) as strict RFC 3339 (`YYYY-MM-DDTHH:MM:SSZ`).
/// Uses Howard Hinnant's civil-from-days algorithm in pure safe arithmetic.
pub fn format_unix_rfc3339(unix_secs: u64) -> String {
    let days = (unix_secs / 86_400) as i64;
    let rem = unix_secs % 86_400;
    let hour = rem / 3_600;
    let minute = (rem % 3_600) / 60;
    let second = rem % 60;

    let z = days + 719_468;
    let era = if z >= 0 { z } else { z - 146_096 } / 146_097;
    let doe = (z - era * 146_097) as u64;
    let yoe = (doe - doe / 1_460 + doe / 36_524 - doe / 146_096) / 365;
    let y = (yoe as i64) + era * 400;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let d = doy - (153 * mp + 2) / 5 + 1;
    let m = if mp < 10 { mp + 3 } else { mp - 9 };
    let year = y + i64::from(m <= 2);

    format!("{year:04}-{m:02}-{d:02}T{hour:02}:{minute:02}:{second:02}Z")
}

/// Parses an RFC 3339 UTC timestamp (`YYYY-MM-DDTHH:MM:SSZ` or `+00:00`, optional `.frac`).
pub fn parse_rfc3339_unix_secs(input: &str) -> Result<u64, ClockError> {
    let s = input.trim();
    let core = if let Some(stripped) = s.strip_suffix('Z') {
        stripped
    } else if let Some(stripped) = s.strip_suffix("+00:00") {
        stripped
    } else {
        return Err(ClockError {
            message: format!("horodatage RFC 3339 UTC requis ('Z' ou '+00:00') : {input}"),
        });
    };

    let main_part = match core.split_once('.') {
        Some((head, frac)) => {
            if frac.is_empty() || frac.len() > 9 || !frac.bytes().all(|b| b.is_ascii_digit()) {
                return Err(ClockError {
                    message: format!("fraction de secondes invalide : {input}"),
                });
            }
            head
        }
        None => core,
    };

    let bytes = main_part.as_bytes();
    if bytes.len() != 19
        || bytes[4] != b'-'
        || bytes[7] != b'-'
        || bytes[10] != b'T'
        || bytes[13] != b':'
        || bytes[16] != b':'
    {
        return Err(ClockError {
            message: format!("format RFC 3339 attendu YYYY-MM-DDTHH:MM:SSZ : {input}"),
        });
    }

    let year: i64 = parse_digits(&main_part[0..4])? as i64;
    let month: u64 = parse_digits(&main_part[5..7])?;
    let day: u64 = parse_digits(&main_part[8..10])?;
    let hour: u64 = parse_digits(&main_part[11..13])?;
    let minute: u64 = parse_digits(&main_part[14..16])?;
    let second: u64 = parse_digits(&main_part[17..19])?;

    if !(1970..=9999).contains(&year)
        || !(1..=12).contains(&month)
        || hour > 23
        || minute > 59
        || second > 59
    {
        return Err(ClockError {
            message: format!("composantes date/heure hors bornes : {input}"),
        });
    }

    let max_day = days_in_month(year, month);
    if day == 0 || day > max_day {
        return Err(ClockError {
            message: format!("jour invalide pour {year:04}-{month:02} : {day}"),
        });
    }

    let days = days_from_civil(year, month, day);
    if days < 0 {
        return Err(ClockError {
            message: format!("date anterieure a UNIX epoch : {input}"),
        });
    }

    Ok((days as u64) * 86_400 + hour * 3_600 + minute * 60 + second)
}

fn parse_digits(s: &str) -> Result<u64, ClockError> {
    if !s.bytes().all(|b| b.is_ascii_digit()) {
        return Err(ClockError {
            message: format!("valeur numerique attendue : {s}"),
        });
    }
    s.parse::<u64>().map_err(|_| ClockError {
        message: format!("debordement numerique : {s}"),
    })
}

fn is_leap_year(year: i64) -> bool {
    (year % 4 == 0 && year % 100 != 0) || (year % 400 == 0)
}

fn days_in_month(year: i64, month: u64) -> u64 {
    match month {
        1 | 3 | 5 | 7 | 8 | 10 | 12 => 31,
        4 | 6 | 9 | 11 => 30,
        2 => {
            if is_leap_year(year) {
                29
            } else {
                28
            }
        }
        _ => 0,
    }
}

fn days_from_civil(year: i64, month: u64, day: u64) -> i64 {
    let y = year - i64::from(month <= 2);
    let era = if y >= 0 { y } else { y - 399 } / 400;
    let yoe = (y - era * 400) as u64;
    let m = month;
    let doy = (153 * (if m > 2 { m - 3 } else { m + 9 }) + 2) / 5 + day - 1;
    let doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
    era * 146_097 + (doe as i64) - 719_468
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn epoch_and_leap_day_roundtrip() {
        assert_eq!(format_unix_rfc3339(0), "1970-01-01T00:00:00Z");
        assert_eq!(parse_rfc3339_unix_secs("1970-01-01T00:00:00Z").unwrap(), 0);

        let leap = "2024-02-29T23:59:59Z";
        let secs = parse_rfc3339_unix_secs(leap).unwrap();
        assert_eq!(format_unix_rfc3339(secs), leap);

        let nov2026 = "2026-11-16T18:30:05Z";
        let secs2 = parse_rfc3339_unix_secs(nov2026).unwrap();
        assert_eq!(format_unix_rfc3339(secs2), nov2026);
        assert_eq!(
            parse_rfc3339_unix_secs("2026-11-16T18:30:05.123456+00:00").unwrap(),
            secs2
        );
    }

    #[test]
    fn rejects_invalid_or_non_leap_dates() {
        assert!(parse_rfc3339_unix_secs("2023-02-29T00:00:00Z").is_err());
        assert!(parse_rfc3339_unix_secs("2026-11-16T18:30:05-05:00").is_err());
        assert!(parse_rfc3339_unix_secs("not-a-timestamp").is_err());
    }

    #[test]
    fn fixed_clock_advances_deterministically() {
        let clock = FixedClock::new(1_700_000_000);
        assert_eq!(clock.now_unix_secs(), 1_700_000_000);
        assert_eq!(clock.advance(42), 1_700_000_042);
        clock.set(0);
        assert_eq!(clock.now_rfc3339(), "1970-01-01T00:00:00Z");
    }
}
