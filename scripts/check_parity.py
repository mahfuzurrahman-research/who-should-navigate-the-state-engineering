from __future__ import annotations
import csv, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"outputs"
def load(path):
    rows=list(csv.DictReader(path.open(encoding="utf-8")))
    return {int(r["redirect_flag"]):r for r in rows}
py=load(OUT/"python_summary.csv"); rr=load(OUT/"r_summary.csv")
fields=["weighted_total","weighted_attained","weighted_attainment_rate","overall_weighted_attainment"]
max_error=0.0
for key in sorted(py):
    if key not in rr: raise SystemExit(f"missing R group {key}")
    for field in fields:
        err=abs(float(py[key][field])-float(rr[key][field])); max_error=max(max_error,err)
        if err>1e-12: raise SystemExit(f"parity failure {key} {field}: {err}")
obj={"status":"PASS","tolerance":1e-12,"max_abs_error":max_error,"scope":"synthetic weighted summary only"}
(OUT/"parity.json").write_text(json.dumps(obj,indent=2)+"\n",encoding="utf-8")
print("CROSS_LANGUAGE_PARITY=PASS")
