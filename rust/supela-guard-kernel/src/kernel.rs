use std::collections::{BTreeMap, BTreeSet};

use crate::json::JsonValue;
use crate::sha256::sha256_hex;

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum GenerationStage {
    G0,
    G1,
    G2,
    G3,
    G4,
    G5,
}

impl GenerationStage {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::G0 => "G0",
            Self::G1 => "G1",
            Self::G2 => "G2",
            Self::G3 => "G3",
            Self::G4 => "G4",
            Self::G5 => "G5",
        }
    }

    pub fn parse(s: &str) -> Result<Self, KernelError> {
        match s {
            "G0" => Ok(Self::G0),
            "G1" => Ok(Self::G1),
            "G2" => Ok(Self::G2),
            "G3" => Ok(Self::G3),
            "G4" => Ok(Self::G4),
            "G5" => Ok(Self::G5),
            _ => Err(KernelError::InvalidInput(format!(
                "generation inconnue : {s}"
            ))),
        }
    }

    pub fn is_transition_allowed(from: Self, to: Self) -> bool {
        matches!(
            (from, to),
            (Self::G0, Self::G1)
                | (Self::G1, Self::G2)
                | (Self::G2, Self::G3)
                | (Self::G3, Self::G4)
                | (Self::G4, Self::G5)
                | (Self::G4, Self::G1)
                | (Self::G4, Self::G2)
                | (Self::G2, Self::G4)
        )
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CompressionLevel {
    C0,
    C1,
    C2,
}

impl CompressionLevel {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::C0 => "C0",
            Self::C1 => "C1",
            Self::C2 => "C2",
        }
    }

    pub fn parse(s: &str) -> Result<Self, KernelError> {
        match s {
            "C0" => Ok(Self::C0),
            "C1" => Ok(Self::C1),
            "C2" => Ok(Self::C2),
            _ => Err(KernelError::InvalidInput(format!(
                "niveau de compression inconnu : {s}"
            ))),
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AccessibilityMode {
    Direct,
    Referential,
    Reconstructible,
}

impl AccessibilityMode {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Direct => "DIRECT",
            Self::Referential => "REFERENTIAL",
            Self::Reconstructible => "RECONSTRUCTIBLE",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum KernelObjectStatus {
    Hypothese,
    Fait,
    Contradiction,
    Refutation,
    Inconnu,
    NonReclame,
    Reclame,
}

impl KernelObjectStatus {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Hypothese => "HYPOTHESE",
            Self::Fait => "FAIT",
            Self::Contradiction => "CONTRADICTION",
            Self::Refutation => "REFUTATION",
            Self::Inconnu => "INCONNU",
            Self::NonReclame => "NON-RÉCLAMÉ",
            Self::Reclame => "RÉCLAMÉ",
        }
    }

    pub fn parse(s: &str) -> Result<Self, KernelError> {
        match s {
            "HYPOTHESE" => Ok(Self::Hypothese),
            "FAIT" => Ok(Self::Fait),
            "CONTRADICTION" => Ok(Self::Contradiction),
            "REFUTATION" => Ok(Self::Refutation),
            "INCONNU" => Ok(Self::Inconnu),
            "NON-RÉCLAMÉ" | "NON-RECLAME" => Ok(Self::NonReclame),
            "RÉCLAMÉ" | "RECLAME" => Ok(Self::Reclame),
            _ => Err(KernelError::InvalidInput(format!(
                "statut d'objet inconnu : {s}"
            ))),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum KernelError {
    InvalidInput(String),
    ForbiddenGenerationFlow {
        from: &'static str,
        to: &'static str,
    },
    SilentAuthorityInheritance,
    C2CannotClaimFullCopy,
    HypothesisToFactWithoutProof,
    ContradictionErased(String),
    ProofErased(String),
    Gf1NonFiniteReward,
    AuthorityExceedsProof(String),
}

impl KernelError {
    pub fn code(&self) -> &'static str {
        match self {
            Self::InvalidInput(_) => "INVALID_KERNEL_INPUT",
            Self::ForbiddenGenerationFlow { .. } => "SUP_ICI_01_FORBIDDEN_TRANSITION",
            Self::SilentAuthorityInheritance => "SUP_ICI_01_SILENT_AUTHORITY_INHERITANCE",
            Self::C2CannotClaimFullCopy => "COMPRESSION_FAIL_C2_FULL_COPY",
            Self::HypothesisToFactWithoutProof => "SUP_ICI_01_HYPOTHESIS_TO_FACT_WITHOUT_PROOF",
            Self::ContradictionErased(_) => "SUP_ICI_01_CONTRADICTION_ERASED",
            Self::ProofErased(_) => "SUP_ICI_01_PROOF_ERASED",
            Self::Gf1NonFiniteReward => "GF1_NON_FINITE_REWARD",
            Self::AuthorityExceedsProof(_) => "AUTHORITY_EXCEEDS_PROOF",
        }
    }
}

impl std::fmt::Display for KernelError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::InvalidInput(msg) => write!(f, "entree invalide : {msg}"),
            Self::ForbiddenGenerationFlow { from, to } => {
                write!(f, "transition de generation interdite : {from} -> {to}")
            }
            Self::SilentAuthorityInheritance => write!(
                f,
                "interdit SUP-ICI-01 : heritage silencieux de l'autorite normative"
            ),
            Self::C2CannotClaimFullCopy => write!(
                f,
                "COMPRESSION-FAIL : C2 ne doit jamais etre presente comme copie complete"
            ),
            Self::HypothesisToFactWithoutProof => write!(
                f,
                "interdit SUP-ICI-01 : impossible de promouvoir HYPOTHESE -> FAIT sans nouvelle preuve"
            ),
            Self::ContradictionErased(id) => {
                write!(f, "interdit SUP-ICI-01 : contradiction active effacee ({id})")
            }
            Self::ProofErased(id) => {
                write!(f, "interdit SUP-ICI-01 : reference de preuve perdue ({id})")
            }
            Self::Gf1NonFiniteReward => write!(
                f,
                "violation GF1 : recompense non finie (NaN/Inf) rejetee immediatement"
            ),
            Self::AuthorityExceedsProof(msg) => {
                write!(f, "barriere fail-closed (Autorite <= Preuve) : {msg}")
            }
        }
    }
}

impl std::error::Error for KernelError {}

#[derive(Debug, Clone)]
pub struct TransitionRequest {
    pub object_id: String,
    pub object_type: String,
    pub author: String,
    pub origin: String,
    pub scope: String,
    pub from_generation: GenerationStage,
    pub to_generation: GenerationStage,
    pub from_status: KernelObjectStatus,
    pub to_status: KernelObjectStatus,
    pub compression_level: CompressionLevel,
    pub previous_hash: String,
    pub reason: String,
    pub transformation: String,
    pub existing_proofs: Vec<String>,
    pub output_proofs: Vec<String>,
    pub existing_contradictions: Vec<String>,
    pub output_contradictions: Vec<String>,
    pub dependencies: Vec<String>,
    pub reopening_conditions: Vec<String>,
    pub location: String,
    pub claim_full_copy: bool,
    pub inherit_authority_silently: bool,
    pub human_ratified: bool,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TransitionDecision {
    pub object_id: String,
    pub from_generation: &'static str,
    pub to_generation: &'static str,
    pub previous_hash: String,
    pub residue_hash: String,
    pub compression_level: &'static str,
    pub preserved_fields: Vec<&'static str>,
    pub removed_content: &'static str,
    pub reason: String,
    pub reversible: bool,
    pub authority: &'static str,
    pub accessibility_mode: &'static str,
    pub semantic_loss_passed: bool,
}

impl TransitionDecision {
    pub fn to_json(&self) -> JsonValue {
        let mut map = BTreeMap::new();
        map.insert(
            "object_id".into(),
            JsonValue::String(self.object_id.clone()),
        );
        map.insert(
            "from_generation".into(),
            JsonValue::String(self.from_generation.into()),
        );
        map.insert(
            "to_generation".into(),
            JsonValue::String(self.to_generation.into()),
        );
        map.insert(
            "previous_hash".into(),
            JsonValue::String(self.previous_hash.clone()),
        );
        map.insert(
            "residue_hash".into(),
            JsonValue::String(self.residue_hash.clone()),
        );
        map.insert(
            "compression_level".into(),
            JsonValue::String(self.compression_level.into()),
        );
        map.insert(
            "preserved_fields".into(),
            JsonValue::Array(
                self.preserved_fields
                    .iter()
                    .map(|s| JsonValue::String((*s).into()))
                    .collect(),
            ),
        );
        map.insert(
            "removed_content".into(),
            JsonValue::String(self.removed_content.into()),
        );
        map.insert("reason".into(), JsonValue::String(self.reason.clone()));
        map.insert("reversible".into(), JsonValue::Bool(self.reversible));
        map.insert("authority".into(), JsonValue::String(self.authority.into()));
        map.insert(
            "accessibility_mode".into(),
            JsonValue::String(self.accessibility_mode.into()),
        );
        map.insert(
            "semantic_loss_passed".into(),
            JsonValue::Bool(self.semantic_loss_passed),
        );
        JsonValue::Object(map)
    }
}

pub fn evaluate_transition(req: &TransitionRequest) -> Result<TransitionDecision, KernelError> {
    if req.object_id.trim().len() < 3 {
        return Err(KernelError::InvalidInput(
            "object_id exige au moins 3 caracteres".into(),
        ));
    }
    if req.author.trim().is_empty() || req.origin.trim().is_empty() || req.scope.trim().is_empty() {
        return Err(KernelError::InvalidInput(
            "author, origin et scope doivent etre non vides (SUP-ICI-01)".into(),
        ));
    }
    if req.reason.trim().len() < 3 || req.transformation.trim().is_empty() {
        return Err(KernelError::InvalidInput(
            "reason (>= 3 car.) et transformation obligatoires".into(),
        ));
    }
    if req.reopening_conditions.is_empty() || req.location.trim().is_empty() {
        return Err(KernelError::InvalidInput(
            "reopening_conditions et location obligatoires pour SUP-ICI-01".into(),
        ));
    }
    if !is_sha256_hex(&req.previous_hash) {
        return Err(KernelError::InvalidInput(
            "previous_hash doit etre un digest SHA-256 hexadecimal minuscule (64 car.)".into(),
        ));
    }
    if !GenerationStage::is_transition_allowed(req.from_generation, req.to_generation) {
        return Err(KernelError::ForbiddenGenerationFlow {
            from: req.from_generation.as_str(),
            to: req.to_generation.as_str(),
        });
    }
    if req.inherit_authority_silently {
        return Err(KernelError::SilentAuthorityInheritance);
    }
    if req.compression_level == CompressionLevel::C2 && req.claim_full_copy {
        return Err(KernelError::C2CannotClaimFullCopy);
    }

    let before_proofs: BTreeSet<&str> = req.existing_proofs.iter().map(String::as_str).collect();
    let after_proofs: BTreeSet<&str> = req.output_proofs.iter().map(String::as_str).collect();
    if let Some(missing) = before_proofs.difference(&after_proofs).next() {
        return Err(KernelError::ProofErased((*missing).to_string()));
    }

    let before_contra: BTreeSet<&str> = req
        .existing_contradictions
        .iter()
        .map(String::as_str)
        .collect();
    let after_contra: BTreeSet<&str> = req
        .output_contradictions
        .iter()
        .map(String::as_str)
        .collect();
    if let Some(missing) = before_contra.difference(&after_contra).next() {
        return Err(KernelError::ContradictionErased((*missing).to_string()));
    }

    if req.from_status == KernelObjectStatus::Hypothese
        && req.to_status == KernelObjectStatus::Fait
        && after_proofs.len() <= before_proofs.len()
    {
        return Err(KernelError::HypothesisToFactWithoutProof);
    }

    let (reversible, removed_content, accessibility_mode) = match req.compression_level {
        CompressionLevel::C0 => (true, "none", AccessibilityMode::Direct),
        CompressionLevel::C1 => (
            true,
            "none_reversible_c1",
            AccessibilityMode::Reconstructible,
        ),
        CompressionLevel::C2 => (false, "declared", AccessibilityMode::Referential),
    };

    let mut residue_map = BTreeMap::new();
    let mut id_map = BTreeMap::new();
    id_map.insert("id".into(), JsonValue::String(req.object_id.clone()));
    id_map.insert("type".into(), JsonValue::String(req.object_type.clone()));

    let mut prov_map = BTreeMap::new();
    prov_map.insert("author".into(), JsonValue::String(req.author.clone()));
    prov_map.insert("origin".into(), JsonValue::String(req.origin.clone()));

    residue_map.insert("identity".into(), JsonValue::Object(id_map));
    residue_map.insert("provenance".into(), JsonValue::Object(prov_map));
    residue_map.insert(
        "original_hash".into(),
        JsonValue::String(req.previous_hash.clone()),
    );
    residue_map.insert(
        "status".into(),
        JsonValue::String(req.to_status.as_str().into()),
    );
    residue_map.insert("scope".into(), JsonValue::String(req.scope.clone()));
    residue_map.insert(
        "dependencies".into(),
        JsonValue::Array(
            req.dependencies
                .iter()
                .map(|s| JsonValue::String(s.clone()))
                .collect(),
        ),
    );
    residue_map.insert(
        "transformation".into(),
        JsonValue::String(req.transformation.clone()),
    );
    residue_map.insert("reason".into(), JsonValue::String(req.reason.clone()));
    residue_map.insert(
        "reopening_conditions".into(),
        JsonValue::Array(
            req.reopening_conditions
                .iter()
                .map(|s| JsonValue::String(s.clone()))
                .collect(),
        ),
    );
    residue_map.insert("location".into(), JsonValue::String(req.location.clone()));

    let residue_hash = sha256_hex(
        JsonValue::Object(residue_map)
            .to_canonical_string()
            .as_bytes(),
    );
    let authority = if req.human_ratified {
        "RATIFIED_HUMAN"
    } else {
        "PENDING_HUMAN_RATIFICATION"
    };

    Ok(TransitionDecision {
        object_id: req.object_id.clone(),
        from_generation: req.from_generation.as_str(),
        to_generation: req.to_generation.as_str(),
        previous_hash: req.previous_hash.clone(),
        residue_hash,
        compression_level: req.compression_level.as_str(),
        preserved_fields: vec![
            "identity",
            "provenance",
            "status",
            "scope",
            "dependencies",
            "reopening_conditions",
        ],
        removed_content,
        reason: req.reason.clone(),
        reversible,
        authority,
        accessibility_mode: accessibility_mode.as_str(),
        semantic_loss_passed: true,
    })
}

#[derive(Debug, Clone)]
pub struct CandidatePolicyRequest {
    pub candidate_id: String,
    pub reward: f64,
    pub r_max: f64,
    pub proof_verified: bool,
    pub requested_status: String,
    pub requested_authority_level: i64,
    pub evidence_level: i64,
    pub human_ratified: bool,
}

#[derive(Debug, Clone, PartialEq)]
pub struct CandidatePolicyOutcome {
    pub candidate_id: String,
    pub bounded_reward: f64,
    pub gf1_clamped: bool,
    pub resulting_status: &'static str,
    pub resulting_authority: &'static str,
    pub promotion_verdict: &'static str,
    pub human_review_required: bool,
}

impl CandidatePolicyOutcome {
    pub fn to_json(&self) -> JsonValue {
        let mut map = BTreeMap::new();
        map.insert(
            "candidate_id".into(),
            JsonValue::String(self.candidate_id.clone()),
        );
        map.insert(
            "bounded_reward".into(),
            JsonValue::Float(self.bounded_reward),
        );
        map.insert("gf1_clamped".into(), JsonValue::Bool(self.gf1_clamped));
        map.insert(
            "resulting_status".into(),
            JsonValue::String(self.resulting_status.into()),
        );
        map.insert(
            "resulting_authority".into(),
            JsonValue::String(self.resulting_authority.into()),
        );
        map.insert(
            "promotion_verdict".into(),
            JsonValue::String(self.promotion_verdict.into()),
        );
        map.insert(
            "human_review_required".into(),
            JsonValue::Bool(self.human_review_required),
        );
        JsonValue::Object(map)
    }
}

pub fn evaluate_candidate_policy(
    req: &CandidatePolicyRequest,
) -> Result<CandidatePolicyOutcome, KernelError> {
    if req.candidate_id.trim().is_empty() {
        return Err(KernelError::InvalidInput(
            "candidate_id ne peut pas etre vide".into(),
        ));
    }
    if !req.reward.is_finite() || !req.r_max.is_finite() || req.r_max <= 0.0 {
        return Err(KernelError::Gf1NonFiniteReward);
    }

    if req.requested_authority_level > req.evidence_level {
        return Err(KernelError::AuthorityExceedsProof(format!(
            "authority_level ({}) > evidence_level ({})",
            req.requested_authority_level, req.evidence_level
        )));
    }

    if matches!(
        req.requested_status.as_str(),
        "ETABLI" | "ÉTABLI" | "FAIT" | "RESOLU" | "RÉSOLU" | "VERITE"
    ) && (!req.proof_verified || !req.human_ratified)
    {
        return Err(KernelError::AuthorityExceedsProof(
            "Score != Preuve != Verite : promotion vers ETABLI/FAIT interdite sans preuve et ratification humaine".into(),
        ));
    }

    let gf1_clamped = req.reward > req.r_max || req.reward < -req.r_max;
    let bounded_reward = req.reward.clamp(-req.r_max, req.r_max);

    Ok(CandidatePolicyOutcome {
        candidate_id: req.candidate_id.clone(),
        bounded_reward,
        gf1_clamped,
        resulting_status: if gf1_clamped {
            "REJETE_GF1_ABERRANT"
        } else {
            "CANDIDAT"
        },
        resulting_authority: "AUCUNE",
        promotion_verdict: if gf1_clamped {
            "BLOQUE_GF1"
        } else {
            "ADMISSIBLE_A_REVUE_HUMAINE"
        },
        human_review_required: true,
    })
}

pub fn is_sha256_hex(s: &str) -> bool {
    s.len() == 64 && s.bytes().all(|b| matches!(b, b'0'..=b'9' | b'a'..=b'f'))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sample_req() -> TransitionRequest {
        TransitionRequest {
            object_id: "OBJ-RUST-01".into(),
            object_type: "grpo_artifact".into(),
            author: "gadbois".into(),
            origin: "rust-unit-test".into(),
            scope: "LOCAL".into(),
            from_generation: GenerationStage::G0,
            to_generation: GenerationStage::G1,
            from_status: KernelObjectStatus::Hypothese,
            to_status: KernelObjectStatus::Hypothese,
            compression_level: CompressionLevel::C1,
            previous_hash: "a".repeat(64),
            reason: "Transition test G0->G1".into(),
            transformation: "c1_lossless".into(),
            existing_proofs: vec!["PRF-1".into()],
            output_proofs: vec!["PRF-1".into()],
            existing_contradictions: vec!["CONTR-T11".into()],
            output_contradictions: vec!["CONTR-T11".into()],
            dependencies: vec!["SUP-ICI-01".into()],
            reopening_conditions: vec!["Nouvelle preuve".into()],
            location: "cas://sha256/test".into(),
            claim_full_copy: false,
            inherit_authority_silently: false,
            human_ratified: false,
        }
    }

    #[test]
    fn rejects_sup_ici_01_violations() {
        let mut r1 = sample_req();
        r1.to_status = KernelObjectStatus::Fait;
        assert_eq!(
            evaluate_transition(&r1).unwrap_err(),
            KernelError::HypothesisToFactWithoutProof
        );

        let mut r2 = sample_req();
        r2.output_contradictions.clear();
        assert!(matches!(
            evaluate_transition(&r2).unwrap_err(),
            KernelError::ContradictionErased(_)
        ));

        let mut r3 = sample_req();
        r3.inherit_authority_silently = true;
        assert_eq!(
            evaluate_transition(&r3).unwrap_err(),
            KernelError::SilentAuthorityInheritance
        );

        let mut r4 = sample_req();
        r4.compression_level = CompressionLevel::C2;
        r4.claim_full_copy = true;
        assert_eq!(
            evaluate_transition(&r4).unwrap_err(),
            KernelError::C2CannotClaimFullCopy
        );
    }

    #[test]
    fn enforces_score_not_proof_not_truth() {
        let bad = CandidatePolicyRequest {
            candidate_id: "C-SCORE-ONLY".into(),
            reward: 0.99,
            r_max: 1.0,
            proof_verified: false,
            requested_status: "ETABLI".into(),
            requested_authority_level: 0,
            evidence_level: 0,
            human_ratified: false,
        };
        assert!(matches!(
            evaluate_candidate_policy(&bad).unwrap_err(),
            KernelError::AuthorityExceedsProof(_)
        ));
    }
}
