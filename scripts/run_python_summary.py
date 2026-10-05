from __future__ import annotations
import csv, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from navigation_engineering.analytics import weighted_summary, overall_weighted_attainment
from navigation_engineering.contracts import read_csv, validate
encounters=read_csv(ROOT/"data"/"synthetic"/"encounters.csv")
registry=read_csv(ROOT/"data"/"synthetic"/"psu_registry.csv")
status=validate(encounters,registry); summary=weighted_summary(encounters); overall=overall_weighted_attainment(encounters)
out=ROOT/"outputs"; out.mkdir(exist_ok=True)
with (out/"python_summary.csv").open("w",newline="",encoding="utf-8") as f:
    fields=["redirect_flag","n","weighted_total","weighted_attained","weighted_attainment_rate","overall_weighted_attainment"]
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
    for row in summary:
        row=dict(row); row["overall_weighted_attainment"]=overall; w.writerow(row)
print("PYTHON_CONTRACT_STATUS="+status["status"])
print("PYTHON_SUMMARY_STATUS=PASS")
