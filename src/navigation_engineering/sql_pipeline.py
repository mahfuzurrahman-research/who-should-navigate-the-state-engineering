from __future__ import annotations
import json
from pathlib import Path
import duckdb

SQL_FILES = ["sql/schema.sql", "sql/marts.sql", "sql/quality_checks.sql"]

def build(root: Path, db_path: Path) -> duckdb.DuckDBPyConnection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    con = duckdb.connect(str(db_path))
    for rel in SQL_FILES:
        con.execute((root / rel).read_text(encoding="utf-8"))
    return con

def validate(con: duckdb.DuckDBPyConnection) -> dict:
    rows = con.execute("SELECT check_name, failures, status FROM quality.check_results ORDER BY check_name").fetchall()
    failed = [r for r in rows if r[2] != "PASS"]
    summary = {"total_checks":len(rows),"passed_checks":len(rows)-len(failed),"failed_checks":len(failed),"overall_status":"PASS" if not failed else "FAIL"}
    if failed:
        raise RuntimeError(f"SQL quality failure: {failed}")
    return summary

def export(con: duckdb.DuckDBPyConnection, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    summary = validate(con)
    (out / "sql_quality_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    con.execute("COPY (SELECT * FROM mart.attainment_summary ORDER BY redirect_flag) TO 'outputs/attainment_summary.csv' (HEADER, DELIMITER ',')")
    con.execute("COPY (SELECT * FROM quality.check_results ORDER BY check_name) TO 'outputs/quality_checks.csv' (HEADER, DELIMITER ',')")
    return summary
