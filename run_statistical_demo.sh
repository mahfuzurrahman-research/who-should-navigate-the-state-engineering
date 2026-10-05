#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
python3 -m stat_validation.pipeline
python3 -m pytest -q tests_stats
python3 -m stat_validation.pipeline --verify-only
echo "STATISTICAL_ENGINEERING_STATUS=PASS"
