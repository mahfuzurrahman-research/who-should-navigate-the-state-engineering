import copy

import pytest

from navigation_engineering.contracts import ContractError, read_csv, validate
from stat_validation.contracts import (DESIGN_FIELDS, IntegrityError, ROOT, build_design,
                                       load_policy, validate_policy, verify_frozen_design)
from stat_validation.io import write_rows


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf"), 0, -1, True, "not-a-number"])
def test_weights_reject_nonfinite_nonpositive_and_nonnumeric(tables, value):
    observations, weights, registry = tables
    weights[0]["weight"] = value
    with pytest.raises(IntegrityError):
        build_design(observations, weights, registry)


@pytest.mark.parametrize("field,value", [("redirect_flag", 2), ("assist_flag", True),
                                         ("outcome", "nan"), ("complexity", "inf"), ("service_type", "D")])
def test_feature_and_outcome_domains(tables, field, value):
    tables[0][-1][field] = value
    with pytest.raises(IntegrityError):
        build_design(*tables)


@pytest.mark.parametrize("table_index", [0, 1, 2])
def test_synthetic_marker_required_on_every_table(tables, table_index):
    tables[table_index][-1]["synthetic_record"] = "false"
    with pytest.raises(IntegrityError, match="synthetic marker"):
        build_design(*tables)


def test_schema_checked_on_later_rows_and_rejects_undeclared_features(tables):
    tables[0][-1]["private_feature"] = 1
    with pytest.raises(IntegrityError, match="schema"):
        build_design(*tables)


@pytest.mark.parametrize("problem", ["missing", "extra", "duplicate"])
def test_weight_join_requires_exact_unique_keys(tables, problem):
    weights = tables[1]
    if problem == "missing":
        weights.pop()
    else:
        row = copy.deepcopy(weights[0])
        if problem == "extra":
            row["record_id"] = "EXTRA"
        weights.append(row)
    with pytest.raises(IntegrityError, match="join|duplicate"):
        build_design(*tables)


@pytest.mark.parametrize("problem", ["cross_stratum", "unknown_psu", "duplicate_psu", "unused_psu", "lonely_psu"])
def test_psu_nesting_and_stratum_integrity(tables, problem):
    observations, _, registry = tables
    if problem == "cross_stratum":
        observations[-1]["stratum_id"] = "STR000"
    elif problem == "unknown_psu":
        observations[-1]["psu_id"] = "UNKNOWN"
    elif problem == "duplicate_psu":
        registry.append(copy.deepcopy(registry[0]))
    elif problem == "unused_psu":
        registry.append(dict(psu_id="UNUSED", stratum_id="STR000", synthetic_record="true"))
    else:
        registry[0]["stratum_id"] = "SINGLETON"
    with pytest.raises(IntegrityError):
        build_design(*tables)


def test_rank_and_condition_gates(tables):
    policy = load_policy()
    policy["condition_limit"] = 2
    with pytest.raises(IntegrityError, match="ill-conditioned"):
        build_design(*tables, policy)
    for row in tables[0]:
        row["assist_flag"] = 0
    with pytest.raises(IntegrityError, match="rank-deficient"):
        build_design(*tables)


@pytest.mark.parametrize("field,value", [("service_reference", "B"), ("features", ["intercept"]),
                                         ("private_data_used", True), ("seed", True),
                                         ("absolute_tolerance", float("nan"))])
def test_policy_changes_cannot_silently_change_protocol(field, value):
    policy = load_policy()
    policy[field] = value
    with pytest.raises(IntegrityError):
        validate_policy(policy)


@pytest.mark.parametrize("problem", ["weight", "interaction", "feature_order", "row_order"])
def test_frozen_design_detects_lineage_and_order_changes(tmp_path, design, problem):
    rows = design.rows()
    fields = DESIGN_FIELDS.copy()
    if problem == "weight":
        rows[0]["raw_weight"] += 0.1
    elif problem == "interaction":
        rows[0]["redirect_x_complexity"] += 0.1
    elif problem == "feature_order":
        fields[-1], fields[-2] = fields[-2], fields[-1]
    else:
        rows.reverse()
    path = tmp_path / "design.csv"
    write_rows(path, fields, rows)
    with pytest.raises(IntegrityError):
        verify_frozen_design(path, design, design.manifest())


def test_frozen_manifest_detects_changed_raw_weight_source(tmp_path, design, tables):
    path = tmp_path / "design.csv"
    write_rows(path, DESIGN_FIELDS, design.rows())
    tables[1][0]["weight"] += 0.1
    changed = build_design(*tables)
    with pytest.raises(IntegrityError, match="manifest changed"):
        verify_frozen_design(path, changed, design.manifest())


def test_original_summary_contract_rejects_nonfinite_and_later_schema_errors():
    observations = read_csv(ROOT / "data/synthetic/encounters.csv")
    registry = read_csv(ROOT / "data/synthetic/psu_registry.csv")
    for bad_weight in ("nan", "inf", "-inf"):
        bad = copy.deepcopy(observations)
        bad[-1]["weight"] = bad_weight
        with pytest.raises(ContractError):
            validate(bad, registry)
    observations[-1].pop("weight")
    with pytest.raises(ContractError, match="schema"):
        validate(observations, registry)
