import customtkinter as ctk
from ui.constants import *
from ui.widgets import make_panel, panel_title, divider, slider_row, help_badge

def build_configuracoes(app, parent):
    p = make_panel(parent)
    p.grid(row=2, column=0, columnspan=2, padx=14, pady=(0, 14), sticky="nsew")

    # ── Title row with buttons ────────────────────────────────────────────────
    title_row = ctk.CTkFrame(p, fg_color="transparent")
    title_row.pack(fill="x", padx=6, pady=(14, 8))

    ctk.CTkLabel(
        title_row, text="⚙", font=("Montserrat UI Semibold", 14), text_color=ICON_COLOR
    ).pack(side="left", padx=(0, 6))
    ctk.CTkLabel(
        title_row,
        text="Configurações",
        font=("Montserrat UI Semibold", 13),
        text_color=TEXT_DARK,
    ).pack(side="left")

    buttons_frame = ctk.CTkFrame(title_row, fg_color="transparent")
    buttons_frame.pack(side="right")

    ctk.CTkButton(
        buttons_frame,
        text="Salvar Configuração",
        fg_color=ACCENT_GREEN,
        hover_color=ACCENT_GREEN_H,
        text_color="#FFFFFF",
        font=("Montserrat UI Semibold", 10),
        height=28,
        corner_radius=4,
        command=app._save_config,
    ).pack(side="left", padx=4)

    ctk.CTkButton(
        buttons_frame,
        text="Carregar Configuração Salva",
        fg_color=SIDEBAR_BG,
        hover_color=SIDEBAR_HOVER,
        text_color="#FFFFFF",
        font=("Montserrat UI Semibold", 10),
        height=28,
        corner_radius=4,
        command=app._load_saved_config,
    ).pack(side="left", padx=4)

    ctk.CTkButton(
        buttons_frame,
        text="Carregar Configuração Padrão",
        fg_color=ACCENT_RED,
        hover_color=ACCENT_RED_H,
        text_color="#FFFFFF",
        font=("Montserrat UI Semibold", 10),
        height=28,
        corner_radius=4,
        command=app._load_default_config,
    ).pack(side="left", padx=4)

    divider(p)

    # ── Inner columns ─────────────────────────────────────────────────────────
    cfg_inner = ctk.CTkFrame(p, fg_color="transparent")
    cfg_inner.pack(fill="both", expand=True, padx=4, pady=(0, 10))
    cfg_inner.columnconfigure((0, 1, 2), weight=1)

    # ── Col 0 – sliders ───────────────────────────────────────────────────────
    col0 = ctk.CTkFrame(cfg_inner, fg_color="transparent")
    col0.grid(row=0, column=0, sticky="nsew", padx=(8, 4))

    app.slider_precisao, app.entry_precisao = slider_row(
        col0,
        "Precisão de correspondência:",
        from_=0, to=100, default=85,
        tooltip="Define o quão rigoroso o algoritmo de correspondência agirá sobre as descrições dos itens. Quanto maior o valor, menor a chance de um item ser preenchido incorretamente, porém maior a chance de falsos negativos, onde itens válidos são rejeitados por não atingirem o limiar exigido.",
    )
    app.slider_velocidade, app.entry_velocidade = slider_row(
        col0,
        "Velocidade de preenchimento:",
        from_=0, to=100, default=50,
        tooltip="Define a velocidade de preenchimento da automação no sistema TransfereGov. Quanto maior o valor, mais rápido o preenchimento, porém mais instável a automação, aumentando o risco de falhas e interrupções.",
    )

    # Vertical separator
    ctk.CTkFrame(cfg_inner, width=1, fg_color=PANEL_BORDER).grid(
        row=0, column=1, sticky="ns", padx=4, pady=6
    )

    # ── Col 1 – small entries ─────────────────────────────────────────────────
    col1 = ctk.CTkFrame(cfg_inner, fg_color="transparent")
    col1.grid(row=0, column=1, sticky="nsew", padx=12)

    app.entry_attempts = _small_entry(
        col1,
        "Tentativas por item:",
        tooltip="Define a quantidade de tentativas de preenchimento serão feitas por item caso o mesmo não seja encontrado no sistema.",
    )

    _build_restarts_row(app, col1)

    # Vertical separator
    ctk.CTkFrame(cfg_inner, width=1, fg_color=PANEL_BORDER).grid(
        row=0, column=2, sticky="ns", padx=4, pady=6
    )

    # ── Col 2 – checkbox ──────────────────────────────────────────────────────
    col2 = ctk.CTkFrame(cfg_inner, fg_color="transparent")
    col2.grid(row=0, column=2, sticky="nsew", padx=12)

    cb_row = ctk.CTkFrame(col2, fg_color="transparent")
    cb_row.pack(anchor="w", pady=10)

    ctk.CTkCheckBox(
        cb_row,
        text="Tentar realizar login\nautomaticamente",
        variable=app.var_auto_login,
        font=("Montserrat UI", 11),
        text_color=TEXT_MID,
        fg_color=SIDEBAR_BG,
        hover_color=SIDEBAR_HOVER,
        checkmark_color="#FFFFFF",
        border_color=FIELD_BORDER,
    ).pack(side="left")

    help_badge(cb_row, "Tenta realizar o login no Gov automaticamente. Atenção: Essa função pode não funcionar corretamente.").pack(side="left", padx=(10, 0))

    # ── Start button ──────────────────────────────────────────────────────────
    footer_frame = ctk.CTkFrame(p, fg_color="transparent")
    footer_frame.pack(fill="x", padx=12, pady=(10, 12))
    footer_frame.pack_propagate(False)

    ctk.CTkButton(
        footer_frame,
        text="Iniciar Preenchimento",
        fg_color=ACCENT_GREEN,
        hover_color=ACCENT_GREEN_H,
        text_color="#FFFFFF",
        font=("Montserrat UI Semibold", 12),
        height=36,
        width=200,
        corner_radius=6,
        command=app._start_filling,
    ).pack(side="right", anchor="e")


# ── Private helpers ───────────────────────────────────────────────────────────
def _small_entry(parent, label, width=90, tooltip=""):
    """Small labeled entry used inside the config panel."""
    f = ctk.CTkFrame(parent, fg_color="transparent")
    f.pack(fill="x", pady=6)

    label_row = ctk.CTkFrame(f, fg_color="transparent")
    label_row.pack(fill="x")

    ctk.CTkLabel(
        label_row,
        text=label,
        font=("Montserrat UI", 11),
        text_color=TEXT_MID,
        anchor="w",
    ).pack(side="left")

    if tooltip:
        help_badge(label_row, tooltip).pack(side="left", padx=(6, 0))

    e = ctk.CTkEntry(
        f,
        width=width,
        height=28,
        fg_color=FIELD_BG,
        border_color=FIELD_BORDER,
        border_width=1,
        corner_radius=4,
        font=("Montserrat UI", 11),
        text_color=TEXT_DARK,
    )
    e.pack(anchor="w")
    return e


def _build_restarts_row(app, parent):
    """Reinicializações máximas entry + checkbox row."""
    f = ctk.CTkFrame(parent, fg_color="transparent")
    f.pack(fill="x", pady=6)

    label_row = ctk.CTkFrame(f, fg_color="transparent")
    label_row.pack(fill="x", pady=(0, 4))

    ctk.CTkLabel(
        label_row,
        text="Reinicializações máximas:",
        font=("Montserrat UI", 11),
        text_color=TEXT_MID,
        anchor="w",
    ).pack(side="left")

    help_badge(label_row, "Define a quantidade de vezes a automação irá reiniciar caso o sistema falhe ou venha a cair.").pack(side="left", padx=(6, 0))

    entry_row = ctk.CTkFrame(f, fg_color="transparent")
    entry_row.pack(fill="x")

    app.entry_restarts = ctk.CTkEntry(
        entry_row,
        width=90,
        height=28,
        fg_color=FIELD_BG,
        border_color=FIELD_BORDER,
        border_width=1,
        corner_radius=4,
        font=("Montserrat UI", 11),
        text_color=TEXT_DARK,
    )
    app.entry_restarts.pack(side="left")

    def on_checkbox_change():
        if app.var_use_restarts.get():
            app.entry_restarts.configure(state="normal")
        else:
            app.entry_restarts.delete(0, "end")
            app.entry_restarts.configure(state="disabled")

    ctk.CTkCheckBox(
        entry_row,
        text="Usar limite",
        variable=app.var_use_restarts,
        command=on_checkbox_change,
        font=("Montserrat UI", 10),
        text_color=TEXT_MID,
        fg_color=SIDEBAR_BG,
        hover_color=SIDEBAR_HOVER,
        checkmark_color="#FFFFFF",
        border_color=FIELD_BORDER,
    ).pack(side="left", padx=(12, 0))