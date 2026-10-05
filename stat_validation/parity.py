from __future__ import annotations

from pathlib import Path

from .contracts import DESIGN_FIELDS, FEATURES, Design, IntegrityError, finite_number
from .io import read_rows
from .statistics import (COEFFICIENT_FIELDS, COVARIANCE_FIELDS, DIAGNOSTIC_FIELDS,
                         DIAGNOSTIC_NAMES, PREDICTION_FIELDS)

ARTIFACTS = {
    "design": (DESIGN_FIELDS, ["record_id"], ["record_id", "psu_id", "stratum_id"]),
    "coefficients": (COEFFICIENT_FIELDS, ["feature"], ["feature"]),
    "covariance": (COVARIANCE_FIELDS, ["row_feature", "column_feature"], ["row_feature", "column_feature"]),
    "predictions": (PREDICTION_FIELDS, ["record_id"], ["record_id"]),
    "diagnostics": (DIAGNOSTIC_FIELDS, ["name"], ["name"]),
}
COUNT_DIAGNOSTICS = {"n", "p", "psus", "strata", "rank"}


def _load(path: Path, fields: list[str], keys: list[str]) -> dict[tuple, dict]:
    rows = read_rows(path)
    if not rows or any(list(row) != fields for row in rows):
        raise IntegrityError(f"parity schema/order mismatch: {path.name}")
    indexed = {}
    for row in rows:
        key = tuple(row[field] for field in keys)
        if key in indexed:
            raise IntegrityError(f"duplicate parity key: {path.name} {key}")
        indexed[key] = row
    return indexed


def compare(directory: Path, design: Design) -> dict:
    atol, rtol = design.policy["absolute_tolerance"], design.policy["relative_tolerance"]
    expected = {"design": {(key,) for key in design.ids}, "predictions": {(key,) for key in design.ids},
                "coefficients": {(name,) for name in FEATURES},
                "covariance": {(row, column) for row in FEATURES for column in FEATURES},
                "diagnostics": {(name,) for name in DIAGNOSTIC_NAMES}}
    expected_counts = {"n": len(design.ids), "p": len(FEATURES), "rank": len(FEATURES),
                       "psus": len(set(design.psus)), "strata": len(set(design.strata))}
    reports = {}
    for name, (fields, keys, text_fields) in ARTIFACTS.items():
        py = _load(directory / f"python_{name}.csv", fields, keys)
        rr = _load(directory / f"r_{name}.csv", fields, keys)
        if set(py) != expected[name] or set(rr) != expected[name]:
            raise IntegrityError(f"missing/extra parity keys against declared design: {name}")
        maximum, maximum_ratio, comparisons = 0.0, 0.0, 0
        for key in py:
            for field in fields:
                if field in text_fields:
                    if py[key][field] != rr[key][field]:
                        raise IntegrityError(f"categorical parity failure: {name} {key} {field}")
                    continue
                left = finite_number(py[key][field], field)
                right = finite_number(rr[key][field], field)
                error = abs(left - right)
                limit = atol + rtol * max(abs(left), abs(right))
                if name == "diagnostics" and key[0] in COUNT_DIAGNOSTICS:
                    limit = 0.0
                    if left != expected_counts[key[0]]:
                        raise IntegrityError(f"diagnostic count disagrees with declared design: {key[0]}")
                if error > limit:
                    raise IntegrityError(f"numeric parity failure: {name} {key} {field}: {error}")
                maximum = max(maximum, error)
                maximum_ratio = max(maximum_ratio, error / limit if limit else 0.0)
                comparisons += 1
        reports[name] = {"rows": len(py), "numeric_comparisons": comparisons,
                         "max_abs_error": maximum, "max_tolerance_fraction": maximum_ratio}
    return {"status": "PASS", "protocol": design.policy["protocol"], "absolute_tolerance": atol,
            "relative_tolerance": rtol, "artifacts": reports,
            "numeric_comparisons": sum(row["numeric_comparisons"] for row in reports.values()),
            "scope": "independent Python SVD / base-R QR WLS and explicit synthetic score covariances"}
