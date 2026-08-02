#!/usr/bin/env bash
# PIPELINE CI/CD — VALIDATION DES GOVERNANCE RULES (ANNEXES A/B/C/D)
# SCDH v1.0 — PV-CVEA-2026-001 — Jean-François Gadbois (Jef)
set -euo pipefail

GREEN='\033[0;32m'; RED='\033[0;31m'; BLUE='\033[0;34m'; NC='\033[0m'
echo -e "${BLUE}==== PROTOCOLE TEST INVARIANTS SCDH v1.0 ====${NC}"

command -v python3 &>/dev/null || { echo -e "${RED}[ERROR] Python3 requis.${NC}"; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "--> Tests unitaires (Python)..."

if python3 "${SCRIPT_DIR}/test_governance_rules.py" -v; then
    echo -e "${GREEN}[PASSED] 17/17 invariants validés — déploiement autorisé.${NC}"
    exit 0
else
    echo -e "${RED}[FAILED] Invariants violés — déploiement bloqué.${NC}"
    exit 1
fi
