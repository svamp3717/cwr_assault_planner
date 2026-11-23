"""WGL group respawn fixes duplicate AI bodies without changing FRevive presets."""
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MISSION = ROOT / "cwr_assault_planner_v203.eden"
sys.path.insert(0, str(ROOT / "tools"))
from asset_packs import apply_asset_pack
from mission_package import create_mission_package

def read(path):
    return Path(path).read_text(encoding="latin-1")

class WGLGroupRespawnTests(unittest.TestCase):
    def test_exported_modes_and_frevive_are_profile_specific(self):
        config = read(MISSION / "worldConfig.sqs")
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            for pack, mode in (("wgl512", 4), ("ww4", 2), ("vanilla", 2)):
                m = create_mission_package(MISSION, base, "Malden", "Respawn"+pack,
                                           config, 5000, 6000, asset_pack=pack)
                with self.subTest(pack=pack):
                    desc = read(m / "description.ext")
                    matches = re.findall(r"(?m)^respawn = (\d+);$", desc)
                    self.assertEqual(matches, [str(mode)])
                    self.assertIn("respawnDelay = 3;", desc)
                    self.assertIn(f'assetProfileName = "{pack}"', read(m/"assets/selection.sqs"))
                    self.assertIn('assetProfileName == "wgl512" : goto "disabled"',
                                  read(m/"mpFReviveBootstrap.sqs"))
                    if pack == "wgl512":
                        self.assertIn("GROUP respawn transfers players", desc)
                        apply_asset_pack(m, "wgl512")
                        self.assertEqual(re.findall(r"(?m)^respawn = (\d+);$",
                                                    read(m/"description.ext")), ["4"])
                    else:
                        self.assertEqual(desc, read(MISSION/"description.ext"))

    def test_extraction_not_blocked_by_permanent_wgl_deaths(self):
        script = read(MISSION/"mpServerExtraction.sqs")
        roster = ["plr","red2","red3","medic1","medic2",
                  "red6","red7","red8","red9","red10","red11","red12"]
        for slot in roster:
            self.assertIn(
                f'"{slot}" in mpFReviveNames && (assetProfileName != "wgl512" || alive {slot})',
                script)
            self.assertIn(
                f'? assetProfileName == "wgl512" && "{slot}" in mpFReviveNames && alive {slot} : _wglLiving = _wglLiving + 1',
                script)
        self.assertEqual(script.count('_allAboard = false'), 13)
        self.assertIn('? assetProfileName == "wgl512" && _wglLiving == 0 : _allAboard = false', script)
        self.assertIn('? _allAboard && _objectivesComplete : goto "depart"', script)

    def test_extraction_logic_reference_cases(self):
        def ready(pack, members, complete=True):
            if not complete:
                return False
            alive = [boarded for is_alive,boarded in members if is_alive]
            if pack == "wgl512":
                return bool(alive) and all(alive)
            return all(is_alive and boarded for is_alive,boarded in members)
        self.assertTrue(ready("wgl512", [(False,False),(True,True)]))
        self.assertFalse(ready("wgl512", [(False,False),(True,False)]))
        self.assertFalse(ready("wgl512", [(False,False),(False,False)]))
        self.assertFalse(ready("ww4", [(False,False),(True,True)]))
        self.assertTrue(ready("ww4", [(True,True),(True,True)]))
        self.assertFalse(ready("wgl512", [(True,True)], complete=False))

    def test_template_remains_instant_for_direct_ww4_editing(self):
        self.assertRegex(read(MISSION/"description.ext"), r"(?m)^respawn = 2;$")
        self.assertNotIn("FREVIVE_ARRAY_INDEX_OF", read(MISSION/"FRevive/Functions.sqf"))
        self.assertIn("_indexes find (_reviving select _i)",
                      read(MISSION/"FRevive/Start.sqs"))

if __name__ == "__main__":
    unittest.main()
