"""Build a complete CWA/OFP mission folder from a mission template.

The world suffix on a mission directory must be the game's world class name.
"""

from __future__ import annotations

import re
import shutil
import tempfile
from pathlib import Path

_WORLD_ID = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_MISSION_ID = re.compile(r"[A-Za-z0-9_-]+\Z")
_POSITION = re.compile(
    r"(position\[\]\s*=\s*\{\s*)(-?\d+(?:\.\d+)?)"
    r"(\s*,\s*)(-?\d+(?:\.\d+)?)(\s*,\s*)"
    r"(-?\d+(?:\.\d+)?)(\s*\})"
)


def mission_folder_name(template: Path, world_name: str, mission_name: str = "") -> str:
    """Return <mission_name>.<world_class>, rejecting unsafe folder names."""
    world_name = world_name.strip()
    if not _WORLD_ID.fullmatch(world_name):
        raise ValueError(
            "World name must be the exact terrain class name "
            "(letters, digits and underscores; cannot begin with a digit)."
        )
    name = mission_name.strip() or template.name.rsplit(".", 1)[0]
    if not _MISSION_ID.fullmatch(name) or name.upper() in {
        "CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
        *(f"LPT{i}" for i in range(1, 10)),
    }:
        raise ValueError("Mission name may contain only letters, digits, _ and -.")
    return f"{name}.{world_name}"


def _old_base(config: str) -> tuple[float, float]:
    values = []
    for field in ("missionBaseX", "missionBaseY"):
        match = re.search(rf"(?m)^\s*{field}\s*=\s*(-?\d+(?:\.\d+)?)", config)
        if not match:
            raise ValueError(f"Mission template worldConfig.sqs is missing {field}.")
        values.append(float(match.group(1)))
    return values[0], values[1]


def relocate_mission_sqm(
    sqm: str, old_x: float, old_y: float, base_x: float, base_y: float
) -> str:
    """Shift placed editor entities and markers together to the new base point.

    CWA's position[] layout is {east, elevation, north}. Elevation is preserved.
    """
    dx, dy = base_x - old_x, base_y - old_y

    def shift(match: re.Match[str]) -> str:
        x = float(match.group(2)) + dx
        y = float(match.group(6)) + dy
        return (
            f"{match.group(1)}{x:.6f}{match.group(3)}{match.group(4)}"
            f"{match.group(5)}{y:.6f}{match.group(7)}"
        )

    updated, count = _POSITION.subn(shift, sqm)
    if count == 0:
        raise ValueError("Mission template mission.sqm has no editor positions to relocate.")
    return updated


def create_mission_package(
    template_dir: Path,
    output_parent: Path,
    world_name: str,
    mission_name: str,
    world_config: str,
    base_x: float,
    base_y: float,
) -> Path:
    """Copy all files and create <name>.<world> with a generated worldConfig.sqs.

    Existing missions are never overwritten. A staging directory keeps incomplete
    copies out of the user's missions folder if copying or writing fails.
    """
    template_dir = Path(template_dir).expanduser().resolve()
    output_parent = Path(output_parent).expanduser().resolve()
    name = mission_folder_name(template_dir, world_name, mission_name)

    if not template_dir.is_dir():
        raise ValueError(f"Mission template folder does not exist: {template_dir}")
    if not output_parent.is_dir():
        raise ValueError(f"Output folder does not exist: {output_parent}")
    if output_parent == template_dir or template_dir in output_parent.parents:
        raise ValueError("Select an output folder outside the mission template folder.")
    sqm_path = template_dir / "mission.sqm"
    config_path = template_dir / "worldConfig.sqs"
    if not sqm_path.is_file() or not config_path.is_file():
        raise ValueError("Mission template must contain mission.sqm and worldConfig.sqs.")

    # Older templates silently ignore new generator settings, which would
    # reintroduce map-edge problems even though worldConfig.sqs looks correct.
    randomize_path = template_dir / "randomize.sqs"
    init_path = template_dir / "init.sqs"
    required_settings = (
        "worldStageMinClearance", "worldStageMaxDistance",
        "worldObjectiveEdgeMargin", "worldAirStageOffset",
    )
    if (not randomize_path.is_file()
            or not init_path.is_file()
            or any(value not in randomize_path.read_text(encoding="utf-8-sig")
                   for value in required_settings)
            or '[] exec "worldConfig.sqs"' not in init_path.read_text(encoding="utf-8-sig")):
        raise ValueError(
            "The selected mission template is outdated. Choose the updated "
            "cwr_assault_planner_v203.eden folder from this branch so the new "
            "placement controls are actually used."
        )

    target = output_parent / name
    if target.exists() or target.is_symlink():
        raise FileExistsError(f"Mission folder already exists; nothing was overwritten: {target}")

    old_x, old_y = _old_base(config_path.read_text(encoding="utf-8-sig"))
    sqm = sqm_path.read_text(encoding="utf-8-sig")
    new_sqm = relocate_mission_sqm(sqm, old_x, old_y, base_x, base_y)

    staging_root = Path(tempfile.mkdtemp(prefix=".mission-build-", dir=output_parent))
    try:
        staged_mission = staging_root / name
        shutil.copytree(template_dir, staged_mission)
        (staged_mission / "worldConfig.sqs").write_text(world_config, encoding="utf-8", newline="\n")
        (staged_mission / "mission.sqm").write_text(new_sqm, encoding="utf-8", newline="\n")
        if target.exists() or target.is_symlink():
            raise FileExistsError(f"Mission folder appeared during generation: {target}")
        staged_mission.rename(target)
    finally:
        shutil.rmtree(staging_root, ignore_errors=True)
    return target
