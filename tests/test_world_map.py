"""Map coordinate geometry and live Tkinter integration, no game needed."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import generate_world_config as gen
from generate_world_config_gui import WorldConfigGui
from world_map import Bounds, View, grid_step, nearest_marker, next_marker_class
import tkinter as tk


class GeometryTests(unittest.TestCase):
    def test_north_up_aspect_and_roundtrip(self):
        bounds = Bounds(-500, 100, 3500, 8100)
        view = View.fit(bounds, 900, 400)
        for x, y in ((-500, 100), (3500, 8100), (0, 3000)):
            px, py = view.screen(x, y)
            xx, yy = view.world(px, py)
            self.assertAlmostEqual(xx, x)
            self.assertAlmostEqual(yy, y)
        self.assertLess(view.screen(0, 4000)[1], view.screen(0, 3000)[1])
        self.assertAlmostEqual(view.screen(1000, 1000)[0] - view.screen(0, 1000)[0],
                               view.screen(0, 0)[1] - view.screen(0, 1000)[1])

    def test_zoom_keeps_pointer_and_pan(self):
        view = View.fit(Bounds(0, 0, 12800, 12800), 600, 400)
        x, y = view.world(155, 205)
        zoom = view.zoom(2, 155, 205, view.scale/4, view.scale*40)
        self.assertAlmostEqual(zoom.world(155, 205)[0], x)
        self.assertAlmostEqual(zoom.world(155, 205)[1], y)
        p = zoom.pan(45, -20)
        before = zoom.screen(x, y)
        after = p.screen(x, y)
        self.assertAlmostEqual(after[0] - before[0], 45)
        self.assertAlmostEqual(after[1] - before[1], -20)
        self.assertTrue(85 <= grid_step(view.scale)*view.scale <= 425)

    def test_bounds_and_hit_testing(self):
        b = Bounds(-5, 10, 500, 1200)
        self.assertEqual(b.clamp(-10, 1300), (-5, 1200))
        with self.assertRaises(ValueError):
            Bounds(0, 0, 0, 5)
        with self.assertRaises(ValueError):
            Bounds(0, 0, float("nan"), 5)
        v = View.fit(b, 500, 500)
        locations = [gen.Location("Custom_SITE_1", "Z", 10, 20), gen.Location("loc2", "A", 350, 800)]
        self.assertEqual(next_marker_class(locations), "custom_site_2")
        self.assertEqual(nearest_marker(v, locations, *v.screen(350, 800)), 1)
        self.assertIsNone(nearest_marker(v, locations, *v.screen(200, 300)))


class MapGuiTests(unittest.TestCase):
    def setUp(self):
        try:
            self.app = WorldConfigGui()
        except tk.TclError as exc:
            self.skipTest(f"Tk display unavailable: {exc}")
        self.addCleanup(self.app.destroy)
        app = self.app
        app.geometry("1000x1000")
        app.config_path = Path("config.cpp")
        app.locations = [gen.Location(f"loc{i}", name, 500+300*i, 500+350*i)
                         for i, name in enumerate(("Z", "A", "B", "C", "D", "E", "F"))]
        app.world_name.set("TestWorld")
        for var, val in ((app.min_x, 100), (app.min_y, 100), (app.max_x, 4000),
                         (app.max_y, 4000), (app.base_x, 800), (app.base_y, 800)):
            var.set(str(val))
        app.refresh_location_table()
        app.map_editor.master.select(app.map_editor)
        app.update_idletasks()
        app.update()
        self.map = app.map_editor
        self.assertIsNotNone(self.map.view)

    def event(self, x, y):
        sx, sy = self.map.view.screen(x, y)
        return SimpleNamespace(x=sx, y=sy)

    def test_edit_export_and_sorted_selection(self):
        app, editor = self.app, self.map
        app.sort_mode.set("name")
        app.refresh_location_table()
        self.assertEqual(app.tree.get_children()[0], "1")
        editor.click(self.event(500, 500))
        self.assertEqual(app.selected_location_index(), 0)
        editor.move(self.event(1000, 1200))
        editor.release(None)
        self.assertEqual((app.locations[0].x, app.locations[0].y), (1000, 1200))
        self.assertEqual(app.tree.set("0", "y"), "1200")
        editor.mode.set("base")
        editor.click(self.event(2000, 2100))
        self.assertEqual((app.base_x.get(), app.base_y.get()), ("2000", "2100"))
        editor.mode.set("add")
        with patch("world_map.simpledialog.askstring", return_value="Custom"):
            editor.click(self.event(3000, 3100))
        self.assertEqual(len(app.locations), 8)
        self.assertEqual(app.selected_location_index(), 7)
        self.assertEqual(app.locations[7].name, "Custom")
        with patch("world_map.simpledialog.askstring", return_value="Custom Renamed"):
            editor.rename()
        self.assertEqual(app.locations[7].name, "Custom Renamed")
        text = gen.build_world_config("TestWorld", app.ordered_locations(), 2000, 2100,
                                      100, 100, 4000, 4000, "config.cpp", "map", "map")
        self.assertIn('"Custom Renamed"', text)
        self.assertIn("missionBaseX = 2000", text)
        self.assertTrue(app.map_dirty)
        with patch("world_map.messagebox.askyesno", return_value=True):
            editor.delete()
        self.assertEqual(len(app.locations), 7)
        self.assertIsNone(app.selected_location_index())
        self.assertNotIn("Custom Renamed", [loc.name for loc in app.locations])


if __name__ == "__main__":
    unittest.main()
