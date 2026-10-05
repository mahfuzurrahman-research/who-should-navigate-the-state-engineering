from __future__ import annotations
import os, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0,str(ROOT/"src"))
from navigation_engineering.sql_pipeline import build, export
out=ROOT/"outputs"
con=build(ROOT,out/"navigation_demo.duckdb"); summary=export(con,out); con.close()
print("SQL_QUALITY_STATUS="+summary["overall_status"])
