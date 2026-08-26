#!/usr/bin/env python3
"""
Tkinter GUI for generate_world_config.py.

Pick a terrain/world folder, load its config.cpp, review the parsed class Names
locations and inferred defaults, then generate a CWA/OFP-safe worldConfig.sqs.

No third-party dependencies are required.
"""

from __future__ import annotations

import math
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

try:
    import generate_world_config as gen
except ImportError:
    # Helpful when launched in unusual ways from another working directory.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import generate_world_config as gen


APP_TITLE = "CWA World Config Generator"


class WorldConfigGui(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.minsize(880, 640)

        self.locations = []
        self.config_path: Path | None = None

        self.source_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.world_name = tk.StringVar()

        self.base_x = tk.StringVar()
        self.base_y = tk.StringVar()
        self.min_x = tk.StringVar()
        self.min_y = tk.StringVar()
        self.max_x = tk.StringVar()
        self.max_y = tk.StringVar()
        self.margin = tk.StringVar(value="250")

        self.sort_mode = tk.StringVar(value="config")
        self.editor_markers = tk.BooleanVar(value=False)
        self.status = tk.StringVar(value="Choose a world folder containing config.cpp.")

        self._build_ui()

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(4, weight=1)

        source = ttk.LabelFrame(root, text="Source world", padding=10)
        source.grid(row=0, column=0, columnspan=3, sticky="ew")
        source.columnconfigure(1, weight=1)

        ttk.Label(source, text="World folder:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        ttk.Entry(source, textvariable=self.source_dir).grid(row=0, column=1, sticky="ew")
        ttk.Button(source, text="Browse folder...", command=self.pick_source_folder).grid(
            row=0, column=2, padx=(8, 0)
        )
        ttk.Button(source, text="Load config.cpp", command=self.load_source).grid(
            row=1, column=2, padx=(8, 0), pady=(8, 0)
        )
        ttk.Label(
            source,
            text="The GUI first checks <folder>/config.cpp, then searches subfolders if needed.",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))

        settings = ttk.LabelFrame(root, text="Generated world settings", padding=10)
        settings.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(10, 0))
        for col in (1, 3, 5):
            settings.columnconfigure(col, weight=1)

        ttk.Label(settings, text="World name:").grid(row=0, column=0, sticky="w")
        ttk.Entry(settings, textvariable=self.world_name).grid(
            row=0, column=1, columnspan=5, sticky="ew", padx=(6, 0)
        )

        ttk.Label(settings, text="Base X:").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(settings, textvariable=self.base_x, width=14).grid(
            row=1, column=1, sticky="ew", padx=(6, 12), pady=(8, 0)
        )
        ttk.Label(settings, text="Base Y:").grid(row=1, column=2, sticky="w", pady=(8, 0))
        ttk.Entry(settings, textvariable=self.base_y, width=14).grid(
            row=1, column=3, sticky="ew", padx=(6, 12), pady=(8, 0)
        )
        ttk.Button(settings, text="Use selected location as base", command=self.use_selected_as_base).grid(
            row=1, column=4, columnspan=2, sticky="ew", pady=(8, 0)
        )

        ttk.Label(settings, text="Min X:").grid(row=2, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(settings, textvariable=self.min_x, width=14).grid(
            row=2, column=1, sticky="ew", padx=(6, 12), pady=(8, 0)
        )
        ttk.Label(settings, text="Min Y:").grid(row=2, column=2, sticky="w", pady=(8, 0))
        ttk.Entry(settings, textvariable=self.min_y, width=14).grid(
            row=2, column=3, sticky="ew", padx=(6, 12), pady=(8, 0)
        )
        ttk.Label(settings, text="Margin:").grid(row=2, column=4, sticky="w", pady=(8, 0))
        ttk.Entry(settings, textvariable=self.margin, width=12).grid(
            row=2, column=5, sticky="ew", padx=(6, 0), pady=(8, 0)
        )

        ttk.Label(settings, text="Max X:").grid(row=3, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(settings, textvariable=self.max_x, width=14).grid(
            row=3, column=1, sticky="ew", padx=(6, 12), pady=(8, 0)
        )
        ttk.Label(settings, text="Max Y:").grid(row=3, column=2, sticky="w", pady=(8, 0))
        ttk.Entry(settings, textvariable=self.max_y, width=14).grid(
            row=3, column=3, sticky="ew", padx=(6, 12), pady=(8, 0)
        )
        ttk.Button(settings, text="Re-infer base/bounds", command=self.reinfer_defaults).grid(
            row=3, column=4, columnspan=2, sticky="ew", pady=(8, 0)
        )

        options = ttk.Frame(root)
        options.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(10, 0))
        ttk.Label(options, text="Location order:").pack(side="left")
        ttk.Radiobutton(
            options, text="Config order", variable=self.sort_mode, value="config",
            command=self.refresh_location_table
        ).pack(side="left", padx=(6, 0))
        ttk.Radiobutton(
            options, text="Alphabetical", variable=self.sort_mode, value="name",
            command=self.refresh_location_table
        ).pack(side="left", padx=(6, 16))
        ttk.Checkbutton(
            options,
            text="Use editor site_* markers",
            variable=self.editor_markers,
        ).pack(side="left")

        preview = ttk.LabelFrame(root, text="Parsed class Names locations", padding=8)
        preview.grid(row=4, column=0, columnspan=3, sticky="nsew", pady=(10, 0))
        preview.columnconfigure(0, weight=1)
        preview.rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            preview,
            columns=("index", "class", "name", "x", "y"),
            show="headings",
            selectmode="browse",
        )
        self.tree.heading("index", text="#")
        self.tree.heading("class", text="Class")
        self.tree.heading("name", text="Name")
        self.tree.heading("x", text="X")
        self.tree.heading("y", text="Y")
        self.tree.column("index", width=50, anchor="e", stretch=False)
        self.tree.column("class", width=160)
        self.tree.column("name", width=250)
        self.tree.column("x", width=120, anchor="e")
        self.tree.column("y", width=120, anchor="e")

        yscroll = ttk.Scrollbar(preview, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")

        output = ttk.LabelFrame(root, text="Output", padding=10)
        output.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(10, 0))
        output.columnconfigure(1, weight=1)

        ttk.Label(output, text="Output folder:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        ttk.Entry(output, textvariable=self.output_dir).grid(row=0, column=1, sticky="ew")
        ttk.Button(output, text="Browse folder...", command=self.pick_output_folder).grid(
            row=0, column=2, padx=(8, 0)
        )
        ttk.Label(output, text="File name: worldConfig.sqs").grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(8, 0)
        )
        self.generate_button = ttk.Button(
            output, text="Generate worldConfig.sqs", command=self.generate
        )
        self.generate_button.grid(row=1, column=2, padx=(8, 0), pady=(8, 0))

        status = ttk.Label(root, textvariable=self.status, anchor="w")
        status.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(10, 0))

    def pick_source_folder(self) -> None:
        folder = filedialog.askdirectory(title="Choose world folder")
        if not folder:
            return
        self.source_dir.set(folder)
        if not self.output_dir.get().strip():
            self.output_dir.set(folder)
        self.load_source()

    def pick_output_folder(self) -> None:
        initial = self.output_dir.get().strip() or self.source_dir.get().strip()
        folder = filedialog.askdirectory(
            title="Choose output folder",
            initialdir=initial if initial else None,
        )
        if folder:
            self.output_dir.set(folder)

    def find_config_cpp(self, folder: Path) -> Path:
        direct = folder / "config.cpp"
        if direct.is_file():
            return direct

        direct_casefold = [
            p for p in folder.iterdir()
            if p.is_file() and p.name.casefold() == "config.cpp"
        ]
        if len(direct_casefold) == 1:
            return direct_casefold[0]

        matches = []
        try:
            for p in folder.rglob("*"):
                if p.is_file() and p.name.casefold() == "config.cpp":
                    matches.append(p)
                    if len(matches) > 50:
                        break
        except OSError:
            pass

        if not matches:
            raise ValueError(f"No config.cpp found under:\n{folder}")
        if len(matches) == 1:
            return matches[0]

        # Prefer the shallowest config.cpp, which is normally the world config.
        matches.sort(key=lambda p: (len(p.relative_to(folder).parts), str(p).casefold()))
        shallowest_depth = len(matches[0].relative_to(folder).parts)
        shallowest = [p for p in matches if len(p.relative_to(folder).parts) == shallowest_depth]
        if len(shallowest) == 1:
            return shallowest[0]

        # Ambiguous folders are safer to reject than to silently parse an addon config.
        choices = "\n".join(str(p.relative_to(folder)) for p in shallowest[:10])
        raise ValueError(
            "Multiple equally likely config.cpp files were found.\n"
            "Choose the specific world folder containing the desired config.cpp.\n\n"
            + choices
        )

    def parse_source(self) -> tuple:
        source_text = self.source_dir.get().strip()
        if not source_text:
            raise ValueError("Choose a world folder first.")

        folder = Path(source_text).expanduser()
        if not folder.is_dir():
            raise ValueError(f"World folder does not exist:\n{folder}")

        config = self.find_config_cpp(folder)
        text = gen.strip_comments(gen.read_text(config))
        blocks = gen.find_class_blocks(text)
        names_block, locations = gen.find_names_block(text, blocks)
        world_block = gen.find_enclosing_world_class(names_block, blocks)
        center = gen.parse_center_position(text, world_block)
        map_size = gen.parse_map_size(text, world_block)
        inferred_name = world_block.name if world_block else config.parent.name

        return config, locations, center, map_size, inferred_name

    def load_source(self) -> None:
        try:
            config, locations, center, map_size, inferred_name = self.parse_source()
            self.config_path = config
            self.locations = locations
            self.world_name.set(inferred_name or "Unknown")

            self._set_inferred_defaults(center, map_size)

            if not self.output_dir.get().strip():
                self.output_dir.set(str(config.parent))

            self.refresh_location_table()
            self.status.set(
                f"Loaded {len(locations)} locations from {config}"
            )
        except Exception as exc:
            self.status.set("Load failed.")
            messagebox.showerror(APP_TITLE, str(exc))

    def _set_inferred_defaults(self, center, map_size) -> None:
        if not self.locations:
            return

        base_x, base_y, _ = gen.infer_base(
            self.locations, center, None, None, None
        )
        self.base_x.set(gen.format_number(base_x))
        self.base_y.set(gen.format_number(base_y))

        margin = self._float_from_var(self.margin, "Margin")
        size, _ = gen.infer_world_size(
            self.locations, center, map_size, None
        )
        if margin < 0 or margin * 2 >= size:
            margin = 250.0
            self.margin.set("250")

        self.min_x.set(gen.format_number(margin))
        self.min_y.set(gen.format_number(margin))
        self.max_x.set(gen.format_number(size - margin))
        self.max_y.set(gen.format_number(size - margin))

    def reinfer_defaults(self) -> None:
        if not self.source_dir.get().strip():
            messagebox.showinfo(APP_TITLE, "Choose and load a world folder first.")
            return
        try:
            config, locations, center, map_size, inferred_name = self.parse_source()
            self.config_path = config
            self.locations = locations
            if not self.world_name.get().strip():
                self.world_name.set(inferred_name or "Unknown")
            self._set_inferred_defaults(center, map_size)
            self.refresh_location_table()
            self.status.set("Re-inferred base point and world bounds.")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    def ordered_locations(self):
        locations = list(self.locations)
        if self.sort_mode.get() == "name":
            locations.sort(key=lambda loc: loc.name.casefold())
        return locations

    def refresh_location_table(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        for index, loc in enumerate(self.ordered_locations()):
            self.tree.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    index,
                    loc.class_name,
                    loc.name,
                    gen.format_number(loc.x),
                    gen.format_number(loc.y),
                ),
            )

    def use_selected_as_base(self) -> None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo(APP_TITLE, "Select a location in the table first.")
            return
        index = int(selection[0])
        locations = self.ordered_locations()
        if index < 0 or index >= len(locations):
            return
        loc = locations[index]
        self.base_x.set(gen.format_number(loc.x))
        self.base_y.set(gen.format_number(loc.y))
        self.status.set(f'Base point set to "{loc.name}".')

    def _float_from_var(self, var: tk.StringVar, label: str) -> float:
        text = var.get().strip()
        if not text:
            raise ValueError(f"{label} is required.")
        try:
            value = float(text)
        except ValueError as exc:
            raise ValueError(f"{label} must be a number.") from exc
        if not math.isfinite(value):
            raise ValueError(f"{label} must be a finite number.")
        return value

    def validate_generation(self):
        if not self.locations or self.config_path is None:
            raise ValueError("Load a world config.cpp before generating.")

        world_name = self.world_name.get().strip()
        if not world_name:
            raise ValueError("World name cannot be empty.")

        base_x = self._float_from_var(self.base_x, "Base X")
        base_y = self._float_from_var(self.base_y, "Base Y")
        min_x = self._float_from_var(self.min_x, "Min X")
        min_y = self._float_from_var(self.min_y, "Min Y")
        max_x = self._float_from_var(self.max_x, "Max X")
        max_y = self._float_from_var(self.max_y, "Max Y")

        if max_x <= min_x or max_y <= min_y:
            raise ValueError("Max bounds must be greater than min bounds.")

        output_text = self.output_dir.get().strip()
        if not output_text:
            raise ValueError("Choose an output folder.")
        output_dir = Path(output_text).expanduser()
        output_dir.mkdir(parents=True, exist_ok=True)

        locations = self.ordered_locations()
        if len(locations) < 6:
            raise ValueError(
                f"Only {len(locations)} locations were parsed. "
                "The mission needs at least 6 for objective clustering and staging."
            )

        return world_name, locations, base_x, base_y, min_x, min_y, max_x, max_y, output_dir

    def generate(self) -> None:
        try:
            (
                world_name,
                locations,
                base_x,
                base_y,
                min_x,
                min_y,
                max_x,
                max_y,
                output_dir,
            ) = self.validate_generation()

            output = gen.build_world_config(
                world_name=world_name,
                locations=locations,
                base_x=base_x,
                base_y=base_y,
                min_x=min_x,
                min_y=min_y,
                max_x=max_x,
                max_y=max_y,
                input_name=self.config_path.name,
                base_source="GUI selection",
                bounds_source="GUI values",
            )

            if self.editor_markers.get():
                output = output.replace(
                    "worldUseEditorLocationMarkers = false",
                    "worldUseEditorLocationMarkers = true",
                    1,
                )

            target = output_dir / "worldConfig.sqs"
            if target.exists():
                overwrite = messagebox.askyesno(
                    APP_TITLE,
                    f"{target.name} already exists in:\n{target.parent}\n\nOverwrite it?",
                )
                if not overwrite:
                    self.status.set("Generation cancelled.")
                    return

            target.write_text(output, encoding="utf-8", newline="\n")
            self.status.set(f"Generated {target}")
            messagebox.showinfo(
                APP_TITLE,
                f"Generated worldConfig.sqs\n\n"
                f"Locations: {len(locations)}\n"
                f"Output: {target}",
            )
        except Exception as exc:
            self.status.set("Generation failed.")
            messagebox.showerror(APP_TITLE, str(exc))


def main() -> int:
    app = WorldConfigGui()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
