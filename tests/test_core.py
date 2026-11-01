import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'plugin'))

from core import ReadTracker, annots_key, needs_scan  # noqa: E402

A = '/lib/Au/A (1)/A.epub'
B = '/lib/Au/B (2)/B.epub'
KA, KB = annots_key(A), annots_key(B)
BOOKS = {KA: 1, KB: 2}


class ReadTrackerTest(unittest.TestCase):
    def setUp(self):
        self.t = ReadTracker()

    def test_first_poll_backfills_and_resorts(self):
        p = self.t.poll({KA: 100.0, KB: 200.0}, BOOKS)
        self.assertEqual(p.updates, ((1, 100.0), (2, 200.0)))
        self.assertTrue(p.resort)

    def test_first_poll_resorts_even_when_empty(self):
        self.assertTrue(self.t.poll({}, BOOKS).resort)

    def test_unchanged_is_quiet(self):
        self.t.poll({KA: 100.0}, BOOKS)
        p = self.t.poll({KA: 100.0}, BOOKS)
        self.assertEqual((p.updates, p.resort), ((), False))

    def test_page_turn_updates_and_resorts(self):
        self.t.poll({KA: 100.0, KB: 200.0}, BOOKS)
        p = self.t.poll({KA: 300.0, KB: 200.0}, BOOKS)
        self.assertEqual((p.updates, p.resort), (((1, 300.0),), True))

    def test_unknown_key_is_retried_after_it_resolves(self):
        self.t.poll({KA: 100.0}, {})
        p = self.t.poll({KA: 100.0}, BOOKS)
        self.assertEqual(p.updates, ((1, 100.0),))
        self.assertTrue(p.resort)

    def test_page_turns_in_top_book_do_not_resort(self):
        self.t.poll({KA: 100.0, KB: 200.0}, BOOKS)
        self.assertTrue(self.t.poll({KA: 300.0, KB: 200.0}, BOOKS).resort)
        p = self.t.poll({KA: 310.0, KB: 200.0}, BOOKS)
        self.assertEqual((p.updates, p.resort), (((1, 310.0),), False))

    def test_two_formats_keep_newest(self):
        k2 = annots_key('/lib/Au/A (1)/A.pdf')
        p = self.t.poll({KA: 100.0, k2: 150.0}, {KA: 1, k2: 1})
        self.assertEqual(p.updates, ((1, 150.0),))

    def test_reset_backfills_again(self):
        self.t.poll({KA: 100.0}, BOOKS)
        self.t.reset()
        p = self.t.poll({KA: 100.0}, BOOKS)
        self.assertEqual(p.updates, ((1, 100.0),))


class NeedsScanTest(unittest.TestCase):
    def test_first_scan(self):
        self.assertTrue(needs_scan({}, {}, 0.0, 1000.0))

    def test_cooldown(self):
        self.assertFalse(needs_scan({KA: 995.0}, {}, 970.0, 1000.0))

    def test_old_unknown_keys_do_not_trigger(self):
        self.assertFalse(needs_scan({KA: 1.0}, {}, 100.0, 1000.0))

    def test_recent_unknown_key_triggers(self):
        self.assertTrue(needs_scan({KA: 990.0}, {}, 100.0, 1000.0))

    def test_recent_known_key_does_not(self):
        self.assertFalse(needs_scan({KA: 990.0}, {KA: 1}, 100.0, 1000.0))


if __name__ == '__main__':
    unittest.main()
