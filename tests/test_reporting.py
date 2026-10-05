import subprocess, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class ReportingTest(unittest.TestCase):
    def test_python_summary_runs(self):
        run=subprocess.run([sys.executable,"scripts/run_python_summary.py"],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr); self.assertTrue((ROOT/"outputs/python_summary.csv").exists())
if __name__=="__main__": unittest.main()
