import numpy as np

from stat_validation.contracts import OBS_FIELDS, PSU_FIELDS, WEIGHT_FIELDS, build_design
from stat_validation.io import write_rows
from stat_validation.parity import compare
from stat_validation.pipeline import run_r
from stat_validation.statistics import export_fit, fit


def known_fixture():
    # Seven linearly independent feature patterns, each observed with weights 1 and 3.
    # Residuals +3 and -1 cancel within each pattern: coefficients are known exactly.
    patterns = [("A", 0, 0, 0), ("A", 1, 0, 0), ("A", 0, 1, 0), ("A", 0, 0, 1),
                ("A", 1, 1, 0), ("B", 0, 0, 0), ("C", 0, 0, 0)]
    expected = np.array([2, -1, 0.5, 0.75, -0.25, 1.25, -0.5])
    observations, weights = [], []
    for i, (service, redirect, complexity, assist) in enumerate(patterns):
        baseline = (2 - redirect + 0.5 * complexity + 0.75 * assist - 0.25 * redirect * complexity
                    + {"A": 0, "B": 1.25, "C": -0.5}[service])
        for g, weight, error in ((0, 1, 3), (1, 3, -1)):
            key = f"K{i:02d}_{g}"
            observations.append(dict(record_id=key, psu_id=f"P{g}", stratum_id="S0", service_type=service,
                                     redirect_flag=redirect, complexity=complexity, assist_flag=assist,
                                     outcome=baseline + error, synthetic_record="true"))
            weights.append(dict(record_id=key, weight=weight, synthetic_record="true"))
    registry = [dict(psu_id=f"P{g}", stratum_id="S0", synthetic_record="true") for g in (0, 1)]
    return (observations, weights, registry), expected


def test_known_coefficients_and_hand_calculated_covariance():
    tables, expected = known_fixture()
    result = fit(build_design(*tables))
    np.testing.assert_allclose(result.beta, expected, atol=1e-12)
    # Both cluster influences are +/-0.75 on the intercept and zero elsewhere.
    # CR1: 2*(0.75^2) * (2/1) * (13/7) = 117/28. Stratum centering: 9/4.
    expected_cluster, expected_stratum = np.zeros((7, 7)), np.zeros((7, 7))
    expected_cluster[0, 0], expected_stratum[0, 0] = 117 / 28, 9 / 4
    np.testing.assert_allclose(result.cluster_cov, expected_cluster, atol=1e-12)
    np.testing.assert_allclose(result.stratum_cov, expected_stratum, atol=1e-12)


def test_known_fixture_also_runs_in_independent_r(tmp_path):
    tables, expected = known_fixture()
    design = build_design(*tables)
    for filename, fields, rows in zip(("observations.csv", "weights.csv", "psu_registry.csv"),
                                      (OBS_FIELDS, WEIGHT_FIELDS, PSU_FIELDS), tables):
        write_rows(tmp_path / filename, fields, rows)
    result = fit(design)
    export_fit(tmp_path, "python", design, result)
    run_r(tmp_path, design.policy)
    assert compare(tmp_path, design)["status"] == "PASS"
    np.testing.assert_allclose(result.beta, expected, atol=1e-12)


def test_global_weight_scaling_preserves_both_covariances_and_fit(tables):
    before = fit(build_design(*tables))
    for row in tables[1]:
        row["weight"] *= 7.25
    after = fit(build_design(*tables))
    for field in ("beta", "predictions", "residuals", "cluster_cov", "stratum_cov"):
        np.testing.assert_allclose(getattr(before, field), getattr(after, field), atol=1e-12)
    assert np.isclose(after.diagnostics["raw_weight_sum"], before.diagnostics["raw_weight_sum"] * 7.25)
    assert np.isclose(after.diagnostics["kish_weight_concentration_n"], before.diagnostics["kish_weight_concentration_n"])


def test_shuffled_rows_and_weights_preserve_keyed_design(tables):
    before = build_design(*tables)
    rng = np.random.default_rng(19)
    for table in tables:
        rng.shuffle(table)
    after = build_design(*tables)
    assert before.manifest() == after.manifest()
    np.testing.assert_array_equal(before.x, after.x)
    np.testing.assert_array_equal(before.raw_weight, after.raw_weight)


def test_positive_but_changed_weight_is_traceable_and_changes_estimate(tables):
    before = build_design(*tables)
    tables[1][0]["weight"] *= 10
    after = build_design(*tables)
    assert before.manifest()["source_hash"] != after.manifest()["source_hash"]
    assert not np.allclose(fit(before).beta, fit(after).beta)


def test_covariances_are_symmetric_positive_semidefinite_and_not_conflated(design):
    result = fit(design)
    for covariance in (result.cluster_cov, result.stratum_cov):
        np.testing.assert_allclose(covariance, covariance.T, atol=1e-12)
        assert np.linalg.eigvalsh(covariance).min() >= -1e-12
    assert not np.allclose(result.cluster_cov, result.stratum_cov)


def test_reference_coding_and_interaction_are_explicit(design):
    for row, encoded in zip(design.observations, design.x):
        if row["service_type"] == "A":
            assert tuple(encoded[-2:]) == (0, 0)
        assert encoded[4] == row["redirect_flag"] * row["complexity"]
