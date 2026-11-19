"""Generator placement controls: adaptive defaults, overrides, CWA-safe output."""
import math
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import generate_world_config as gen


class WorldPlacementTests(unittest.TestCase):
    def test_scales_to_small_world(self):
        values = gen.resolve_placement_settings(0, 0, 4000, 4000)
        self.assertEqual(
            values,
            {"stage_min": 800, "stage_max": 2600, "objective_edge": 400, "air_offset": 800},
        )

    def test_scales_to_usable_shorter_side(self):
        values = gen.resolve_placement_settings(250, 250, 3750, 5750)
        self.assertEqual(values["stage_min"], 700)
        self.assertEqual(values["stage_max"], 2300)
        self.assertEqual(values["objective_edge"], 350)
        self.assertEqual(values["air_offset"], 700)

    def test_large_world_caps(self):
        values = gen.resolve_placement_settings(0, 0, 12800, 12800)
        self.assertEqual(
            values,
            {"stage_min": 1500, "stage_max": 6000, "objective_edge": 500, "air_offset": 1600},
        )

    def test_manual_overrides(self):
        result = gen.resolve_placement_settings(
            0, 0, 4000, 4000,
            stage_min=600, stage_max=2400, objective_edge=300, air_offset=700,
        )
        self.assertEqual(result["stage_min"], 600)
        self.assertEqual(result["stage_max"], 2400)
        self.assertEqual(result["objective_edge"], 300)
        self.assertEqual(result["air_offset"], 700)

    def test_invalid_placement_rejected(self):
        cases = (
            {"stage_min": -10}, {"stage_max": 400}, {"stage_min": 1000, "stage_max": 1200},
            {"objective_edge": 2000}, {"air_offset": math.inf},
        )
        for kwargs in cases:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                gen.resolve_placement_settings(0, 0, 4000, 4000, **kwargs)

    def test_worldconfig_contains_all_settings_and_one_line_arrays(self):
        locations = [
            SimpleNamespace(class_name=f"town{i}", name=f"Village {i}", x=1000 + i*150, y=1200 + i*100)
            for i in range(6)
        ]
        config = gen.build_world_config(
            world_name="Abel", locations=locations,
            base_x=1800, base_y=1900,
            min_x=0, min_y=0, max_x=4000, max_y=4000,
            input_name="config.cpp", base_source="test", bounds_source="test",
        )
        for expected in (
            "worldStageMinClearance = 800", "worldStageMaxDistance = 2600",
            "worldObjectiveEdgeMargin = 400", "worldAirStageOffset = 800",
        ):
            self.assertIn(expected, config)
        for key in ("missionLocationLabels", "missionLocationXs", "missionLocationYs"):
            lines = [line for line in config.splitlines() if line.startswith(key + " = [")]
            self.assertEqual(len(lines), 1)

    def test_mission_scripts_consume_generated_variables(self):
        script = (ROOT / "cwr_assault_planner_v203.eden" / "randomize.sqs").read_text()
        config = (ROOT / "cwr_assault_planner_v203.eden" / "worldConfig.sqs").read_text()
        init = (ROOT / "cwr_assault_planner_v203.eden" / "init.sqs").read_text()
        for var in (
            "worldStageMinClearance", "worldStageMaxDistance",
            "worldObjectiveEdgeMargin", "worldAirStageOffset",
        ):
            self.assertIn(var + " =", config)
            self.assertIn(var, script)
        self.assertIn('[] exec "worldConfig.sqs"', init)
        self.assertIn("@ worldConfigReady", init)
        self.assertIn("count _eligibleIndices >= townCount", script)
        self.assertIn("worldStageMaxDistance - 400", script)


    def test_runtime_bounds_initialized_from_world(self):
        mission = ROOT / "cwr_assault_planner_v203.eden"
        randomize = (mission / "randomize.sqs").read_text()
        for axis in ("X", "Y"):
            self.assertIn(f"_safeMin{axis} = worldMin{axis} + _insertionEdge", randomize)
            self.assertIn(f"_safeMax{axis} = worldMax{axis} - _insertionEdge", randomize)
        init = (mission / "init.sqs").read_text()
        self.assertLess(init.index("@ worldConfigReady"), init.index('call preProcessFile "worldPlacementFunctions.sqf"'))
        helpers = (mission / "worldPlacementFunctions.sqf").read_text()
        for symbol in ("worldClampPosition", "worldOffsetPosition", "worldSetupPosition"):
            self.assertIn(symbol + " = {", helpers)

    def test_runtime_spawn_sites_use_world_config(self):
        mission = ROOT / "cwr_assault_planner_v203.eden"
        for name in (
            "friendlyRuntimeAlliedInfantry.sqs", "friendlyRuntimeInsertionVehicles.sqs",
            "friendlyRuntimeSupport.sqs", "enemyRuntimeReserves.sqs",
        ):
            with self.subTest(name=name):
                script = (mission / name).read_text()
                self.assertIn("call worldSetupPosition", script)
                self.assertNotRegex(script, r"\b1[012]\d{3}\s*,\s*1[012]\d{3}\b")
        for name in (
            "mpServerExtraction.sqs", "mpServerLogisticsDrop.sqs",
            "enemyAirReinforcement.sqs", "enemyReinforcements.sqs",
            "enemyAirSupport.sqs", "callAirSupport.sqs",
        ):
            with self.subTest(name=name):
                script = (mission / name).read_text()
                self.assertIn("call worldOffsetPosition", script)
                self.assertNotRegex(script, r"\b(?:10880|11520|12200|12700)\b")
        for name in ("init.sqs", "cobraMarker.sqs", "radioAirControl.sqs"):
            script = (mission / name).read_text()
            self.assertNotRegex(script, r"\b(?:10875|11700)\b")

    def test_setup_footprint_and_offset_bounds(self):
        # Reference arithmetic for rectangular/small/nonzero-origin terrains.
        # The actual SQF still requires an engine playtest.
        for min_x, min_y, max_x, max_y in ((0, 0, 4000, 4000),
                                          (250, 500, 2000, 3000),
                                          (-500, 100, -200, 500),
                                          (250, 250, 12550, 12550)):
            scale = min(1, (max_x - min_x) / 640, (max_y - min_y) / 850)
            for bx, by in ((min_x, min_y), (max_x, max_y)):
                ax = min(max(bx, min_x + 150 * scale), max_x - 490 * scale)
                ay = min(max(by, min_y + 810 * scale), max_y - 40 * scale)
                for dx, dy in ((-125, -420), (450, -420), (245, -780), (333, -690)):
                    self.assertGreaterEqual(ax + dx * scale, min_x - 1e-8)
                    self.assertLessEqual(ax + dx * scale, max_x + 1e-8)
                    self.assertGreaterEqual(ay + dy * scale, min_y - 1e-8)
                    self.assertLessEqual(ay + dy * scale, max_y + 1e-8)


if __name__ == "__main__":
    unittest.main()
