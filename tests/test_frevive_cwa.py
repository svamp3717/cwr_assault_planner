"""Guard against Arma-only array lookup and stale timers in CWA FRevive."""
import re
import unittest
from pathlib import Path

MISSION = Path(__file__).resolve().parents[1] / "cwr_assault_planner_v203.eden"
REVIVE = MISSION / "FRevive"


def contents(file):
    return (REVIVE / file).read_text(encoding="latin-1")


class FReviveCWATests(unittest.TestCase):
    def test_no_unsupported_array_find_in_any_frevive_script(self):
        # Code-only lines: ignore comments mentioning the unsupported operator.
        for path in REVIVE.rglob("*"):
            if path.suffix.lower() not in {".sqs", ".sqf"}:
                continue
            source = path.read_text(encoding="latin-1")
            for number, line in enumerate(source.splitlines(), 1):
                code = line.split("//", 1)[0]
                if code.lstrip().startswith(";"):
                    continue
                self.assertNotRegex(code, r"\bfind\s*(?:\(|[A-Za-z_])",
                                    f"{path.name}:{number}")

    def test_revive_lookups_use_safe_first_index(self):
        source = contents("Start.sqs")
        self.assertIn("_which=[_indexes,(_reviving select _i)] call FREVIVE_ARRAY_INDEX_OF", source)
        self.assertIn("_which=[_status,_i] call FREVIVE_ARRAY_INDEX_OF", source)
        self.assertIn('if (_which>=0) then {[_bodies select _which,_body] exec "FRevive\\MoveAI.sqs"}', source)
        helper = contents("Functions.sqf")
        self.assertIn("FREVIVE_ARRAY_INDEX_OF = {", helper)
        self.assertIn("_found = -1;", helper)
        self.assertIn("if (_found < 0 && _x == _wanted) then {_found = _index}", helper)
        self.assertIn("} forEach _items;", helper)
        self.assertIn("_found\n};", helper)

    def test_clock_snapshot_precedes_revive_checks(self):
        start = contents("Start.sqs")
        self.assertRegex(start, r"#Start\s*\n~FREVIVE_INTERVAL\s*\n(?:;[^\n]*\n)*_time = time\s*\n_i = 0")
        self.assertIn("_timing set [_i, _time+FREVIVE_PICKUP_TIME]", start)
        self.assertIn("_remind set [_i, _time+10]", start)
        self.assertIn("if (local _new_body) then {_new_body call FREVIVE_SUSPEND}", start)

    def test_reference_search_first_match_and_missing(self):
        def array_index_of(items, wanted):
            found = -1
            for i, item in enumerate(items):
                if found < 0 and item == wanted:
                    found = i
            return found

        self.assertEqual(array_index_of([], 1), -1)
        self.assertEqual(array_index_of([-1, 3, 7], 7), 2)
        self.assertEqual(array_index_of([4, 2, 4], 4), 0)
        self.assertEqual(array_index_of([9, 4], 2), -1)

if __name__ == "__main__":
    unittest.main()
