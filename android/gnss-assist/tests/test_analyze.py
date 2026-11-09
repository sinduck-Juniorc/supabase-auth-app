import importlib.util,json,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('analyze',Path(__file__).resolve().parents[1]/'tools/analyze.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
class AnalyzeTest(unittest.TestCase):
    def read(self, rows):
        # 단위 검사 전용 합성 입력. 실물 TTFF 데이터가 아니다.
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'test.jsonl';p.write_text('\n'.join(json.dumps(r) for r in rows));return a.read_trials(p)
    def test_interruptions_remain_in_denominator(self):
        rows=self.read([dict(event='trial_start',trial_id='test',mode='baseline')]);self.assertEqual(rows[0]['reason'],'interrupted_no_end');self.assertFalse(rows[0]['eligible_first_fix'])
    def test_invalid_time_duplicate_and_empty(self):
        start=dict(event='trial_start',trial_id='test',mode='baseline')
        for rows in [[],[start,start],[start,dict(event='trial_end',trial_id='test',mode='baseline',engine_ttff_ms=True)]]:
            with self.assertRaises(ValueError):self.read(rows)
    def test_mock_not_counted(self):
        rows=self.read([dict(event='trial_start',trial_id='test',mode='baseline'),dict(event='trial_end',trial_id='test',mode='baseline',reason='first_fix',eligible_first_fix=True,mock_seen=True,log_failed=False,engine_started_observed=True,engine_ttff_ms=100,request_to_gps_ms=110)]);self.assertFalse(rows[0]['eligible_first_fix'])
if __name__=='__main__':unittest.main()
