from pathlib import Path
import sys

APP_VERSION = "1.0.0"

# ── Appearance ────────────────────────────────────────────────────────────────
SIDEBAR_BG      = "#2D4A5A"
SIDEBAR_HOVER   = "#3A5F72"
SIDEBAR_ACTIVE  = "#1E3545"
HEADER_BG       = "#FFFFFF"
MAIN_BG         = "#EAEEF0"
PANEL_BG        = "#FFFFFF"
PANEL_BORDER    = "#D0D8DC"
ACCENT_GREEN    = "#4A7C59"
ACCENT_GREEN_H  = "#3D6B4A"
ACCENT_RED      = "#8B3A3A"
ACCENT_RED_H    = "#7A2E2E"
TEXT_DARK       = "#1A2B35"
TEXT_MID        = "#4A6070"
TEXT_LIGHT      = "#8A9EAA"
FIELD_BG        = "#F5F7F8"
FIELD_BORDER    = "#C8D4DA"
SLIDER_BG       = "#B0C4CE"
SLIDER_FG       = "#2D4A5A"
LISTBOX_BG      = "#F5F7F8"
ICON_COLOR      = "#2D4A5A"

# ── Fixed resolution ──────────────────────────────────────────────────────────
APP_W = 1440
APP_H = 900

# ── Folders ───────────────────────────────────────────────────────────────────
def resource_path(relative_path: str) -> Path:
    if hasattr(sys, '_MEIPASS'):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).parent.parent
    return base / relative_path

def get_base_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent

BASE_DIR = get_base_dir()
SHEETS_DIR = BASE_DIR / "Sheets"
SHEETS_DIR.mkdir(exist_ok=True)
sheets = [f for f in SHEETS_DIR.iterdir() if f.suffix in (".xlsx", ".xls")]