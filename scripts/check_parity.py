"""Strict parity for the original synthetic weighted-summary demo."""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

FIELDS = ["redirect_flag", "n", "weighted_total", "weighted_attained",
          "weighted_attainment_rate", "overall_weighted_attainment"]


def load(path: Path) -> dict[int, dict]:
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != FIELDS:
            raise ValueError("summary parity schema mismatch")
        rows = list(reader)
    if not rows:
        raise ValueError("empty parity summary")
    result = {}
    for row in rows:
        if set(row) != set(FIELDS) or any(value is None for value in row.values()):
            raise ValueError("ragged parity row")
        if row["redirect_flag"] not in ("0", "1"):
            raise ValueError("invalid parity group")
        key = int(row["redirect_flag"])
        if key in result:
            raise ValueError("duplicate parity group")
        result[key] = row
    return result


def compare(python_path: Path, r_path: Path) -> dict:
    py, rr = load(python_path), load(r_path)
    if set(py) != set(rr):
        raise ValueError("missing or extra parity groups")
    max_error = 0.0
    for key in sorted(py):
        for field in FIELDS[1:]:
            left, right = float(py[key][field]), float(rr[key][field])
            if not math.isfinite(left) or not math.isfinite(right):
                raise ValueError("nonfinite parity values")
            error = abs(left - right)
            max_error = max(max_error, error)
            if error > (0 if field == "n" else 1e-12):
                raise ValueError(f"summary parity failure: {key} {field}: {error}")
    return {"status": "PASS", "tolerance": 1e-12, "max_abs_error": max_error,
            "scope": "synthetic weighted summary only"}


def main() -> None:
    out = Path(__file__).resolve().parents[1] / "outputs"
    report = compare(out / "python_summary.csv", out / "r_summary.csv")
    (out / "parity.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print("CROSS_LANGUAGE_PARITY=PASS")


if __name__ == "__main__":
    main()
