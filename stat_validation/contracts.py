from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
import re

import numpy as np

from .io import object_hash, read_rows

ROOT = Path(__file__).resolve().parents[1]
FEATURES = ["intercept", "redirect_flag", "complexity", "assist_flag",
            "redirect_x_complexity", "service_B", "service_C"]
OBS_FIELDS = ["record_id", "psu_id", "stratum_id", "service_type", "redirect_flag",
              "complexity", "assist_flag", "outcome", "synthetic_record"]
WEIGHT_FIELDS = ["record_id", "weight", "synthetic_record"]
PSU_FIELDS = ["psu_id", "stratum_id", "synthetic_record"]
DESIGN_FIELDS = ["record_id", "psu_id", "stratum_id", "raw_weight", "analysis_weight",
                 "outcome", *FEATURES]


class IntegrityError(ValueError):
    """A public input or statistical artifact violated the declared protocol."""


def finite_number(value: object, field: str) -> float:
    if isinstance(value, (bool, np.bool_)):
        raise IntegrityError(f"boolean is not a numeric {field}")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise IntegrityError(f"invalid numeric {field}") from exc
    if not math.isfinite(number):
        raise IntegrityError(f"nonfinite {field}")
    return number


def load_policy(path: Path | None = None) -> dict:
    policy = json.loads((path or ROOT / "contracts/statistical_contract.json").read_text())
    return validate_policy(policy)


def validate_policy(policy: dict) -> dict:
    required = {"protocol", "seed", "synthetic_only", "private_data_used", "scientific_results_claimed",
                "service_levels", "service_reference", "features", "weight_semantics",
                "weight_normalization", "covariance", "absolute_tolerance", "relative_tolerance",
                "condition_limit", "generation"}
    if set(policy) != required:
        raise IntegrityError("statistical policy schema mismatch")
    fixed = {"protocol": "synthetic-wls-v1", "service_levels": ["A", "B", "C"],
             "service_reference": "A", "features": FEATURES,
             "weight_semantics": "synthetic positive relative analysis weights",
             "weight_normalization": "raw_weight / mean(raw_weight)",
             "covariance": ["psu_cluster_CR1", "stratum_centered_scores"]}
    if any(policy[key] != value for key, value in fixed.items()):
        raise IntegrityError("unsupported feature, weight, or covariance policy")
    if (policy["synthetic_only"] is not True or policy["private_data_used"] is not False
            or policy["scientific_results_claimed"] is not False):
        raise IntegrityError("synthetic-only claim boundary violated")
    for field in ("absolute_tolerance", "relative_tolerance", "condition_limit"):
        if finite_number(policy[field], field) <= 0:
            raise IntegrityError(f"nonpositive policy {field}")
    if policy["condition_limit"] <= 1:
        raise IntegrityError("condition limit must exceed one")
    if type(policy["seed"]) is not int or policy["seed"] < 0:
        raise IntegrityError("invalid generator seed")
    generation = policy["generation"]
    if not isinstance(generation, dict) or set(generation) != {"strata", "psus_per_stratum", "rows_per_psu"}:
        raise IntegrityError("generator schema mismatch")
    for field, lower in (("strata", 1), ("psus_per_stratum", 2), ("rows_per_psu", 8)):
        if type(generation[field]) is not int or generation[field] < lower:
            raise IntegrityError(f"invalid generator {field}")
    return policy


def _schema(rows: list[dict], fields: list[str], table: str) -> None:
    if not rows:
        raise IntegrityError(f"empty {table}")
    for row in rows:
        if set(row) != set(fields):
            raise IntegrityError(f"{table} schema mismatch")
        if row["synthetic_record"] != "true":
            raise IntegrityError(f"{table} requires explicit synthetic marker")


def _identifier(value: object, field: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", value):
        raise IntegrityError(f"invalid {field}")
    return value


def _index(rows: list[dict], key: str) -> dict[str, dict]:
    indexed = {}
    for row in rows:
        value = _identifier(row[key], key)
        if value in indexed:
            raise IntegrityError(f"duplicate {key}")
        indexed[value] = row
    return indexed


@dataclass
class Design:
    observations: list[dict]
    weights: list[dict]
    registry: list[dict]
    x: np.ndarray
    y: np.ndarray
    raw_weight: np.ndarray
    analysis_weight: np.ndarray
    ids: list[str]
    psus: list[str]
    strata: list[str]
    policy: dict

    def rows(self) -> list[dict]:
        return [dict(record_id=self.ids[i], psu_id=self.psus[i], stratum_id=self.strata[i],
                     raw_weight=float(self.raw_weight[i]), analysis_weight=float(self.analysis_weight[i]),
                     outcome=float(self.y[i]), **dict(zip(FEATURES, map(float, self.x[i]))))
                for i in range(len(self.ids))]

    def manifest(self) -> dict:
        return {"protocol": self.policy["protocol"], "features": FEATURES,
                "reference_service": "A", "row_ids": self.ids,
                "source_hash": object_hash({"observations": self.observations,
                                            "weights": self.weights, "registry": self.registry}),
                "policy_hash": object_hash(self.policy), "design_hash": object_hash(self.rows()),
                "rows": len(self.ids), "psus": len(set(self.psus)), "strata": len(set(self.strata))}


def build_design(observations: list[dict], weights: list[dict], registry: list[dict],
                 policy: dict | None = None) -> Design:
    policy = validate_policy(policy) if policy is not None else load_policy()
    _schema(observations, OBS_FIELDS, "observations")
    _schema(weights, WEIGHT_FIELDS, "weights")
    _schema(registry, PSU_FIELDS, "registry")
    obs_by_id = _index(observations, "record_id")
    weight_by_id = _index(weights, "record_id")
    psu_by_id = _index(registry, "psu_id")
    if set(obs_by_id) != set(weight_by_id):
        raise IntegrityError("weight join must be exactly one-to-one by record_id")
    strata_by_psu = {key: _identifier(row["stratum_id"], "stratum_id") for key, row in psu_by_id.items()}
    stratum_counts = {}
    for stratum in strata_by_psu.values():
        stratum_counts[stratum] = stratum_counts.get(stratum, 0) + 1
    if any(count < 2 for count in stratum_counts.values()):
        raise IntegrityError("at least two PSUs per stratum required; no lonely-PSU fallback")
    parsed_obs, parsed_weights, x, y, raw_weight, ids, psus, strata = [], [], [], [], [], [], [], []
    for record_id in sorted(obs_by_id):
        row, weight_row = obs_by_id[record_id], weight_by_id[record_id]
        psu = _identifier(row["psu_id"], "psu_id")
        stratum = _identifier(row["stratum_id"], "stratum_id")
        if psu not in strata_by_psu or strata_by_psu[psu] != stratum:
            raise IntegrityError("PSU registry or stratum nesting mismatch")
        if row["service_type"] not in policy["service_levels"]:
            raise IntegrityError("unknown service category")
        redirect = finite_number(row["redirect_flag"], "redirect_flag")
        assist = finite_number(row["assist_flag"], "assist_flag")
        if redirect not in (0.0, 1.0) or assist not in (0.0, 1.0):
            raise IntegrityError("flags must be binary")
        complexity = finite_number(row["complexity"], "complexity")
        outcome = finite_number(row["outcome"], "outcome")
        weight = finite_number(weight_row["weight"], "weight")
        if weight <= 0:
            raise IntegrityError("weights must be strictly positive")
        parsed_obs.append({**row, "redirect_flag": redirect, "assist_flag": assist,
                           "complexity": complexity, "outcome": outcome})
        parsed_weights.append({**weight_row, "weight": weight})
        x.append([1.0, redirect, complexity, assist, redirect * complexity,
                  float(row["service_type"] == "B"), float(row["service_type"] == "C")])
        y.append(outcome)
        raw_weight.append(weight)
        ids.append(record_id)
        psus.append(psu)
        strata.append(stratum)
    if set(psus) != set(psu_by_id):
        raise IntegrityError("registry contains unused PSUs")
    if {row["service_type"] for row in parsed_obs} != set(policy["service_levels"]):
        raise IntegrityError("all declared service levels must be represented")
    w = np.asarray(raw_weight)
    with np.errstate(over="ignore", invalid="ignore", under="ignore"):
        a = w / w.mean()
        total = w.sum()
    if not np.isfinite(total) or not np.all(np.isfinite(a)) or np.any(a <= 0):
        raise IntegrityError("unsafe weight normalization")
    design = Design(parsed_obs, parsed_weights, [psu_by_id[key] for key in sorted(psu_by_id)],
                    np.asarray(x), np.asarray(y), w, a, ids, psus, strata, policy)
    wx = np.sqrt(a)[:, None] * design.x
    if len(ids) <= len(FEATURES) or np.linalg.matrix_rank(wx) != len(FEATURES):
        raise IntegrityError("rank-deficient design or insufficient residual degrees of freedom")
    if np.linalg.cond(wx) > policy["condition_limit"]:
        raise IntegrityError("ill-conditioned weighted design")
    return design


def read_design(directory: Path, policy: dict | None = None) -> Design:
    return build_design(read_rows(directory / "observations.csv"), read_rows(directory / "weights.csv"),
                        read_rows(directory / "psu_registry.csv"), policy)


def verify_frozen_design(path: Path, design: Design, manifest: dict) -> None:
    # Exact hashes protect feature order and retained raw weights, not just numerical closeness.
    if manifest != design.manifest():
        raise IntegrityError("source, feature, weight, or policy manifest changed")
    actual = read_rows(path)
    if not actual or list(actual[0]) != DESIGN_FIELDS or len(actual) != len(design.ids):
        raise IntegrityError("frozen design schema/order mismatch")
    parsed = []
    for row in actual:
        parsed.append({field: row[field] if field in ("record_id", "psu_id", "stratum_id")
                       else finite_number(row[field], field) for field in DESIGN_FIELDS})
    if object_hash(parsed) != manifest["design_hash"]:
        raise IntegrityError("frozen feature or weight values changed")
