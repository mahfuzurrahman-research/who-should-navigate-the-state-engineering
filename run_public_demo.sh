#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
command -v Rscript >/dev/null 2>&1 || { echo "Rscript is required for cross-language validation." >&2; exit 1; }
mkdir -p outputs
python3 scripts/generate_synthetic_data.py
python3 scripts/run_python_summary.py
python3 scripts/run_sql_pipeline.py
Rscript --vanilla r/synthetic_parity.R data/synthetic/encounters.csv outputs/r_summary.csv
python3 scripts/check_parity.py
python3 src/navigation_engineering/reporting.py
python3 dashboards/build_demo_dashboard.py
echo "PUBLIC_DEMO_STATUS=PASS"
