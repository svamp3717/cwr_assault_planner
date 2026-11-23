"""End-to-end profile selection and shared runtime invariants."""
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from asset_packs import apply_asset_pack, manifest, unknown_classes, TEXT_SUFFIXES
from mission_package import create_mission_package

TEMPLATE = ROOT / "cwr_assault_planner_v203.eden"

class AssetPackTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.output = Path(self.tmp.name)
        self.config = (TEMPLATE / "worldConfig.sqs").read_text(encoding="utf-8-sig")

    def export(self, pack, name):
        return create_mission_package(TEMPLATE, self.output, "Malden", name,
                                      self.config, 5000, 6000, asset_pack=pack)

    def test_real_vanilla_export_and_no_mod_classes(self):
        mission = self.export("vanilla", "VanillaTest")
        self.assertEqual((mission / "assetPack.txt").read_text().strip(), "vanilla")
        sqm = (mission / "mission.sqm").read_text()
        self.assertNotRegex(sqm, r'(?i)vehicle\s*=\s*"ww4')
        self.assertNotIn("WW4EXT_VEHICLES", sqm)
        self.assertIn("editorupdate102", sqm)
        self.assertEqual(len(re.findall(r'player="(?:PLAYER COMMANDER|PLAY CDG)"', sqm)), 12)
        self.assertIn('vehicle="SoldierWMedic"', sqm)
        self.assertIn('vehicle="OfficerW"', sqm)
        self.assertTrue((mission / "assets/vanilla.sqs").is_file())
        self.assertFalse((mission / "assets/ww4.sqs").exists())
        self.assertIn('[] exec "assets\\vanilla.sqs"', (mission / "assets/selection.sqs").read_text())
        for file in mission.rglob("*"):
            if file.is_file() and file.suffix.lower() in TEXT_SUFFIXES and file.name != "worldConfig.sqs":
                self.assertFalse(unknown_classes(file.read_bytes().decode("latin-1")), str(file))
        profile = (mission / "assets/vanilla.sqs").read_text()
        self.assertIn('enemyEastReinforcementTransportPool = ["Ural"]', profile)
        self.assertIn('enemyResistanceReinforcementTransportPool = ["TruckV3SG"]', profile)
        self.assertIn('assetClassWestCobra = "Cobra"', profile)
        self.assertIn('assetClassEastAttackJet = "Su25"', profile)
        self.assertEqual((mission / "worldConfig.sqs").read_text(), self.config)

    def test_ww4_export_and_shared_gameplay_are_byte_identical(self):
        vanilla = self.export("vanilla", "VanillaTest")
        ww4 = self.export("ww4", "WW4Test")
        self.assertEqual((ww4 / "assetPack.txt").read_text().strip(), "ww4")
        self.assertIn("WW4_FORECRifleman", (ww4 / "mission.sqm").read_text())
        self.assertTrue((ww4 / "assets/ww4.sqs").exists())
        self.assertFalse((ww4 / "assets/vanilla.sqs").exists())
        self.assertIn('[] exec "assets\\ww4.sqs"', (ww4 / "assets/selection.sqs").read_text())
        for file in TEMPLATE.rglob("*"):
            rel = file.relative_to(TEMPLATE)
            if not file.is_file() or rel.parts[0] == "assets" or rel.name == "mission.sqm":
                continue
            self.assertEqual((ww4 / rel).read_bytes(), (vanilla / rel).read_bytes(), str(rel))
            if rel.name != "worldConfig.sqs":
                self.assertEqual((ww4 / rel).read_bytes(), file.read_bytes(), str(rel))

    def test_profile_aliases_and_factions_complete(self):
        profiles = {pack: (TEMPLATE / "assets" / f"{pack}.sqs").read_text(encoding="latin-1")
                    for pack in ("vanilla", "ww4")}
        defs = {pack: set(re.findall(r"(?m)^(assetClass\w+)\s*=", text)) for pack, text in profiles.items()}
        self.assertEqual(defs["vanilla"], defs["ww4"])
        self.assertGreater(len(defs["ww4"]), 60)
        for file in TEMPLATE.rglob("*"):
            if file.suffix.lower() not in (".sqs", ".sqf") or "assets" in file.relative_to(TEMPLATE).parts:
                continue
            content = file.read_bytes().decode("latin-1")
            refs = set(re.findall(r"\bassetClass\w+\b", content))
            self.assertFalse(refs - defs["ww4"], str(file))
            self.assertFalse(unknown_classes(content), str(file))
        for pack, text in profiles.items():
            self.assertEqual(len(manifest(text, "assetEditorSlots")), 12)
            for name, expect in (("East", 11), ("Res", 9)):
                lines = re.findall(rf"(?m)^asset{name}Factions = asset{name}Factions \+ (.*)$", text)
                self.assertEqual(len(lines), expect if pack == "ww4" else 1)
                self.assertTrue(all(len(json.loads(line)[0][1]) == 17 for line in lines))
        init = (TEMPLATE / "init.sqs").read_text()
        self.assertIn('[] exec "assets\\selection.sqs"\n@ assetProfileReady', init)

    def test_vanilla_arsenal_indices_and_ammunition(self):
        mission = self.export("vanilla", "ArsenalTest")
        data = (mission / "assets/vanilla.sqs").read_text()
        entries = [json.loads(l.split(" + ", 1)[1])[0] for l in data.splitlines()
                   if l.startswith("WW4_ArsenalEntries = WW4_ArsenalEntries + ")]
        families = [json.loads(l.split(" + ", 1)[1])[0] for l in data.splitlines()
                    if l.startswith("WW4_ArsenalFamilies = WW4_ArsenalFamilies + ")]
        self.assertGreater(len(entries), 30)
        self.assertEqual(sorted(i for _, ids in families for i in ids), list(range(len(entries))))
        self.assertIn(["M16GrenadeLauncher", "M16GrenadeLauncher",
                       ["M16", "GrenadeLauncher", "Flare", "FlareGreen", "FlareRed", "FlareYellow"]], entries)
        self.assertFalse(unknown_classes(data))

    def test_unknown_class_prevents_partial_export(self):
        template = self.output / "template.eden"
        shutil.copytree(TEMPLATE, template)
        (template / "new.sqs").write_text('"WW4EXT_UnknownFutureVehicle" createVehicle [1,2,0]\n')
        with self.assertRaisesRegex(ValueError, "WW4EXT_UnknownFutureVehicle"):
            create_mission_package(template, self.output, "Malden", "Bad", self.config, 5000, 6000,
                                   asset_pack="vanilla")
        self.assertFalse((self.output / "Bad.Malden").exists())
        self.assertFalse(list(self.output.glob(".mission-build-*")))

    def test_reexport_vanilla_and_reject_reverse_conversion(self):
        mission = self.export("vanilla", "First")
        apply_asset_pack(mission, "vanilla")
        with self.assertRaisesRegex(ValueError, "original mission template"):
            apply_asset_pack(mission, "ww4")

if __name__ == "__main__":
    unittest.main()
