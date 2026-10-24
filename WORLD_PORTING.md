# Moving Assault Planner to another world

World-specific objective/traffic locations live in `cwr_assault_planner_v203.eden/worldConfig.sqs`.

## GUI generator

For a desktop interface with folder pickers, run:

```bash
python tools/generate_world_config_gui.py
```

The GUI uses only Python's standard library (`tkinter`) and shares the same parser/generator code as the command-line tool.

Workflow:

1. Click **Browse folder...** under **Source world** and choose the terrain/world folder containing `config.cpp`.
2. The GUI loads `config.cpp`, finds `class Names`, and previews the parsed locations with their X/Y coordinates.
3. Review or edit the inferred world name, base point, and usable world bounds.
4. Optionally select a location in the preview and click **Use selected location as base**.
5. Click the **Output folder** picker and choose where `worldConfig.sqs` should be written, normally the target mission folder.
6. Click **Generate worldConfig.sqs**.

The source picker first checks `<selected folder>/config.cpp`. If it is not there, it searches below the selected folder and prefers the shallowest unambiguous `config.cpp`. If several equally likely files exist, choose the more specific world folder instead of letting the tool guess which addon config humanity intended this time.

The generated location arrays remain single-line CWA-safe arrays. The **Use editor site_* markers** checkbox is off by default and should normally stay off.

## Objective placement on small maps

The **Objective / insertion placement (metres)** panel in the GUI controls
four values stored in generated `worldConfig.sqs`. No manual editing of
`randomize.sqs` is needed for missions generated with this branch:

| GUI control | World config variable | Effect |
| --- | --- | --- |
| Min objective-to-staging | `worldStageMinClearance` | Preferred minimum distance from a non-objective staging town to **each active objective** |
| Max objective-to-insertion | `worldStageMaxDistance` | Preferred maximum insertion distance to the **furthest active objective** |
| Objective edge margin | `worldObjectiveEdgeMargin` | Objective locations must be inside the playable map bounds by this margin where enough points exist |
| Aircraft extra offset | `worldAirStageOffset` | Extra aircraft staging distance beyond the selected landing zone |

**Auto-scale distances to usable map size** is enabled by default. It
uses the shorter side of the **usable bounds** (Max X minus Min X and
Max Y minus Min Y), so adjusting the bounds updates the suggestions.
For a 4,000 m × 4,000 m usable area, defaults are **800 m / 2,600 m /
400 m / 800 m** in the order shown above. A larger world caps these
values at **1,500 m / 6,000 m / 500 m / 1,600 m**. Uncheck auto-scale
to enter custom distances before generating.

Objective candidates are drawn from the terrain's `class Names`
locations, not arbitrary coordinates. If an edge margin excludes too
many locations for the requested objective count, the mission halves
the margin until enough locations remain. If no locations are within
the configured usable bounds, it falls back to all locations so the
mission can still start. Staging distance constraints are also
**preferences**, not guarantees: if no non-objective location meets
both distance limits, the mission chooses the closest available fallback.
Landing zones and aircraft positions receive additional padding from
the map edges, but terrain quality and water still need editor testing.

When generating **only** `worldConfig.sqs`, install it into a mission
folder that already has the updated `randomize.sqs` and `init.sqs`
from this branch. They are automatically included when generating a
**complete mission folder** from the updated repository template.

For scripting, the command-line generator also accepts
`--stage-min-clearance`, `--stage-max-distance`,
`--objective-edge-margin`, and `--air-stage-offset`, all in metres.
Omitted values are auto-scaled.

## Create a complete mission folder from the GUI

To create a playable/editable mission for the new terrain instead of just a
`worldConfig.sqs` file:

1. Load the target terrain's `config.cpp` as above, and verify its **World name**
   is the actual **CfgWorlds class name** (the required mission folder extension,
   which may be different from the terrain's display name). Verify the base point
   and bounds too.
2. In **Output**, choose the **Destination folder** (normally your CWA/OFP user
   `missions` directory or a staging directory, **not** the mission template).
3. Check **Create a complete new mission folder (copy all mission files)**.
4. Choose an existing **Mission template** folder. The repository's
   `cwr_assault_planner_v203.eden` is preselected when available.
5. Set **New mission name** (without the world extension) and leave
   **Use editor site_* markers** **unchecked**.
6. Click **Create mission folder**.

The GUI creates `<mission name>.<world class>/` within the destination folder
(e.g. `cwr_assault_planner_v203.Abel/` for the original Malden terrain).
It copies **every file and subdirectory** from the selected template, replaces
`worldConfig.sqs` with the generated world-specific version, and relocates the
editor-placed units, markers, and triggers in `mission.sqm` relative to the
new base point. It preserves their original relative offsets and stored
elevations. Open the generated mission in the game editor to check unit height
and terrain suitability before playing, especially on steep terrain.

**Existing mission folders are never overwritten**; choose a different mission
name if the destination name already exists. A partially failed copy is cleaned
up. Uncheck the full-mission option to keep the original single-file generator
behavior and overwrite confirmation.

Run the packaging tests with:

```bash
python -m unittest discover -s tests -v
```

## Generate it from config.cpp on the command line

The command-line helper remains useful for scripts and batch conversions:

```bash
python tools/generate_world_config.py /path/to/config.cpp -o cwr_assault_planner_v203.eden/worldConfig.sqs
```

The script finds the `class Names` block, extracts each location `name` and `position[]`, and writes the CWA-safe one-line `missionLocationLabels`, `missionLocationXs`, and `missionLocationYs` arrays.

It also tries to detect the world class containing `class Names`, uses `centerPosition[]` as the default `missionBaseX/Y` when available, and derives usable bounds from `mapSize`/`worldSize` or the world center. Review the generated base point and bounds before shipping a port.

Useful overrides:

```bash
python tools/generate_world_config.py config.cpp -o worldConfig.sqs --world-name Malden
python tools/generate_world_config.py config.cpp -o worldConfig.sqs --base-location "Airport"
python tools/generate_world_config.py config.cpp -o worldConfig.sqs --base-x 5000 --base-y 5000
python tools/generate_world_config.py config.cpp -o worldConfig.sqs --world-size 12800
python tools/generate_world_config.py config.cpp -o worldConfig.sqs --min-x 250 --min-y 250 --max-x 12550 --max-y 12550
```

Both generators use only the Python standard library.

## Manual workflow

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
