use std::collections::BTreeMap;
use std::fmt::Write as _;

const MAX_JSON_DEPTH: usize = 64;

#[derive(Debug, Clone, PartialEq)]
pub enum JsonValue {
    Null,
    Bool(bool),
    Integer(i64),
    Float(f64),
    String(String),
    Array(Vec<JsonValue>),
    Object(BTreeMap<String, JsonValue>),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct JsonError {
    pub message: String,
    pub offset: usize,
}

impl std::fmt::Display for JsonError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "JsonError at byte {}: {}", self.offset, self.message)
    }
}

impl std::error::Error for JsonError {}

impl JsonValue {
    pub fn as_object(&self) -> Option<&BTreeMap<String, JsonValue>> {
        match self {
            Self::Object(map) => Some(map),
            _ => None,
        }
    }

    pub fn as_array(&self) -> Option<&[JsonValue]> {
        match self {
            Self::Array(arr) => Some(arr),
            _ => None,
        }
    }

    pub fn as_str(&self) -> Option<&str> {
        match self {
            Self::String(s) => Some(s.as_str()),
            _ => None,
        }
    }

    pub fn as_bool(&self) -> Option<bool> {
        match self {
            Self::Bool(b) => Some(*b),
            _ => None,
        }
    }

    pub fn as_i64(&self) -> Option<i64> {
        match self {
            Self::Integer(n) => Some(*n),
            _ => None,
        }
    }

    pub fn as_u64(&self) -> Option<u64> {
        match self {
            Self::Integer(n) if *n >= 0 => Some(*n as u64),
            _ => None,
        }
    }

    pub fn as_f64(&self) -> Option<f64> {
        match self {
            Self::Integer(n) => Some(*n as f64),
            Self::Float(v) => Some(*v),
            _ => None,
        }
    }

    pub fn get(&self, key: &str) -> Option<&JsonValue> {
        self.as_object().and_then(|map| map.get(key))
    }

    pub fn to_canonical_string(&self) -> String {
        let mut out = String::new();
        self.write_canonical(&mut out);
        out
    }

    fn write_canonical(&self, out: &mut String) {
        match self {
            Self::Null => out.push_str("null"),
            Self::Bool(true) => out.push_str("true"),
            Self::Bool(false) => out.push_str("false"),
            Self::Integer(n) => {
                let _ = write!(out, "{n}");
            }
            Self::Float(v) => {
                if v.is_finite() {
                    if *v == 0.0 {
                        out.push('0');
                    } else {
                        let _ = write!(out, "{v}");
                    }
                } else {
                    out.push_str("null");
                }
            }
            Self::String(s) => write_escaped_string(s, out),
            Self::Array(items) => {
                out.push('[');
                for (i, item) in items.iter().enumerate() {
                    if i > 0 {
                        out.push(',');
                    }
                    item.write_canonical(out);
                }
                out.push(']');
            }
            Self::Object(map) => {
                out.push('{');
                for (i, (k, v)) in map.iter().enumerate() {
                    if i > 0 {
                        out.push(',');
                    }
                    write_escaped_string(k, out);
                    out.push(':');
                    v.write_canonical(out);
                }
                out.push('}');
            }
        }
    }
}

fn write_escaped_string(s: &str, out: &mut String) {
    out.push('"');
    for ch in s.chars() {
        match ch {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\u{08}' => out.push_str("\\b"),
            '\u{0C}' => out.push_str("\\f"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            c if (c as u32) < 0x20 => {
                let _ = write!(out, "\\u{:04x}", c as u32);
            }
            c => out.push(c),
        }
    }
    out.push('"');
}

pub fn parse_json(input: &str) -> Result<JsonValue, JsonError> {
    let mut parser = Parser {
        bytes: input.as_bytes(),
        pos: 0,
    };
    parser.skip_ws();
    let value = parser.parse_value(0)?;
    parser.skip_ws();
    if parser.pos < parser.bytes.len() {
        return Err(parser.err("caracteres excedentaires apres la racine JSON"));
    }
    Ok(value)
}

struct Parser<'a> {
    bytes: &'a [u8],
    pos: usize,
}

impl<'a> Parser<'a> {
    fn err(&self, msg: &str) -> JsonError {
        JsonError {
            message: msg.to_string(),
            offset: self.pos,
        }
    }

    fn peek(&self) -> Option<u8> {
        self.bytes.get(self.pos).copied()
    }

    fn skip_ws(&mut self) {
        while let Some(b) = self.peek() {
            if matches!(b, b' ' | b'\n' | b'\r' | b'\t') {
                self.pos += 1;
            } else {
                break;
            }
        }
    }

    fn expect(&mut self, expected: u8) -> Result<(), JsonError> {
        match self.peek() {
            Some(b) if b == expected => {
                self.pos += 1;
                Ok(())
            }
            _ => Err(self.err(&format!("attendu '{}'", expected as char))),
        }
    }

    fn parse_value(&mut self, depth: usize) -> Result<JsonValue, JsonError> {
        if depth > MAX_JSON_DEPTH {
            return Err(self.err("profondeur JSON maximale depassee"));
        }
        self.skip_ws();
        match self.peek() {
            Some(b'n') => self.parse_null(),
            Some(b't') => self.parse_true(),
            Some(b'f') => self.parse_false(),
            Some(b'"') => self.parse_string().map(JsonValue::String),
            Some(b'[') => self.parse_array(depth + 1),
            Some(b'{') => self.parse_object(depth + 1),
            Some(b'-' | b'0'..=b'9') => self.parse_number(),
            Some(_) => Err(self.err("jeton JSON inattendu")),
            None => Err(self.err("fin d'entree JSON inattendue")),
        }
    }

    fn parse_null(&mut self) -> Result<JsonValue, JsonError> {
        if self.bytes[self.pos..].starts_with(b"null") {
            self.pos += 4;
            Ok(JsonValue::Null)
        } else {
            Err(self.err("litteral null invalide"))
        }
    }

    fn parse_true(&mut self) -> Result<JsonValue, JsonError> {
        if self.bytes[self.pos..].starts_with(b"true") {
            self.pos += 4;
            Ok(JsonValue::Bool(true))
        } else {
            Err(self.err("litteral true invalide"))
        }
    }

    fn parse_false(&mut self) -> Result<JsonValue, JsonError> {
        if self.bytes[self.pos..].starts_with(b"false") {
            self.pos += 5;
            Ok(JsonValue::Bool(false))
        } else {
            Err(self.err("litteral false invalide"))
        }
    }

    fn parse_array(&mut self, depth: usize) -> Result<JsonValue, JsonError> {
        self.expect(b'[')?;
        self.skip_ws();
        let mut items = Vec::new();
        if self.peek() == Some(b']') {
            self.pos += 1;
            return Ok(JsonValue::Array(items));
        }
        loop {
            items.push(self.parse_value(depth)?);
            self.skip_ws();
            match self.peek() {
                Some(b',') => {
                    self.pos += 1;
                }
                Some(b']') => {
                    self.pos += 1;
                    return Ok(JsonValue::Array(items));
                }
                _ => return Err(self.err("attendu ',' ou ']' dans tableau JSON")),
            }
        }
    }

    fn parse_object(&mut self, depth: usize) -> Result<JsonValue, JsonError> {
        self.expect(b'{')?;
        self.skip_ws();
        let mut map = BTreeMap::new();
        if self.peek() == Some(b'}') {
            self.pos += 1;
            return Ok(JsonValue::Object(map));
        }
        loop {
            self.skip_ws();
            if self.peek() != Some(b'"') {
                return Err(self.err("cle chaine attendue dans objet JSON"));
            }
            let key = self.parse_string()?;
            self.skip_ws();
            self.expect(b':')?;
            let val = self.parse_value(depth)?;
            map.insert(key, val);
            self.skip_ws();
            match self.peek() {
                Some(b',') => {
                    self.pos += 1;
                }
                Some(b'}') => {
                    self.pos += 1;
                    return Ok(JsonValue::Object(map));
                }
                _ => return Err(self.err("attendu ',' ou '}' dans objet JSON")),
            }
        }
    }

    fn parse_string(&mut self) -> Result<String, JsonError> {
        self.expect(b'"')?;
        let mut out = String::new();
        while self.pos < self.bytes.len() {
            let b = self.bytes[self.pos];
            if b == b'"' {
                self.pos += 1;
                return Ok(out);
            }
            if b == b'\\' {
                self.pos += 1;
                let esc = self
                    .peek()
                    .ok_or_else(|| self.err("echappement inacheve"))?;
                self.pos += 1;
                match esc {
                    b'"' => out.push('"'),
                    b'\\' => out.push('\\'),
                    b'/' => out.push('/'),
                    b'b' => out.push('\u{08}'),
                    b'f' => out.push('\u{0C}'),
                    b'n' => out.push('\n'),
                    b'r' => out.push('\r'),
                    b't' => out.push('\t'),
                    b'u' => {
                        let code = self.parse_hex4()?;
                        if (0xD800..=0xDBFF).contains(&code) {
                            if !self.bytes[self.pos..].starts_with(b"\\u") {
                                return Err(self.err("paire de substitution UTF-16 orpheline"));
                            }
                            self.pos += 2;
                            let low = self.parse_hex4()?;
                            if !(0xDC00..=0xDFFF).contains(&low) {
                                return Err(self.err("substitution UTF-16 basse invalide"));
                            }
                            let combined = 0x10000
                                + (((u32::from(code) - 0xD800) << 10) | (u32::from(low) - 0xDC00));
                            let ch = char::from_u32(combined)
                                .ok_or_else(|| self.err("point de code Unicode invalide"))?;
                            out.push(ch);
                        } else if (0xDC00..=0xDFFF).contains(&code) {
                            return Err(self.err("substitution UTF-16 basse isolee"));
                        } else {
                            let ch = char::from_u32(u32::from(code))
                                .ok_or_else(|| self.err("point de code Unicode invalide"))?;
                            out.push(ch);
                        }
                    }
                    _ => return Err(self.err("sequence d'echappement invalide")),
                }
            } else if b < 0x20 {
                return Err(self.err("caractere de controle non echappe dans chaine"));
            } else if b < 0x80 {
                out.push(b as char);
                self.pos += 1;
            } else {
                let s = std::str::from_utf8(&self.bytes[self.pos..])
                    .map_err(|_| self.err("UTF-8 invalide dans chaine JSON"))?;
                let ch = s
                    .chars()
                    .next()
                    .ok_or_else(|| self.err("fin UTF-8 inattendue"))?;
                out.push(ch);
                self.pos += ch.len_utf8();
            }
        }
        Err(self.err("chaine JSON non fermee"))
    }

    fn parse_hex4(&mut self) -> Result<u16, JsonError> {
        if self.pos + 4 > self.bytes.len() {
            return Err(self.err("sequence \\uXXXX tronquee"));
        }
        let hex = std::str::from_utf8(&self.bytes[self.pos..self.pos + 4])
            .map_err(|_| self.err("\\uXXXX non ASCII"))?;
        let val =
            u16::from_str_radix(hex, 16).map_err(|_| self.err("\\uXXXX hexadecimal invalide"))?;
        self.pos += 4;
        Ok(val)
    }

    fn parse_number(&mut self) -> Result<JsonValue, JsonError> {
        let start = self.pos;
        if self.peek() == Some(b'-') {
            self.pos += 1;
        }
        match self.peek() {
            Some(b'0') => {
                self.pos += 1;
            }
            Some(b'1'..=b'9') => {
                while matches!(self.peek(), Some(b'0'..=b'9')) {
                    self.pos += 1;
                }
            }
            _ => return Err(self.err("nombre JSON invalide")),
        }

        let mut is_float = false;
        if self.peek() == Some(b'.') {
            is_float = true;
            self.pos += 1;
            if !matches!(self.peek(), Some(b'0'..=b'9')) {
                return Err(self.err("chiffre attendu apres '.' dans nombre"));
            }
            while matches!(self.peek(), Some(b'0'..=b'9')) {
                self.pos += 1;
            }
        }
        if matches!(self.peek(), Some(b'e' | b'E')) {
            is_float = true;
            self.pos += 1;
            if matches!(self.peek(), Some(b'+' | b'-')) {
                self.pos += 1;
            }
            if !matches!(self.peek(), Some(b'0'..=b'9')) {
                return Err(self.err("chiffre attendu dans exposant"));
            }
            while matches!(self.peek(), Some(b'0'..=b'9')) {
                self.pos += 1;
            }
        }

        let raw = std::str::from_utf8(&self.bytes[start..self.pos])
            .map_err(|_| self.err("nombre non UTF-8"))?;
        if !is_float {
            if let Ok(int_val) = raw.parse::<i64>() {
                return Ok(JsonValue::Integer(int_val));
            }
        }
        let float_val = raw
            .parse::<f64>()
            .map_err(|_| self.err("nombre flottant invalide"))?;
        if !float_val.is_finite() {
            return Err(self.err("nombre non fini rejete"));
        }
        Ok(JsonValue::Float(float_val))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn canonical_ordering_and_unicode_roundtrip() {
        let a = parse_json(r#"{"z": 10, "a": "hello\n\uD83D\uDE00", "b": [true, null]}"#).unwrap();
        let b = parse_json(r#"{"b":[true,null],"a":"hello\n😀","z":10}"#).unwrap();
        assert_eq!(a.to_canonical_string(), b.to_canonical_string());
        assert_eq!(a.get("a").and_then(JsonValue::as_str), Some("hello\n😀"));
        assert_eq!(a.get("z").and_then(JsonValue::as_i64), Some(10));
    }

    #[test]
    fn rejects_excessive_nesting_and_trailing_tokens() {
        let deep = "[".repeat(80) + &"]".repeat(80);
        assert!(parse_json(&deep).is_err());
        assert!(parse_json(r#"{"ok":true} extra"#).is_err());
    }
}
