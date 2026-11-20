"""Select one pre-defined mission asset profile; only editor metadata is rewritten."""
from __future__ import annotations

import json
import re
from pathlib import Path

PROFILES = ("vanilla", "ww4")
PROFILE_FILE = "assetPack.txt"
TEXT_SUFFIXES = {".sqs", ".sqf", ".sqm", ".ext", ".hpp", ".cpp", ".cfg", ".txt", ".html"}
QUOTED = re.compile(r'"([A-Za-z_][A-Za-z_0-9]*)"')
WW4_CLASS = re.compile(r"ww4(?:ext)?_[a-z_0-9]+", re.I)
NON_ASSET_NAMES = {
    "ww4_arsenal_dialog", "ww4_playermodel_dialog", "ww4_preview_abortdialog",
    "ww4_modelnewplayer", "ww4_modelpreviewunit", "ww4_modelswapidentity",
}
ADDONS = {"ww4_vehicles", "ww4ext_vehicles", "ww4ext_vehicles_cw"}

def unknown_classes(text):
    return sorted({m[1] for m in QUOTED.finditer(text)
                   if WW4_CLASS.fullmatch(m[1]) and m[1].casefold() not in NON_ASSET_NAMES})

def manifest(text, name):
    match = re.search(rf"(?m)^{name}\s*=\s*(\[[^\r\n]*\])\s*$", text)
    if not match:
        raise ValueError(f"Asset profile missing {name}")
    return json.loads(match[1])

def select_editor_classes(sqm, slot_classes, addons):
    """Replace only named playable slots, keep all other editor entities."""
    slots = dict(slot_classes)
    if len(slots) != len(slot_classes):
        raise ValueError("Duplicate editor slot in asset profile")
    seen = set()
    parts = re.split(r"(?=\bclass\s+Item\d+\b)", sqm)
    for i, part in enumerate(parts):
        name = re.search(r'\btext\s*=\s*"([^"]+)"', part)
        if not name or name[1] not in slots:
            continue
        if name[1] in seen:
            raise ValueError(f"Duplicate playable slot {name[1]}")
        part, count = re.subn(r'(\bvehicle\s*=\s*")[^"]+(")',
                              lambda m: m[1]+slots[name[1]]+m[2], part, count=1)
        if count != 1:
            raise ValueError(f"Missing vehicle class for {name[1]}")
        seen.add(name[1])
        parts[i] = part
    missing = set(slots)-seen
    if missing:
        raise ValueError("Asset profile editor slots missing: "+", ".join(sorted(missing)))
    def replace(match):
        items = re.findall(r'"([^"]+)"', match[2])
        kept = [name for name in items if name.casefold() not in ADDONS]
        for addon in addons:
            if addon.casefold() not in {name.casefold() for name in kept}:
                kept.append(addon)
        return match[1]+",".join(json.dumps(name) for name in kept)+match[3]
    text, count = re.subn(r"(?i)(\baddOns(?:Auto)?\s*\[\]\s*=\s*\{)([^{}]*)(\})", replace, "".join(parts))
    if count < 2 and (slots or addons):
        raise ValueError("Missing editor addon metadata")
    return text

def apply_asset_pack(mission: Path, profile: str) -> None:
    """Select packaged profile without modifying gameplay scripts or catalogs."""
    if profile not in PROFILES:
        raise ValueError(f"Unknown asset pack: {profile}")
    marker = mission / PROFILE_FILE
    source = mission / "assets" / (profile + ".sqs")
    prior = marker.read_text(encoding="ascii").strip() if marker.exists() else None
    if not source.is_file():
        # Backward-compatible WW4-only export for pre-profile callers. A
        # selected vanilla pack always needs the matching profile.
        if profile == "ww4" and prior != "vanilla" and not (mission / "assets").exists():
            marker.write_text("ww4\n", encoding="ascii")
            return
        raise ValueError("Selected pack unavailable. Choose the original mission template containing both asset profiles.")
    content = source.read_text(encoding="latin-1")
    slot_classes = manifest(content, "assetEditorSlots")
    addons = manifest(content, "assetRequiredAddons")
    sqm_path = mission / "mission.sqm"
    sqm = sqm_path.read_text(encoding="utf-8-sig")
    updated = select_editor_classes(sqm, slot_classes, addons)
    if profile == "vanilla":
        unresolved = {}
        for path in mission.rglob("*"):
            if path.suffix.lower() not in TEXT_SUFFIXES or not path.is_file() or path.name == "worldConfig.sqs":
                continue
            if path.parent == source.parent and path.name != source.name:
                continue
            text = updated if path == sqm_path else path.read_bytes().decode("latin-1")
            unknown = unknown_classes(text)
            if unknown:
                unresolved[path.relative_to(mission).as_posix()] = unknown
        if unresolved:
            details = "; ".join(f"{path}: {', '.join(classes)}" for path, classes in unresolved.items())
            raise ValueError("Unmapped WW4 references; vanilla export aborted: "+details)
        updated = updated.replace("randomized WW4 assault", "randomized CWA assault")
    sqm_path.write_text(updated, encoding="utf-8", newline="\n")
    # Do not leave inactive mod class catalogs in a vanilla mission package.
    for pack in PROFILES:
        if pack != profile:
            (source.parent / (pack+".sqs")).unlink(missing_ok=True)
    (source.parent / "selection.sqs").write_text(
        f'; Generated by mission exporter.\nassetProfileName = "{profile}"\n[] exec "assets\\{profile}.sqs"\nexit\n',
        encoding="ascii", newline="\n")
    marker.write_text(profile+"\n", encoding="ascii", newline="\n")
