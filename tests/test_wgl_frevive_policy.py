"""Profile-specific FRevive policy: disabled only for WGL 5.12."""
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MISSION = ROOT / "cwr_assault_planner_v203.eden"
sys.path.insert(0, str(ROOT / "tools"))
from mission_package import create_mission_package

def script(path):
    return (MISSION / path).read_text(encoding="latin-1")

class WGLFRevivePolicyTests(unittest.TestCase):
    def test_wgl_off_other_profiles_on_by_default(self):
        init = script("init.sqs")
        self.assertIn('[] exec "assets\\selection.sqs"', init)
        self.assertLess(init.index("@ assetProfileReady"), init.index('guiFReviveEnabled = assetProfileName != "wgl512"'))
        self.assertIn('guiFReviveEnabled = assetProfileName != "wgl512"', init)
        for pack, expect in (("wgl512", False),("ww4", True),("vanilla", True)):
            self.assertEqual(pack != "wgl512", expect)

    def test_hard_gate_after_roster_cull_and_before_revive_start(self):
        boot = script("mpFReviveBootstrap.sqs")
        gate = '? assetProfileName == "wgl512" : goto "disabled"'
        self.assertLess(boot.index("@ mpAISlotsCulled"), boot.index(gate))
        self.assertLess(boot.index(gate), boot.index('mpFReviveNames exec "FRevive\\Start.sqs"'))
        self.assertIn('? !(guiFReviveEnabled) : goto "disabled"', boot)
        disabled = boot[boot.index("#disabled"):]
        self.assertIn("mpFReviveStarted = true", disabled)
        self.assertIn('publicVariable "mpFReviveStarted"', disabled)
        self.assertNotIn('exec "FRevive\\Start.sqs"', disabled)

    def test_ui_and_submission_cannot_enable_wgl(self):
        settings = script("missionSettingsMenu.sqs")
        self.assertIn('assetProfileName == "wgl512" : guiFReviveEnabled = false', settings)
        self.assertIn('ctrlSetText [4330, "WGL: OFF"]', settings)
        controls = script("description.ext")
        on = next(line for line in controls.splitlines() if "class FReviveOn" in line)
        self.assertIn('assetProfileName != ""wgl512""', on)
        self.assertIn("guiFReviveEnabled=true", on)
        submit = script("mpSubmitSetup.sqs")
        self.assertLess(submit.index('assetProfileName == "wgl512" : guiFReviveEnabled = false'),
                        submit.index('publicVariable "guiFReviveEnabled"'))

    def test_original_frevive_lookup_and_timing_patch_removed(self):
        start = script("FRevive/Start.sqs")
        functions = script("FRevive/Functions.sqf")
        self.assertIn("_indexes find (_reviving select _i)", start)
        self.assertIn("_status find _i", start)
        self.assertNotIn("FREVIVE_ARRAY_INDEX_OF", functions + start)
        self.assertNotIn("_time = time", start)

    def test_real_wgl_vanilla_and_ww4_exports_share_policy(self):
        config = (MISSION / "worldConfig.sqs").read_text(encoding="utf-8-sig")
        with tempfile.TemporaryDirectory() as tmp:
            outs=[]
            for pack in ("wgl512","vanilla","ww4"):
                target=create_mission_package(MISSION, Path(tmp), "Malden", "Policy"+pack,
                                              config, 5000, 6000, asset_pack=pack)
                selector=(target / "assets/selection.sqs").read_text(encoding="latin-1")
                self.assertIn(f'assetProfileName = "{pack}"', selector)
                self.assertIn(f'[] exec "assets\\{pack}.sqs"', selector)
                outs.append(target)
            for script_name in ("init.sqs","mpFReviveBootstrap.sqs",
                                "missionSettingsMenu.sqs","mpSubmitSetup.sqs",
                                "FRevive/Start.sqs","FRevive/Functions.sqf"):
                original=script(script_name)
                for folder in outs:
                    self.assertEqual((folder/script_name).read_text(encoding="latin-1"), original,
                                     (folder.name,script_name))
            self.assertRegex((outs[0]/"description.ext").read_text(encoding="latin-1"),
                             r"(?m)^respawn = 4;$")
            for folder in outs[1:]:
                self.assertEqual((folder/"description.ext").read_text(encoding="latin-1"),
                                 script("description.ext"))

if __name__ == "__main__":
    unittest.main()
