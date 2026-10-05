from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
import re

from .contracts import ROOT, IntegrityError, load_policy, read_design, verify_frozen_design
from .io import file_hash, write_json
from .parity import compare

RECEIPT = "run_receipt.json"
REQUIRED_FILES = {"observations.csv", "weights.csv", "psu_registry.csv", "statistical_contract.json",
                  "design_manifest.json", "r_version.txt", "statistical_parity.json", "statistical.duckdb",
                  "statistical_quality_checks.csv", "statistical_sql_quality.json", "engineering_report.md",
                  *{f"{prefix}_{artifact}.csv" for prefix in ("python", "r")
                    for artifact in ("design", "coefficients", "covariance", "predictions", "diagnostics")}}


def source_inventory() -> dict:
    paths = [*sorted((ROOT / "stat_validation").glob("*.py")),
             ROOT / "r/statistical_validation.R", ROOT / "sql/statistical_validation.sql"]
    return {str(path.relative_to(ROOT)): file_hash(path) for path in paths}


def seal(directory: Path, runtime: dict) -> dict:
    inventory = {path.name: file_hash(path) for path in sorted(directory.iterdir()) if path.is_file() and path.name != RECEIPT}
    if set(inventory) != REQUIRED_FILES:
        raise IntegrityError("incomplete artifact set cannot be sealed")
    receipt = {"protocol": "synthetic-wls-v1", "status": "PASS", "synthetic_only": True,
               "private_data_used": False, "scientific_results_claimed": False,
               "runtime": runtime, "files": inventory, "software": source_inventory(),
               "hash_scope": "unsigned artifact consistency, not provenance authentication"}
    write_json(directory / RECEIPT, receipt)
    return receipt


def verify(directory: Path) -> dict:
    receipt = json.loads((directory / RECEIPT).read_text())
    required = {"protocol", "status", "synthetic_only", "private_data_used", "scientific_results_claimed",
                "runtime", "files", "software", "hash_scope"}
    if set(receipt) != required or receipt["protocol"] != "synthetic-wls-v1" or receipt["status"] != "PASS":
        raise IntegrityError("invalid run receipt")
    if (receipt["synthetic_only"] is not True or receipt["private_data_used"] is not False
            or receipt["scientific_results_claimed"] is not False):
        raise IntegrityError("receipt claim boundary violated")
    inventory = receipt["files"]
    if not isinstance(inventory, dict) or set(inventory) != REQUIRED_FILES:
        raise IntegrityError("empty receipt inventory")
    if receipt["software"] != source_inventory():
        raise IntegrityError("statistical source changed; rerun before verifying")
    actual = {path.name for path in directory.iterdir() if path.name != RECEIPT}
    if actual != set(inventory):
        raise IntegrityError("receipt artifact inventory changed")
    for name, digest in inventory.items():
        if PurePosixPath(name).name != name or name in (".", "..") or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise IntegrityError("unsafe receipt entry")
        path = directory / name
        if not path.is_file() or path.is_symlink() or file_hash(path) != digest:
            raise IntegrityError(f"artifact hash mismatch: {name}")
    policy = load_policy(directory / "statistical_contract.json")
    design = read_design(directory, policy)
    manifest = json.loads((directory / "design_manifest.json").read_text())
    verify_frozen_design(directory / "python_design.csv", design, manifest)
    parity = compare(directory, design)
    if parity != json.loads((directory / "statistical_parity.json").read_text()):
        raise IntegrityError("saved parity report changed")
    quality = json.loads((directory / "statistical_sql_quality.json").read_text())
    if quality["status"] != "PASS" or quality["failed_checks"] != 0:
        raise IntegrityError("SQL receipt is not passing")
    return {"status": "PASS", "files_verified": len(inventory), "protocol": receipt["protocol"]}
