# Public Engineering Architecture

This companion intentionally separates engineering evidence from the private scientific analysis.

The original pipeline builds a weighted-summary warehouse, reports, and an HTML dashboard from 192 fabricated encounters. The statistical module fabricates a separate 288-record continuous-index dataset and uses three raw relations: observations, weights, and a nested PSU registry.

`stat_validation/contracts.py` enforces the tracked policy and constructs a frozen Python design. `statistics.py` fits via SVD. `r/statistical_validation.R` independently reads raw tables, performs keyed joins and feature coding, and fits via QR. `parity.py` compares the declared complete designs and results. DuckDB independently reconstructs features, normalized weights, predictions, and weighted score conditions from the raw relations.

`pipeline.py` stages every artifact and only publishes after R, parity, SQL, and receipt checks succeed. `receipts.py` supports later hash/design/parity verification. Tests exercise analytical invariants, a hand-calculated oracle, independent R rejection, SQL corruption, and failed publication.

The system validates this public synthetic protocol without exposing restricted source records or accepted empirical results. See [feature/weight integrity](feature_weight_integrity.md) for the lineage boundary and [cross-language validation](cross_language_validation.md) for the exact formulas.
