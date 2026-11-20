import tempfile
import unittest
from pathlib import Path
from shift_log import load, status, summarize, render

class ShiftTests(unittest.TestCase):
    def read(self, content):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'test.csv'
            p.write_text(content, encoding='utf-8')
            return load(p)
    def test_demo_counts(self):
        self.assertEqual(summarize(load('examples/checks.csv')), dict(total=4,checked=1,follow_up=2,incomplete=1,failed_without_ticket=1))
    def test_all_pass(self):
        self.assertEqual(status(dict(live='pass',playback='pass',image='pass')), 'checked')
    def test_fail_dominates_unchecked(self):
        self.assertEqual(status(dict(live='fail',playback='unchecked',image='pass')), 'follow_up')
    def test_incomplete(self):
        self.assertEqual(status(dict(live='pass',playback='unchecked',image='pass')), 'incomplete')
    def test_html_escape(self):
        rows=load('examples/checks.csv'); rows[0]['action']='<script>alert(1)</script>'
        self.assertNotIn('<script>',render(rows)); self.assertIn('&lt;script&gt;',render(rows))
    def test_bad_inputs(self):
        header='camera_id,live,playback,image,ticket,action\n'
        for content in [header, 'wrong\n',header+'CAM-001,ok,pass,pass,,x\n',header+'real-site,pass,pass,pass,,x\n',header+'CAM-001,pass,pass,pass,real,x\n',header+('CAM-001,pass,pass,pass,,x\n'*2),header+'CAM-001,pass\n',header+'CAM-001,pass,pass,pass,,x,extra\n']:
            with self.subTest(content=content):
                with self.assertRaises(ValueError): self.read(content)

if __name__=='__main__': unittest.main()
