"""Own synthetic scanner/guard tests, no OEM data or external engine."""
import sys
from dataclasses import dataclass
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from ep7_t27_placement_review import all_relative_candidates, remove_regions


@dataclass(frozen=True)
class Region:
    name: str
    address: int
    data: bytes
    permissions: str = 'r'
    capture: bool = False
    alias_of: str | None = None


class PlacementChecks(unittest.TestCase):
    def test_first_range_empty_does_not_discard_last_range_hit(self):
        ranges = [(10,20), (30,40), (50,60)]
        hit = {'site': 'synthetic', 'target': 55}
        def scanner(data, base, provided):
            self.assertEqual(provided, ranges)
            return [[], [], [hit]]
        self.assertEqual(all_relative_candidates(scanner, b'own', ranges), [hit])

    def test_scanner_dimensions_fail_closed(self):
        with self.assertRaisesRegex(ValueError, 'dimensions'):
            all_relative_candidates(lambda *args: [[]], b'own', [(1,2),(3,4)])

    def test_guard_removes_all_access_and_preserves_coherent_alias_parts(self):
        data = bytes(range(16))
        regions = [Region('ram', 0x1000, data, 'rwx', True),
                   Region('alias', 0x2000, data, 'rwx', False, 'ram')]
        guarded = remove_regions(regions, [(0x1004,0x100C),(0x2004,0x200C)])
        self.assertEqual([(r.address,len(r.data)) for r in guarded],
                         [(0x1000,4),(0x100C,4),(0x2000,4),(0x200C,4)])
        for at in (*range(0x1004,0x100C), *range(0x2004,0x200C)):
            self.assertFalse(any(r.address <= at < r.address+len(r.data) for r in guarded))
        names = {r.name:r for r in guarded}
        for r in guarded:
            if r.alias_of:
                self.assertEqual(r.data, names[r.alias_of].data)
                self.assertEqual(r.permissions, 'rwx')


if __name__ == '__main__':
    unittest.main()
