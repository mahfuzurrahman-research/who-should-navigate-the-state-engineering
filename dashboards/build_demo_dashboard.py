from __future__ import annotations
import csv, html
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"outputs"
rows=list(csv.DictReader((OUT/"python_summary.csv").open(encoding="utf-8")))
items="".join(f"<tr><td>{html.escape(r['redirect_flag'])}</td><td>{html.escape(r['n'])}</td><td>{float(r['weighted_attainment_rate']):.4f}</td></tr>" for r in rows)
page = "<!doctype html><html><head><meta charset='utf-8'><title>State Navigation Engineering Demo</title>" \
       "<style>body{font-family:system-ui;max-width:900px;margin:40px auto;padding:0 20px}table{border-collapse:collapse;width:100%}td,th{border:1px solid #bbb;padding:8px;text-align:left}code{background:#eee;padding:2px 4px}</style></head>" \
       "<body><h1>Who Should Navigate the State? — Engineering Demonstration</h1><p><strong>Data class:</strong> SYNTHETIC ONLY</p>" \
       "<p>This dashboard demonstrates reporting infrastructure. It contains no private scientific results.</p>" \
       "<table><thead><tr><th>Redirect flag</th><th>Synthetic N</th><th>Weighted attainment rate</th></tr></thead><tbody>" + items + \
       "</tbody></table><p><code>scientific_result_claimed=false</code></p></body></html>"
(OUT/"dashboard.html").write_text(page,encoding="utf-8")
print("DASHBOARD_STATUS=PASS")
