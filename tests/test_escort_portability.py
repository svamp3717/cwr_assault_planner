"""Regression checks for numeric escort destinations and traffic. CWA runtime requires playtesting."""
import re
import unittest
from pathlib import Path

MISSION = Path(__file__).resolve().parents[1] / "cwr_assault_planner_v203.eden"

def script(name):
    return (MISSION / name).read_text(encoding="latin-1")

class EscortPortabilityTests(unittest.TestCase):
    def test_shared_destination_selection(self):
        helpers = script("worldPlacementFunctions.sqf")
        for symbol in ("worldTownPosition", "worldPositionInBounds", "worldPositionIsObjective", "worldNearestTown", "worldFindEscortTown"):
            self.assertIn(symbol + " = {", helpers)
        self.assertIn("missionTownXs select _i", helpers)
        self.assertIn("missionTownYs select _i", helpers)
        self.assertIn("if (worldUseEditorLocationMarkers) then", helpers)
        self.assertIn("500,-1,[]] call worldNearestTown", helpers)
        self.assertIn("250,-1,[]] call worldNearestTown", helpers)
        for name in ("downedPilotObjective.sqs", "civilianRescueDestination.sqs", "stealVehicleObjective.sqs"):
            with self.subTest(name=name):
                s = script(name)
                self.assertIn("call worldFindEscortTown", s)
                self.assertIn("call worldTownPosition", s)
                self.assertNotIn("getMarkerPos", s)
                for i in range(1, 6):
                    self.assertIn(f"objectiveType{i} = 0", s)
        s = script("objectiveAssets.sqs")
        for i in range(1, 6):
            for ready in ("civilianRescueDestinationReady", "downedPilotObjectiveReady", "stealVehicleSiteReady"):
                self.assertRegex(s, rf"@ {ready}\n\? objectiveType{i} == 0 : objectiveTypeLabel{i} = \"Clear Area\"")
        self.assertNotIn("getMarkerPos", script("enemyRoutePatrols.sqs"))

    def test_escorts_require_safe_altitude_and_server_completion(self):
        self.assertIn("getPos (vehicle _pilot) select 2) > 5", script("downedPilotMonitor.sqs"))
        self.assertEqual(script("civilianRescueMonitor.sqs").count("getPos (vehicle _u) select 2) > 5"), 4)
        for name in ("pilotEscortStep.sqs", "civilianEscortStep.sqs"):
            s = script(name)
            self.assertIn("getPos _leaderVehicle select 2) > 5", s)
            self.assertIn('#leaveOldVehicle', s)
            self.assertIn("unassignVehicle", s)
        for name in ("mpClientTrackDownedPilot.sqs", "mpClientTrackRescueCivilian.sqs"):
            self.assertNotRegex(script(name), r"\)\) <= (14400|19600)")
        for name, k in (("downedPilotMonitor.sqs","Pilot"),("civilianRescueMonitor.sqs","Rescue"),("stealVehicleMonitor.sqs","Steal")):
            for i in range(1,6):
                self.assertIn(f'publicVariable "objective{k}Failed{i}"', script(name))
                self.assertIn(f'publicVariable "objective{k}Ready{i}"', script(name))

    def test_nearby_traffic_profiles_and_persistence(self):
        s = script("civilianNonObjectiveCars.sqs")
        self.assertIn("_first = [_sx,_sy,0,-1,[]] call worldNearestTown", s)
        self.assertIn("_second = [_sx,_sy,0,-1,[_first]] call worldNearestTown", s)
        self.assertIn('_roll >= 1 && !(_i in _guaranteed)', s)
        self.assertIn("call worldPositionIsObjective", script("civilianNonObjectiveCarProfile.sqs"))
        self.assertIn("call worldOffsetPosition", script("civilianNonObjectiveCarProfile.sqs"))
        worker = script("civilianNonObjectiveCarTown.sqs")
        for text in ("_carDamage = getDammage _car", "_carFuel = fuel _car", "_car setDammage _carDamage", "_car setFuel _carFuel", "_carClass = assetClassSkodaCiv"):
            self.assertIn(text, worker)

    def test_sqs_labels_resolve(self):
        for name in ("downedPilotObjective.sqs", "civilianRescueDestination.sqs", "stealVehicleObjective.sqs", "enemyRoutePatrols.sqs", "civilianNonObjectiveCars.sqs", "civilianNonObjectiveCarTown.sqs", "pilotEscortStep.sqs", "civilianEscortStep.sqs", "mpClientPilotMarkers.sqs", "mpClientRescueMarkers.sqs", "mpClientStealMarkers.sqs"):
            s = script(name)
            labels = set(re.findall(r"(?m)^\s*#(\w+)", s))
            targets = set(re.findall(r'\bgoto\s+"(\w+)"', s, re.I))
            self.assertFalse(targets-labels, (name,targets-labels))

    def test_selection_reference_cases(self):
        # Independent reference arithmetic for documented SQF behaviour.
        def nearest(source, towns, occupied, bounds, minimum, maximum=-1, excluded=()):
            options = []
            for i, (x,y) in enumerate(towns):
                if i in excluded or not(bounds[0]<=x<=bounds[2] and bounds[1]<=y<=bounds[3]):
                    continue
                if any((x-a)**2+(y-b)**2<=1 for a,b in occupied):
                    continue
                d2 = (x-source[0])**2+(y-source[1])**2
                if d2>=minimum**2 and (maximum<0 or d2<=maximum**2):
                    options.append((d2,i))
            return min(options)[1] if options else -1
        towns = [(1000,1000),(1200,1000),(1300,1000),(1700,1000),(1450,1000),(1700,1700),(0,0)]
        bounds = (500,500,2000,2000)
        occupied = [(1000,1000),(1450,1000)]
        self.assertEqual(nearest(towns[0],towns,occupied,bounds,500),3)
        self.assertEqual(nearest(towns[0],towns[:3],occupied,bounds,500),-1)
        self.assertEqual(nearest(towns[0],towns[:3],occupied,bounds,250),2)
        self.assertEqual(nearest(towns[0],towns,occupied,bounds,0),1)
        self.assertEqual(nearest(towns[0],towns,occupied,bounds,0,excluded=(1,)),2)

if __name__ == "__main__":
    unittest.main()
