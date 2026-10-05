from __future__ import annotations
import csv, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs"

def main() -> None:
    py = list(csv.DictReader((OUT / "python_summary.csv").open(encoding="utf-8")))
    sql = json.loads((OUT / "sql_quality_summary.json").read_text(encoding="utf-8"))
    parity_path = OUT / "parity.json"
    parity = json.loads(parity_path.read_text(encoding="utf-8")) if parity_path.exists() else {"status":"NOT_RUN"}
    report = {"repository":"who-should-navigate-the-state-engineering","data_class":"SYNTHETIC_ONLY","python_groups":py,"sql_quality":sql,"cross_language_parity":parity,"scientific_result_claimed":False,"restricted_source_data_included":False}
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md = ["# Public Engineering Demonstration Report","","- Data class: **SYNTHETIC_ONLY**",f"- SQL QA: **{sql['overall_status']}** ({sql['passed_checks']}/{sql['total_checks']} checks passed)",f"- Python/R parity: **{parity.get('status','NOT_RUN')}**","- Restricted source data included: **false**","- Scientific result claimed: **false**","","Synthetic outputs are engineering fixtures only."]
    (OUT / "report.md").write_text("\n".join(md) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
