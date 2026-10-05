import copy, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"src"))
from navigation_engineering.contracts import ContractError, read_csv, validate
class ContractsTest(unittest.TestCase):
    def setUp(self): self.enc=read_csv(ROOT/"data/synthetic/encounters.csv"); self.reg=read_csv(ROOT/"data/synthetic/psu_registry.csv")
    def test_valid(self): self.assertEqual(validate(self.enc,self.reg)["status"],"PASS")
    def test_bad_redirect_fails(self):
        x=copy.deepcopy(self.enc); x[0]["redirect_flag"]="9"
        with self.assertRaises(ContractError): validate(x,self.reg)
    def test_nonpositive_weight_fails(self):
        x=copy.deepcopy(self.enc); x[0]["weight"]="0"
        with self.assertRaises(ContractError): validate(x,self.reg)
    def test_unknown_psu_fails(self):
        x=copy.deepcopy(self.enc); x[0]["psu_id"]="UNKNOWN"
        with self.assertRaises(ContractError): validate(x,self.reg)
if __name__=="__main__": unittest.main()
