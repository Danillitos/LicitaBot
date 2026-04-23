import customtkinter as ctk
import tkinter as tk
from itertools import cycle
from ui.constants import *

class Tooltip:
    def __init__(self, widget, text: str):
        self.widget = widget
        self.text   = text
        self.tw     = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        x = self.widget.winfo_rootx() + self.widget.winfo_width() + 6
        y = self.widget.winfo_rooty() + (self.widget.winfo_height() // 2)

        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry(f"+{x}+{y}")
        self.tw.attributes("-topmost", True)

        frame = tk.Frame(self.tw, background=TEXT_DARK, bd=0)
        frame.pack()

        tk.Label(
            frame,
            text=self.text,
            background=TEXT_DARK,
            foreground="#FFFFFF",
            font=("Montserrat UI", 10),
            wraplength=220,
            justify="left",
            padx=10,
            pady=8,
        ).pack()

    def hide(self, event=None):
        if self.tw:
            self.tw.destroy()
            self.tw = None


# ── Helper widgets ────────────────────────────────────────────────────────────
def make_panel(parent, **kwargs):
    """White rounded card panel."""
    return ctk.CTkFrame(
        parent,
        fg_color=PANEL_BG,
        corner_radius=8,
        border_width=1,
        border_color=PANEL_BORDER,
        **kwargs,
    )


def panel_title(parent, icon: str, text: str):
    """Icon + bold title row for a panel."""
    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(fill="x", padx=6, pady=(14, 8))
    ctk.CTkLabel(
        row, text=icon, font=("Montserrat UI Semibold", 14), text_color=ICON_COLOR
    ).pack(side="left", padx=(0, 6))
    ctk.CTkLabel(
        row,
        text=text,
        font=("Montserrat UI Semibold", 13),
        text_color=TEXT_DARK,
    ).pack(side="left")


def divider(parent):
    ctk.CTkFrame(parent, height=1, fg_color=PANEL_BORDER).pack(
        fill="x", padx=16, pady=(0, 10)
    )


def info_row(parent, label: str, var: tk.StringVar):
    """Key-value info row."""
    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(fill="x", padx=16, pady=2)
    ctk.CTkLabel(
        row,
        text=label,
        font=("Montserrat UI", 11),
        text_color=TEXT_MID,
        anchor="w",
    ).pack(side="left", fill="x", expand=True)
    ctk.CTkLabel(
        row,
        textvariable=var,
        font=("Montserrat UI Semibold", 11),
        text_color=TEXT_DARK,
        anchor="e",
        width=60,
    ).pack(side="right")


def help_badge(parent, tooltip_text: str):
    """Small ? label that shows a tooltip on hover."""
    badge = ctk.CTkLabel(
        parent,
        text=" ? ",
        font=("Montserrat UI Semibold", 10),
        text_color="#FFFFFF",
        fg_color=SLIDER_FG,
        corner_radius=10,
        width=18,
        height=18,
        cursor="question_arrow",
    )
    Tooltip(badge, tooltip_text)
    return badge


def slider_row(parent, label: str, from_=0, to=100, default=50, entry_width=50, tooltip: str = ""):
    """Label + slider + value entry, with an optional ? tooltip badge."""
    col = ctk.CTkFrame(parent, fg_color="transparent")
    col.pack(fill="x", padx=12, pady=(6, 2))

    # Label row (with optional badge)
    label_row = ctk.CTkFrame(col, fg_color="transparent")
    label_row.pack(fill="x")

    ctk.CTkLabel(
        label_row, text=label, font=("Montserrat UI", 11), text_color=TEXT_MID, anchor="w"
    ).pack(side="left")

    if tooltip:
        help_badge(label_row, tooltip).pack(side="left", padx=(6, 0))

    # Slider + entry row
    row = ctk.CTkFrame(col, fg_color="transparent")
    row.pack(fill="x")

    val_var = tk.StringVar(value=str(default))

    entry = ctk.CTkEntry(
        row,
        textvariable=val_var,
        width=entry_width,
        height=26,
        fg_color=FIELD_BG,
        border_color=FIELD_BORDER,
        border_width=1,
        corner_radius=4,
        font=("Montserrat UI", 11),
        text_color=TEXT_DARK,
        justify="center",
    )

    def on_slide(v):
        val_var.set(str(int(float(v))))

    slider = ctk.CTkSlider(
        row,
        from_=from_,
        to=to,
        command=on_slide,
        button_color=SLIDER_FG,
        button_hover_color=SIDEBAR_HOVER,
        progress_color=SLIDER_FG,
        fg_color=SLIDER_BG,
        height=14,
    )
    slider.set(default)
    slider.pack(side="left", fill="x", expand=True, padx=(0, 8), pady=4)
    entry.pack(side="left")

    def on_entry_change(*_):
        try:
            v = int(val_var.get())
        except ValueError:
            return

        clamped = max(from_, min(to, v))
        if v != clamped:
            val_var.set(str(clamped))
        slider.set(clamped)

    val_var.trace_add("write", on_entry_change)

    return slider, entry


# ── Loading Spinner ───────────────────────────────────────────────────────────
class LoadingSpinner:
    """Rotating loading spinner for background operations."""
    SPINNER_CHARS = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    
    def __init__(self, label_widget):
        self.label = label_widget
        self.spinner = cycle(self.SPINNER_CHARS)
        self.is_spinning = False
        self.after_id = None
    
    def _spin(self):
        if self.is_spinning:
            self.label.configure(text=next(self.spinner))
            self.after_id = self.label.after(100, self._spin)
    
    def start(self):
        self.is_spinning = True
        self._spin()
    
    def stop(self):
        self.is_spinning = False
        if self.after_id:
            self.label.after_cancel(self.after_id)
        self.label.configure(text="")

