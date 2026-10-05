import fcntl
import json
import os
import shutil

import pytest

from stat_validation import pipeline
from stat_validation.contracts import IntegrityError
from stat_validation.io import file_hash, write_json
from stat_validation.receipts import verify


def clone(completed_run, tmp_path):
    destination = tmp_path / "statistics"
    shutil.copytree(completed_run, destination)
    return destination


def test_completed_run_has_real_r_parity_and_sql_evidence(completed_run):
    assert verify(completed_run)["files_verified"] == 21
    parity = json.loads((completed_run / "statistical_parity.json").read_text())
    quality = json.loads((completed_run / "statistical_sql_quality.json").read_text())
    assert parity["numeric_comparisons"] == 3586
    assert quality == dict(status="PASS", total_checks=23, passed_checks=23, failed_checks=0)
    assert (completed_run / "r_version.txt").read_text().startswith("R version ")


def test_r_is_required_and_failure_preserves_completed_run(monkeypatch, completed_run, tmp_path):
    destination = clone(completed_run, tmp_path)
    before = file_hash(destination / "run_receipt.json")
    monkeypatch.setattr(pipeline.shutil, "which", lambda name: None)
    with pytest.raises(RuntimeError, match="Rscript is required"):
        pipeline.run(destination)
    assert file_hash(destination / "run_receipt.json") == before


@pytest.mark.parametrize("stage", ["run_r", "validate_sql"])
def test_failed_stage_does_not_publish_partial_results(monkeypatch, completed_run, tmp_path, stage):
    destination = clone(completed_run, tmp_path)
    before = file_hash(destination / "run_receipt.json")
    def fail(*args):
        raise RuntimeError("deliberate gate failure")
    monkeypatch.setattr(pipeline, stage, fail)
    with pytest.raises(RuntimeError, match="deliberate gate failure"):
        pipeline.run(destination)
    assert file_hash(destination / "run_receipt.json") == before
    assert verify(destination)["status"] == "PASS"
    assert not list(tmp_path.glob(".statistics-stage-*"))


def test_publish_rename_failure_restores_previous_run(monkeypatch, completed_run, tmp_path):
    destination = clone(completed_run, tmp_path)
    before = file_hash(destination / "run_receipt.json")
    original_replace = os.replace
    failed = False
    def fail_once(source, target):
        nonlocal failed
        if target == destination and source.name == "statistics" and not failed:
            failed = True
            raise OSError("deliberate rename failure")
        return original_replace(source, target)
    monkeypatch.setattr(pipeline.os, "replace", fail_once)
    with pytest.raises(OSError, match="rename failure"):
        pipeline.run(destination)
    assert failed
    assert file_hash(destination / "run_receipt.json") == before
    assert verify(destination)["status"] == "PASS"


def test_process_lock_prevents_competing_publishers(completed_run, tmp_path):
    destination = clone(completed_run, tmp_path)
    with (tmp_path / ".statistics.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(RuntimeError, match="another statistical run"):
            pipeline.run(destination)
    assert verify(destination)["status"] == "PASS"


def test_destination_guard_protects_unrelated_files(tmp_path):
    unrelated = tmp_path / "personal_files"
    unrelated.mkdir()
    important = unrelated / "notes.txt"
    important.write_text("keep")
    with pytest.raises(RuntimeError, match="without a statistical run receipt"):
        pipeline.run(unrelated)
    assert important.read_text() == "keep"


@pytest.mark.parametrize("problem", ["changed_file", "extra_file", "removed_file_and_hash", "claim_boundary"])
def test_receipt_detects_corruption_and_incomplete_inventory(completed_run, tmp_path, problem):
    destination = clone(completed_run, tmp_path)
    receipt_path = destination / "run_receipt.json"
    receipt = json.loads(receipt_path.read_text())
    if problem == "changed_file":
        (destination / "weights.csv").write_text("corrupted")
    elif problem == "extra_file":
        (destination / "extra.csv").write_text("unexpected")
    elif problem == "removed_file_and_hash":
        (destination / "engineering_report.md").unlink()
        receipt["files"].pop("engineering_report.md")
        write_json(receipt_path, receipt)
    else:
        receipt["private_data_used"] = True
        write_json(receipt_path, receipt)
    with pytest.raises(IntegrityError):
        verify(destination)


def test_repeated_run_is_deterministic_for_csv_and_scientific_json(completed_run, tmp_path):
    second = tmp_path / "second"
    pipeline.run(second)
    for original in completed_run.iterdir():
        if original.suffix == ".csv" or (original.suffix == ".json" and original.name != "run_receipt.json"):
            assert original.read_bytes() == (second / original.name).read_bytes(), original.name
    assert verify(second)["status"] == "PASS"
