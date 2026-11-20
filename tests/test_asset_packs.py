"""Build and audit both complete mission variants, not just synthetic snippets."""
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from asset_packs import apply_asset_pack, unknown_classes, ARSENAL, ROLES, POOLS, TEXT_SUFFIXES
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
        for file in mission.rglob("*"):
            if file.is_file() and file.suffix.lower() in TEXT_SUFFIXES and file.name != "worldConfig.sqs":
                self.assertFalse(unknown_classes(file.read_bytes().decode("latin-1")), str(file))
        for side, roles in (("East", 1), ("Res", 2)):
            factions = (mission / "ww4FactionSelect.sqs").read_text()
            for role, classes in ROLES.items():
                self.assertIn(f'ww4{side}{role} = "{classes[roles]}"', factions)
        pools = (mission / "vehiclePools.sqs").read_text()
        for variable, classes in POOLS.items():
            self.assertIn(variable + " = " + json.dumps(classes, separators=(",", ":")), pools)
        self.assertIn('"Cobra"', pools)
        self.assertIn('"Su25"', (mission / "enemyAirSupport.sqs").read_text())
        self.assertEqual((mission / "FRevive/Start.sqs").read_bytes(),
                         (TEMPLATE / "FRevive/Start.sqs").read_bytes())
        self.assertEqual((mission / "worldConfig.sqs").read_text(), self.config)

    def test_ww4_export_keeps_original_assets(self):
        mission = self.export("ww4", "WW4Test")
        self.assertEqual((mission / "assetPack.txt").read_text().strip(), "ww4")
        self.assertIn("WW4_FORECRifleman", (mission / "mission.sqm").read_text())
        for file in ("vehiclePools.sqs", "ww4FactionSelect.sqs", "ww4_arsenal/data.sqs",
                     "ww4_arsenal/model_data.sqs", "FRevive/Start.sqs"):
            self.assertEqual((mission / file).read_bytes(), (TEMPLATE / file).read_bytes(), file)

    def test_vanilla_arsenal_indices_and_ammunition(self):
        mission = self.export("vanilla", "ArsenalTest")
        data = (mission / "ww4_arsenal/data.sqs").read_text()
        entries = [json.loads(l.split(" + ", 1)[1])[0] for l in data.splitlines()
                   if l.startswith("WW4_ArsenalEntries = WW4_ArsenalEntries + ")]
        families = [json.loads(l.split(" + ", 1)[1])[0] for l in data.splitlines()
                    if l.startswith("WW4_ArsenalFamilies = WW4_ArsenalFamilies + ")]
        self.assertEqual(len(entries), sum(len(items) for items in ARSENAL.values()))
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
        with self.assertRaisesRegex(ValueError, "original WW4 template"):
            apply_asset_pack(mission, "ww4")

if __name__ == "__main__":
    unittest.main()
