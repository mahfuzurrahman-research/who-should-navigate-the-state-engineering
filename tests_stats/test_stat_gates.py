import copy
import shutil

import pytest

from scripts.check_parity import FIELDS, compare as compare_summary
from stat_validation.contracts import IntegrityError, load_policy, read_design
from stat_validation.io import read_rows, write_rows
from stat_validation.parity import compare
from stat_validation.pipeline import run_r
from stat_validation.warehouse import validate_sql


@pytest.fixture
def artifacts(tmp_path, completed_run):
    directory = tmp_path / "statistics"
    shutil.copytree(completed_run, directory)
    return directory


def mutate_csv(path, field, value):
    rows = read_rows(path)
    rows[0][field] = value
    write_rows(path, list(rows[0]), rows)


@pytest.mark.parametrize("artifact,field,value", [
    ("coefficients", "estimate", "nan"), ("covariance", "cluster_cov", "inf"),
    ("predictions", "residual", "-inf"), ("design", "analysis_weight", "nan"),
    ("diagnostics", "value", "nan"), ("coefficients", "estimate", 99),
    ("covariance", "stratum_cov", 99), ("design", "service_B", 99),
])
def test_parity_rejects_nonfinite_or_changed_r_artifacts(artifacts, artifact, field, value):
    mutate_csv(artifacts / f"r_{artifact}.csv", field, value)
    with pytest.raises(IntegrityError):
        compare(artifacts, read_design(artifacts))


@pytest.mark.parametrize("problem", ["missing", "extra", "duplicate"])
def test_parity_requires_exact_key_sets(artifacts, problem):
    path = artifacts / "r_predictions.csv"
    rows = read_rows(path)
    if problem == "missing":
        rows.pop()
    else:
        extra = copy.deepcopy(rows[0])
        if problem == "extra":
            extra["record_id"] = "UNEXPECTED"
        rows.append(extra)
    write_rows(path, list(rows[0]), rows)
    with pytest.raises(IntegrityError, match="keys|duplicate"):
        compare(artifacts, read_design(artifacts))


def test_parity_rejects_feature_column_order_drift(artifacts):
    path = artifacts / "r_design.csv"
    rows = read_rows(path)
    fields = list(rows[0])
    fields[-1], fields[-2] = fields[-2], fields[-1]
    write_rows(path, fields, rows)
    with pytest.raises(IntegrityError, match="schema/order"):
        compare(artifacts, read_design(artifacts))


@pytest.mark.parametrize("problem", ["nonfinite_weight", "duplicate_weight", "nesting"])
def test_r_independently_rejects_invalid_raw_inputs(artifacts, problem):
    if problem == "nonfinite_weight":
        mutate_csv(artifacts / "weights.csv", "weight", "nan")
    elif problem == "duplicate_weight":
        path = artifacts / "weights.csv"
        rows = read_rows(path)
        write_rows(path, list(rows[0]), rows + [rows[0]])
    else:
        mutate_csv(artifacts / "observations.csv", "stratum_id", "WRONG")
    with pytest.raises(RuntimeError, match="R validation failed"):
        run_r(artifacts, load_policy())


@pytest.mark.parametrize("filename,field,value", [
    ("python_design.csv", "redirect_x_complexity", 100),
    ("python_design.csv", "raw_weight", 100),
    ("python_coefficients.csv", "estimate", 100),
    ("python_predictions.csv", "residual", 100),
    ("python_covariance.csv", "cluster_cov", -1),
    ("python_design.csv", "service_B", ""),
    ("python_design.csv", "raw_weight", ""),
    ("python_coefficients.csv", "estimate", ""),
    ("python_predictions.csv", "residual", ""),
    ("python_covariance.csv", "cluster_cov", ""),
])
def test_sql_independently_rejects_feature_weight_or_result_corruption(artifacts, filename, field, value):
    mutate_csv(artifacts / filename, field, value)
    with pytest.raises(IntegrityError, match="SQL checks failed"):
        validate_sql(artifacts)


def test_matching_missing_rows_in_both_languages_cannot_pass(artifacts):
    for prefix in ("python", "r"):
        path = artifacts / f"{prefix}_predictions.csv"
        rows = read_rows(path)
        write_rows(path, list(rows[0]), rows[:-1])
    with pytest.raises(IntegrityError, match="declared design"):
        compare(artifacts, read_design(artifacts))


@pytest.mark.parametrize("problem", ["nan", "extra", "duplicate"])
def test_original_summary_gate_cannot_pass_nonfinite_or_hidden_groups(tmp_path, problem):
    rows = [dict(redirect_flag="0", n=2, weighted_total=3, weighted_attained=2,
                 weighted_attainment_rate=2/3, overall_weighted_attainment=2/3)]
    python_path, r_path = tmp_path / "python.csv", tmp_path / "r.csv"
    write_rows(python_path, FIELDS, rows)
    rr = copy.deepcopy(rows)
    if problem == "nan":
        rr[0]["weighted_total"] = "nan"
    else:
        row = copy.deepcopy(rr[0])
        if problem == "extra":
            row["redirect_flag"] = "1"
        rr.append(row)
    write_rows(r_path, FIELDS, rr)
    with pytest.raises(ValueError):
        compare_summary(python_path, r_path)
