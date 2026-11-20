"""One-time migration of the pre-profile Assault Planner template."""
from pathlib import Path
import json
import re
import sys

root = Path(__file__).resolve().parent.parent
mission = root / "cwr_assault_planner_v203.eden"
sys.path.insert(0, str(root / "tools"))
import asset_packs as old

def read(path):
    return path.read_bytes().decode("latin-1")

def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("latin-1"))

def normalized(path):
    return read(path).replace("\r\n", "\n")

def sqs(obj):
    return json.dumps(obj, ensure_ascii=True, separators=(",", ":"))

def quoted(token):
    return '"' + token + '"'

# Stable descriptive names for roles with WW4-specific classes; generic stock
# and remaining literal IDs use assetClass<original ID>.
roles = {
    "WW4EXT_5TBIS":"WestTruck",
    "WW4EXT_5T2BIS":"WestOpenTruck",
    "WW4EXT_5TAm":"WestAmmoTruck",
    "WW4EXT_M113":"WestAPC",
    "WW4EXT_M2A2BIS":"WestIFV",
    "WW4EXT_M60A3BIS":"WestTank",
    "WW4EXT_VulcanBIS":"WestAirDefense",
    "WW4EXT_JeepBIS":"WestJeep",
    "WW4EXT_HMMWVBIS":"WestHMMWV",
    "WW4EXT_A10BIS":"WestAttackJet",
    "WW4EXT_A10LGBBIS":"WestLaserJet",
    "WW4EXT_Su25_CW":"EastAttackJet",
    "WW4EXT_JeepMGE":"EastArmedLightVehicle",
    "WW4EXT_JeepMGR":"ResistanceArmedLightVehicle",
    "WW4EXT_UAZ_CW":"EastEmptyCar",
    "WW4EXT_UralBIS":"EastEmptyTruck",
    "WW4EXT_JeepR":"ResistanceEmptyCar",
    "WW4EXT_PV3SBIS":"ResistanceEmptyTruck",
    "WW4EXT_UralAmmo":"EastAmmoTruck",
    "WW4EXT_PV3SAR":"ResistanceAmmoTruck",
    "WW4EXT_ZSU":"EastAirDefense",
    "WW4EXT_ZSUR":"ResistanceAirDefense",
    "WW4EXT_tripodKord":"EastHeavyStaticGun",
    "WW4EXT_tripodPKME":"EastLightStaticGun",
    "WW4EXT_tripodNSVE":"EastMediumStaticGun",
    "WW4EXT_tripodKordR":"ResistanceHeavyStaticGun",
    "WW4EXT_tripodPKMR":"ResistanceLightStaticGun",
    "WW4EXT_tripodNSVR":"ResistanceMediumStaticGun",
    "WW4_WARRifleman":"WestRifleman",
    "WW4_WARGrenadier":"WestGrenadier",
    "WW4_WARMedic":"WestMedic",
    "WW4_WARMachinegun":"WestMachinegunner",
    "WW4_WARAT":"WestAT",
    "WW4_WARPilot":"WestPilot",
    "WW4_WARCrew":"WestCrew",
    "WW4_M16":"WestRifle",
    "WW4_W556_30mag":"WestRifleMagazine",
    "WW4_M433grenade":"WestGrenadeLauncherMagazine",
    "WW4_W556M_200mag":"WestLightMachinegunMagazine",
    "WW4_W762M_200mag":"WestMachinegunMagazine",
    "WW4_W762Sniper_20mag":"WestSemiAutoSniperMagazine",
    "WW4_W762Sniper_5mag":"WestBoltActionSniperMagazine",
    "WW4_LAWLauncher":"WestLightAT",
    "WW4_CarlGustavLauncher":"WestHeavyAT",
    "WW4_AK74M":"EastRifle",
    "WW4_AK74MGP25":"EastGrenadierRifle",
    "WW4_PKM":"EastMachinegun",
    "WW4_RPK74":"EastLightMachinegun",
    "WW4_SVD":"EastSniperRifle",
    "WW4_RPGLauncher":"EastAT",
    "WW4_E545_30mag":"EastRifleMagazine",
    "WW4_VOG25grenade":"EastGrenadeLauncherMagazine",
    "WW4_E762M_200mag":"EastMachinegunMagazine",
    "WW4_E545M_75mag":"EastLightMachinegunMagazine",
    "WW4_E762_10mag":"EastSniperMagazine",
    "WW4_AK47":"ResistanceRifle",
    "WW4_AK47GP25":"ResistanceGrenadierRifle",
    "WW4_RPK47":"ResistanceMachinegun",
    "WW4_FAL":"ResistanceBattleRifle",
    "WW4_E762_30mag":"ResistanceRifleMagazine",
    "WW4_E762M_40mag":"ResistanceMachinegunMagazine",
    "WW4_W762_20mag":"ResistanceBattleRifleMagazine",
    "WW4EXT_SOFLAM":"OptionalSOFLAM",
    "ww4_radio":"OptionalRadio",
    "ww4_radiobat":"OptionalRadioBattery",
    "MAP_Rucksack":"OptionalRucksack",
    "AH1":"WestCobra",
    "AH64":"WestApache",
    "OH58":"WestKiowa",
    "Ch47D":"WestHeavyTransportHeli",
    "UH60":"WestTransportHeli",
    "UH60MG":"WestArmedTransportHeli",
    "Mi24":"EastAttackHeli",
    "Mi17":"EastTransportHeli",
    "Kamov":"EastKamov",
    "ReammoBoxWest":"WestAmmoBox",
    "ReammoBoxEast":"EastAmmoBox",
    "ReammoBoxGuer":"ResistanceAmmoBox",
}
roles = {k.casefold(): v for k, v in roles.items()}
optional = {"ww4ext_soflam", "ww4_radio", "ww4_radiobat", "map_rucksack"}
keywords = set()
# Stock asset literals including common weapon and magazine references, props,
# helicopters, cars, soldiers and ammunition support classes.
stock = """
AH1 AH64 OH58 Ch47D UH60 UH60MG Mi24 Mi17 Kamov A10 A10LGB Su25 Cobra
Truck5t Truck5tOpen Truck5tReammo Truck5tRepair Truck5tRefuel Ural UralReammo UralRepair UralRefuel
TruckV3SG TruckV3SGReammo TruckV3SGRepair TruckV3SGRefuel TruckV3SCivil TruckV3SC
BMP BMP2 BMPRes BRDM M113 Bradley M60 Vulcan M1Abrams T55G T72 T72Res T80 T80Res ZSU Jeep JeepMG HMMWV UAZ GJeep GJeepMG
M2StaticMG M2StaticMGE M2StaticMGWest HeliHEmpty HeliH ParachuteWest ParachuteEast ParachuteG
Skoda SkodaBlue SkodaRed SkodaGreen Trabant Mini Rapid Civilian Civilian2 Civilian3 Civilian4 Civilian5 Civilian6 Civilian7 Civilian8 Civilian9 Civilian10 Civilian11 Civilian12
ReammoBoxWest ReammoBoxEast ReammoBoxGuer ReammoBoxRes AmmoBoxW AmmoBoxE AmmoBoxG AmmoBoxAddW AmmoBoxAddE AmmoBoxAddG HeavyReammoBoxWest HeavyReammoBoxEast AmmoBoxOUTW AmmoBoxOUTWW
Fortress1 Fortress2 FenceWood Fence Wire Barrel Barrel1 Barrel2 Barrel3
M16 M16GrenadeLauncher AK47 AK47CZ AK74 AK74GrenadeLauncher AK47GrenadeLauncher M4 M21 PK SVDDragunov FAL FALMag LAWLauncher RPGLauncher CarlGustavLauncher AT4Launcher GrenadeLauncher
HandGrenade SmokeShell SmokeShellGreen SmokeShellRed PipeBomb TimeBomb Mine MineE Binocular NVGoggles LaserDesignator Throw Put Flare FlareGreen FlareRed FlareYellow Mortar
""".split()
stock += [c for rr in old.ROLES.values() for c in rr]
stock += [v for v in old.CLASS_MAP.values()]
# Include explicitly used classes in the creation/literal-class contexts from
# the actual template, rather than assuming every possible class is used.
stock_lookup = {k.casefold() for k in stock}
skip = {"ww4FactionSelect.sqs", "ww4_arsenal/data.sqs", "ww4_arsenal/model_data.sqs", "worldConfig.sqs"}
runtime = [p for p in mission.rglob("*") if p.suffix.lower() in (".sqs", ".sqf") and
           not p.relative_to(mission).as_posix().startswith("FRevive/") and
           p.relative_to(mission).as_posix() not in skip]
direct_class = re.compile(r'"([A-Za-z_][A-Za-z_0-9]*)"\s+(?:createVehicle|createUnit|camCreate)\b', re.I)
cargo_class = re.compile(r'\b(?:addWeapon(?:Cargo)?|addMagazine(?:Cargo)?|removeWeapon|removeMagazine|selectWeapon)\s+(?:\[\s*)?"([A-Za-z_][A-Za-z_0-9]*)"', re.I)
assignment = re.compile(r'\b(?:_class|[A-Za-z_][A-Za-z_0-9]*Class)\s*=\s*"([A-Za-z_][A-Za-z_0-9]*)"', re.I)
# Camera/logic engine helpers are not equipment or gameplay assets.
engine_types = {"camera", "logic", "emptydetector", "body", "seagull"}
for p in runtime:
    source = read(p)
    for pat in (direct_class, cargo_class, assignment):
        for cl in pat.findall(source):
            if cl.casefold() not in engine_types:
                stock_lookup.add(cl.casefold())

pools_path = mission / "vehiclePools.sqs"
pool_source = normalized(pools_path)
pool_values = {}
for key in old.POOLS:
    match = re.search(rf"(?m)^{key}\s*=\s*(\[[^\n]*\])", pool_source)
    assert match, key
    pool_values[key] = json.loads(match[1])
    pool_source = pool_source[:match.start()] + pool_source[match.end():]
# Runtime scripts own the readiness flag and random aircraft selection; data
# pools are already initialized by the selected profile.
write(pools_path, pool_source)

aliases = {}
def register(token, suffix=None, vanilla=None):
    key = token.casefold()
    var = "assetClass" + (suffix or roles.get(key) or re.sub(r"[^A-Za-z_0-9]", "", token.removeprefix("WW4EXT_").removeprefix("WW4_")))
    # Generic stock IDs may be case-insensitively identical to a role suffix.
    if var.casefold() in {x[0].casefold() for x in aliases.values()} and key not in aliases:
        var = "assetClassStock" + token
    if key not in aliases:
        if vanilla is None:
            vanilla = "" if key in optional else old.CLASS_MAP.get(key, token)
            # Unknown mod classes are errors, not silently retained.
            if old.WW4_CLASS.fullmatch(token) and vanilla == token:
                raise ValueError("No vanilla mapping: " + token)
        aliases[key] = (var, token, vanilla)
    return aliases[key][0]

# Different role than a light objective/stealable vehicle; preserve patrol
# capacity in vanilla by retaining the specific APC substitution.
patrol = mission / "enemyRoutePatrolProfile.sqs"
patrol_text = read(patrol)
patrol_text = patrol_text.replace('"WW4EXT_JeepMGE"', 'assetClassEastPatrolVehicle').replace('"WW4EXT_JeepMGR"', 'assetClassResistancePatrolVehicle')
write(patrol, patrol_text)

shared_changes = []
for p in runtime:
    original = read(p)
    def repl(m):
        token = m[1]
        key = token.casefold()
        if key in old.NON_ASSET_NAMES or key in engine_types:
            return m[0]
        if key not in stock_lookup and key not in old.CLASS_MAP and key not in optional and not old.WW4_CLASS.fullmatch(token):
            return m[0]
        # Preserve goto labels, variable names sent over the network and marker names.
        prefix = original[max(0, m.start()-50):m.start()]
        if re.search(r'\b(?:goto|publicVariable|setMarkerType|setMarkerColor|setMarkerShape|setMarkerBrush|playMove|switchMove)\s*$', prefix, re.I):
            return m[0]
        return register(token)
    updated = old.QUOTED.sub(repl, original)
    # Optional utilities are represented by empty strings when absent.
    for var in ("assetClassOptionalRadio", "assetClassOptionalSOFLAM", "assetClassOptionalRucksack"):
        updated = updated.replace("? _weapon == " + var, '? ' + var + ' != "" && _weapon == ' + var)
    updated = re.sub(r"\bWW4 Arsenal\b", "Mission Arsenal", updated, flags=re.I)
    if updated != original:
        write(p, updated)
        shared_changes.append(p.relative_to(mission).as_posix())

# Register explicit semantic patrol choices used above.
aliases["#eastpatrol"] = ("assetClassEastPatrolVehicle", "WW4EXT_JeepMGE", "BMP2")
aliases["#respatrol"] = ("assetClassResistancePatrolVehicle", "WW4EXT_JeepMGR", "BMPRes")
assert len({v[0].casefold() for v in aliases.values()}) == len(aliases)
print("Shared runtime files changed:", len(shared_changes), shared_changes)
print("Shared class aliases:", len(aliases))

# Faction data: exact original categories, labels, class/role order and fallback
# roles. Generic runtime script draws from profile arrays on each mission roll.
role_names = list(old.ROLES)
faction_path = mission / "ww4FactionSelect.sqs"
faction_source = normalized(faction_path)
factions = {}
for stem, label, expected, index in (("east", "East", 11, 1), ("res", "Res", 9, 2)):
    groups = []
    for m in re.finditer(rf"(?ms)^#{stem}Cat\d+\n(.*?)(?=^#|\Z)", faction_source):
        values = dict(re.findall(r'(?m)^ww4'+label+r'(\w+)\s*=\s*"([^"]+)"\s*$', m[1]))
        groups.append([values["CategoryLabel"], [values[role] for role in role_names]])
    assert len(groups) == expected, (stem, len(groups))
    factions[label] = (groups, [["Soviet Army" if index == 1 else "Resistance", [old.ROLES[r][index] for r in role_names]]])
faction_runtime = ["; Select the configured faction and keep the established shared role variables.",
                   "ww4FactionReady = false"]
for side in ("East", "Res"):
    faction_runtime += [f"_r = random (count asset{side}Factions)",
                        f"_entry = asset{side}Factions select (_r - (_r % 1))",
                        f"ww4{side}CategoryLabel = _entry select 0",
                        "_roles = _entry select 1"]
    faction_runtime += [f"ww4{side}{role} = _roles select {i}" for i, role in enumerate(role_names)]
faction_runtime += ["ww4FactionReady = true", "exit"]
write(faction_path, "\n".join(faction_runtime) + "\n")

# The arsenal UI still uses the same variables/entry structure. Its old data
# scripts become tiny ready-only wrappers, so callers and scheduling stay intact.
catalogs = []
for name, vanilla, ready in (("data.sqs", old.vanilla_arsenal(), "WW4_ArsenalDataReady"),
                             ("model_data.sqs", old.vanilla_models(), "WW4_PlayerModelDataReady")):
    p = mission / "ww4_arsenal" / name
    def content(text):
        return "\n".join(line for line in text.replace("\r\n", "\n").splitlines()
                         if line.strip().lower() != "exit" and not line.startswith(ready+" ="))
    catalogs.append((content(normalized(p)), content(vanilla)))
    write(p, f"; Catalog loaded by assets/selection.sqs at mission init.\n{ready} = true\nexit\n")

# Editor-side role manifest keyed by stable playable slot variable; no original
# WW4 identifiers are required in the vanilla manifest.
sqm = normalized(mission / "mission.sqm")
slots = []
for part in re.split(r"(?=\bclass\s+Item\d+\b)", sqm):
    unit = re.search(r'\bvehicle\s*=\s*"([^"]+)"', part)
    name = re.search(r'\btext\s*=\s*"([^"]+)"', part)
    player = re.search(r'\bplayer\s*=\s*"(?:PLAYER COMMANDER|PLAY CDG)"', part)
    if unit and name and player:
        slots.append((name[1], unit[1], old.CLASS_MAP[unit[1].casefold()]))
assert len(slots) == 12
for pack, idx in (("ww4", 0), ("vanilla", 1)):
    lines = [
        "; Assault Planner asset profile. This is the only runtime class catalog for this pack.",
        "; Editor manifest is also read by the Python generator. Keep these two arrays on one line.",
        "assetEditorSlots = " + sqs([[s[0], s[idx+1]] for s in slots]),
        "assetRequiredAddons = " + sqs(["WW4_vehicles", "WW4EXT_VEHICLES", "WW4EXT_VEHICLES_CW"] if idx == 0 else []),
        "",
        "; Roles and direct runtime class references",
    ]
    lines += [var + " = " + quoted(ww4 if idx == 0 else vanilla)
              for var, ww4, vanilla in sorted(aliases.values(), key=lambda x:x[0].casefold())]
    lines += ["", "; Vehicle pools"]
    lines += [name + " = " + sqs(classes if idx == 0 else old.POOLS[name]) for name, classes in pool_values.items()]
    lines += ["", "; Infantry faction groups: role order matches ww4FactionSelect.sqs"]
    for side, data in factions.items():
        variable = "asset" + side + "Factions"
        lines.append(variable+" = []")
        lines.extend(variable+" = "+variable+" + "+sqs([entry]) for entry in data[idx])
    lines += ["", "; Arsenal and player model catalogs"]
    for catalog in catalogs:
        lines += [catalog[idx], ""]
    lines += ["assetProfileReady = true", "exit"]
    write(mission / "assets" / (pack+".sqs"), "\n".join(lines)+"\n")

write(mission / "assets/selection.sqs", '; The generator selects a profile for the exported mission.\nassetProfileName = "ww4"\n[] exec "assets\\ww4.sqs"\nexit\n')
init = mission / "init.sqs"
s = read(init)
needle = '@ worldConfigReady'
assert s.count(needle) == 1
nl = "\r\n" if "\r\n" in s else "\n"
s = s.replace(needle, needle+nl+'assetProfileReady = false'+nl+'[] exec "assets\\selection.sqs"'+nl+'@ assetProfileReady')
write(init,s)

# Make user-facing arsenal labels neutral in dialogs/briefing, not class names.
for p in mission.rglob("*"):
    if p.suffix.lower() in (".ext", ".hpp", ".html"):
        original = read(p)
        updated = re.sub(r"\bWW4 Arsenal\b", "Mission Arsenal", original, flags=re.I)
        if updated != original:
            write(p, updated)

# Never leak unresolved addon class literals to scripts outside profiles.
for p in mission.rglob("*"):
    if p.suffix.lower() not in old.TEXT_SUFFIXES or p.name in ("mission.sqm", "worldConfig.sqs") or "assets" in p.relative_to(mission).parts:
        continue
    unknown = old.unknown_classes(read(p))
    if unknown:
        raise ValueError(f"{p}: {unknown}")

# Runtime stock class literals are centralized except for engine primitives,
# marker/resource/trigger identifiers, and the third-party FRevive subsystem.
print("Profiles generated. Direct WW4 references outside profiles/editor: none.")
