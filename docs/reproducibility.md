# Reproducibility

## Local

```bash
python3 -m pip install -r requirements.txt
Rscript --version
./run_all_demos.sh
```

Python 3.12 and base R are required. Python dependencies are pinned in `requirements.txt`; the R scripts require no additional R packages. Install R using your platform's package manager and place `Rscript` on `PATH`. A missing R runtime fails rather than printing a successful skipped comparison. Local execution was validated using R 4.3.3; other versions must pass the same numerical gates.

The original weighted-summary runner remains `./run_public_demo.sh`. The statistical runner is `./run_statistical_demo.sh`. Both are invoked by `./run_all_demos.sh`. Run the full test suite with `python3 -m pytest -q tests tests_stats`.

## Statistical artifacts

```bash
python3 -m stat_validation.pipeline
python3 -m stat_validation.pipeline --verify-only
python3 -m stat_validation.pipeline --output /tmp/new-statistical-run
```

The default destination is `outputs/statistics/`. A custom destination must be new or contain a recognized statistical run receipt; unrelated directories are protected. A process lock rejects competing publishers. Raw data, Python results, R results, parity, SQL QA, and a receipt are built and checked in a temporary sibling directory before publication. Gate failures preserve the last completed result. A failed final rename restores the previous directory; publication is not a claim of crash-durable transactional storage and has a brief directory-swap interval.

The receipt inventories 21 artifacts and records Python/R/dependency versions and statistical source hashes. Verification checks file inventory/hashes, recomputes the raw-table design and its manifest, and rechecks saved Python/R parity. It does not refit or rerun SQL. Source changes require a new run. These unsigned hashes check consistency; they do not authenticate provenance or prevent coherent rewriting of both files and receipts.

CSV outputs, the policy, manifest, and parity/QA JSON are deterministic for the tested runtime. DuckDB database bytes and the receipt's database checksum are not promised to be identical across executions or platforms. Floating-point differences across runtimes must remain within the documented comparison tolerances.

## Docker and CI

```bash
docker build -t state-navigation-engineering .
docker run --rm state-navigation-engineering
```

The Docker image installs base R and runs both demos and their tests. Docker was unavailable in the local validation environment, so no local container success is claimed. GitHub Actions includes required-R execution, tests, public-boundary checks, Docker build/run, and public artifact upload. Check the [workflow page](https://github.com/mahfuzurrahman-research/who-should-navigate-the-state-engineering/actions/workflows/public-validation.yml) for the status of the current commit; workflow configuration alone does not establish a passed run.

Generated files are written under `outputs/` and are intentionally ignored by Git except for `.gitkeep`. Statistical fixtures are generated from the tracked code and policy rather than copied from any private source.

A successful run proves only that the public synthetic engineering demonstration executes reproducibly within its stated boundary.
