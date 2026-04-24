import tkinter as tk
import customtkinter as ctk
from logic.sheet_loader import load_sheets
from ui.constants import *
from ui.widgets import make_panel, panel_title, divider

def build_sheets(app, parent):
    p = make_panel(parent)
    p.grid(row=0, column=1, rowspan=2, padx=(0, 14), pady=(14, 7), sticky="nsew")
    p.rowconfigure(1, weight=1)
    p.columnconfigure(0, weight=1)

    panel_title(p, "≡", "Listagem de planilhas")
    divider(p)

    list_inner = ctk.CTkFrame(p, fg_color="transparent")
    list_inner.pack(fill="both", expand=True, padx=12, pady=(0, 12))
    list_inner.columnconfigure(0, weight=1)
    list_inner.rowconfigure(0, weight=1)

    lb_frame = ctk.CTkFrame(
        list_inner,
        fg_color=LISTBOX_BG,
        border_width=1,
        border_color=FIELD_BORDER,
        corner_radius=4,
    )
    lb_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
    lb_frame.rowconfigure(0, weight=1)
    lb_frame.columnconfigure(0, weight=1)

    app.listbox = tk.Listbox(
        lb_frame,
        bg=LISTBOX_BG,
        fg=TEXT_DARK,
        selectbackground=SIDEBAR_BG,
        selectforeground="#FFFFFF",
        activestyle="none",
        font=("Montserrat UI", 11),
        relief="flat",
        bd=0,
        highlightthickness=0,
    )
    app.listbox.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
    initial_sheets = load_sheets()
    if initial_sheets:
        app.listbox.insert("end", *[f.name for f in initial_sheets])

    scrollbar = ctk.CTkScrollbar(lb_frame, command=app.listbox.yview)
    scrollbar.grid(row=0, column=1, sticky="ns")
    app.listbox.configure(yscrollcommand=scrollbar.set)

    btn_col = ctk.CTkFrame(list_inner, fg_color="transparent", width=130)
    btn_col.grid(row=0, column=1, sticky="n")
    btn_col.pack_propagate(False)

    ctk.CTkButton(
        btn_col,
        text="Selecionar Planilha",
        fg_color=ACCENT_GREEN,
        hover_color=ACCENT_GREEN_H,
        text_color="#FFFFFF",
        font=("Montserrat UI Semibold", 12),
        height=36,
        corner_radius=6,
        command=app._select_sheet,
    ).pack(fill="x", pady=(0, 8))

    ctk.CTkButton(
        btn_col,
        text="Remover Seleção",
        fg_color=ACCENT_RED,
        hover_color=ACCENT_RED_H,
        text_color="#FFFFFF",
        font=("Montserrat UI Semibold", 12),
        height=36,
        corner_radius=6,
        command=app._remove_selection,
    ).pack(fill="x", pady=(0, 8))

    ctk.CTkButton(
        btn_col,
        text="Pasta de Planilhas",
        fg_color=SIDEBAR_BG,
        hover_color=SIDEBAR_HOVER,
        text_color="#FFFFFF",
        font=("Montserrat UI Semibold", 12),
        height=36,
        corner_radius=6,
        command=app._open_sheets_folder,
    ).pack(fill="x", pady=(0, 8))

    ctk.CTkButton(
        btn_col,
        text="Atualizar lista",
        fg_color=SIDEBAR_BG,
        hover_color=SIDEBAR_HOVER,
        text_color="#FFFFFF",
        font=("Montserrat UI Semibold", 12),
        height=36,
        corner_radius=6,
        command=app._update_sheets_list,
    ).pack(fill="x")
    