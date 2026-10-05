from __future__ import annotations
from collections import defaultdict

def weighted_summary(rows: list[dict[str, str]]) -> list[dict]:
    acc = defaultdict(lambda: {"weighted_total": 0.0, "weighted_attained": 0.0, "n": 0})
    for row in rows:
        key = int(row["redirect_flag"]); w = float(row["weight"]); y = int(row["attained_flag"])
        acc[key]["weighted_total"] += w
        acc[key]["weighted_attained"] += w * y
        acc[key]["n"] += 1
    out = []
    for key in sorted(acc):
        total = acc[key]["weighted_total"]
        out.append({"redirect_flag":key,"n":acc[key]["n"],"weighted_total":total,"weighted_attained":acc[key]["weighted_attained"],"weighted_attainment_rate":acc[key]["weighted_attained"] / total})
    return out

def overall_weighted_attainment(rows: list[dict[str, str]]) -> float:
    total = sum(float(r["weight"]) for r in rows)
    attained = sum(float(r["weight"]) * int(r["attained_flag"]) for r in rows)
    return attained / total
