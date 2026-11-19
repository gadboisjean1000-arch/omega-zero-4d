#!/usr/bin/env python3
"""Vérificateur déterministe VR Structura Supela (VR-01..VR-20) pour omega-zero-4d."""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from omega_zero.vr_compliance import verify_vr_compliance


def main() -> int:
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
    result = verify_vr_compliance(ROOT_DIR)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
