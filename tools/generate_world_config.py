#!/usr/bin/env python3
"""
Generate a CWA/OFP-safe worldConfig.sqs from an island/world config.cpp.

The generated SQS deliberately uses simple one-line arrays:
    missionLocationLabels = [...]
    missionLocationXs = [...]
    missionLocationYs = [...]

That avoids old SQS parser problems with multiline/nested array expressions.
"""
from __future__ import annotations

import argparse
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

NUMBER_RE = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")
CLASS_RE = re.compile(r"\bclass\s+([A-Za-z_][A-Za-z0-9_]*)(?:\s*:\s*[A-Za-z_][A-Za-z0-9_]*)?\s*\{", re.I)
NAME_RE = re.compile(r'\bname\s*=\s*"((?:""|\\.|[^"])*)"\s*;', re.I | re.S)
POSITION_RE = re.compile(r"\bposition\s*\[\s*\]\s*=\s*\{([^{}]*)\}\s*;", re.I | re.S)
CENTER_RE = re.compile(r"\bcenterPosition\s*\[\s*\]\s*=\s*\{([^{}]*)\}\s*;", re.I | re.S)
MAP_SIZE_RE = re.compile(r"\b(?:mapSize|worldSize)\s*=\s*(" + NUMBER_RE.pattern + r")\s*;", re.I)

@dataclass
class ClassBlock:
    name: str
    start: int
    open_brace: int
    close_brace: int

@dataclass
class Location:
    class_name: str
    name: str
    x: float
    y: float

def read_text(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            pass
    return data.decode("utf-8", errors="replace")

def strip_comments(text: str) -> str:
    out = []
    i = 0
    in_string = False
    while i < len(text):
        ch = text[i]
        if in_string:
            out.append(ch)
            if ch == '"':
                if i + 1 < len(text) and text[i + 1] == '"':
                    out.append(text[i + 1]); i += 2; continue
                backslashes = 0
                j = i - 1
                while j >= 0 and text[j] == "\\":
                    backslashes += 1; j -= 1
                if backslashes % 2 == 0:
                    in_string = False
            i += 1; continue
        if ch == '"':
            in_string = True; out.append(ch); i += 1; continue
        if ch == "/" and i + 1 < len(text) and text[i + 1] == "/":
            i += 2
            while i < len(text) and text[i] not in "\r\n": i += 1
            continue
        if ch == "/" and i + 1 < len(text) and text[i + 1] == "*":
            i += 2
            while i < len(text):
                if text[i] == "*" and i + 1 < len(text) and text[i + 1] == "/":
                    i += 2; break
                if text[i] in "\r\n": out.append(text[i])
                i += 1
            continue
        out.append(ch); i += 1
    return "".join(out)

def find_matching_brace(text: str, open_brace: int) -> int:
    depth = 0
    in_string = False
    i = open_brace
    while i < len(text):
        ch = text[i]
        if in_string:
            if ch == '"':
                if i + 1 < len(text) and text[i + 1] == '"':
                    i += 2; continue
                backslashes = 0
                j = i - 1
                while j >= 0 and text[j] == "\\":
                    backslashes += 1; j -= 1
                if backslashes % 2 == 0: in_string = False
            i += 1; continue
        if ch == '"': in_string = True
        elif ch == "{": depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0: return i
        i += 1
    raise ValueError(f"Unmatched '{{' at character {open_brace}")

def find_class_blocks(text: str) -> list[ClassBlock]:
    blocks = []
    for match in CLASS_RE.finditer(text):
        open_brace = text.find("{", match.start(), match.end())
        if open_brace < 0: continue
        try: close_brace = find_matching_brace(text, open_brace)
        except ValueError: continue
        blocks.append(ClassBlock(match.group(1), match.start(), open_brace, close_brace))
    return blocks

def direct_child_classes(text: str, parent: ClassBlock) -> Iterable[ClassBlock]:
    pos = parent.open_brace + 1
    end = parent.close_brace
    while pos < end:
        match = CLASS_RE.search(text, pos, end)
        if not match: return
        depth = 0
        in_string = False
        i = pos
        while i < match.start():
            ch = text[i]
            if in_string:
                if ch == '"':
                    if i + 1 < match.start() and text[i + 1] == '"': i += 2; continue
                    in_string = False
                i += 1; continue
            if ch == '"': in_string = True
            elif ch == "{": depth += 1
            elif ch == "}": depth -= 1
            i += 1
        if depth != 0:
            pos = match.end(); continue
        open_brace = text.find("{", match.start(), match.end())
        close_brace = find_matching_brace(text, open_brace)
        yield ClassBlock(match.group(1), match.start(), open_brace, close_brace)
        pos = close_brace + 1

def parse_numbers(value: str) -> list[float]:
    return [float(m.group(0)) for m in NUMBER_RE.finditer(value)]

def parse_location_block(text: str, block: ClassBlock) -> Optional[Location]:
    body = text[block.open_brace + 1:block.close_brace]
    pos_match = POSITION_RE.search(body)
    if not pos_match: return None
    numbers = parse_numbers(pos_match.group(1))
    if len(numbers) < 2: return None
    name_match = NAME_RE.search(body)
    name = name_match.group(1).replace('""', '"').replace(r'\"', '"').strip() if name_match else block.name
    return Location(block.name, name, numbers[0], numbers[1])

def find_names_block(text: str, blocks: list[ClassBlock]) -> tuple[ClassBlock, list[Location]]:
    candidates = []
    for block in blocks:
        if block.name.lower() != "names": continue
        locations = [loc for child in direct_child_classes(text, block) if (loc := parse_location_block(text, child))]
        if locations: candidates.append((block, locations))
    if not candidates:
        raise ValueError("Could not find class Names entries with position[]={x,y,...}.")
    candidates.sort(key=lambda item: len(item[1]), reverse=True)
    return candidates[0]

def find_enclosing_world_class(names_block: ClassBlock, blocks: list[ClassBlock]) -> Optional[ClassBlock]:
    parents = [b for b in blocks if b.name.lower() != "names" and b.open_brace < names_block.start < b.close_brace]
    return min(parents, key=lambda b: b.close_brace - b.open_brace) if parents else None

def parse_center_position(text: str, world: Optional[ClassBlock]) -> Optional[tuple[float, float]]:
    if world is None: return None
    match = CENTER_RE.search(text[world.open_brace + 1:world.close_brace])
    if not match: return None
    values = parse_numbers(match.group(1))
    return (values[0], values[1]) if len(values) >= 2 else None

def parse_map_size(text: str, world: Optional[ClassBlock]) -> Optional[float]:
    if world is None: return None
    match = MAP_SIZE_RE.search(text[world.open_brace + 1:world.close_brace])
    if not match: return None
    value = float(match.group(1))
    return value if value > 0 else None

def format_number(value: float) -> str:
    if not math.isfinite(value): raise ValueError(f"Non-finite coordinate: {value}")
    if abs(value - round(value)) < 1e-9: return str(int(round(value)))
    text = f"{value:.6f}".rstrip("0").rstrip(".")
    return "0" if text == "-0" else text

def sqs_quote(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'

def infer_base(locations, center, base_location, base_x, base_y):
    if (base_x is None) != (base_y is None): raise ValueError("--base-x and --base-y must be supplied together.")
    if base_x is not None: return base_x, base_y, "command-line --base-x/--base-y"
    if base_location:
        wanted = base_location.casefold()
        matches = [loc for loc in locations if loc.name.casefold() == wanted or loc.class_name.casefold() == wanted]
        if not matches:
            partial = [loc for loc in locations if wanted in loc.name.casefold() or wanted in loc.class_name.casefold()]
            if len(partial) == 1: matches = partial
        if len(matches) != 1: raise ValueError(f'Could not uniquely resolve base location "{base_location}".')
        loc = matches[0]
        return loc.x, loc.y, f'location "{loc.name}"'
    if center is not None: return center[0], center[1], "config.cpp centerPosition[]"
    xs = [loc.x for loc in locations]; ys = [loc.y for loc in locations]
    return (min(xs)+max(xs))/2, (min(ys)+max(ys))/2, "center of parsed Names positions"

def infer_world_size(locations, center, parsed_map_size, requested_world_size):
    if requested_world_size is not None:
        if requested_world_size <= 0: raise ValueError("--world-size must be greater than zero.")
        return requested_world_size, "command-line --world-size"
    if parsed_map_size is not None: return parsed_map_size, "config.cpp mapSize/worldSize"
    if center is not None:
        estimate = math.ceil((2.0 * max(center[0], center[1])) / 100.0) * 100.0
        if estimate > max(max(loc.x, loc.y) for loc in locations): return estimate, "2 x config.cpp centerPosition[] estimate"
    estimate = math.ceil((max(max(loc.x, loc.y) for loc in locations) + 500.0) / 100.0) * 100.0
    return estimate, "furthest Names position + 500 m estimate"

def determine_bounds(locations, center, parsed_map_size, args):
    explicit = [args.min_x, args.min_y, args.max_x, args.max_y]
    if any(v is not None for v in explicit):
        if not all(v is not None for v in explicit): raise ValueError("--min-x, --min-y, --max-x and --max-y must be supplied together.")
        if args.max_x <= args.min_x or args.max_y <= args.min_y: raise ValueError("Explicit max bounds must be greater than min bounds.")
        return args.min_x, args.min_y, args.max_x, args.max_y, "explicit bounds"
    size, source = infer_world_size(locations, center, parsed_map_size, args.world_size)
    if args.margin < 0 or args.margin * 2 >= size: raise ValueError("--margin must be >= 0 and less than half the world size.")
    return args.margin, args.margin, size - args.margin, size - args.margin, source

def build_world_config(world_name, locations, base_x, base_y, min_x, min_y, max_x, max_y, input_name, base_source, bounds_source):
    labels = ",".join(sqs_quote(loc.name) for loc in locations)
    xs = ",".join(format_number(loc.x) for loc in locations)
    ys = ",".join(format_number(loc.y) for loc in locations)
    return f'''; Generated by generate_world_config.py from {input_name}
; Parsed {len(locations)} class Names locations.
; Base point source: {base_source}
; Bounds source: {bounds_source}
; Keep the three location arrays on one line for old OFP/CWA SQS compatibility.
worldConfigReady = false
worldUseEditorLocationMarkers = false
worldName = {sqs_quote(world_name)}

missionBaseX = {format_number(base_x)}
missionBaseY = {format_number(base_y)}
worldMinX = {format_number(min_x)}
worldMinY = {format_number(min_y)}
worldMaxX = {format_number(max_x)}
worldMaxY = {format_number(max_y)}

missionLocationLabels = [{labels}]
missionLocationXs = [{xs}]
missionLocationYs = [{ys}]

missionLocationMarkers = []
_i = 0
#worldMarkerLoop
? _i >= count missionLocationLabels : goto "worldMarkerDone"
missionLocationMarkers = missionLocationMarkers + [format ["site_%1", _i]]
_i = _i + 1
goto "worldMarkerLoop"

#worldMarkerDone
missionLocationTotal = count missionLocationLabels
missionTownMarkers = missionLocationMarkers
missionTownLabels = missionLocationLabels
missionTownXs = missionLocationXs
missionTownYs = missionLocationYs
missionTownTotal = missionLocationTotal
missionTrafficMarkers = missionLocationMarkers
missionTrafficLabels = missionLocationLabels
missionTrafficXs = missionLocationXs
missionTrafficYs = missionLocationYs
missionTrafficTotal = missionLocationTotal
missionUnnamedTrafficMarkers = []
missionUnnamedTrafficLabels = []
missionUnnamedTrafficXs = []
missionUnnamedTrafficYs = []
missionUnnamedTrafficTotal = 0
worldConfigReady = true
exit
'''

def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Generate a CWA-safe worldConfig.sqs from config.cpp class Names.")
    parser.add_argument("config", type=Path)
    parser.add_argument("-o", "--output", type=Path, default=Path("worldConfig.sqs"))
    parser.add_argument("--world-name")
    parser.add_argument("--base-location")
    parser.add_argument("--base-x", type=float)
    parser.add_argument("--base-y", type=float)
    parser.add_argument("--world-size", type=float)
    parser.add_argument("--margin", type=float, default=250.0)
    parser.add_argument("--min-x", type=float); parser.add_argument("--min-y", type=float)
    parser.add_argument("--max-x", type=float); parser.add_argument("--max-y", type=float)
    parser.add_argument("--sort", choices=("config", "name"), default="config")
    return parser.parse_args(argv)

def main(argv=None) -> int:
    args = parse_args(argv)
    if not args.config.is_file():
        print(f"error: config file not found: {args.config}", file=sys.stderr); return 2
    try:
        text = strip_comments(read_text(args.config))
        blocks = find_class_blocks(text)
        names_block, locations = find_names_block(text, blocks)
        world_block = find_enclosing_world_class(names_block, blocks)
        if args.sort == "name": locations.sort(key=lambda loc: loc.name.casefold())
        center = parse_center_position(text, world_block)
        parsed_map_size = parse_map_size(text, world_block)
        world_name = args.world_name or (world_block.name if world_block else args.config.parent.name) or "Unknown"
        base_x, base_y, base_source = infer_base(locations, center, args.base_location, args.base_x, args.base_y)
        min_x, min_y, max_x, max_y, bounds_source = determine_bounds(locations, center, parsed_map_size, args)
        output = build_world_config(world_name, locations, base_x, base_y, min_x, min_y, max_x, max_y, args.config.name, base_source, bounds_source)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8", newline="\n")
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr); return 2
    print(f"Parsed {len(locations)} locations from: {args.config}")
    print(f"World name: {world_name}")
    print(f"Base: {format_number(base_x)}, {format_number(base_y)} ({base_source})")
    print(f"Bounds: {format_number(min_x)}, {format_number(min_y)} -> {format_number(max_x)}, {format_number(max_y)} ({bounds_source})")
    print(f"Wrote: {args.output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
