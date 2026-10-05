# Feature and Weight Integrity

## Declared inputs and coding

Every raw row must have the exact declared schema and `synthetic_record=true`. There is no automatic selection of numeric columns, outcome-derived predictors, or inferred reference category. The seven-column matrix includes an intercept, two binary flags, a continuous complexity field, their declared redirect/complexity interaction, and B/C service indicators referenced to A. Missing levels, extra fields, nonfinite values, rank deficiency, and unsafe conditioning stop the run.

Observation and weight tables are separate. Keys must be unique and their sets must match exactly. The join uses `record_id`; reordering either table cannot reassign weights. Registry PSUs must exactly match observed PSUs, nest in one stratum, and have at least one observation. Each stratum needs at least two PSUs.

## Lineage checks

The manifest records ordered features, reference service, canonical row IDs, policy hash, a canonical source hash, and a full design hash. Source hashing normalizes numeric representations and sorts records/PSUs by key, so harmless input-row permutations preserve identity. Raw weights remain in the frozen design alongside their mean-normalized counterparts.

Frozen design verification reconstructs the expected matrix from the raw tables and checks column order, row order, every feature/weight/outcome value, and manifest identity. It rejects changed interaction values, reordered columns, changed weights, and mismatched source manifests. R rebuilds independently from raw data, while SQL separately rebuilds coding and normalization; agreement is not obtained by sharing a generated Python matrix.

Uniform scaling preserves normalized fit and covariance results while changing raw-weight lineage. Changing one positive weight remains legal under the numerical contract but changes source identity and can change estimates. The checks detect missing, invalid, misjoined, or changed weights relative to the declared source; they cannot certify a scientifically correct weighting scheme.

## Limits

The generator fabricates all values. There is no ingestion of restricted survey data, scientific variable dictionary, accepted paper specification, or private execution record. Synthetic markers are required declarations, not automatic proof that arbitrary external data are artificial.

The unsigned receipt checks consistency relative to its saved files and source hashes. Someone who rewrites both data and receipt can create a different consistent run. Authentic provenance, valid sampling weights, substantive feature choice, and scientific interpretation require evidence beyond this demonstration.
