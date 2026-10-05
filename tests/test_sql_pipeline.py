import os, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"src")); os.chdir(ROOT)
try: import duckdb
except Exception: duckdb=None
@unittest.skipIf(duckdb is None,"duckdb unavailable")
class SQLPipelineTest(unittest.TestCase):
    def test_quality_passes(self):
        from navigation_engineering.sql_pipeline import build, validate
        with tempfile.TemporaryDirectory() as td:
            con=build(ROOT,Path(td)/"demo.duckdb"); summary=validate(con)
            self.assertEqual(summary["total_checks"],15); self.assertEqual(summary["failed_checks"],0); self.assertEqual(summary["overall_status"],"PASS"); con.close()
    def test_marts_exist(self):
        from navigation_engineering.sql_pipeline import build
        with tempfile.TemporaryDirectory() as td:
            con=build(ROOT,Path(td)/"demo.duckdb"); self.assertEqual(con.execute("SELECT COUNT(*) FROM mart.attainment_summary").fetchone()[0],2); self.assertEqual(con.execute("SELECT COUNT(*) FROM mart.service_summary").fetchone()[0],6); con.close()
if __name__=="__main__": unittest.main()
