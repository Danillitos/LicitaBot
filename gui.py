import customtkinter as ctk
from tkinter import filedialog
import tkinter as tk

# ── Appearance ────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# ── Palette ───────────────────────────────────────────────────────────────────
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
    row.pack(fill="x", padx=16, pady=(14, 8))
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


def slider_row(parent, label: str, from_=0, to=100, default=50, entry_width=50):
    """Label + slider + value entry."""
    col = ctk.CTkFrame(parent, fg_color="transparent")
    col.pack(fill="x", padx=12, pady=(6, 2))

    ctk.CTkLabel(
        col, text=label, font=("Montserrat UI", 11), text_color=TEXT_MID, anchor="w"
    ).pack(fill="x")

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

    return slider, entry


# ══════════════════════════════════════════════════════════════════════════════
#  Main App
# ══════════════════════════════════════════════════════════════════════════════
class LicitaBotApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("LicitaBot")
        self.geometry(f"{APP_W}x{APP_H}")
        self.configure(fg_color=MAIN_BG)
        self.resizable(False, False)

        # Info variables
        self.var_total     = tk.StringVar(value="0")
        self.var_filled    = tk.StringVar(value="0")
        self.var_remaining = tk.StringVar(value="0")
        self.var_inits     = tk.StringVar(value="0")
        self.var_errors    = tk.StringVar(value="0")
        self.var_auto_login = tk.BooleanVar(value=False)

        self._build_header()
        self._build_body()

    # ── Header ────────────────────────────────────────────────────────────────
    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=HEADER_BG, height=52, corner_radius=0)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        # Logo image (falls back to text if file not found)
        try:
            from PIL import Image
            logo_img = ctk.CTkImage(
                light_image=Image.open("assets/LOGO.png"),
                size=(140, 36),
            )
            ctk.CTkLabel(header, image=logo_img, text="").pack(
                side="left", padx=20, pady=8
            )
        except Exception:
            ctk.CTkLabel(
                header,
                text="⊙  Estratégia  Consultoria Técnica",
                font=("Montserrat UI Semibold", 13),
                text_color=TEXT_DARK,
            ).pack(side="left", padx=20, pady=14)

        # Bottom border line
        ctk.CTkFrame(self, height=1, fg_color=PANEL_BORDER, corner_radius=0).pack(
            fill="x"
        )

    # ── Body (sidebar + main) ─────────────────────────────────────────────────
    def _build_body(self):
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)

        self._build_sidebar(body)
        self._build_main(body)

    # ── Sidebar ───────────────────────────────────────────────────────────────
    def _build_sidebar(self, parent):
        sidebar = ctk.CTkFrame(
            parent, fg_color=SIDEBAR_BG, width=175, corner_radius=0
        )
        sidebar.pack(fill="y", side="left")
        sidebar.pack_propagate(False)

        nav_items = [("Inicio", True)]
        for text, active in nav_items:
            bg = SIDEBAR_ACTIVE if active else SIDEBAR_BG
            btn = ctk.CTkButton(
                sidebar,
                text=text,
                font=("Montserrat UI Semibold" if active else "Montserrat UI", 13),
                text_color="#FFFFFF",
                fg_color=bg,
                hover_color=SIDEBAR_HOVER,
                corner_radius=0,
                height=42,
                anchor="center",
            )
            btn.pack(fill="x", pady=(0, 1))

    # ── Main content ──────────────────────────────────────────────────────────
    def _build_main(self, parent):
        main = ctk.CTkFrame(parent, fg_color=MAIN_BG)
        main.pack(fill="both", expand=True, padx=0)

        main.columnconfigure(0, weight=3)
        main.columnconfigure(1, weight=2)
        main.rowconfigure(0, weight=0)
        main.rowconfigure(1, weight=0)
        main.rowconfigure(2, weight=1)

        # ── Row 0, Col 0: Instrumento/Planilha ───────────────────────────────
        p_instr = make_panel(main)
        p_instr.grid(row=0, column=0, padx=(14, 7), pady=(14, 7), sticky="nsew")

        panel_title(p_instr, "▦", "Instrumento/Planilha")
        divider(p_instr)
        self.entry_num = self.labeled_entry(p_instr, "Numero do Instrumento", width=200)
        self.entry_dir = self.labeled_entry(
            p_instr, "Diretório da planilha", width=160, browse=True
        )
        ctk.CTkFrame(p_instr, height=10, fg_color="transparent").pack()

        # ── Row 1, Col 0: Informações Gerais ─────────────────────────────────
        p_info = make_panel(main)
        p_info.grid(row=1, column=0, padx=(14, 7), pady=(0, 7), sticky="nsew")

        panel_title(p_info, "ℹ", "Informações Gerais")
        divider(p_info)

        info_row(p_info, "Quantidade de linhas:",                self.var_total)
        info_row(p_info, "Quantidade de linhas já preenchidas:", self.var_filled)
        info_row(p_info, "Quantidade de linhas restantes:",      self.var_remaining)
        info_row(p_info, "Quantidade de inicializações:",        self.var_inits)
        info_row(p_info, "Erros encontrados:",                   self.var_errors)
        ctk.CTkFrame(p_info, height=10, fg_color="transparent").pack()

        # ── Row 0-1 span, Col 1: Listagem de planilhas ───────────────────────
        p_list = make_panel(main)
        p_list.grid(
            row=0, column=1, rowspan=2, padx=(0, 14), pady=(14, 7), sticky="nsew"
        )
        p_list.rowconfigure(1, weight=1)
        p_list.columnconfigure(0, weight=1)

        panel_title(p_list, "≡", "Listagem de planilhas")
        divider(p_list)

        list_inner = ctk.CTkFrame(p_list, fg_color="transparent")
        list_inner.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        list_inner.columnconfigure(0, weight=1)
        list_inner.rowconfigure(0, weight=1)

        # Listbox (tk native inside a frame for scrolling)
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

        self.listbox = tk.Listbox(
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
        self.listbox.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        scrollbar = ctk.CTkScrollbar(lb_frame, command=self.listbox.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.listbox.configure(yscrollcommand=scrollbar.set)

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
            command=self._select_sheet,
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
            command=self._remove_selection,
        ).pack(fill="x")

        # ── Row 2, full width: Configurações ─────────────────────────────────
        p_cfg = make_panel(main)
        p_cfg.grid(
            row=2, column=0, columnspan=2, padx=14, pady=(0, 14), sticky="nsew"
        )

        panel_title(p_cfg, "⚙", "Configurações")
        divider(p_cfg)

        cfg_inner = ctk.CTkFrame(p_cfg, fg_color="transparent")
        cfg_inner.pack(fill="both", expand=True, padx=4, pady=(0, 10))
        cfg_inner.columnconfigure((0, 1, 2), weight=1)

        # Col 0 – sliders
        col0 = ctk.CTkFrame(cfg_inner, fg_color="transparent")
        col0.grid(row=0, column=0, sticky="nsew", padx=(8, 4))
        slider_row(col0, "Precisão de correspondência:", from_=0, to=100, default=50)
        slider_row(col0, "Velocidade de preenchimento:", from_=0, to=100, default=40)

        # Vertical separator
        ctk.CTkFrame(cfg_inner, width=1, fg_color=PANEL_BORDER).grid(
            row=0, column=1, sticky="ns", padx=4, pady=6
        )

        # Col 1 – small entries
        col1 = ctk.CTkFrame(cfg_inner, fg_color="transparent")
        col1.grid(row=0, column=1, sticky="nsew", padx=12)

        def small_labeled_entry(parent, label, width=90):
            f = ctk.CTkFrame(parent, fg_color="transparent")
            f.pack(fill="x", pady=6)
            ctk.CTkLabel(
                f, text=label, font=("Montserrat UI", 11), text_color=TEXT_MID, anchor="w"
            ).pack(fill="x")
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

        self.entry_attempts = small_labeled_entry(col1, "Tentativas por item:")
        self.entry_restarts = small_labeled_entry(col1, "Reinicializações máximas:")

        # Vertical separator
        ctk.CTkFrame(cfg_inner, width=1, fg_color=PANEL_BORDER).grid(
            row=0, column=2, sticky="ns", padx=4, pady=6
        )

        # Col 2 – checkbox
        col2 = ctk.CTkFrame(cfg_inner, fg_color="transparent")
        col2.grid(row=0, column=2, sticky="nsew", padx=12)

        ctk.CTkCheckBox(
            col2,
            text="Tentar realizar login\nautomaticamente",
            variable=self.var_auto_login,
            font=("Montserrat UI", 11),
            text_color=TEXT_MID,
            fg_color=SIDEBAR_BG,
            hover_color=SIDEBAR_HOVER,
            checkmark_color="#FFFFFF",
            border_color=FIELD_BORDER,
        ).pack(anchor="w", pady=10)

    def _browse(self, entry_widget):
        path = filedialog.askopenfilename(
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if path:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, path)
            self._load_sheet_info(path)

    def labeled_entry(self, parent, label: str, width=160, browse=False):
        """Label + entry (+ optional browse button) row."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=4)

        ctk.CTkLabel(
            row,
            text=label,
            font=("Montserrat UI", 11),
            text_color=TEXT_MID,
            width=180,
            anchor="w",
        ).pack(side="left")

        entry = ctk.CTkEntry(
            row,
            width=width,
            height=28,
            fg_color=FIELD_BG,
            border_color=FIELD_BORDER,
            border_width=1,
            corner_radius=4,
            font=("Montserrat UI", 11),
            text_color=TEXT_DARK,
        )
        entry.pack(side="left")

        if browse:
            btn = ctk.CTkButton(
                row,
                text="...",
                width=28,
                height=28,
                fg_color=FIELD_BG,
                hover_color=PANEL_BORDER,
                border_color=FIELD_BORDER,
                border_width=1,
                corner_radius=4,
                text_color=TEXT_DARK,
                font=("Montserrat UI", 11),
                command=lambda e=entry: self._browse(e),
            )
            btn.pack(side="left", padx=(4, 0))

        return entry    


    # ── Button callbacks ──────────────────────────────────────────────────────
    def _select_sheet(self):
        path = filedialog.askopenfilename(
            title="Selecionar Planilha",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")],
        )
        if path:
            name = path.split("/")[-1]
            if name not in self.listbox.get(0, "end"):
                self.listbox.insert("end", name)
            self._load_sheet_info(path)  # ← add this

    def _load_sheet_info(self, path: str):
        try:
            import pandas as pd
            df = pd.read_excel(path)

            total      = len(df)
            filled     = int(df.iloc[:, 4].notna().sum() & (df.iloc[:, 4] != 0).sum())
            # mirror your bot's filter logic exactly
            mask       = df.iloc[:, 4].notna() & (df.iloc[:, 4] != 0)
            filled     = int(mask.sum())
            remaining  = total - filled

            self.var_total.set(str(total))
            self.var_filled.set(str(filled))
            self.var_remaining.set(str(remaining))
            self.var_inits.set("0")   # resets on new sheet load
            self.var_errors.set("0")
        except Exception as e:
            self.var_total.set("Erro")
            self.var_filled.set("—")
            self.var_remaining.set("—")
            print(f"Erro ao carregar planilha: {e}")

    def _remove_selection(self):
        sel = self.listbox.curselection()
        if sel:
            self.listbox.delete(sel[0])


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = LicitaBotApp()
    app.mainloop()