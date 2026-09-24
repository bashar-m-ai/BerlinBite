import unittest
from datetime import datetime
from backend.app.scoring import crowd_estimate

class CrowdTests(unittest.TestCase):
    def test_berlin_timezone_not_server_timezone(self):
        result=crowd_estimate(datetime.fromisoformat('2026-09-25T17:00:00+00:00'))
        self.assertEqual(result['label'],'Busy')
        self.assertIn('Friday or Saturday',result['basis'])
    def test_off_peak(self):
        result=crowd_estimate(datetime.fromisoformat('2026-09-24T08:00:00+00:00'))
        self.assertEqual(result['label'],'Quiet')
        self.assertIn('not live occupancy',result['disclaimer'])
    def test_same_instant_same_result(self):
        self.assertEqual(crowd_estimate(datetime.fromisoformat('2026-09-25T17:00:00+00:00')),crowd_estimate(datetime.fromisoformat('2026-09-25T19:00:00+02:00')))
if __name__=='__main__': unittest.main()
