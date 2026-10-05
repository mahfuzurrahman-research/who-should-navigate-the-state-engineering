# CV Evidence: Statistical Validation Engineering

Suggested project bullet, supported by the public implementation and local validation:

> Built a synthetic Python/R statistical validation pipeline for weighted regression and PSU/stratum covariance checks, with explicit feature coding, keyed weight joins, 94 passing tests, and 38 DuckDB quality checks.

An optional technical detail for a longer project description:

> Compared independently constructed design matrices, coefficients, standard errors, full covariance matrices, and fitted values across Python SVD and R QR implementations; validated 3,586 numeric comparisons and added source/artifact integrity receipts.

| Claim | Reviewable evidence |
|---|---|
| Python/R statistical validation | `stat_validation/statistics.py`, `r/statistical_validation.R`, `stat_validation/parity.py` |
| Feature/weight integrity | `contracts/statistical_contract.json`, `stat_validation/contracts.py`, `docs/feature_weight_integrity.md` |
| SQL quality engineering | `sql/statistical_validation.sql`, original schema/mart/QA scripts |
| Analytical/failure-mode testing | `tests_stats/`, including the hand-calculated covariance oracle |
| Reproducible execution | runners, pinned Python requirements, versioned policy and receipt verification |
| CI/container engineering | GitHub Actions workflow and Dockerfile; execution status is separate |

Use “synthetic,” “engineering demonstration,” and “explicit covariance conventions” when discussing this project. The repository supports these implementation claims; it does not support claims of private empirical replication, canonical survey-estimator validation, production deployment, authenticated data provenance, or a locally passed Docker run.

The counts above record [the tested upgrade](statistical_validation_record.md). Re-run and revise them if the implementation changes. No actual CV document is modified by this repository upgrade.
