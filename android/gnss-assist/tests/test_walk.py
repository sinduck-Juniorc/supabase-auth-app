import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from validate_walk import validate
class WalkTest(unittest.TestCase):
 def sample(self):
  return [dict(event=n,session_id='fixture',elapsed_ms=i*1000,wall_utc_ms=10000+i*1000,cleanup_success=True) for i,n in enumerate(['observation_start','outdoor_location_ready','indoor_arrival','observation_end'])]
 def test_no_indoor_sample_is_not_proof(self):
  r=validate(self.sample())[0];self.assertTrue(r['structurally_valid']);self.assertIn('실내 통신 표본 없음',r['warnings']);self.assertFalse(r['acceleration_proven'])
 def test_missing_end(self):self.assertFalse(validate(self.sample()[:-1])[0]['structurally_valid'])
 def test_clock_reversal(self):
  r=self.sample();r[2]['elapsed_ms']=-1;self.assertFalse(validate(r)[0]['structurally_valid'])
 def test_duplicate_sequence(self):
  r=self.sample()
  for e in r:e['sequence']=1
  self.assertFalse(validate(r)[0]['structurally_valid'])
 def test_empty(self):
  with self.assertRaises(ValueError):validate([])
