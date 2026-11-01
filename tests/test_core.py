import tempfile
import unittest
from pathlib import Path
from binpulse.core import connect, initialize, record, snapshot, pending, mark_synced, simulate, status, fill_from_distance

class BinPulseTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.db=connect(Path(self.tmp.name)/'test.db');initialize(self.db)
    def tearDown(self):self.db.close();self.tmp.cleanup()
    def test_seed(self):self.assertEqual(len(snapshot(self.db)),5)
    def test_fill_conversion(self):self.assertEqual(fill_from_distance(25),75)
    def test_fill_invalid(self):
        with self.assertRaises(ValueError):fill_from_distance(-1)
    def test_status(self):self.assertEqual([status(i) for i in (10,75,95)],['normal','collect','critical'])
    def test_store(self):
        record(self.db,'BIN-101',95,50)
        self.assertEqual(snapshot(self.db)[0]['status'],'critical')
    def test_invalid_fill(self):
        with self.assertRaises(ValueError):record(self.db,'BIN-101',110)
    def test_unknown_bin(self):
        with self.assertRaises(ValueError):record(self.db,'BAD',50)
    def test_pending_queue(self):
        id=record(self.db,'BIN-101',30)
        self.assertEqual(len(pending(self.db)),1)
        mark_synced(self.db,[id]);self.assertEqual(pending(self.db),[])
    def test_simulation(self):
        self.assertEqual(len(simulate(self.db,seed=1)),5)
        self.assertEqual(len(pending(self.db)),5)
    def test_unmodified_history(self):
        record(self.db,'BIN-101',20);record(self.db,'BIN-101',90)
        self.assertEqual(snapshot(self.db)[0]['fill_pct'],90)
        self.assertEqual(len(pending(self.db)),2)

if __name__=='__main__':unittest.main()
