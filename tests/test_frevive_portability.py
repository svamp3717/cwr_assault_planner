"""Static regression checks for the CWA FRevive integration.

These checks guard against the known relocation paths, not game-engine behavior.
A hosted/dedicated CWA playtest remains necessary.
"""
import re
import unittest
from pathlib import Path

MISSION = Path(__file__).resolve().parents[1] / "cwr_assault_planner_v203.eden"


def source(path):
    return (MISSION / path).read_text(encoding="utf-8-sig")


class FRevivePortabilityTests(unittest.TestCase):
    def test_water_recovery_opt_in_and_one_owner_call(self):
        bootstrap = source("mpFReviveBootstrap.sqs")
        start = source("FRevive/Start.sqs")
        self.assertIn("FREVIVE_ANTI_WATER = false", bootstrap)
        calls = [line for line in start.splitlines() if 'exec "FRevive\\AntiWater.sqs"' in line]
        self.assertEqual(len(calls), 1)
        self.assertIn("FREVIVE_ANTI_WATER", calls[0])
        self.assertIn("local _body", calls[0])
        self.assertIn("getPosASL _body", calls[0])
        self.assertNotIn("_sea_level", start)
        self.assertNotIn("_measure", start)
        ready = start[start.index("#Set_Ready_For_Revive"):start.index("#Check_If_Revive")]
        self.assertLess(ready.index("? !local _new_body"), ready.index(calls[0]))
        self.assertLess(ready.index("_new_body call FREVIVE_SUSPEND"), ready.index(calls[0]))

    def test_shore_search_is_bounded_and_has_no_unit_fallback(self):
        anti = source("FRevive/AntiWater.sqs")
        self.assertIn("? !FREVIVE_ANTI_WATER : exit", anti)
        self.assertIn("_probe setPosASL [_ox, _oy, 0]", anti)
        self.assertIn("_radius <= 600", anti)
        for bound in ("worldMinX", "worldMaxX", "worldMinY", "worldMaxY"):
            self.assertIn(bound, anti)
        self.assertEqual(anti.count("_body setPos ["), 1)
        self.assertNotIn("_body setPosASL", anti)
        self.assertNotIn("_bodies", anti)
        self.assertNotIn("_unit", anti)
        self.assertIn("deleteVehicle _probe", anti)
        labels = set(re.findall(r"(?m)^#(\w+)", anti))
        targets = set(re.findall(r'goto "(\w+)"', anti))
        self.assertEqual(targets - labels, set())
        move = anti[anti.index("#move"):anti.index("#cleanup")]
        self.assertLess(move.index("!local _body"), move.index("_body setPos"))
        self.assertLess(move.index("getDammage _replacement > 0"), move.index("_body setPos"))
        self.assertLess(move.index("getPosASL _body select 2"), move.index("_body setPos"))

    def test_remote_client_requires_observed_suspension(self):
        start = source("FRevive/Start.sqs")
        check = start[start.index("#Check_If_Revive"):start.index("#Revived")]
        self.assertIn("_suspended_seen set [count _suspended_seen,false]", start)
        self.assertIn("_suspended_seen set [_i, false]", start)
        self.assertLess(check.index("!(_suspended_seen select _i)"), check.index('goto "Revived"'))
        self.assertIn('if (local _new_body && _time>(_timing select _i)) then {goto "Revived"}', check)

    def test_placeholder_and_camera_use_death_position(self):
        start = source("FRevive/Start.sqs")
        spectator = source("FRevive/Spectator.sqs")
        self.assertIn('_body setPosASL _savedPos', start)
        self.assertNotIn("_fixX", start)
        self.assertIn('typeOf _body != "body" && [getPosASL _body', start)
        self.assertNotIn("9578.59", spectator)
        self.assertNotIn('camCreate [0,0,0]', spectator)
        self.assertIn('camCreate (getPos _bodyPLR)', spectator)

    def test_existing_suspension_encoding_preserved(self):
        functions = source("FRevive/Functions.sqf")
        self.assertIn("9999", functions)
        self.assertIn("(_this+10)*1000+999", functions)
        self.assertIn("_this setPos [(_location select _i) select 0,(_location select _i) select 1,(_reviving select _i) call FREVIVE_ID_TO_HEIGHT]", functions)
        self.assertIn("FREVIVE_TIMEOUT = 300", source("mpFReviveBootstrap.sqs"))


if __name__ == "__main__":
    unittest.main()
