import customtkinter as ctk
from ui.constants import *
from ui.widgets import make_panel, panel_title, divider

def build_instrumento(app, parent):
    p = make_panel(parent)
    p.grid(row=0, column=0, padx=(14, 7), pady=(14, 7), sticky="nsew")

    panel_title(p, "▦", "Instrumento/Planilha")
    divider(p)
    app.entry_num = app.labeled_entry(p, "Numero do Instrumento", width=200)
    app.entry_dir = app.labeled_entry(p, "Diretório da planilha", width=160, browse=True)
    ctk.CTkFrame(p, height=10, fg_color="transparent").pack()