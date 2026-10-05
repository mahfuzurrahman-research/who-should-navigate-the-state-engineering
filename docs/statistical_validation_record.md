# Local Validation Record

Executed on **2026-10-05 UTC** against the public synthetic implementation. These are local results, not results from the private paper or evidence of a hosted deployment.

| Check | Observed result |
|---|---|
| Original weighted-summary demo | PASS; R actually executed |
| Statistical pipeline | PASS; 288 records, 24 PSUs, six strata, seven features |
| Tests | 94 passed, none skipped: 10 original + 84 statistical/integrity tests |
| SQL QA | 38 passed: 15 original + 23 statistical |
| Statistical Python/R parity | 3,586 numeric comparisons passed |
| Maximum coefficient/SE absolute error | `7.55e-15` |
| Maximum covariance-cell absolute error | `5.00e-16` |
| Maximum prediction/residual absolute error | `1.34e-14` |
| Saved-run verification | PASS; 21 artifact hashes, source hashes, reconstructed design and saved parity |
| Hand-calculated fixture | Known coefficients and intercept variances `117/28`, `9/4`; independent R comparison passed |
| Runtime | Python 3.12.14; R 4.3.3; NumPy 2.3.5; DuckDB 1.5.6; pytest 9.1.1 |
| Docker | Unavailable locally; not executed locally |

The original tests and new tests ran together with `python3 -m pytest -q tests tests_stats`. `./run_all_demos.sh` runs the same two suites separately after their associated demos. The statistical run uses absolute tolerance `1e-10` plus relative tolerance `1e-8`; integer diagnostics match exactly.

Negative tests cover nonfinite/nonpositive weights, invalid domains, exact join failures, unknown categories, PSU nesting, lonely PSUs, rank/condition gates, policy/claim changes, corrupted matrix lineage, duplicate/missing/extra parity keys, matching incomplete outputs, independently rejected R inputs, SQL numeric NULLs/corruption, receipt tampering, concurrent publishing, and failed-stage/rename rollback.

The local runtime used an isolated R installation; no R package beyond base R was needed. The runner requires an actual `Rscript` execution and cannot turn a missing runtime into a passing comparison. Docker and hosted CI must be assessed from their own execution evidence. See the [GitHub Actions workflow](https://github.com/mahfuzurrahman-research/who-should-navigate-the-state-engineering/actions/workflows/public-validation.yml) for the current commit's status.

Numerical agreement checks implementation under this synthetic protocol. It does not validate scientific sampling assumptions, causal inference, empirical coefficients, or production operation.
