import sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"src"))
from navigation_engineering.analytics import weighted_summary, overall_weighted_attainment
from navigation_engineering.contracts import read_csv
class AnalyticsTest(unittest.TestCase):
    def setUp(self): self.rows=read_csv(ROOT/"data/synthetic/encounters.csv")
    def test_two_groups(self): self.assertEqual(len(weighted_summary(self.rows)),2)
    def test_rates_bounded(self):
        for r in weighted_summary(self.rows): self.assertTrue(0 <= r["weighted_attainment_rate"] <= 1)
    def test_overall_bounded(self): self.assertTrue(0 <= overall_weighted_attainment(self.rows) <= 1)
if __name__=="__main__": unittest.main()
