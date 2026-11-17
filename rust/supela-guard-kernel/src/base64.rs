const ALPHABET: &[u8; 64] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Base64Error {
    pub message: String,
}

impl std::fmt::Display for Base64Error {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "Base64Error: {}", self.message)
    }
}

impl std::error::Error for Base64Error {}

pub fn encode(input: &[u8]) -> String {
    if input.is_empty() {
        return String::new();
    }
    let mut out = String::with_capacity(input.len().div_ceil(3) * 4);
    for chunk in input.chunks(3) {
        let b0 = chunk[0];
        let b1 = if chunk.len() > 1 { chunk[1] } else { 0 };
        let b2 = if chunk.len() > 2 { chunk[2] } else { 0 };

        out.push(ALPHABET[(b0 >> 2) as usize] as char);
        out.push(ALPHABET[(((b0 & 0x03) << 4) | (b1 >> 4)) as usize] as char);
        if chunk.len() > 1 {
            out.push(ALPHABET[(((b1 & 0x0f) << 2) | (b2 >> 6)) as usize] as char);
        } else {
            out.push('=');
        }
        if chunk.len() > 2 {
            out.push(ALPHABET[(b2 & 0x3f) as usize] as char);
        } else {
            out.push('=');
        }
    }
    out
}

/// Decodes strict canonical RFC 4648 Base64 (rejects whitespace, bad padding,
/// invalid characters, and non-zero unused pad bits).
pub fn decode(input: &str) -> Result<Vec<u8>, Base64Error> {
    let bytes = input.as_bytes();
    if bytes.is_empty() {
        return Ok(Vec::new());
    }
    if !bytes.len().is_multiple_of(4) {
        return Err(Base64Error {
            message: "longueur Base64 non multiple de 4".to_string(),
        });
    }

    let padding = if bytes.ends_with(b"==") {
        2usize
    } else if bytes.ends_with(b"=") {
        1usize
    } else {
        0usize
    };

    let total_quads = bytes.len() / 4;
    let mut out = Vec::with_capacity(total_quads * 3 - padding);

    for (q_idx, quad) in bytes.as_chunks::<4>().0.iter().enumerate() {
        let is_last = q_idx + 1 == total_quads;

        let c0 = decode_sextet(quad[0])?;
        let c1 = decode_sextet(quad[1])?;

        match (quad[2], quad[3]) {
            (b'=', b'=') => {
                if !is_last {
                    return Err(Base64Error {
                        message: "padding Base64 avant le dernier bloc".to_string(),
                    });
                }
                if (c1 & 0x0f) != 0 {
                    return Err(Base64Error {
                        message: "bits de remplissage non nuls (forme non canonique)".to_string(),
                    });
                }
                out.push((c0 << 2) | (c1 >> 4));
            }
            (_, b'=') => {
                if !is_last {
                    return Err(Base64Error {
                        message: "padding Base64 avant le dernier bloc".to_string(),
                    });
                }
                let c2 = decode_sextet(quad[2])?;
                if (c2 & 0x03) != 0 {
                    return Err(Base64Error {
                        message: "bits de remplissage non nuls (forme non canonique)".to_string(),
                    });
                }
                out.push((c0 << 2) | (c1 >> 4));
                out.push((c1 << 4) | (c2 >> 2));
            }
            (b'=', _) => {
                return Err(Base64Error {
                    message: "padding Base64 '=' mal place avant le 4e caractere".to_string(),
                });
            }
            (raw2, raw3) => {
                let c2 = decode_sextet(raw2)?;
                let c3 = decode_sextet(raw3)?;
                out.push((c0 << 2) | (c1 >> 4));
                out.push((c1 << 4) | (c2 >> 2));
                out.push((c2 << 6) | c3);
            }
        }
    }

    Ok(out)
}

fn decode_sextet(byte: u8) -> Result<u8, Base64Error> {
    match byte {
        b'A'..=b'Z' => Ok(byte - b'A'),
        b'a'..=b'z' => Ok(byte - b'a' + 26),
        b'0'..=b'9' => Ok(byte - b'0' + 52),
        b'+' => Ok(62),
        b'/' => Ok(63),
        b'=' => Err(Base64Error {
            message: "padding '=' inattendu dans les deux premiers caracteres".to_string(),
        }),
        _ => Err(Base64Error {
            message: format!("caractere Base64 invalide : 0x{byte:02x}"),
        }),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rfc4648_vectors() {
        let cases = [
            ("", ""),
            ("f", "Zg=="),
            ("fo", "Zm8="),
            ("foo", "Zm9v"),
            ("foob", "Zm9vYg=="),
            ("fooba", "Zm9vYmE="),
            ("foobar", "Zm9vYmFy"),
        ];
        for (plain, b64) in cases {
            assert_eq!(encode(plain.as_bytes()), b64);
            assert_eq!(decode(b64).unwrap(), plain.as_bytes());
        }
    }

    #[test]
    fn rejects_non_canonical_and_malformed_inputs() {
        assert!(decode("Zh==").is_err()); // low bits of 'h' (33 = 0x21) != 0
        assert!(decode("Zm9=").is_err()); // low bits of '9' (61) != 0
        assert!(decode("Zm==".repeat(2).as_str()).is_err());
        assert!(decode("A===").is_err());
        assert!(decode("A=AA").is_err());
        assert!(decode("abc").is_err());
        assert!(decode("ab c").is_err());
    }
}
