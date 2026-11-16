#!/usr/bin/env python3
"""Point d'entrée exécutable du harnais TEST-4D-ESC-01 (PLAN-4D-ΩZERO-ESC-01)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from omega_zero.harness import evaluate_escalation_protocol  # noqa: E402
from omega_zero.scenarios import run_second_domain_hydrology_example  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Exécute le harnais TEST-4D-ESC-01.")
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT_DIR / "reports" / "TEST-4D-ESC-01.report.json",
        help="Chemin du rapport JSON d'exécution à écrire.",
    )
    args = parser.parse_args()

    protocol_path = ROOT_DIR / "docs" / "constitution" / "PLAN-4D-ΩZERO-ESC-01.json"
    schema_dir = ROOT_DIR / "schemas"

    report = evaluate_escalation_protocol(protocol_path, schema_dir)
    second_example = run_second_domain_hydrology_example()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"VERDICT={report['verdict']} PROMOTION={report['promotion']} CONDITIONS={len(report['condition_results'])}/10")
    print(f"SECOND_EXEMPLE={second_example['example_id']} PI0_IDEMPOTENT={second_example['pi0_idempotent']} CONFLICT_PRESERVED={second_example['conflict_preserved']}")
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
