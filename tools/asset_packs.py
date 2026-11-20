"""Build-time asset profiles for the shared CWA mission template.

Use actual OFP/CWA class names (OFPEC OFP CfgVehicles and Weapons references).
No runtime fallback to an unloaded addon: unknown WW4 literals fail the export.
The source template is never modified. Legacy WW4 script/global names remain
for compatibility with shared mission logic; they are not addon classes.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

PROFILES = ("vanilla", "ww4")
PROFILE_FILE = "assetPack.txt"

# Each line is a stock replacement followed by WW4EXT class suffixes.
# Side-specific stock classes where available. There is no stock resistance
# Shilka, so use the stock Shilka with the mission's resistance crew.
VEHICLE_GROUPS = """
Truck5t 5TBIS
Truck5tOpen 5T2BIS
Truck5tReammo 5TAm
A10 A10BIS
A10LGB A10LGBBIS
Su25 Su25_CW
M113 M113
Bradley M2A2BIS
M60 M60A3BIS
Vulcan VulcanBIS
Jeep JeepBIS
HMMWV HMMWVBIS
BMP M113E BMP BMPExportE
BMP2 BMP2 BMP2_CW BMP3 BMD3 BMP2ExportE BMP3ExportE BTR80 BTR80_CW BTR80ExportE
BMPRes M113R BMPRes BMPExportR BMP2ExportR BMP3ExportR BTR80ExportR
BRDM BRDM BRDM_MG BRDM2 BRDM2M BRDM2ExportE
BMPRes BRDM2ExportR
BRDM JeepMGE
BMPRes JeepMGR
BRDM Zil157MGE ToyotaDshk1E ToyotaDshk2E ToyotaDshk3E ToyotaDshk4E
BMPRes Zil157MGR Zil157MG ToyotaDshk1R ToyotaDshk2R ToyotaDshk3R ToyotaDshk4R
T72 T55 T55ME T72 T72_CW T72ME M60ME
T80 T80 T80_CW T90 T90SE M1A1ME
T55G T55Res T55MR
T72Res T72Res T72MR M60MR
T80Res T80Res T90SR M1A1MR
ZSU ZSU ZSU_CW ZSUE ZSUR
Ural UralE PV3SE UralBIS
TruckV3SG UralR PV3SR Zil157 PV3SBIS
UralReammo UralAmmo
TruckV3SGReammo PV3SAR
UAZ UAZ_CW
GJeep JeepR
Skoda SkodaCiv
SkodaBlue SkodaBlueCiv
SkodaRed SkodaRedCiv
SkodaGreen SkodaGreenCiv
Trabant Trabant
Mini Mini
Rapid Rapid
TruckV3SCivil PV3SCiv
M2StaticMGE tripodKord tripodPKME tripodNSVE
M2StaticMG tripodKordR tripodPKMR tripodNSVR
"""

# Stock soldier roles, used for editor slots, allied spawns and faction tables.
ROLES = {
    "Rifleman": ("SoldierWB", "SoldierEB", "SoldierGB"),
    "Grenadier": ("SoldierWG", "SoldierEG", "SoldierGG"),
    "Medic": ("SoldierWMedic", "SoldierEMedic", "SoldierGMedic"),
    "Autorifleman": ("SoldierWMG", "SoldierEMG", "SoldierGMG"),
    "Machinegun": ("SoldierWMG", "SoldierEMG", "SoldierGMG"),
    "Rocket": ("SoldierWLAW", "SoldierELAW", "SoldierGLAW"),
    "AT": ("SoldierWLAW", "SoldierELAW", "SoldierGLAW"),
    "ATH": ("SoldierWAT", "SoldierEAT", "SoldierGAT"),
    "AA": ("SoldierWAA", "SoldierEAA", "SoldierGAA"),
    "Marksman": ("SoldierWSniper", "SoldierESniper", "SoldierGSniper"),
    "Sniper": ("SoldierWSniper", "SoldierESniper", "SoldierGSniper"),
    "Demolition": ("SoldierWSaboteurPipe", "SoldierESaboteurPipe", "SoldierGB"),
    "Engineer": ("SoldierWMiner", "SoldierEMiner", "SoldierGB"),
    "SquadLeader": ("OfficerW", "OfficerE", "OfficerG"),
    "Officer": ("OfficerW", "OfficerE", "OfficerG"),
    "Pilot": ("SoldierWPilot", "SoldierEPilot", "SoldierGPilot"),
    "Crew": ("SoldierWCrew", "SoldierECrew", "SoldierGCrew"),
}

CLASS_MAP = {}
for line in VEHICLE_GROUPS.strip().splitlines():
    replacement, *suffixes = line.split()
    for suffix in suffixes:
        CLASS_MAP[("WW4EXT_" + suffix).casefold()] = replacement
for prefix in ("WW4_FOREC", "WW4_WAR"):
    for role, classes in ROLES.items():
        CLASS_MAP[(prefix + role).casefold()] = classes[0]
CLASS_MAP.update({
    k.casefold(): v for k, v in {
        "WW4_AK74M": "AK74", "WW4_AK74MGP25": "AK74GrenadeLauncher",
        "WW4_PKM": "PK", "WW4_RPK74": "PK", "WW4_SVD": "SVDDragunov",
        "WW4_RPGLauncher": "RPGLauncher", "WW4_E545_30mag": "AK74",
        "WW4_VOG25grenade": "GrenadeLauncher", "WW4_E762M_200mag": "PK",
        "WW4_E545M_75mag": "PK", "WW4_E762_10mag": "SVDDragunov",
        "WW4_AK47": "AK47CZ", "WW4_AK47GP25": "AK47GrenadeLauncher",
        "WW4_RPK47": "PK", "WW4_FAL": "FAL", "WW4_E762_30mag": "AK47",
        "WW4_E762M_40mag": "PK", "WW4_W762_20mag": "FALMag",
        "WW4_W556_30mag": "M16", "WW4_M433grenade": "GrenadeLauncher",
        "WW4_W556M_200mag": "M60", "WW4_W762M_200mag": "M60",
        "WW4_W762Sniper_20mag": "M21", "WW4_W762Sniper_5mag": "M21",
        "WW4_LAWLauncher": "LAWLauncher", "WW4_CarlGustavLauncher": "CarlGustavLauncher",
        "AH1": "Cobra",
    }.items()
})

# Curated stock arsenal, not blind renaming of modded magazine variants.
ARSENAL = {
    "Rifles": [
        ("M16", ["M16", "Mortar"]), ("M16GrenadeLauncher", ["M16", "GrenadeLauncher", "Flare", "FlareGreen", "FlareRed", "FlareYellow"]),
        ("M4", ["M4", "Mortar"]), ("XMS", ["M4"]), ("AK74", ["AK74"]),
        ("AK74SU", ["AK74"]), ("AK74GrenadeLauncher", ["AK74", "GrenadeLauncher", "Flare"]),
        ("AK47", ["AK47"]), ("AK47CZ", ["AK47"]), ("AK47GrenadeLauncher", ["AK47", "GrenadeLauncher"]),
        ("FAL", ["FALMag"]), ("HKG3", ["HKG3Mag"]), ("G36a", ["G36aMag"]), ("Steyr", ["SteyrMag"]),
    ],
    "SMGs": [("HK", ["HK"]), ("Bizon", ["BizonMag"]), ("UZI", ["UZIMag"])],
    "Machine guns": [("M60", ["M60"]), ("PK", ["PK"])],
    "Sniper rifles": [("M21", ["M21"]), ("SVDDragunov", ["SVDDragunov"]), ("HuntingRifle", ["HuntingRifleMag"])],
    "Pistols": [(w, [m]) for w, m in (("Beretta", "BerettaMag"), ("CZ75", "CZ75Mag"), ("Glock", "GlockMag"),
                ("GlockS", "GlockSMag"), ("Ingram", "IngramMag"), ("Revolver", "RevolverMag"), ("Skorpion", "SkorpionMag"))],
    "Launchers": [(w, [w]) for w in ("LAWLauncher", "CarlGustavLauncher", "RPGLauncher", "AT4Launcher", "AALauncher", "9K32Launcher")],
    "Grenade launchers": [("MM1", ["MM1Magazine"]), ("6G30", ["6G30Magazine"])],
    "Shotguns": [("Kozlice", ["KozliceBall", "KozliceShell"])],
    "Equipment": [("Binocular", []), ("NVGoggles", []), ("LaserDesignator", ["LaserDesignator"])],
    "Grenades": [("Throw", ["HandGrenade", "SmokeShell", "SmokeShellGreen", "SmokeShellRed"])],
    "Explosives": [("Put", ["PipeBomb", "TimeBomb", "Mine", "MineE"])],
}

def sqs(value):
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"))

def vanilla_arsenal():
    lines = ["; Vanilla CWA asset profile.", "WW4_ArsenalEntries = []"]
    families = []
    index = 0
    for family, items in ARSENAL.items():
        indexes = []
        for weapon, mags in items:
            lines.append("WW4_ArsenalEntries = WW4_ArsenalEntries + " + sqs([[weapon, weapon, mags]]))
            indexes.append(index)
            index += 1
        families.append([family, indexes])
    lines.extend([f"WW4_ArsenalEntryCount = {index}", "WW4_ArsenalFamilies = []"])
    lines.extend("WW4_ArsenalFamilies = WW4_ArsenalFamilies + " + sqs([item]) for item in families)
    lines.extend([f"WW4_ArsenalFamilyCount = {len(families)}", "WW4_ArsenalCurrentEntryIndexes = []",
                  "WW4_ArsenalDataReady = true", "exit"])
    return "\n".join(lines) + "\n"

def vanilla_models():
    groups = []
    for index, side in enumerate(("West", "East", "Resistance")):
        classes = list(dict.fromkeys(value[index] for value in ROLES.values()))
        groups.append([side, classes])
    lines = ["; Vanilla CWA model catalog.", "WW4_PlayerModelGroups = []"]
    lines.extend("WW4_PlayerModelGroups = WW4_PlayerModelGroups + " + sqs([g]) for g in groups)
    for key, group in zip(("West", "East", "Resistance"), groups):
        lines.extend([f"WW4_PlayerModel{key}GroupCount = 1", f"WW4_PlayerModel{key}ClassCount = {len(group[1])}"])
    lines.extend(["WW4EXT_PlayerModelExactGroupCount = 0", "WW4EXT_PlayerModelExactClassCount = 0",
                  "WW4_PlayerModelGroupCount = 3", f"WW4_PlayerModelClassCount = {sum(len(g[1]) for g in groups)}",
                  "WW4_PlayerModelDataReady = true", "exit"])
    return "\n".join(lines) + "\n"

def vanilla_factions():
    lines = ["; Vanilla CWA faction profile; shared variable names retained.", "ww4FactionReady = false",
             'ww4EastCategoryLabel = "Soviet Army"', 'ww4ResCategoryLabel = "Resistance"']
    for side, index in (("East", 1), ("Res", 2)):
        for role, classes in ROLES.items():
            lines.append(f'ww4{side}{role} = "{classes[index]}"')
    return "\n".join(lines + ["ww4FactionReady = true", "exit"]) + "\n"

# Avoid filling a 12-man reinforcement wave into an 8-seat BMP and avoid
# weighting one stock vehicle multiple times after collapsing WW4 variants.
POOLS = {
    "enemyEastAPCVehiclePool": ["BMP", "BMP2"],
    "enemyEastLightVehiclePool": ["BRDM"],
    "enemyEastTankVehiclePool": ["T72", "T80"],
    "enemyEastSupportVehiclePool": ["ZSU"],
    "enemyEastHeavyVehiclePool": ["BMP", "BMP2", "T72", "T80", "ZSU"],
    "enemyResistanceAPCVehiclePool": ["BMPRes"],
    "enemyResistanceLightVehiclePool": ["BMPRes"],
    "enemyResistanceTankVehiclePool": ["T55G", "T72Res", "T80Res"],
    "enemyResistanceSupportVehiclePool": ["ZSU"],
    "enemyResistanceHeavyVehiclePool": ["BMPRes", "T55G", "T72Res", "T80Res", "ZSU"],
    "enemyEastReinforcementTransportPool": ["Ural"],
    "enemyResistanceReinforcementTransportPool": ["TruckV3SG"],
}

# Only quoted class-like tokens, not variable names or file paths.
QUOTED = re.compile(r'"([A-Za-z_][A-Za-z_0-9]*)"')
WW4_CLASS = re.compile(r"ww4(?:ext)?_[a-z_0-9]+", re.I)
# Script/dialog names & multiplayer variable names are not addon references.
NON_ASSET_NAMES = {
    "ww4_arsenal_dialog", "ww4_playermodel_dialog", "ww4_preview_abortdialog",
    "ww4_modelnewplayer", "ww4_modelpreviewunit", "ww4_modelswapidentity",
}
ADDONS = {"ww4_vehicles", "ww4ext_vehicles", "ww4ext_vehicles_cw"}
TEXT_SUFFIXES = {".sqs", ".sqf", ".sqm", ".ext", ".hpp", ".cpp", ".cfg", ".txt", ".html"}

def replace_classes(text):
    return QUOTED.sub(lambda m: '"' + CLASS_MAP.get(m[1].casefold(), m[1]) + '"', text)

def strip_ww4_addons(text):
    def replace(match):
        items = re.findall(r'"([^"]+)"', match[2])
        kept = [name for name in items if name.casefold() not in ADDONS]
        return match[1] + ",".join(sqs(name) for name in kept) + match[3]
    return re.sub(r"(?i)(\baddOns(?:Auto)?\s*\[\]\s*=\s*\{)([^{}]*)(\})", replace, text)

def unknown_classes(text):
    return sorted({m[1] for m in QUOTED.finditer(text)
                   if WW4_CLASS.fullmatch(m[1]) and m[1].casefold() not in NON_ASSET_NAMES})

def apply_asset_pack(mission: Path, profile: str) -> None:
    """Apply profile to a staged folder. Reject unknown WW4 classes before publish."""
    if profile not in PROFILES:
        raise ValueError(f"Unknown asset pack: {profile}")
    marker = mission / PROFILE_FILE
    prior = marker.read_text(encoding="ascii").strip() if marker.exists() else "ww4"
    if profile == "ww4":
        if prior == "vanilla":
            raise ValueError("Choose the original WW4 template to export the WW4 asset pack.")
        marker.write_text("ww4\n", encoding="ascii")
        return

    required = ("mission.sqm", "vehiclePools.sqs", "ww4FactionSelect.sqs",
                "ww4_arsenal/data.sqs", "ww4_arsenal/model_data.sqs")
    if not all((mission / name).is_file() for name in required):
        raise ValueError("The vanilla profile requires the updated Assault Planner mission template.")

    if prior != "vanilla":
        (mission / "ww4FactionSelect.sqs").write_text(vanilla_factions(), encoding="ascii")
        (mission / "ww4_arsenal/data.sqs").write_text(vanilla_arsenal(), encoding="ascii")
        (mission / "ww4_arsenal/model_data.sqs").write_text(vanilla_models(), encoding="ascii")

    unresolved = {}
    for path in sorted(mission.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES or path.name == "worldConfig.sqs":
            continue
        # Latin-1 round-trips original ASCII/CP1252/UTF-8 bytes, including
        # third-party FRevive source, without rewriting unchanged files.
        original = path.read_bytes().decode("latin-1")
        text = original
        relative = path.relative_to(mission).as_posix()
        if relative == "mission.sqm":
            text = strip_ww4_addons(text)
        if relative == "vehiclePools.sqs":
            for variable, classes in POOLS.items():
                text, n = re.subn(rf"(?m)^({variable}\s*=\s*)\[[^\r\n]*\]",
                                  lambda m: m[1] + sqs(classes), text)
                if n != 1:
                    raise ValueError(f"Missing or duplicate stock pool: {variable}")
        if relative == "enemyRoutePatrolProfile.sqs":
            # Stock armed jeeps carry too few passengers. APCs carry patrols.
            text = text.replace('"WW4EXT_JeepMGE"', '"BMP2"').replace('"WW4EXT_JeepMGR"', '"BMPRes"')
        if relative in ("ww4_arsenal/apply_loadout.sqs", "ww4_arsenal/add_weapon.sqs"):
            # These are optional WW4 equipment branches, not stock equipment.
            text = "".join(line for line in text.splitlines(keepends=True)
                           if not any('"' + k + '"' in line for k in
                                      ("WW4EXT_SOFLAM", "ww4_radio", "ww4_radiobat", "MAP_Rucksack")))
        text = replace_classes(text)
        # Preserve script/global identifiers, change user-facing labels only.
        text = re.sub(r"\bWW4 Arsenal\b", "Vanilla Arsenal", text, flags=re.I)
        text = text.replace("randomized WW4 assault", "randomized CWA assault")
        unknown = unknown_classes(text)
        if unknown:
            unresolved[relative] = unknown
        if text != original:
            path.write_bytes(text.encode("latin-1"))
    if unresolved:
        details = "; ".join(f"{path}: {', '.join(classes)}" for path, classes in unresolved.items())
        raise ValueError("Unmapped WW4 references; vanilla export aborted: " + details)
    marker.write_text("vanilla\n", encoding="ascii")
