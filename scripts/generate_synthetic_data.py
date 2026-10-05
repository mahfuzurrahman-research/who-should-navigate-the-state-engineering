from __future__ import annotations
import csv
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "synthetic"
DATA.mkdir(parents=True, exist_ok=True)
registry=[]; encounters=[]; encounter_id=1
for region in range(1,4):
    for stratum_local in range(1,3):
        stratum=f"R{region}-S{stratum_local}"
        for psu_local in range(1,5):
            psu=f"{stratum}-P{psu_local}"
            registry.append({"psu_id":psu,"stratum_id":stratum,"region":f"R{region}"})
            for j in range(8):
                service=["A","B","C"][j%3]
                redirect=(region+stratum_local+psu_local+j)%2
                attained=1 if ((region*7+psu_local*3+j+redirect)%7) not in {0,1} else 0
                weight=1.0+region*0.25+stratum_local*0.1+psu_local*0.03+j*0.01
                encounters.append({"encounter_id":f"E{encounter_id:04d}","region":f"R{region}","stratum_id":stratum,"psu_id":psu,"service_type":service,"redirect_flag":redirect,"attained_flag":attained,"weight":f"{weight:.4f}"})
                encounter_id+=1
with (DATA/"psu_registry.csv").open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=["psu_id","stratum_id","region"]); w.writeheader(); w.writerows(registry)
with (DATA/"encounters.csv").open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=["encounter_id","region","stratum_id","psu_id","service_type","redirect_flag","attained_flag","weight"]); w.writeheader(); w.writerows(encounters)
print(f"SYNTHETIC_ENCOUNTERS={len(encounters)}")
print(f"SYNTHETIC_PSUS={len(registry)}")
