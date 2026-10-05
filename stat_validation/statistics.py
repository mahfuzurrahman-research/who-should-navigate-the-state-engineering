from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .contracts import DESIGN_FIELDS, FEATURES, Design, IntegrityError
from .io import write_rows

COEFFICIENT_FIELDS = ["feature", "estimate", "se_cluster", "se_stratum"]
COVARIANCE_FIELDS = ["row_feature", "column_feature", "cluster_cov", "stratum_cov"]
PREDICTION_FIELDS = ["record_id", "prediction", "residual"]
DIAGNOSTIC_FIELDS = ["name", "value"]
DIAGNOSTIC_NAMES = {"n", "p", "psus", "strata", "rank", "raw_weight_sum", "analysis_weight_sum",
                    "weighted_outcome_mean", "kish_weight_concentration_n", "weighted_sse", "condition_number"}


@dataclass
class Fit:
    beta: np.ndarray
    cluster_cov: np.ndarray
    stratum_cov: np.ndarray
    predictions: np.ndarray
    residuals: np.ndarray
    diagnostics: dict[str, float]


def fit(design: Design) -> Fit:
    x, y, a = design.x, design.y, design.analysis_weight
    n, p = x.shape
    weighted_x = np.sqrt(a)[:, None] * x
    beta, _, rank, singular_values = np.linalg.lstsq(weighted_x, np.sqrt(a) * y, rcond=None)
    if rank != p or singular_values[0] / singular_values[-1] > design.policy["condition_limit"]:
        raise IntegrityError("unsafe weighted least-squares fit")
    predictions = x @ beta
    residuals = y - predictions
    scores = x * (a * residuals)[:, None]
    bread = np.linalg.solve(x.T @ (a[:, None] * x), np.eye(p))
    psu_ids = sorted(set(design.psus))
    clusters = np.asarray(design.psus)
    cluster_scores = np.stack([scores[clusters == key].sum(axis=0) for key in psu_ids])
    g = len(psu_ids)
    influence = cluster_scores @ bread.T
    cluster_cov = influence.T @ influence
    cluster_cov *= g / (g - 1) * (n - 1) / (n - p)
    # Explicit toy score-centering convention, with no finite-population correction.
    stratum_cov = np.zeros((p, p))
    nesting = {row["psu_id"]: row["stratum_id"] for row in design.registry}
    for stratum in sorted(set(design.strata)):
        u = cluster_scores[[nesting[key] == stratum for key in psu_ids]]
        centered = u - u.mean(axis=0)
        centered_influence = centered @ bread.T
        stratum_cov += len(u) / (len(u) - 1) * centered_influence.T @ centered_influence
    # Remove machine rounding asymmetry before exporting either implementation.
    cluster_cov = (cluster_cov + cluster_cov.T) / 2
    stratum_cov = (stratum_cov + stratum_cov.T) / 2
    normal_error = float(np.max(np.abs(scores.sum(axis=0))))
    if normal_error > 1e-8 * max(1.0, float(np.sum(np.abs(a * y))) * np.max(np.abs(x))):
        raise IntegrityError("weighted normal equations failed")
    if (not all(np.all(np.isfinite(value)) for value in (beta, cluster_cov, stratum_cov, predictions, residuals))
            or np.any(np.diag(cluster_cov) < 0) or np.any(np.diag(stratum_cov) < 0)):
        raise IntegrityError("invalid statistical outputs")
    diagnostics = dict(n=n, p=p, psus=g, strata=len(set(design.strata)), rank=int(rank),
                       raw_weight_sum=float(design.raw_weight.sum()), analysis_weight_sum=float(a.sum()),
                       weighted_outcome_mean=float(np.average(y, weights=a)),
                       kish_weight_concentration_n=float(a.sum() ** 2 / (a @ a)),
                       weighted_sse=float(np.sum(a * residuals ** 2)),
                       condition_number=float(singular_values[0] / singular_values[-1]))
    return Fit(beta, cluster_cov, stratum_cov, predictions, residuals, diagnostics)


def export_fit(directory: Path, prefix: str, design: Design, result: Fit) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    write_rows(directory / f"{prefix}_design.csv", DESIGN_FIELDS, design.rows())
    write_rows(directory / f"{prefix}_coefficients.csv", COEFFICIENT_FIELDS,
               [dict(feature=feature, estimate=float(result.beta[i]),
                     se_cluster=float(np.sqrt(result.cluster_cov[i, i])),
                     se_stratum=float(np.sqrt(result.stratum_cov[i, i]))) for i, feature in enumerate(FEATURES)])
    write_rows(directory / f"{prefix}_covariance.csv", COVARIANCE_FIELDS,
               [dict(row_feature=row, column_feature=column, cluster_cov=float(result.cluster_cov[i, j]),
                     stratum_cov=float(result.stratum_cov[i, j]))
                for i, row in enumerate(FEATURES) for j, column in enumerate(FEATURES)])
    write_rows(directory / f"{prefix}_predictions.csv", PREDICTION_FIELDS,
               [dict(record_id=record_id, prediction=float(result.predictions[i]), residual=float(result.residuals[i]))
                for i, record_id in enumerate(design.ids)])
    write_rows(directory / f"{prefix}_diagnostics.csv", DIAGNOSTIC_FIELDS,
               [dict(name=name, value=value) for name, value in sorted(result.diagnostics.items())])
