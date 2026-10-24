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
        self.assertEqual(values["stage_max"], 2250)
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


if __name__ == "__main__":
    unittest.main()
