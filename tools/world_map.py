"""North-up coordinate grid and map editing for the world configuration GUI."""
from __future__ import annotations

import math
import tkinter as tk
from dataclasses import dataclass
from tkinter import messagebox, simpledialog, ttk

import generate_world_config as gen


@dataclass(frozen=True)
class Bounds:
    min_x: float
    min_y: float
    max_x: float
    max_y: float

    def __post_init__(self):
        if not all(math.isfinite(v) for v in (self.min_x, self.min_y, self.max_x, self.max_y)):
            raise ValueError("Bounds must be finite.")
        if self.max_x <= self.min_x or self.max_y <= self.min_y:
            raise ValueError("Bounds must have positive width and height.")

    def contains(self, x, y):
        return self.min_x <= x <= self.max_x and self.min_y <= y <= self.max_y

    def clamp(self, x, y):
        return (max(self.min_x, min(self.max_x, x)), max(self.min_y, min(self.max_y, y)))


@dataclass(frozen=True)
class View:
    cx: float
    cy: float
    scale: float
    width: float
    height: float

    @classmethod
    def fit(cls, b, width, height, padding=32):
        scale = min(max(1, width - 2 * padding) / (b.max_x - b.min_x),
                    max(1, height - 2 * padding) / (b.max_y - b.min_y))
        return cls((b.min_x + b.max_x) / 2, (b.min_y + b.max_y) / 2, scale, width, height)

    def screen(self, x, y):
        return self.width / 2 + (x - self.cx) * self.scale, self.height / 2 - (y - self.cy) * self.scale

    def world(self, sx, sy):
        return self.cx + (sx - self.width / 2) / self.scale, self.cy - (sy - self.height / 2) / self.scale

    def pan(self, dx, dy):
        return View(self.cx - dx / self.scale, self.cy + dy / self.scale, self.scale, self.width, self.height)

    def zoom(self, factor, sx, sy, minimum, maximum):
        x, y = self.world(sx, sy)
        scale = min(max(self.scale * factor, minimum), maximum)
        return View(x - (sx - self.width / 2) / scale, y + (sy - self.height / 2) / scale,
                    scale, self.width, self.height)


def grid_step(scale):
    metres = 85 / scale
    p = 10 ** math.floor(math.log10(metres))
    return next(f * p for f in (1, 2, 5, 10) if f * p >= metres)


def nearest_marker(view, locations, sx, sy, radius=12):
    best, distance = None, radius ** 2
    for i, loc in enumerate(locations):
        x, y = view.screen(loc.x, loc.y)
        d = (x - sx) ** 2 + (y - sy) ** 2
        if d <= distance:
            best, distance = i, d
    return best


def next_marker_class(locations):
    used = {loc.class_name.casefold() for loc in locations}
    i = 1
    while f"custom_site_{i}" in used:
        i += 1
    return f"custom_site_{i}"


class MapEditor(ttk.Frame):
    """Shared model: app.locations holds the exact values exported by Generate."""

    def __init__(self, parent, app):
        super().__init__(parent, padding=6)
        self.app = app
        self.view = None
        self.fit_scale = None
        self.pending = None
        self.drag = None
        self.pan_start = None
        self.mode = tk.StringVar(value="select")
        self.labels = tk.BooleanVar(value=True)
        self.info = tk.StringVar(value="Load a world to display its locations.")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        bar = ttk.Frame(self)
        bar.grid(row=0, column=0, sticky="ew")
        for label, mode in (("Select / move", "select"), ("Add marker", "add"), ("Set base", "base")):
            ttk.Radiobutton(bar, text=label, value=mode, variable=self.mode).pack(side="left", padx=(0, 8))
        ttk.Button(bar, text="Rename", command=self.rename).pack(side="left")
        ttk.Button(bar, text="Delete", command=self.delete).pack(side="left", padx=4)
        ttk.Button(bar, text="Fit map", command=self.fit).pack(side="right")
        options = ttk.Frame(self)
        options.grid(row=1, column=0, sticky="ew")
        ttk.Checkbutton(options, text="Labels", variable=self.labels, command=self.schedule).pack(side="left")
        ttk.Label(options, text="Wheel: zoom | Middle/right drag: pan | Grid only").pack(side="right")
        self.canvas = tk.Canvas(self, background="#e5edf0", highlightthickness=1, takefocus=True)
        self.canvas.grid(row=2, column=0, sticky="nsew")
        ttk.Label(self, textvariable=self.info, anchor="w").grid(row=3, column=0, sticky="ew")
        self.canvas.bind("<Configure>", self.resize)
        self.canvas.bind("<Motion>", self.motion)
        self.canvas.bind("<ButtonPress-1>", self.click)
        self.canvas.bind("<B1-Motion>", self.move)
        self.canvas.bind("<ButtonRelease-1>", self.release)
        for n in (2, 3):
            self.canvas.bind(f"<ButtonPress-{n}>", self.start_pan)
            self.canvas.bind(f"<B{n}-Motion>", self.pan)
        for event in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.canvas.bind(event, self.zoom)
        self.canvas.bind("<Delete>", lambda _: self.delete())

    def bounds(self):
        try:
            return Bounds(*(float(v.get()) for v in (self.app.min_x, self.app.min_y, self.app.max_x, self.app.max_y)))
        except (ValueError, OverflowError):
            return None

    def fit(self):
        self.view = self.fit_scale = None
        self.schedule()

    def schedule(self):
        if self.pending is None:
            self.pending = self.after_idle(self.draw)

    def resize(self, event):
        # Fit to the new size; avoids stale pixel scales after changing tabs.
        self.fit()

    def draw(self):
        self.pending = None
        c = self.canvas
        w, h = c.winfo_width(), c.winfo_height()
        if w < 10 or h < 10:
            return
        c.delete("all")
        b = self.bounds()
        if self.app.config_path is None or b is None:
            self.view = None
            c.create_text(w/2, h/2, text="Load config.cpp and enter valid world bounds.", fill="#52646f")
            return
        if self.view is None:
            xs = [b.min_x, b.max_x] + [loc.x for loc in self.app.locations]
            ys = [b.min_y, b.max_y] + [loc.y for loc in self.app.locations]
            if self.app.map_world_size is not None:
                xs.extend((0, self.app.map_world_size))
                ys.extend((0, self.app.map_world_size))
            try:
                bx, by = float(self.app.base_x.get()), float(self.app.base_y.get())
                if math.isfinite(bx) and math.isfinite(by):
                    xs.append(bx)
                    ys.append(by)
            except ValueError:
                pass
            self.view = View.fit(Bounds(min(xs), min(ys), max(xs), max(ys)), w, h)
            self.fit_scale = self.view.scale
        v = self.view
        c.create_rectangle(*v.screen(b.min_x, b.max_y), *v.screen(b.max_x, b.min_y),
                           fill="#fbfcfd", outline="#407553", width=2)
        step = grid_step(v.scale)
        x0, y0 = v.world(0, h)
        x1, y1 = v.world(w, 0)
        x = math.ceil(x0 / step) * step
        while x <= x1:
            sx, _ = v.screen(x, 0)
            c.create_line(sx, 0, sx, h, fill="#cbd6dc")
            c.create_text(sx+3, 4, text=gen.format_number(x), anchor="nw", fill="#52646f")
            x += step
        y = math.ceil(y0 / step) * step
        while y <= y1:
            _, sy = v.screen(0, y)
            c.create_line(0, sy, w, sy, fill="#cbd6dc")
            c.create_text(4, sy-3, text=gen.format_number(y), anchor="sw", fill="#52646f")
            y += step
        try:
            m = float(self.app.objective_edge.get())
            if 0 < 2*m < min(b.max_x-b.min_x, b.max_y-b.min_y):
                c.create_rectangle(*v.screen(b.min_x+m, b.max_y-m), *v.screen(b.max_x-m, b.min_y+m),
                                   outline="#b17735", dash=(5, 4))
        except ValueError:
            pass
        selected = self.app.selected_location_index()
        indices = [i for i in range(len(self.app.locations)) if i != selected]
        if selected is not None:
            indices.append(selected)
        for i in indices:
            loc = self.app.locations[i]
            x, y = v.screen(loc.x, loc.y)
            if not (-15 <= x <= w+15 and -15 <= y <= h+15):
                continue
            color = "#d66b1c" if i == selected else ("#2563a5" if b.contains(loc.x, loc.y) else "#87939a")
            r = 6 if i == selected else 4
            c.create_oval(x-r, y-r, x+r, y+r, fill=color, outline="white")
            if self.labels.get() or i == selected:
                c.create_text(x+7, y-5, text=loc.name, anchor="sw", fill="#223848")
        try:
            x, y = v.screen(float(self.app.base_x.get()), float(self.app.base_y.get()))
            if math.isfinite(x) and math.isfinite(y):
                c.create_polygon(x, y-9, x+9, y, x, y+9, x-9, y, fill="#26794a", outline="white", width=2)
                c.create_text(x+10, y+6, text="BASE", anchor="nw", fill="#175d38")
        except ValueError:
            pass
        c.create_text(w-6, 4, text="N ↑", anchor="ne", fill="#223848")
        c.create_text(w-6, h-4, text="Blue: location | Orange: selected | Green: base/bounds | Dashed: objective margin",
                      anchor="se", fill="#52646f", font=("TkDefaultFont", 8))

    def motion(self, event):
        if self.view:
            x, y = self.view.world(event.x, event.y)
            self.info.set(f"X: {x:.1f} m   Y: {y:.1f} m   |   {len(self.app.locations)} locations")

    def click(self, event):
        self.canvas.focus_set()
        self.drag = None
        b = self.bounds()
        if not self.view or b is None or self.app.config_path is None:
            return
        x, y = self.view.world(event.x, event.y)
        mode = self.mode.get()
        if mode in ("base", "add"):
            if not b.contains(x, y):
                self.info.set("Choose a point inside the usable world bounds.")
                return
            x, y = b.clamp(round(x, 1), round(y, 1))
            if mode == "base":
                self.app.base_x.set(gen.format_number(x))
                self.app.base_y.set(gen.format_number(y))
                self.app.status.set("Base point placed on map.")
            else:
                name = simpledialog.askstring("Add marker", "Location name:", parent=self)
                if name and name.strip():
                    self.add_location(name.strip(), x, y)
            return
        index = nearest_marker(self.view, self.app.locations, event.x, event.y)
        self.app.select_location(index)
        if index is not None:
            loc = self.app.locations[index]
            self.drag = (index, event.x, event.y, loc.x, loc.y)
        self.schedule()

    def add_location(self, name, x, y):
        self.app.locations.append(gen.Location(next_marker_class(self.app.locations), name, x, y))
        self.app.map_dirty = True
        self.app.refresh_location_table(selected=len(self.app.locations)-1)
        self.app.status.set(f'Added location "{name}".')

    def move(self, event):
        if self.drag is None or self.view is None:
            return
        i, sx, sy, ox, oy = self.drag
        b = self.bounds()
        if b is None or i >= len(self.app.locations) or abs(event.x-sx)+abs(event.y-sy) < 3:
            return
        x, y = b.clamp(round(ox+(event.x-sx)/self.view.scale, 1),
                       round(oy-(event.y-sy)/self.view.scale, 1))
        loc = self.app.locations[i]
        loc.x, loc.y = x, y
        self.app.tree.set(str(i), "x", gen.format_number(x))
        self.app.tree.set(str(i), "y", gen.format_number(y))
        self.app.map_dirty = True
        self.schedule()
        self.motion(event)

    def release(self, event):
        self.drag = None

    def start_pan(self, event):
        self.drag = None
        self.pan_start = (event.x, event.y)

    def pan(self, event):
        if self.view and self.pan_start:
            x, y = self.pan_start
            self.view = self.view.pan(event.x-x, event.y-y)
            self.pan_start = (event.x, event.y)
            self.schedule()

    def zoom(self, event):
        if self.view and self.fit_scale:
            direction = 1 if getattr(event, "num", None) == 4 or getattr(event, "delta", 0) > 0 else -1
            self.view = self.view.zoom(1.25**direction, event.x, event.y, self.fit_scale/4, self.fit_scale*40)
            self.schedule()
        return "break"

    def rename(self):
        i = self.app.selected_location_index()
        if i is None:
            return
        loc = self.app.locations[i]
        name = simpledialog.askstring("Rename marker", "Location name:", initialvalue=loc.name, parent=self)
        if name and name.strip() and name.strip() != loc.name:
            loc.name = name.strip()
            self.app.map_dirty = True
            self.app.refresh_location_table(selected=i)

    def delete(self):
        i = self.app.selected_location_index()
        if i is None:
            return
        if len(self.app.locations) <= 6:
            messagebox.showinfo("Map editor", "Keep at least six locations for mission generation.", parent=self)
            return
        if not messagebox.askyesno("Map editor", f'Delete "{self.app.locations[i].name}"?', parent=self):
            return
        self.drag = None
        self.app.select_location(None)
        del self.app.locations[i]
        self.app.map_dirty = True
        self.app.refresh_location_table()
        self.app.status.set("Location deleted.")
