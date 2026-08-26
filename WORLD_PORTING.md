# Moving Assault Planner to another world

World-specific objective/traffic locations now live in `cwr_assault_planner_v203.eden/worldConfig.sqs`.

## Recommended workflow

1. Copy/rename the mission folder for the target world as usual.
2. Open that world's `config.cpp` and find its `class Names` entries.
3. Replace `worldLocations` in `worldConfig.sqs` with entries in this form:

   `["Location name",[x,y]]`

   Keep at least six locations so the objective cluster and non-objective insertion staging logic always has candidates.
4. Set `worldName`, `missionBaseX`, and `missionBaseY` for the target world.
5. Leave `worldUseEditorLocationMarkers = false` to have the mission create/reposition hidden `site_*` compatibility markers automatically.

## Optional editor markers

The old `site_0`, `site_1`, ... editor markers are no longer the location source of truth. With `worldUseEditorLocationMarkers = false`, the values in `worldConfig.sqs` drive their positions at runtime, so those editor markers may be omitted when building a port.

Set `worldUseEditorLocationMarkers = true` only if you deliberately want the previous workflow where manually placed `site_*` markers provide the positions. In that mode, keep the marker count and order aligned with `worldLocations`.

## Why compatibility markers still exist at runtime

Several legacy CWA-safe scripts use `getMarkerPos` and marker names. Replacing every one of those call sites would make a simple world-porting change much larger and riskier. The bootstrap therefore generates hidden compatibility markers from the single world config instead. Mission logic keeps behaving the same while ports stop requiring marker-by-marker editor work.
