# Data Quality Controls

The synthetic pipeline fails closed on:

1. missing required columns;
2. duplicate encounter identifiers;
3. duplicate PSU registry identifiers;
4. unknown PSU references;
5. invalid redirect domain values;
6. invalid attainment domain values;
7. nonpositive weights;
8. missing service types;
9. missing region identifiers;
10. missing stratum identifiers;
11. empty analytic inputs;
12. mismatched Python/R summaries;
13. duplicate relational keys;
14. failed DuckDB domain checks;
15. failed weighted-summary reconciliation.

All tracked data are artificial and generated from fixed deterministic rules.
