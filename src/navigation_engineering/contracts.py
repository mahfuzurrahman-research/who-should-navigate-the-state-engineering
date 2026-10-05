from __future__ import annotations
import csv
import math
from pathlib import Path

REQUIRED_ENCOUNTER_COLUMNS = {"encounter_id","region","stratum_id","psu_id","service_type","redirect_flag","attained_flag","weight"}
REQUIRED_PSU_COLUMNS = {"psu_id", "stratum_id", "region"}

class ContractError(ValueError):
    pass

def read_csv(path: Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def validate(encounters: list[dict[str, str]], registry: list[dict[str, str]]) -> dict:
    if not encounters:
        raise ContractError("encounters are empty")
    if not registry:
        raise ContractError("registry is empty")
    if any(set(row) != REQUIRED_ENCOUNTER_COLUMNS for row in encounters):
        raise ContractError("encounter schema mismatch")
    if any(set(row) != REQUIRED_PSU_COLUMNS for row in registry):
        raise ContractError("registry schema mismatch")
    encounter_ids = [r["encounter_id"] for r in encounters]
    if len(encounter_ids) != len(set(encounter_ids)):
        raise ContractError("duplicate encounter_id")
    psu_ids = [r["psu_id"] for r in registry]
    if len(psu_ids) != len(set(psu_ids)):
        raise ContractError("duplicate registry psu_id")
    registry_map = {r["psu_id"]: r for r in registry}
    for row in encounters:
        if row["psu_id"] not in registry_map:
            raise ContractError("unknown psu_id")
        if row["stratum_id"] != registry_map[row["psu_id"]]["stratum_id"]:
            raise ContractError("stratum mismatch")
        if row["region"] != registry_map[row["psu_id"]]["region"]:
            raise ContractError("region mismatch")
        if row["redirect_flag"] not in {"0", "1"}:
            raise ContractError("invalid redirect_flag")
        if row["attained_flag"] not in {"0", "1"}:
            raise ContractError("invalid attained_flag")
        if not row["service_type"]:
            raise ContractError("missing service_type")
        if not row["region"] or not row["stratum_id"]:
            raise ContractError("missing design field")
        try:
            weight = float(row["weight"])
        except (ValueError, TypeError) as exc:
            raise ContractError("invalid weight") from exc
        if not math.isfinite(weight) or weight <= 0:
            raise ContractError("nonfinite or nonpositive weight")
    return {"status":"PASS","encounters":len(encounters),"psus":len(registry),"strata":len({r["stratum_id"] for r in registry}),"regions":len({r["region"] for r in registry})}
