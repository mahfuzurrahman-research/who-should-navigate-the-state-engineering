#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
./run_public_demo.sh
python3 -m pytest -q tests
./run_statistical_demo.sh
echo "ALL_PUBLIC_DEMOS_STATUS=PASS"
