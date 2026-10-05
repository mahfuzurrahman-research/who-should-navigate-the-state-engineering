# Cross-Language Validation

Two demonstrations execute R rather than accepting a skipped reference implementation. The original weighted-summary gate checks exact group sets, unique keys, counts, and finite weighted totals/rates at absolute tolerance `1e-12`.

## Statistical protocol

`contracts/statistical_contract.json` declares protocol `synthetic-wls-v1`. Python and R independently read the same three raw CSV tables, join weights by `record_id`, and build these ordered features:

`intercept`, `redirect_flag`, `complexity`, `assist_flag`, `redirect_x_complexity`, `service_B`, `service_C`.

Service A is the fixed reference. The interaction is `redirect_flag * complexity`. Every declared service level must occur; flags must be binary. The input contract rejects undeclared columns, nonfinite values, invalid weights, unmatched or duplicate weight keys, inconsistent PSU nesting, unused registry PSUs, and strata with fewer than two PSUs. Weighted rank must equal seven, residual degrees of freedom must be positive, and the weighted design condition number must not exceed the declared limit.

Python uses NumPy's SVD-based least-squares solver. R uses base `stats::lm.wfit`, which fits via QR. R never reads the Python feature matrix, coefficients, or residuals. Both retain raw weights and independently calculate normalized analysis weights:

$$a_i = w_i / \overline{w}, \qquad \hat\beta = \arg\min_\beta \sum_i a_i(y_i-x_i^T\beta)^2.$$

Normalization removes arbitrary global weight scale. Tests confirm that global scaling preserves coefficients and both covariance matrices; changing an individual positive weight changes its source hash and can change the estimate. Positive weights alone do not certify a scientifically valid weighting scheme.

## Explicit covariance conventions

Let $e_i=y_i-x_i^T\hat\beta$, $s_i=a_ix_ie_i$, $U_g=\sum_{i\in g}s_i$, and $B=(X^TAX)^{-1}$. There are $n$ records, $p$ fitted columns, and $G$ PSUs.

The PSU-cluster convention is:

$$V_C = \frac{G}{G-1}\frac{n-1}{n-p}\,B\left(\sum_g U_gU_g^T\right)B^T.$$

The separately reported stratum-centered convention, with $m_h$ PSUs in stratum $h$, is:

$$V_S = B\left[\sum_h \frac{m_h}{m_h-1}\sum_{g\in h}(U_g-\overline{U}_h)(U_g-\overline{U}_h)^T\right]B^T.$$

The second convention applies no additional residual-degrees-of-freedom factor and no finite-population correction. Implementations calculate equivalent cross-products of transformed cluster scores to preserve nonnegative diagonal values under rounding. No lonely-PSU approximation or automatic fallback is allowed.

These are explicitly chosen **synthetic score conventions**. The fake weights have no established sampling interpretation, so neither output is presented as a canonical survey variance, a population estimate, or the private paper's estimator. No inferential p-values, confidence intervals, or substantive conclusions are produced. The Kish-style diagnostic describes weight concentration; it is not an effective sample size adjusted for clustering.

## Compared artifacts

| Artifact | Gate |
|---|---|
| Design | Record/PSU/stratum identities, raw and normalized weights, outcome, all seven features |
| Coefficients | Seven estimates and both sets of standard errors |
| Covariance | Every cell of both 7 × 7 matrices |
| Predictions | Every fitted value and residual, keyed by record |
| Diagnostics | Counts, rank, condition number, weight sums, weighted mean, SSE, weight concentration |

The comparator requires the exact declared key inventory and column order, rejects duplicates and nonfinite values, and applies `abs(left-right) <= 1e-10 + 1e-8 * max(abs(left), abs(right))`. Counts must match the input design exactly. Matching incomplete outputs from both languages also fail. The default fixture performs 3,586 numeric comparisons.

A second, hand-calculated 14-record fixture has seven independent feature patterns. Within each pattern, weights 1 and 3 multiply residuals +3 and −1, so the seven coefficients are known exactly. Its only nonzero covariance entry is the intercept variance: `117/28` under CR1 and `9/4` under stratum centering. Python matches these constants; the independent R result must pass the same gate.

## Method references

- [NumPy `lstsq` documentation](https://numpy.org/doc/stable/reference/generated/numpy.linalg.lstsq.html): least-squares objective, singular-value rank cutoff, and returned diagnostics.
- [R `lm.wfit` documentation](https://stat.ethz.ch/R-manual/R-devel/library/stats/html/lmfit.html): weighted QR fitting and rank handling.
- [sandwich `vcovCL` documentation](https://sandwich.r-forge.r-project.org/reference/vcovCL.html): clusterwise score sums and finite-cluster adjustments. This repository declares its own formulas and does not claim package-level parity with `sandwich` or a survey package.

Agreement establishes implementation consistency under this protocol. It does not certify feature choice, sampling design, causality, or empirical replication.
