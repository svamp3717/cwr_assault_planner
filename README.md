# CWR Assault Planner v203

Randomized cooperative mission for **ArmA: Cold War Assault / Operation Flashpoint** on **Everon**, built around WW4 units and vehicles.

This repository contains the `assault_planner_v203_no_intro_outro_test.eden` mission build. The mission uses the classic OFP/CWA SQS mission format and generates the operation after mission start from a configurable assault-planning screen.

## Required mods

Launch CWA/OFP with these mod folders enabled:

- `WW4_EXT`
- `WW4_EXT_VEH`
- `WW4EXT_CW`

Example mod string:

```text
WW4_EXT;WW4_EXT_VEH;WW4EXT_CW
```

### Add-on compatibility note

`mission.sqm` also references the add-on class `editorupdate102`, used by the mission's static artillery objective. Make sure that add-on is available in your installation if it is not already supplied by your existing WW4/CWA setup.

## Mission features

- **Randomized Everon assault:** operation locations, objectives, enemy composition, support and insertion are generated at mission start.
- **Co-op / multiplayer support:** a WEST player squad with selectable AI squad strength and synchronized mission setup.
- **1 to 5 objectives** per operation.
- **10 objective types:** Clear Area, Destroy Strategic Target, Collect Intel, Destroy Ammo Box, Destroy Communications, Neutralize Mortar Position, Destroy Fuel Depot, Save Civilians, Steal a Vehicle, and Recover Downed Pilot.
- **Objective filtering:** use all objective types randomly or enable a custom subset in the planner.
- **Multiple insertion methods:** on foot, truck, APC, direct paradrop, or helicopter insertion.
- **Configurable opposition:** random, EAST, or Resistance opposition with WW4 faction selection.
- **Enemy force controls:** infantry strength, vehicle strength, AI skill, fortified bunker defenses, patrol density, enemy aircraft frequency, and reinforcement strength.
- **Dynamic enemy activity:** objective defenders, building defenders, streamed route patrols, ground reinforcements, airborne reinforcements, attack aircraft, armed vehicles, and scripted mortar/artillery fire.
- **Friendly support controls:** up to four additional allied WEST squads, optional armored support, and radio-called air support with target selection.
- **Radio logistics drop:** one operation-level request for a Jeep, HMMWV, or WW4 Arsenal ammo box, delivered by Chinook.
- **Final extraction:** Radio Bravo calls a Chinook to the squad leader's chosen pickup position; early calls can wait until the operation is complete.
- **Civilian systems:** ambient civilians, persistent/streamed civilian traffic, parked vehicles, rescue objectives, Follow Me / Stop controls, and vehicle transport for rescued civilians.
- **Recover Downed Pilot:** locate a wounded WEST pilot, control his movement, transport him if needed, and escort him to a safe settlement.
- **Steal a Vehicle:** capture a designated enemy vehicle and deliver it to a separate recovery location.
- **WW4 Arsenal:** optional mission setting with support for the player and squad AI.
- **FRevive:** bundled and toggleable from Mission Settings; when disabled, the mission falls back to its normal instant respawn behavior.
- **Mission settings:** WW4 Arsenal, FRevive, and mission music can be enabled or disabled before launch.
- **Environment controls:** selectable start time and weather presets.
- **Debug option:** optional diagnostics and reinforcement transport markers for testing.
- **Everon location pool:** imported settlement, military, landmark, harbour, industrial, and unnamed-area markers are used by the objective, patrol, rescue, traffic, and recovery systems as appropriate.
- **CWA-era scripting:** the mission intentionally stays with OFP/CWA-compatible SQS/SQF behavior rather than relying on later ArmA commands.

## Installing the mission

1. Download or clone the repository.
2. Extract `assault_planner_v203_no_intro_outro_test.eden.zip`.
3. Copy the extracted `assault_planner_v203_no_intro_outro_test.eden` folder into your CWA/OFP user `missions` folder for editor/single-player use, or into the appropriate `MPMissions` workflow for multiplayer use.
4. Start the game with the required mods enabled.
5. Load the mission on Everon.

## Notes

This is the **v203 no-intro/outro test build** from the supplied archive. The project contains extensive changelog and validation files documenting the mission's development history and compatibility work.

The mission has been structured around Cold War Assault / OFP-era scripting constraints. As with any mission from this engine generation, final behavior should be verified in the actual game, because the CWA AI occasionally interprets a waypoint as a philosophical suggestion.
