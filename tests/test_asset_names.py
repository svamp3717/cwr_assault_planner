"""Asset profile display-name coverage for all currently selectable vehicles."""
import re
import unittest
from pathlib import Path

MISSION = Path(__file__).resolve().parents[1] / "cwr_assault_planner_v203.eden"

def read(name):
    return (MISSION / name).read_text(encoding="latin-1")

def profile(pack):
    source = read("assets/" + pack + ".sqs")
    return dict(re.findall(r'(?m)^(asset(?:Class|Name)\w+)\s*=\s*"([^"]*)"\s*$', source))

class AssetNameTests(unittest.TestCase):
    def test_profile_name_coverage(self):
        profiles = [profile(pack) for pack in ("vanilla", "ww4")]
        references = set()
        for path in MISSION.rglob("*"):
            if path.suffix.lower() not in (".sqs", ".sqf") or "assets" in path.relative_to(MISSION).parts:
                continue
            references.update(re.findall(r"\bassetName\w+\b", path.read_text(encoding="latin-1")))
        self.assertGreater(len(references), 20)
        for data in profiles:
            for ref in references:
                self.assertTrue(data.get(ref), ref)
                self.assertTrue(data.get(ref.replace("assetName", "assetClass", 1)), ref)
        self.assertEqual({k for k in profiles[0] if k.startswith("assetName")},
                         {k for k in profiles[1] if k.startswith("assetName")})

    def test_vanilla_names_match_replacement_classes(self):
        data = profile("vanilla")
        expected = {
            "EastArmedLightVehicle": ("BRDM", "BRDM scout car"),
            "BRDM_MG": ("BRDM", "BRDM scout car"),
            "BTR80": ("BMP2", "BMP-2"),
            "ResistanceArmedLightVehicle": ("BMPRes", "BMP-1"),
            "BRDM2ExportR": ("BMPRes", "BMP-1"),
            "BTR80ExportR": ("BMPRes", "BMP-1"),
            "Zil157": ("TruckV3SG", "Resistance truck"),
        }
        for role, (cls, label) in expected.items():
            self.assertEqual(data["assetClass" + role], cls)
            self.assertEqual(data["assetName" + role], label)
        self.assertEqual(profile("ww4")["assetNameBTR80"], "BTR-80")
        self.assertEqual(profile("ww4")["assetNameBTR80ExportR"], "BTR-80")

    def test_steal_class_and_name_selected_as_pair(self):
        script = read("stealVehicleObjective.sqs")
        pairs = re.findall(r"\[assetClass(\w+),assetName(\w+)\]", script)
        self.assertEqual(len(pairs), 10)
        self.assertTrue(all(cls == label for cls, label in pairs))
        self.assertIn("_class = _choice select 0", script)
        self.assertIn("_vehicleLabel = _choice select 1", script)
        self.assertIn("_vehicleLabel = assetNameUAZ", script)
        self.assertIn("_vehicleLabel = assetNameJeepMG", script)
        self.assertNotIn('"BTR-80"', script)
        for i in range(1, 6):
            self.assertIn(f"objectiveStealVehicleLabel{i} = _vehicleLabel", script)
            for name in ("objectiveAssets.sqs", "mpClientStealMarkers.sqs", "mpPublishState.sqs"):
                self.assertIn(f"objectiveStealVehicleLabel{i}", read(name))

    def test_support_and_logistics_use_profile_names(self):
        for name, refs in {
            "vehiclePools.sqs": ("WestCobra", "WestApache", "WestAttackJet", "WestLaserJet",
                                 "WestKiowa", "EastAttackHeli", "EastAttackJet", "EastKamov"),
            "randomize.sqs": ("WestTransportHeli", "WestHeavyTransportHeli", "WestIFV", "WestTank"),
            "mpServerExtraction.sqs": ("WestHeavyTransportHeli",),
            "mpServerExtractionRequestMonitor.sqs": ("WestHeavyTransportHeli",),
            "mpServerLogisticsDrop.sqs": ("WestHeavyTransportHeli",),
            "mpServerLogisticsDropRequestMonitor.sqs": ("WestJeep", "WestHMMWV", "WestAmmoBox", "WestHeavyTransportHeli"),
            "radioCharlie.sqs": ("WestJeep", "WestHMMWV", "WestAmmoBox"),
            "objectiveAssets.sqs": ("Scud", "EastAirDefense", "ResistanceAirDefense", "EastAmmoTruck", "ResistanceAmmoTruck"),
        }.items():
            for role in refs:
                self.assertIn("assetName" + role, read(name), name)
        self.assertNotIn("WW4 PLAYER MODEL", read("ww4_arsenal/dialog.hpp"))

if __name__ == "__main__":
    unittest.main()
