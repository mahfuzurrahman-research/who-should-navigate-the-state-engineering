#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
rm -rf outputs
mkdir -p outputs
python scripts/generate_synthetic_data.py
python scripts/run_python_summary.py
python scripts/run_sql_pipeline.py
if command -v Rscript >/dev/null 2>&1; then
  Rscript r/synthetic_parity.R data/synthetic/encounters.csv outputs/r_summary.csv
  python scripts/check_parity.py
else
  echo "Rscript not found: cross-language parity step skipped locally."
fi
python src/navigation_engineering/reporting.py
python dashboards/build_demo_dashboard.py
echo "PUBLIC_DEMO_STATUS=PASS"
