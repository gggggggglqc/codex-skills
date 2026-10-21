import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import no_order_return_reconcile as module
from fms_source_reconcile import FmsDataset, get_fms_dataset


class SnapshotScopeTest(unittest.TestCase):
    def test_different_period_cannot_reuse_previous_month_snapshot(self):
        dataset = FmsDataset("no_order_return")
        self.addCleanup(dataset.close)
        conn = SimpleNamespace(_fms_source_dataset=(("no_order_return", "2026-09-01 00:00:00", "2026-09-30 23:59:59", None), dataset))
        with self.assertRaises(ValueError):
            get_fms_dataset(conn, module, "no_order_return", "2026-08-01 00:00:00", "2026-08-31 23:59:59")


if __name__ == "__main__":
    unittest.main()
