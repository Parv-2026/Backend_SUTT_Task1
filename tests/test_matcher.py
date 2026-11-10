import json
import tempfile
import unittest
from pathlib import Path
from models import Cab
from matcher import CabPoolMatcher


class MatcherTests(unittest.TestCase):
    def setUp(self):
        self.app = CabPoolMatcher([Cab('A', 2, 'Delhi', 'Morning'),
                                   Cab('B', 1, 'Delhi', 'Morning'),
                                   Cab('C', 4, 'Jaipur', 'Night')])

    def test_seniority_and_fifo(self):
        for name, year in [('junior', 1), ('senior-first', 5), ('senior-second', 5), ('third', 3)]:
            self.app.add_request(name, 'Delhi', 'Morning', year)
        cab, _ = self.app.dispatch('Delhi', 'Morning')
        self.assertEqual([r.name for r in cab.passengers], ['senior-first', 'senior-second'])
        self.assertEqual([r.name for r in self.app.waiting('Delhi', 'Morning')], ['third', 'junior'])

    def test_preview_is_pure_and_reserves_across_cabs(self):
        for name in ['a', 'b', 'c', 'd']:
            self.app.add_request(name, 'Delhi', 'Morning', 3)
        before = [r.name for r in self.app.waiting('Delhi', 'Morning')]
        preview = self.app.preview()
        self.assertEqual([[r.name for r in p] for _, _, p in preview], [['a', 'b'], ['c'], []])
        self.assertEqual(before, [r.name for r in self.app.waiting('Delhi', 'Morning')])
        self.assertFalse(any(c.departed for c in self.app.cabs))

    def test_empty_queue_does_not_dispatch(self):
        cab, _ = self.app.dispatch('Delhi', 'Morning')
        self.assertIsNone(cab)
        self.assertFalse(self.app.cabs[0].departed)

    def test_half_empty_and_no_open_cabs(self):
        self.app.add_request('only', 'Delhi', 'Morning', 2)
        cab, _ = self.app.dispatch('Delhi', 'Morning')
        self.assertEqual(len(cab.passengers), 1)
        self.assertTrue(cab.departed)
        self.app.add_request('next', 'Delhi', 'Morning', 1)
        self.app.dispatch('Delhi', 'Morning')
        self.app.add_request('still-waiting', 'Delhi', 'Morning', 5)
        cab, message = self.app.dispatch('Delhi', 'Morning')
        self.assertIsNone(cab)
        self.assertIn('No open cab', message)
        self.assertEqual([r.name for r in self.app.waiting('Delhi', 'Morning')], ['still-waiting'])

    def test_validation(self):
        for args in [('', 'Delhi', 'Morning', 2), ('x', 'Mumbai', 'Morning', 2),
                     ('x', 'Delhi', 'Dawn', 2), ('x', 'Delhi', 'Morning', 7)]:
            with self.assertRaises(ValueError):
                self.app.add_request(*args)
        self.assertEqual(self.app.next_sequence, 0)

    def test_restore_queue_order_and_departures(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'state.json'
            app = CabPoolMatcher([Cab('A', 1, 'Delhi', 'Morning')], path)
            app.add_request('first', 'Delhi', 'Morning', 3)
            app.add_request('second', 'Delhi', 'Morning', 3)
            app.add_request('senior', 'Delhi', 'Morning', 5)
            app.dispatch('Delhi', 'Morning')
            restored = CabPoolMatcher([Cab('sample', 2, 'Jaipur', 'Night')], path)
            self.assertIn('successfully', restored.load())
            self.assertTrue(restored.cabs[0].departed)
            self.assertEqual(restored.cabs[0].passengers[0].name, 'senior')
            self.assertEqual([r.name for r in restored.waiting()], ['first', 'second'])
            restored.add_request('third', 'Delhi', 'Morning', 3)
            self.assertEqual([r.name for r in restored.waiting()], ['first', 'second', 'third'])

    def test_missing_and_corrupt_save(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'state.json'
            app = CabPoolMatcher([Cab('A', 2, 'Delhi', 'Morning')], path)
            self.assertIn('No saved state', app.load())
            path.write_text('{not json', encoding='utf-8')
            self.assertIn('Starting fresh', app.load())
            self.assertEqual(len(app.cabs), 1)

    def test_duplicate_sequence_save_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'state.json'
            app = CabPoolMatcher([Cab('A', 2, 'Delhi', 'Morning')], path)
            app.add_request('one', 'Delhi', 'Morning', 1)
            data = json.loads(path.read_text())
            data['waiting'].append(dict(data['waiting'][0]))
            path.write_text(json.dumps(data))
            restored = CabPoolMatcher([Cab('Fresh', 1, 'Jaipur', 'Night')], path)
            self.assertIn('Starting fresh', restored.load())
            self.assertEqual(restored.cabs[0].driver, 'Fresh')


if __name__ == '__main__':
    unittest.main()
