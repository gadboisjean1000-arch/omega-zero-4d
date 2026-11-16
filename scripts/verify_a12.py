#!/usr/bin/env python3
"""Vérificateur de Règle A12 (anti-orphelins & cohérence bidirectionnelle) pour omega-zero-4d."""

from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT_DIR / "docs" / "constitution" / "INDEX_CONSTITUTION.md"

EXCLUDED_DIRS = {
    ".git",
    ".venv",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".hypothesis",
    ".omega_vault",
    "__pycache__",
    "dist",
    "omega_zero_4d.egg-info",
}

EXCLUDED_ROOT_FILES = {
    ".gitignore",
    "README.md",
    "pyproject.toml",
    "Makefile",
    "omega.ps1",
    "cosign.key",
    "cosign.pub",
    "docs/constitution/local_pc_inventory.json",
}


def verify_a12(root: Path = ROOT_DIR) -> tuple[bool, dict[str, list[str]]]:
    index_path = root / "docs" / "constitution" / "INDEX_CONSTITUTION.md"
    index_text = index_path.read_text(encoding="utf-8")

    # 1. Extraire tous les chemins référencés dans INDEX_CONSTITUTION.md
    referenced: set[str] = set()
    # Liens markdown relatifs à docs/constitution/
    for m in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", index_text):
        target = m.group(1).replace("%CE%A9", "Ω")
        if target.startswith("http"):
            continue
        rel = (index_path.parent / target).resolve().relative_to(root.resolve())
        referenced.add(rel.as_posix())

    # Chemins explicites en backticks depuis la racine du projet
    for m in re.finditer(r"`([A-Za-z0-9_.\-/]+)`", index_text):
        candidate = m.group(1)
        if "/" in candidate and (root / candidate).exists():
            referenced.add(candidate)

    # Le fichier INDEX_CONSTITUTION.md s'auto-référence implicitement
    referenced.add("docs/constitution/INDEX_CONSTITUTION.md")

    # 2. Lister tous les fichiers réels soumis à A12
    actual_files: set[str] = set()
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel_parts = p.relative_to(root).parts
        if any(part in EXCLUDED_DIRS or part.endswith(".egg-info") for part in rel_parts):
            continue
        if p.suffix in {".bundle", ".pyc", ".pyo"} or p.name == ".DS_Store":
            continue
        rel_posix = p.relative_to(root).as_posix()
        if rel_posix in EXCLUDED_ROOT_FILES:
            continue
        actual_files.add(rel_posix)

    orphans = sorted(actual_files - referenced)
    broken = sorted(ref for ref in referenced if not (root / ref).exists())

    # 3. Cohérence croisée JSON <-> Rego <-> Markdown
    drift: list[str] = []
    plan = json.loads((root / "docs" / "constitution" / "PLAN-4D-ΩZERO-ESC-01.json").read_text(encoding="utf-8"))
    rego = (root / "policies" / "omega_zero_invariants.rego").read_text(encoding="utf-8")
    md = (root / "docs" / "constitution" / "PLAN_4D_OMEGA_ZERO_ESC_01.md").read_text(encoding="utf-8")

    for row in plan["matrix_normative"]:
        cid = row["id"]
        pid = row["palier"]
        if cid not in rego:
            drift.append(f"Condition {cid} absente de omega_zero_invariants.rego")
        if cid not in md or pid not in md:
            drift.append(f"{cid}/{pid} absent de PLAN_4D_OMEGA_ZERO_ESC_01.md")

    ok = not orphans and not broken and not drift
    return ok, {"orphans": orphans, "broken_links": broken, "drift": drift}


def main() -> int:
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
    ok, details = verify_a12()
    print(json.dumps({"a12_ok": ok, **details}, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
