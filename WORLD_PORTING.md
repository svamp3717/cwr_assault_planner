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
new base point. XY offsets are preserved. **Editor unit elevation (m)** is an optional full-mission setting; enter the target setup elevation only if known (blank keeps the template elevation). The override applies only to playable units; marker and trigger heights are preserved. The config parser cannot determine the terrain height from `class Names`. Open and save the generated mission in CWA's editor to verify ground placement, especially on steep terrain.

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


## Runtime staging and validation

The mission loads `worldPlacementFunctions.sqf` after `worldConfig.sqs`. Runtime friendly vehicles, allied infantry, and enemy reserves use relative setup offsets that are fitted within the usable world rectangle. Extraction, logistics and air/ground reinforcement approaches use bounded target-relative positions; aircraft headings follow the selected approach rather than assuming Everon's direction. Existing off-map departure paths are redirected inward when needed.

Choose a flat inland setup point with clear space for the staging layout (roughly 640 × 850 m on ordinary maps). Rectangular bounds do not establish whether a location is on land, flat, or free of obstacles. In the editor and in hosted/dedicated multiplayer, check truck/APC/heli/foot insertions, Radio Alpha/Bravo/Charlie, enemy attack air and both reinforcement types on the target terrain. FRevive now defaults to stationary corpses (no automatic shore relocation); see below.


## FRevive body-position regression

Automatic water recovery is disabled by default via `FREVIVE_ANTI_WATER = false` in `mpFReviveBootstrap.sqs`. This does not disable revival, spectator mode, the 300-second timeout or the airborne replacement-unit protocol. A corpse can still settle or fall naturally; FRevive tracks that real position.

For a terrain that has been playtested, change the setting to `true` to enable optional shore recovery. The worker checks the corpse's actual ASL height, checks a private local sea-plane probe, searches at most 600 m within the configured bounds, never falls back to another soldier, and aborts if the body moves, locality changes or revival begins. If no shore is found, the body stays where it is. The probe-based test is conservative and still requires testing in CWA, especially on custom terrain.

Test on a hosted and a dedicated server: die on land, wait without reviving, observe from another player, revive at the corpse, die on a slope, die in a vehicle, and incapacitate two players at once. Verify the owner and remote clients agree on revival and that the spectator follows the actual body. With the optional setting enabled, additionally test drowned units near shore and far offshore. A player whose corpse is out of reach can still time out normally when recovery is disabled.

The hidden replacement continues to be held above 7000 m until revival; do not change that altitude encoding without also updating the mission's multiplayer and extraction checks.


## Basic map editor

Open the **Map editor** tab after loading config.cpp. The north-up coordinate grid shows imported locations, the base, usable bounds (green), and the objective edge margin (dashed). It does not show terrain imagery or distinguish land from water.

- **Select / move**: click a marker to select it in the Locations tab, or drag it to reposition it inside the usable bounds.
- **Add marker**: click inside the bounds and name a new location.
- **Set base**: click inside the bounds to update Base X/Y.
- **Rename / Delete**: edit the selected location. Keep at least six locations.
- Scroll to zoom around the pointer, middle/right drag to pan, **Fit map** to reset, and toggle **Labels** to reduce clutter.

Map edits are kept in memory and exported by the normal Generate/Create mission action. They modify the numeric location arrays, not config.cpp or CWA editor markers. Reloading discards changes after confirmation. Re-infer base/bounds preserves edited locations. Keep **Use editor site_* markers** off when exporting edits. Verify placement against the actual CWA terrain.


## Asset pack selection (full mission exports)

Enable **Create a complete new mission folder**, then select **Vanilla CWA** (default) or **WW4 + WW4 Extended** in Asset pack. Config-only exports do not change assets. Both packs share exactly the same gameplay scripts.

### Centralized asset profiles

| File | Purpose |
| --- | --- |
| `assets/ww4.sqs` | All WW4 runtime class definitions, faction tables, vehicle pools, arsenal, model catalog and playable-slot metadata. |
| `assets/vanilla.sqs` | Corresponding stock CWA classes and catalogs. |
| `assets/selection.sqs` | Loads the selected profile before mission startup on each machine. |
| `tools/asset_packs.py` | Selects the pack and updates only editor class/addon metadata in the exported mission copy. |

The source template defaults to WW4 so it can still be opened directly. In a generated mission, only the selected profile is included. The pack is recorded in `assetPack.txt`. The exporter rejects unresolved WW4 class literals in vanilla missions; it no longer searches and replaces gameplay script class names.

### Edit or extend the profile

Edit the role value inside the relevant profile, not the gameplay script. For example:

```sqs
assetClassWestHeavyTransportHeli = "Ch47D"
assetClassWestAPC = "M113"
```

The insertion scripts use these variables and therefore do not need changing for compatible replacements. Choose aircraft and transport classes with appropriate side, seating, and weapons. Update the faction tables, vehicle pools, arsenal magazine compatibility and model catalog as needed. Keep the 17-role faction order aligned with `ww4FactionSelect.sqs`; keep editor slot and addon arrays on one line. Both profiles must define each referenced `assetClass...` role. To add a third pack, create a profile and extend the generator's supported pack list and UI.

CWA reads `mission.sqm` before script execution, so the generator must still apply the selected profile's editor manifest (`assetEditorSlots`, `assetRequiredAddons`) at export time. The source editor file retains WW4 playable slots for direct WW4 editing. Legacy WW4-prefixed scripts, dialogs and variables are shared identifiers, not addon dependencies. FRevive's internal engine helper classes are unchanged.

Vanilla vehicle variety is smaller. Stock trucks carry reinforcement waves; stock APCs substitute for armed jeep patrols. Resistance uses stock Shilka/static machine guns with its own crew where direct faction-specific equivalents do not exist. `editorupdate102` and terrain-specific dependencies remain; this is a non-WW4 profile, not a guaranteed addon-free mission. Use the original template containing both packs to switch profiles. Test both sides, static weapons, arsenal, cargo capacities, extraction and revival in hosted/dedicated CWA. The automated tests check static references and actual folder exports, not game-engine execution.

Reference tables: https://www.ofpec.com/COMREF/index.php?action=read&id=69 and https://www.ofpec.com/COMREF/index.php?action=read&id=67.


## Escort destinations and nearby civilian vehicles

Pilot, civilian rescue and vehicle theft now share numeric settlement selection in worldPlacementFunctions.sqf. The nearest in-bounds non-objective settlement at least 500 m away is preferred; on small maps the minimum relaxes to 250 m. If no suitable settlement exists (or a required pilot/vehicle cannot be created), the objective becomes Clear Area instead of pointing to the origin or preventing mission completion. Legacy editor markers are only read in legacy mode, with numeric fallback when missing. A rescue is not secured while the escort vehicle is airborne above 5 m. Ground transport can still complete the delivery. Multiplayer clients keep target markers until server completion/deletion and receive the final ready/failed status.

Civilian vehicles now have guaranteed streamed profiles at the two nearest eligible non-objective towns per active objective, with duplicates shared; other towns retain the 25% chance. Vehicles spawn when a player is within 1000 m and stream out beyond 1300 m. Damage and fuel are remembered across streaming, and a failed class spawn retries with the profile's standard civilian car. Patrol routes also use bounded non-objective towns and skip impossible routes. These are coordinate/bounds checks, not water, road or obstacle checks: test the actual terrain in CWA.


### Profile display names

Player-facing vehicle names use the corresponding assetName variables next to the assetClass variables in each profile. Change both together when replacing an asset. The theft objective draws a class/name pair, including its fallback; air support, destruction objectives, insertion, armored support, extraction and logistics messages use those names too. Legacy script variables, dialog control identifiers and internal comments may still use historical names. The vanilla preset labels its BTR-80 replacement as BMP-2 (East) or BMP-1 (Resistance).


## WarGames League 5.12 asset preset

For a complete mission export, select **WGL 5.12**. The template contains `assets/wgl512.sqs`, which is loaded on each client/server instead of the inactive WW4 or vanilla profile. Its editor slots, infantry factions, vehicle pools, models, weapon/magazine catalog and display names use WGL-specific class names where the uploaded source lists explicitly identify them. Ordinary CWA civilians, structures and other common engine helpers remain stock where there is no verified WGL alternative. The 12 playable editor units become WGL BLUFOR.

Source catalogs supplied for this preset: `unitlist.xls` (WGL CfgVehicles and vehicles), `inflist.xls` (infantry, role names, loadouts), `weplist.xls` (weapons/magazine compatibility), and `grouplist.xls` (squad compositions). The files are historical reference lists from 2006; they are not a copy of the installed WGL 5.12 `config.cpp`. WGL's specific `CfgPatches` dependency identifiers are **not listed** in these spreadsheets, so the exporter deliberately does not invent them. It removes WW4 declarations and preserves the existing `editorupdate102` requirement. **Start CWA with the complete WGL 5.1 installation and WGL 5.12 update on each multiplayer client and the server.** The preset does not install or activate WGL.

WGL is a gameplay conversion, not merely an asset replacement. Test playable slot placement, WGL unit loadouts, armor/cargo capacity, air support, WGL injury treatment and normal respawn, logistics deliveries, WGL ammunition compatibility and mission extraction in hosted and dedicated play. The automated tests only verify profile structure, known historical classnames and output packaging. Never treat them as engine compatibility certification.

WGL references: https://community.bistudio.com/wiki/Wargames:Help_Site:Installation and https://www.moddb.com/mods/wargames/downloads/wgl-512-patch .

## FRevive policy by asset preset

- **Vanilla CWA and WW4 + WW4 Extended:** FRevive remains available and enabled by default; the mission-settings toggle can turn it off. The original FRevive 0.51 `Start.sqs` and `Functions.sqf` files have been restored to their state prior to the experimental array-lookup/timer patch.
- **WGL 5.12:** FRevive is always disabled. The profile is selected before `init.sqs` sets the default toggle, the settings dialog cannot re-enable it, the squad leader broadcasts it disabled, and `mpFReviveBootstrap.sqs` independently skips `FRevive\\Start.sqs` on every machine. It still sets `mpFReviveStarted = true`, so server/client startup waits are satisfied.

WGL medical treatment is handled by WGL itself. **Turning off FRevive does not replace the mission's `respawn=INSTANT` behavior** or guarantee that WGL provides a dead-player revival mechanic. Test WGL injury treatment and instant respawn in hosted/dedicated CWA; verify Vanilla/WW4 FRevive separately.
