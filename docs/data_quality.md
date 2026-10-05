# Data Quality Controls

The synthetic pipeline fails closed on:

1. missing required columns;
2. duplicate encounter identifiers;
3. duplicate PSU registry identifiers;
4. unknown PSU references;
5. invalid redirect domain values;
6. invalid attainment domain values;
7. nonfinite or nonpositive weights;
8. missing service types;
9. missing region identifiers;
10. missing stratum identifiers;
11. empty analytic inputs;
12. mismatched Python/R summaries;
13. duplicate relational keys;
14. failed DuckDB domain checks;
15. failed weighted-summary reconciliation.

The original contract now checks every row's schema, and its parity gate rejects hidden duplicate/extra groups and nonfinite numeric values.

The statistical module additionally requires exact observation/weight key sets, explicit synthetic markers, known categories, binary flags, finite continuous fields, represented service levels, correct PSU nesting, and at least two PSUs per stratum. Weighted designs must have full rank, positive residual degrees of freedom, and an acceptable condition number.

Its 23 DuckDB checks independently reconstruct the declared features and weights and reconcile predictions, residuals, weighted normal equations, covariance properties, standard errors, the weighted mean, and SSE. Numeric NULLs are explicitly rejected as well as NaN/infinity. SQL complements the Python/R gate; it does not independently invert the regression matrix or calculate either covariance estimator.

All tracked data are artificial and generated from fixed deterministic rules. See [feature/weight integrity](feature_weight_integrity.md) and [the validation record](statistical_validation_record.md).
