from __future__ import annotations

from pathlib import Path

import duckdb

from .contracts import IntegrityError, ROOT
from .io import write_json, write_rows

TABLE_FILES = {"observations": "observations.csv", "weights": "weights.csv", "psu_registry": "psu_registry.csv",
               "python_design": "python_design.csv", "coefficients": "python_coefficients.csv",
               "covariance": "python_covariance.csv", "predictions": "python_predictions.csv",
               "diagnostics": "python_diagnostics.csv"}


def validate_sql(directory: Path) -> dict:
    db_path = directory / "statistical.duckdb"
    with duckdb.connect(str(db_path)) as con:
        for table, filename in TABLE_FILES.items():
            con.execute(f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM read_csv_auto(?, header=true)",
                        [str(directory / filename)])
        con.execute((ROOT / "sql/statistical_validation.sql").read_text())
        checks = [dict(check_name=name, failures=int(failures), status=status)
                  for name, failures, status in con.execute("SELECT * FROM statistical_checks ORDER BY check_name").fetchall()]
    failed = [row for row in checks if row["status"] != "PASS"]
    summary = {"status": "FAIL" if failed else "PASS", "total_checks": len(checks),
               "passed_checks": len(checks) - len(failed), "failed_checks": len(failed)}
    write_rows(directory / "statistical_quality_checks.csv", ["check_name", "failures", "status"], checks)
    write_json(directory / "statistical_sql_quality.json", summary)
    if failed:
        raise IntegrityError(f"independent SQL checks failed: {failed}")
    return summary
