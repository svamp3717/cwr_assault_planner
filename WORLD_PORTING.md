# Moving Assault Planner to another world

World-specific objective/traffic locations now live in `cwr_assault_planner_v203.eden/worldConfig.sqs`.

## Recommended workflow

1. Copy/rename the mission folder for the target world as usual.
2. Open that world's `config.cpp` and find its `class Names` entries.
3. Replace the three location arrays in `worldConfig.sqs`:

   - `missionLocationLabels = ["Name 1","Name 2",...]`
   - `missionLocationXs = [x1,x2,...]`
   - `missionLocationYs = [y1,y2,...]`

   Keep all three arrays in the same order and with the same number of entries. Keep at least six locations so the objective cluster and non-objective insertion staging logic always has candidates.

   The arrays deliberately stay on one line. Old OFP/CWA SQS can reject multiline array expressions with `Invalid number in expression`.
4. Set `worldName`, `missionBaseX`, and `missionBaseY` to a safe setup/staging point on the target world.
5. Set `worldMinX`, `worldMinY`, `worldMaxX`, and `worldMaxY` to safe usable map bounds for generated insertion positions.
6. Leave `worldUseEditorLocationMarkers = false` for the normal portable setup.

## What changed with markers

Only the editor-placed `site_*` location markers were removed from `mission.sqm`. All functional mission markers are kept, including objective, LZ, extraction, logistics, rescue, steal, pilot, reinforcement, and support markers.

With `worldUseEditorLocationMarkers = false`, mission scripts read numeric X/Y values directly from `worldConfig.sqs`. No `site_*` markers are required.

This direct-coordinate path is necessary for Operation Flashpoint / Cold War Assault because that engine cannot create map markers at runtime. The later `createMarker` command used by ArmA therefore cannot be used as a compatibility layer here.

If you deliberately want the old editor-marker workflow, set `worldUseEditorLocationMarkers = true` and add `site_0`, `site_1`, etc. back to the mission in the same order as the three location arrays. In that mode the existing marker positions override the configured X/Y values where location positions are read.

## One world data file

The values normally changed while porting are kept in `worldConfig.sqs`: location names and coordinates, the setup/base point, and the usable world bounds. The rest of the mission keeps its functional editor markers and gameplay scripts unchanged wherever possible.
