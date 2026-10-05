from __future__ import annotations

import argparse
import fcntl
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile

from .contracts import ROOT, load_policy, read_design, verify_frozen_design
from .generator import generate
from .io import write_json
from .parity import compare
from .receipts import seal, verify
from .statistics import export_fit, fit
from .warehouse import validate_sql


def run_r(directory: Path, policy: dict) -> None:
    rscript = shutil.which("Rscript")
    if not rscript:
        raise RuntimeError("Rscript is required; cross-language validation cannot be skipped")
    result = subprocess.run([rscript, "--vanilla", str(ROOT / "r/statistical_validation.R"),
                             str(directory), str(directory), str(policy["condition_limit"])],
                            text=True, capture_output=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(f"R validation failed: {result.stderr.strip()}")
    if "R_STATISTICAL_VALIDATION=PASS" not in result.stdout:
        raise RuntimeError("R did not report a completed validation")


def _stage(directory: Path, policy: dict) -> None:
    write_json(directory / "statistical_contract.json", policy)
    generate(directory, policy)
    design = read_design(directory, policy)
    manifest = design.manifest()
    write_json(directory / "design_manifest.json", manifest)
    result = fit(design)
    export_fit(directory, "python", design, result)
    verify_frozen_design(directory / "python_design.csv", design, manifest)
    run_r(directory, policy)
    parity = compare(directory, design)
    write_json(directory / "statistical_parity.json", parity)
    quality = validate_sql(directory)
    runtime = {"python": platform.python_version(), "R": (directory / "r_version.txt").read_text().strip(),
               **{name: importlib.metadata.version(name) for name in ("numpy", "duckdb")}}
    report = ("# Synthetic statistical engineering run\n\n"
              f"Status: PASS. {len(design.ids)} records, {len(set(design.psus))} PSUs, "
              f"{len(set(design.strata))} strata, {len(design.policy['features'])} declared features.\n\n"
              f"Independent Python/R gate: {parity['numeric_comparisons']} numeric comparisons. "
              f"DuckDB: {quality['passed_checks']}/{quality['total_checks']} checks.\n\n"
              "Weights are fabricated relative analysis weights. Covariances follow two explicitly "
              "declared score conventions; they are not the private paper's survey estimator. "
              "No empirical findings, population estimates, or production deployment are claimed.\n\n"
              "The Kish-style value in diagnostics describes weight concentration only; it is not "
              "an effective sample size adjusted for clustering.\n\n"
              "Artifact hashes detect changes relative to this unsigned receipt. They do not "
              "authenticate the data or certify a scientific specification.\n")
    (directory / "engineering_report.md").write_text(report)
    seal(directory, runtime)
    verify(directory)


def run(output: Path | None = None) -> dict:
    output = (output or ROOT / "outputs/statistics").absolute()
    if output.is_symlink() or output == ROOT or output in ROOT.parents:
        raise RuntimeError("unsafe statistical output destination")
    if output.exists():
        try:
            previous = json.loads((output / "run_receipt.json").read_text())
        except (OSError, ValueError) as exc:
            raise RuntimeError("refusing to replace a directory without a statistical run receipt") from exc
        if previous.get("protocol") != "synthetic-wls-v1":
            raise RuntimeError("refusing to replace an unrelated output directory")
    if not shutil.which("Rscript"):
        raise RuntimeError("Rscript is required; cross-language validation cannot be skipped")
    policy = load_policy()
    output.parent.mkdir(parents=True, exist_ok=True)
    # Lock survives directory swaps and releases automatically when the process exits.
    with (output.parent / f".{output.name}.lock").open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("another statistical run is publishing to this destination") from exc
        with tempfile.TemporaryDirectory(prefix=f".{output.name}-stage-", dir=output.parent) as temporary:
            staged = Path(temporary) / "statistics"
            staged.mkdir()
            _stage(staged, policy)
            backup = Path(temporary) / "previous"
            had_previous = output.exists()
            if had_previous:
                os.replace(output, backup)
            try:
                os.replace(staged, output)
            except BaseException:
                if had_previous:
                    os.replace(backup, output)
                raise
        return verify(output)


def main() -> None:
    parser = argparse.ArgumentParser(description="Independent synthetic Python/R statistical validation")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/statistics")
    parser.add_argument("--verify-only", action="store_true", help="check saved artifact consistency without running R")
    args = parser.parse_args()
    status = verify(args.output) if args.verify_only else run(args.output)
    print(json.dumps(status, sort_keys=True))


if __name__ == "__main__":
    main()
