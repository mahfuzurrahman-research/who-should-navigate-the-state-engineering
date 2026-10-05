from __future__ import annotations

from pathlib import Path

import numpy as np

from .contracts import OBS_FIELDS, PSU_FIELDS, WEIGHT_FIELDS, load_policy, validate_policy
from .io import write_rows


def synthetic_tables(policy: dict | None = None) -> tuple[list[dict], list[dict], list[dict]]:
    """Fabricate every value here; no data access or private variable mapping."""
    policy = validate_policy(policy) if policy is not None else load_policy()
    rng = np.random.default_rng(policy["seed"])
    cfg = policy["generation"]
    observations, weights, registry = [], [], []
    for s in range(cfg["strata"]):
        stratum_id = f"STR{s:03d}"
        for g in range(cfg["psus_per_stratum"]):
            psu_id = f"PSU{s * cfg['psus_per_stratum'] + g:03d}"
            registry.append(dict(psu_id=psu_id, stratum_id=stratum_id, synthetic_record="true"))
            cluster_offset = rng.normal(0, 0.8)
            for j in range(cfg["rows_per_psu"]):
                record_id = f"OBS{len(observations):06d}"
                service = ("A", "B", "C")[j % 3]
                redirect, assist = map(int, rng.integers(0, 2, size=2))
                complexity = round(float(rng.uniform(0.1, 5.0)), 6)
                outcome = (4.0 - 0.7 * redirect + 0.45 * complexity + 0.9 * assist
                           - 0.2 * redirect * complexity + {"A": 0.0, "B": 0.3, "C": -0.4}[service]
                           + cluster_offset + rng.normal(0, 0.6))
                observations.append(dict(record_id=record_id, psu_id=psu_id, stratum_id=stratum_id,
                                         service_type=service, redirect_flag=redirect, complexity=complexity,
                                         assist_flag=assist, outcome=round(float(outcome), 6), synthetic_record="true"))
                weights.append(dict(record_id=record_id, weight=round(float(rng.uniform(0.4, 4.0)), 6),
                                    synthetic_record="true"))
    return observations, weights, registry


def generate(directory: Path, policy: dict | None = None) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    observations, weights, registry = synthetic_tables(policy)
    write_rows(directory / "observations.csv", OBS_FIELDS, observations)
    write_rows(directory / "weights.csv", WEIGHT_FIELDS, weights)
    write_rows(directory / "psu_registry.csv", PSU_FIELDS, registry)
