"""Four Radio Charlie logistical choices are wired for all supported packs."""
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MISSION = ROOT / "cwr_assault_planner_v203.eden"
sys.path.insert(0, str(ROOT / "tools"))
from mission_package import create_mission_package

def read(path):
    return Path(path).read_text(encoding="latin-1")

class LogisticsTruckTests(unittest.TestCase):
    def test_four_visible_buttons_and_correct_selection(self):
        dialog = read(MISSION / "description.ext")
        for index, name in enumerate(("Jeep", "HMMWV", "AmmoBox", "FiveTonTruck"), 1):
            line = next(line for line in dialog.splitlines() if f"class {name} : ERA_RscButton" in line)
            self.assertIn(f"idc={4200+index}", line)
            self.assertIn(f"logisticsDropMenuChoice={index}", line)
        self.assertEqual(dialog.count("class FiveTonTruck : ERA_RscButton"), 1)

    def test_ui_and_server_agree_on_request_type_four(self):
        client = read(MISSION/"radioCharlie.sqs")
        server = read(MISSION/"mpServerLogisticsDropRequestMonitor.sqs")
        delivery = read(MISSION/"mpServerLogisticsDrop.sqs")
        self.assertIn("ctrlSetText [4204,assetNameWestTruck]", client)
        for script in (client,server):
            self.assertIn("logisticsDropRequestType == 4 : logisticsDropRequestLabel = assetNameWestTruck", script)
        self.assertIn("logisticsDropRequestType > 4 : goto \"invalidRequest\"", server)
        self.assertIn("logisticsDropRequestType == 4 : logisticsDropAsset = assetClassWestTruck createVehicle", delivery)
        self.assertIn("logisticsDropRequestType != 3 : logisticsDropAsset setFuel 1", delivery)
        self.assertIn("logisticsDropRequestType == 3 : [logisticsDropAsset] exec \"logisticsAmmoBoxLoad.sqs\"", delivery)
        self.assertNotIn("logisticsDropRequestType == 4 : [logisticsDropAsset] exec", delivery)
        self.assertIn("logisticsDropDelivered = true", delivery)
        self.assertIn('publicVariable "logisticsDropAsset"', delivery)
        self.assertIn("logisticsDropsRemaining = logisticsDropsRemaining - 1", server)

    def test_truck_class_and_label_in_each_asset_profile(self):
        expected = {"vanilla":"Truck5t", "ww4":"WW4EXT_5TBIS","wgl512":"WGL_Truck5T"}
        for pack, classname in expected.items():
            with self.subTest(pack=pack):
                profile = read(MISSION/"assets"/f"{pack}.sqs")
                self.assertIn(f'assetClassWestTruck = "{classname}"', profile)
                self.assertIn('assetNameWestTruck = "5-ton truck"', profile)

    def test_real_export_preserves_four_logistics_choices(self):
        config = read(MISSION/"worldConfig.sqs")
        with tempfile.TemporaryDirectory() as temp:
            for pack in ("vanilla","ww4","wgl512"):
                dest = create_mission_package(MISSION, Path(temp), "Malden", f"Truck{pack}",
                                              config, 5000, 6000, asset_pack=pack)
                with self.subTest(pack=pack):
                    self.assertIn("class FiveTonTruck", read(dest/"description.ext"))
                    self.assertIn("assetNameWestTruck",read(dest/"radioCharlie.sqs"))
                    self.assertIn("assetClassWestTruck createVehicle",read(dest/"mpServerLogisticsDrop.sqs"))
                    self.assertIn(f'assetProfileName = "{pack}"',read(dest/"assets/selection.sqs"))
                    self.assertRegex(read(dest/"description.ext"),
                                     r"(?m)^respawn = "+("4" if pack=="wgl512" else "2")+";")

if __name__ == "__main__":
    unittest.main()
