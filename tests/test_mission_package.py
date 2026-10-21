"""Tests for complete mission export (no GUI or game installation required)."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from mission_package import create_mission_package, mission_folder_name, relocate_mission_sqm


class MissionPackageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.template = self.root / "assault_planner.eden"
        self.template.mkdir()
        (self.template / "worldConfig.sqs").write_text(
            'worldName = "Everon"\nmissionBaseX = 10875\nmissionBaseY = 11700\n', encoding="utf-8"
        )
        (self.template / "mission.sqm").write_text(
            'position[]={10865.000000,25.000000,11696.000000};\n'
            'position[]={10875.000000,0.000000,11700.000000};\n', encoding="utf-8"
        )
        (self.template / "FRevive").mkdir()
        (self.template / "FRevive" / "Start.sqs").write_text("#hello\n", encoding="utf-8")
        self.destination = self.root / "Missions"
        self.destination.mkdir()

    def test_full_copy_and_position_rebase(self):
        result = create_mission_package(
            self.template, self.destination, "Malden", "", 'worldName = "Malden"\n', 5000, 6000
        )
        self.assertEqual(result.name, "assault_planner.Malden")
        self.assertEqual((result / "worldConfig.sqs").read_text(), 'worldName = "Malden"\n')
        self.assertEqual((result / "FRevive" / "Start.sqs").read_text(), "#hello\n")
        sqm = (result / "mission.sqm").read_text()
        self.assertIn("position[]={4990.000000,25.000000,5996.000000}", sqm)
        self.assertIn("position[]={5000.000000,0.000000,6000.000000}", sqm)

    def test_existing_target_is_untouched(self):
        existing = self.destination / "assault_planner.Malden"
        existing.mkdir()
        sentinel = existing / "keep"
        sentinel.write_text("original")
        with self.assertRaises(FileExistsError):
            create_mission_package(self.template, self.destination, "Malden", "", "test", 5000, 6000)
        self.assertEqual(sentinel.read_text(), "original")

    def test_reject_bad_world_and_name(self):
        for world in ("", "My World", "../Everon", "9Malden", "foo.bar"):
            with self.subTest(world=world), self.assertRaises(ValueError):
                mission_folder_name(self.template, world)
        with self.assertRaises(ValueError):
            mission_folder_name(self.template, "Malden", "../escape")

    def test_reject_copy_inside_source(self):
        nested = self.template / "output"
        nested.mkdir()
        with self.assertRaises(ValueError):
            create_mission_package(self.template, nested, "Malden", "", "test", 5000, 6000)

    def test_reject_missing_metadata(self):
        (self.template / "worldConfig.sqs").write_text("not a base\n")
        with self.assertRaises(ValueError):
            create_mission_package(self.template, self.destination, "Malden", "", "test", 5000, 6000)
        self.assertEqual(list(self.destination.iterdir()), [])

    def test_relocation_rejects_empty_sqm(self):
        with self.assertRaises(ValueError):
            relocate_mission_sqm("no positions", 0, 0, 1, 1)


if __name__ == "__main__":
    unittest.main()
