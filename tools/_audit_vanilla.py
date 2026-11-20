from pathlib import Path
import tempfile, re, json, collections
from mission_package import create_mission_package
from asset_packs import unknown_classes

template = Path("cwr_assault_planner_v203.eden")
with tempfile.TemporaryDirectory() as td:
    d = create_mission_package(template, Path(td), "eden", "AuditVanilla",
                               (template/"worldConfig.sqs").read_text(), 10875, 11700, asset_pack="vanilla")
    files = {p.relative_to(d).as_posix(): p.read_bytes().decode("latin-1") for p in d.rglob("*") if p.is_file()}
    print("FILES:", len(files), dict(collections.Counter(Path(p).suffix for p in files)))
    print("ASSET FILES:", [p for p in files if p.startswith("assets/")])
    print("SELECTION:", repr(files["assets/selection.sqs"]))
    sqm=files["mission.sqm"]
    print("ADDONS:", re.findall(r"(?i)addOns(?:Auto)?\s*\[\]\s*=\s*\{[^}]+\}", sqm))
    print("EDITOR VEHICLES:", collections.Counter(re.findall(r'\bvehicle\s*=\s*"([^"]+)"', sqm)))
    print("WW4 CLASS LITERALS:", {p:unknown_classes(s) for p,s in files.items() if unknown_classes(s)})
    ww4lines = {}
    strings = {}
    resources = collections.defaultdict(set)
    missing = []
    for p,s in files.items():
        for line in s.splitlines():
            if re.search(r"ww4|map_rucksack",line,re.I):
                ww4lines[p]=ww4lines.get(p,0)+1
            for val in re.findall(r'"([^"\r\n]+)"', line):
                if re.search(r"ww4|map_rucksack", val, re.I):
                    strings.setdefault(val,set()).add(p)
                if re.search(r'\.(?:sqs|sqf|paa|pac|p3d|ogg|wss|wav|hpp|txt|pbo|html)$',val,re.I):
                    path=val.replace("\\","/")
                    if path.startswith("/"):
                        resources["external"].add(path)
                    elif path.casefold() not in {x.casefold() for x in files}:
                        resources["unresolved-relative"].add(path)
                    else:
                        resources["local"].add(path)
    print("WW4 TEXT FILES:", len(ww4lines), "LINES:",sum(ww4lines.values()))
    print("ALL WW4/MAP QUOTED STRINGS:", json.dumps({v:sorted(p) for v,p in strings.items()},sort_keys=True))
    print("EXTERNAL RESOURCE PATHS:", sorted(resources["external"]))
    print("UNRESOLVED RESOURCE PATHS:", sorted(resources["unresolved-relative"]))
    print("LOCAL RESOURCE COUNT:", len(resources["local"]))
    # Compare against the exact set of original profile's mod-only
    # quoted tokens, including classes which are not WW4-prefixed.
    old=(template/"assets/ww4.sqs").read_text(encoding="latin-1")
    new=files["assets/vanilla.sqs"]
    ids=lambda s: set(v.casefold() for v in re.findall(r'"([A-Za-z_]\w*)"',s))
    removed=ids(old)-ids(new)
    occurrences = {p:sorted(ids(s)&removed) for p,s in files.items() if ids(s)&removed}
    print("REMOVED PROFILE TOKEN MATCHES (including labels and generic class names):",json.dumps(occurrences))
    print("DYNAMIC LOADING:", json.dumps({p:[l.strip() for l in s.splitlines() if re.search(r"\b(?:exec|preprocessfile|loadfile|compile)\s+(?!\")",l,re.I) and not l.lstrip().startswith(";")] for p,s in files.items() if re.search(r"\b(?:exec|preprocessfile|loadfile|compile)\s+(?!\")",s,re.I)}))
    assert not any(unknown_classes(s) for s in files.values())
    assert not (d/"assets/ww4.sqs").exists()
    assert not any(re.search(r'ww4',m,re.I) for m in re.findall(r"(?i)addOns(?:Auto)?\s*\[\]\s*=\s*\{([^}]+)\}",sqm))
