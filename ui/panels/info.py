import customtkinter as ctk
from ui.constants import *
from ui.widgets import make_panel, panel_title, divider, info_row, LoadingSpinner

def build_info(app, parent):
    p = make_panel(parent)
    p.grid(row=1, column=0, padx=(14, 7), pady=(0, 7), sticky="nsew")

    panel_title(p, "ℹ", "Informações Gerais")
    divider(p)

    app.loading_label = ctk.CTkLabel(
        p,
        text="",
        font=("Montserrat UI", 12),
        text_color=ACCENT_GREEN,
    )
    app.loading_label.pack(pady=4)
    app.loading_spinner = LoadingSpinner(app.loading_label)

    info_row(p, "Quantidade de linhas:",                app.var_total)
    info_row(p, "Quantidade de linhas já preenchidas:", app.var_filled)
    info_row(p, "Quantidade de linhas restantes:",      app.var_remaining)
    info_row(p, "Quantidade de inicializações:",        app.var_inits)
    info_row(p, "Erros encontrados:",                   app.var_errors)

    ctk.CTkFrame(p, height=10, fg_color="transparent").pack()