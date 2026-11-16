.POSIX:
.PHONY: test lint typecheck a12 vr doctor vault rust-lint rust-test sign verify attest clean all

PYTHON := $(shell if [ -x .venv/bin/python ]; then echo .venv/bin/python; else echo python3; fi)
PYTEST := $(shell if [ -x .venv/bin/pytest ]; then echo .venv/bin/pytest; else echo pytest; fi)
OPA    := $(shell if [ -x .venv/bin/opa ]; then echo .venv/bin/opa; else command -v opa 2>/dev/null; fi)
COSIGN := $(shell if [ -x .venv/bin/cosign ]; then echo .venv/bin/cosign; else command -v cosign 2>/dev/null; fi)
RUFF   := $(shell if [ -x .venv/bin/ruff ]; then echo .venv/bin/ruff; else command -v ruff 2>/dev/null; fi)
MYPY   := $(shell if [ -x .venv/bin/mypy ]; then echo .venv/bin/mypy; else command -v mypy 2>/dev/null; fi)
CARGO  := $(shell command -v cargo 2>/dev/null)

REPORT := reports/TEST-4D-ESC-01.report.json
VAULT  := .omega_vault

test:
	$(PYTHON) docs/constitution/HARNAIS_TEST_ESCALADE_4D.py --out $(REPORT)
	$(PYTEST) -v
	@if [ -n "$(OPA)" ]; then \
		out=$$($(OPA) fmt --diff policies/ tests/rego/); \
		test -z "$$out" || { echo "$$out"; exit 1; }; \
		$(OPA) check --strict policies/ tests/rego/; \
		$(OPA) test policies/ tests/rego/ -v --explain=fails; \
	else \
		echo "[!] opa absent du PATH - verrou Rego non execute"; exit 1; \
	fi

lint:
	$(RUFF) check src/ tests/ scripts/

typecheck:
	$(MYPY) src/ scripts/verify_a12.py scripts/build_encyclopedie.py scripts/vr_compliance_check.py

a12:
	$(PYTHON) scripts/verify_a12.py

vr:
	$(PYTHON) scripts/vr_compliance_check.py

doctor:
	PYTHONPATH=src $(PYTHON) -m omega_zero.network_bus doctor

vault:
	PYTHONPATH=src $(PYTHON) -c "import hashlib, pathlib; from omega_zero import WormVault; p=pathlib.Path('docs/constitution/PLAN-4D-ΩZERO-ESC-01.json'); h=hashlib.sha256(p.read_bytes()).hexdigest(); v=WormVault(pathlib.Path('$(VAULT)')); r1=v.init_idempotent(h); r2=v.init_idempotent(h); assert r1.manifest_sha256==r2.manifest_sha256; assert r2.ledger_lines==r1.ledger_lines+1; assert r2.chain_valid; print('VAULT_IDEMPOTENT_OK', r2.manifest_sha256, r2.ledger_lines)"

rust-lint:
	@if [ -n "$(CARGO)" ]; then \
		cd rust/supela-guard-kernel && $(CARGO) fmt --check && $(CARGO) clippy --all-targets --all-features -- -D warnings; \
	else \
		echo "[!] cargo absent du PATH - lint Rust non execute"; exit 1; \
	fi

rust-test:
	@if [ -n "$(CARGO)" ]; then \
		cd rust/supela-guard-kernel && $(CARGO) test --locked --all-targets; \
	else \
		echo "[!] cargo absent du PATH - tests Rust non executes"; exit 1; \
	fi

sign:
	@if [ -z "$(COSIGN)" ]; then echo "[!] cosign absent - signature NON executee"; exit 1; fi
	COSIGN_PASSWORD=omega-local-test $(COSIGN) sign-blob --key cosign.key --yes --bundle $(REPORT).bundle $(REPORT)

verify:
	@if [ -z "$(COSIGN)" ]; then echo "[!] cosign absent - verification NON executee"; exit 1; fi
	$(COSIGN) verify-blob --key cosign.pub --bundle $(REPORT).bundle $(REPORT)

attest:
	@command -v tpm2_quote >/dev/null 2>&1 || { echo "[i] tpm2_quote absent : ancrage silicium DECLARATIF sur cette machine."; exit 1; }
	tpm2_quote -c primary.ctx -l sha256:15,16,22 -m quote.msg -s quote.sig -p pcr.bin -g sha256

clean:
	rm -f $(REPORT).bundle quote.msg quote.sig pcr.bin
	rm -rf $(VAULT)

all: lint typecheck a12 vr test vault rust-lint rust-test
