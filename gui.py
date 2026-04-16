import customtkinter as ctk
import os

# Aparencia
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# Paleta de cores
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

#Pre-definições de janela
window = ctk.CTk()

#Resolução adaptativa
APP_W = 1440
APP_H = 900
MONITOR_W_REFERENCE = 1920
MONITOR_H_REFERENCE = 1080
MONITOR_W = window.winfo_screenwidth()
MONITOR_H = window.winfo_screenheight()
scale = min(MONITOR_W / MONITOR_W_REFERENCE,
            MONITOR_H / MONITOR_H_REFERENCE 
            )
adaptative_resolution_w = int(APP_W * scale)
adaptative_resolution_h = int(APP_H * scale)

print(adaptative_resolution_w)
print(adaptative_resolution_h)