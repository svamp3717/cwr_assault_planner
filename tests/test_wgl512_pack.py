"""WGL 5.12 preset: historical class references, export isolation and parity.

The input classnames came from the 2006 WGL spreadsheets supplied by the
mission author (unitlist/inflist/weplist/grouplist.xls). An engine run is still
required to verify the actual installed WGL configuration and scripts.
"""
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MISSION = ROOT / "cwr_assault_planner_v203.eden"
sys.path.insert(0, str(ROOT / "tools"))
from asset_packs import PROFILES, manifest, unknown_classes, apply_asset_pack
from mission_package import create_mission_package

def read(path):
    return Path(path).read_text(encoding="latin-1")

def defs(pack, prefix):
    return dict(re.findall(rf'(?m)^({prefix}\w+)\s*=\s*"([^"]*)"\s*$',
                           read(MISSION / "assets" / f"{pack}.sqs")))

def append_arrays(profile, name):
    return [json.loads(m) for m in re.findall(
        rf"(?m)^{re.escape(name)} = {re.escape(name)} \+ (\[[^\n]+\])$", profile)]

class WGL512PackTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name)
        self.config = (MISSION / "worldConfig.sqs").read_text(encoding="utf-8-sig")

    def export(self, pack):
        return create_mission_package(MISSION, self.out, "Malden",
                                      "Assault" + pack, self.config,
                                      5000, 6000, asset_pack=pack)

    def test_profile_catalog_is_complete_and_matches_shared_gameplay(self):
        self.assertEqual(PROFILES, ("vanilla", "ww4", "wgl512"))
        for prefix in ("assetClass", "assetName"):
            sets = {pack: set(defs(pack, prefix)) for pack in PROFILES}
            self.assertEqual(sets["wgl512"], sets["vanilla"], prefix)
            self.assertEqual(sets["wgl512"], sets["ww4"], prefix)
        wgl = read(MISSION / "assets/wgl512.sqs")
        self.assertFalse(unknown_classes(wgl))
        self.assertIn("assetClassLaserDesignatorMagazine = \"WGL_LaserDesignatorMag\"", wgl)
        self.assertIn("assetProfileReady = true", wgl)
        for script in ("ww4_arsenal/add_weapon.sqs", "ww4_arsenal/apply_loadout.sqs"):
            self.assertIn("assetClassLaserDesignatorMagazine", read(MISSION / script))

    def test_classes_and_roles_confirmed_from_uploaded_lists(self):
        c = defs("wgl512", "assetClass")
        n = defs("wgl512", "assetName")
        # The specific classnames below appear in the supplied Excel lists.
        expected = {
            "WestRifle": "WGL_M16", "WestRifleMagazine": "WGL_M16Mag",
            "WestPilot": "WGL_SoldierWPilot", "WestMedic": "WGL_SoldierWMedic",
            "WestHeavyTransportHeli": "WGL_CH47D",
            "WestCobra": "WGL_AH1", "WestIFV": "WGL_M2A2",
            "WestAPC": "WGL_M113", "WestTank": "WGL_M60A3",
            "EastRifle": "WGL_AK74", "EastRifleMagazine": "WGL_AK74Mag",
            "EastAttackJet": "WGL_SU25", "EastAttackHeli": "WGL_Mi24",
            "EastHeavyStaticGun": "WGL_NSVStaticMG",
            "BTR80": "WGL_BTR80", "BTR80ExportR": "WGL_BTR80FIA",
            "ResistanceRifle": "WGL_AK47",
            "ResistanceEmptyTruck": "WGL_UralFIA",
            "ResistanceArmedLightVehicle": "WGL_BRDMFIA",
            "ResistanceAirDefense": "WGL_ZSU_R",
            "Scud": "WGL_Scud",
            "WestAmmoBox": "WGL_ReammoBoxWest",
            "WestLaserJet": "WGL_A10GBU",
        }
        for role, cls in expected.items():
            self.assertEqual(c["assetClass" + role], cls, role)
        self.assertEqual(n["assetNameBTR80"], "BTR-80")
        self.assertEqual(n["assetNameBTR80ExportR"], "BTR-80 FIA")
        self.assertEqual(n["assetNameWestIFV"], "M2A2 Bradley")

    def test_editor_slots_and_faction_unit_arrays(self):
        profile = read(MISSION / "assets/wgl512.sqs")
        slots = manifest(profile, "assetEditorSlots")
        self.assertEqual(len(slots), 12)
        self.assertEqual(slots[0], ["plr", "WGL_CommanderW"])
        self.assertEqual(slots[3], ["medic1", "WGL_SoldierWMedic"])
        self.assertTrue(all(cls.startswith("WGL_") for _,cls in slots))
        self.assertEqual(manifest(profile, "assetRequiredAddons"), [])
        for name, count in (("assetEastFactions", 2), ("assetResFactions", 3)):
            factions = append_arrays(profile, name)
            self.assertEqual(len(factions), count)
            for faction in factions:
                self.assertEqual(len(faction), 1)
                self.assertEqual(len(faction[0][1]), 17)
                self.assertTrue(all(c.startswith("WGL_") for c in faction[0][1]))
        self.assertEqual(len(append_arrays(profile, "WW4_PlayerModelGroups")), 3)
        for group in append_arrays(profile, "WW4_PlayerModelGroups"):
            self.assertTrue(all(cls.startswith("WGL_") for cls in group[0][1]))

    def test_arsenal_ammunition_from_weplist(self):
        profile = read(MISSION / "assets/wgl512.sqs")
        entries = [line[0] for line in append_arrays(profile, "WW4_ArsenalEntries")]
        families = [line[0] for line in append_arrays(profile, "WW4_ArsenalFamilies")]
        self.assertEqual(len(entries), 38)
        self.assertEqual(sorted(i for _, indexes in families for i in indexes),
                         list(range(len(entries))))
        weapons = {weapon: mags for weapon, label, mags in entries}
        for weapon, mag in {
            "WGL_M16": "WGL_M16Mag",
            "WGL_M4A1SD": "WGL_M4A1SDMag",
            "WGL_AK74": "WGL_AK74Mag",
            "WGL_AK47": "WGL_AK47Mag",
            "WGL_PKM": "WGL_PKMMag",
            "WGL_RPK74": "WGL_RPK74Mag",
            "WGL_M21": "WGL_M21Mag",
            "WGL_M240": "WGL_M240Mag",
            "WGL_RPG7Launcher": "WGL_RPG7Mag",
            "WGL_CarlGustavLauncher": "WGL_CarlGustavMag",
            "WGL_LaserDesignator": "WGL_LaserDesignatorMag",
        }.items():
            self.assertIn(mag, weapons[weapon], weapon)

    def test_wgl_export_contains_single_profile_and_isolated_editor_units(self):
        wgl = self.export("wgl512")
        self.assertEqual((wgl / "assetPack.txt").read_text().strip(), "wgl512")
        self.assertTrue((wgl / "assets/wgl512.sqs").exists())
        self.assertFalse((wgl / "assets/ww4.sqs").exists())
        self.assertFalse((wgl / "assets/vanilla.sqs").exists())
        self.assertIn('[] exec "assets\\wgl512.sqs"',
                      read(wgl / "assets/selection.sqs"))
        sqm = read(wgl / "mission.sqm")
        self.assertEqual(len(re.findall(r'\bvehicle="WGL_[^"]+"', sqm)), 12)
        self.assertIn('vehicle="WGL_CommanderW"', sqm)
        self.assertIn('vehicle="WGL_SoldierWMedic"', sqm)
        self.assertNotRegex(sqm, r'(?i)ww4(?:ext)?_')
        self.assertIn("editorupdate102", sqm)
        for file in wgl.rglob("*"):
            if not file.is_file() or file.name == "worldConfig.sqs":
                continue
            if file.suffix.lower() in (".sqm", ".sqs", ".sqf", ".ext", ".hpp"):
                self.assertFalse(unknown_classes(file.read_bytes().decode("latin-1")), str(file))

    def test_shared_gameplay_and_frevive_remain_unchanged(self):
        wgl = self.export("wgl512")
        vanilla = self.export("vanilla")
        for file in MISSION.rglob("*"):
            if not file.is_file():
                continue
            rel = file.relative_to(MISSION)
            if rel.parts[0] == "assets" or file.name in ("mission.sqm", "worldConfig.sqs"):
                continue
            self.assertEqual((wgl / rel).read_bytes(), (vanilla / rel).read_bytes(), str(rel))
            self.assertEqual((wgl / rel).read_bytes(), file.read_bytes(), str(rel))

    def test_gui_wgl_choice_exists_without_changing_vanilla_default(self):
        text = read(ROOT / "tools/generate_world_config_gui.py")
        self.assertIn('tk.StringVar(value="Vanilla CWA")', text)
        self.assertIn('"WGL 5.12"', text)
        self.assertIn('"WGL 5.12": "wgl512"', text)

    def test_no_wgl_pack_fails_before_output_published(self):
        source = self.out / "old.eden"
        shutil.copytree(MISSION, source)
        (source / "assets/wgl512.sqs").unlink()
        with self.assertRaisesRegex(ValueError, "Selected pack unavailable"):
            create_mission_package(source, self.out, "Malden", "MissingWGL",
                                   self.config, 5000, 6000, asset_pack="wgl512")
        self.assertFalse((self.out / "MissingWGL.Malden").exists())
        self.assertFalse(list(self.out.glob(".mission-build-*")))

if __name__ == "__main__":
    unittest.main()
