# Moving Assault Planner to another world

World-specific objective/traffic locations now live in `cwr_assault_planner_v203.eden/worldConfig.sqs`.

## Recommended workflow

1. Copy/rename the mission folder for the target world as usual.
2. Open that world's `config.cpp` and find its `class Names` entries.
3. Replace `worldLocations` in `worldConfig.sqs` with entries in this form:

   `["Location name",[x,y]]`

   Keep at least six locations so the objective cluster and non-objective insertion staging logic always has candidates.
4. Set `worldName`, `missionBaseX`, and `missionBaseY` to a safe setup/staging point on the target world.
5. Leave `worldUseEditorLocationMarkers = false` for the normal portable setup.

## What changed with markers

Only the editor-placed `site_*` location markers were removed from `mission.sqm`. All functional mission markers are kept, including objective, LZ, extraction, logistics, rescue, steal, pilot, reinforcement, and support markers.

With `worldUseEditorLocationMarkers = false`, `worldConfig.sqs` creates hidden `site_0`, `site_1`, etc. compatibility markers at runtime from `worldLocations`. Existing legacy CWA-safe scripts can therefore keep using `getMarkerPos` without requiring the mission porter to place dozens of location markers manually.

If you deliberately want the old editor-marker workflow, set `worldUseEditorLocationMarkers = true` and add `site_0`, `site_1`, etc. back to the mission in the same order as `worldLocations`.

## Why runtime compatibility markers remain

Several legacy scripts still consume marker names. Replacing every marker-based call site would turn a world-portability change into a much larger gameplay rewrite. Runtime compatibility markers keep that old interface while making `worldConfig.sqs` the location source of truth.
