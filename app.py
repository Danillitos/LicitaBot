import customtkinter as ctk
from tkinter import filedialog
import tkinter as tk
from pathlib import Path
import json
import threading
from ui.constants import *
from ui.widgets import *

# ── Appearance ────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

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
        self.var_total           = tk.StringVar(value="0")
        self.var_filled          = tk.StringVar(value="0")
        self.var_remaining       = tk.StringVar(value="0")
        self.var_inits           = tk.StringVar(value="0")
        self.var_errors          = tk.StringVar(value="0")
        self.var_auto_login      = tk.BooleanVar(value=False)
        self.var_use_restarts    = tk.BooleanVar(value=True)
        
        # Configuration sliders and entries (will be created in _build_main)
        self.slider_precisao     = None
        self.slider_velocidade   = None
        self.entry_attempts      = None
        self.entry_restarts      = None
        
        # Message display and loading spinner
        self.message_display     = None
        self.loading_spinner     = None
        self.loading_label       = None

        self._build_header()
        self._build_body()
        self._build_footer()
        self._load_config()

        # Show startup message
        self.show_message("✓ LicitaBot iniciado com sucesso!", "success")

        self.bind_all(
            "<Button-1>",
            lambda e: self.focus_set()
            if not isinstance(e.widget, (ctk.CTkEntry, tk.Entry))
            else None,
        )

    # ── Header ────────────────────────────────────────────────────────────────
    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=HEADER_BG, height=52, corner_radius=0)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

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

        ctk.CTkFrame(self, height=1, fg_color=PANEL_BORDER, corner_radius=0).pack(
            fill="x"
        )

    # ── Body ─────────────────────────────────────────────────────────────────
    def _build_body(self):
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)
        self._build_sidebar(body)
        self._build_main(body)

    # ── Sidebar ───────────────────────────────────────────────────────────────
    def _build_sidebar(self, parent):
        sidebar = ctk.CTkFrame(parent, fg_color=SIDEBAR_BG, width=175, corner_radius=0)
        sidebar.pack(fill="y", side="left")
        sidebar.pack_propagate(False)

        nav_items = [("Inicio", True)]
        for text, active in nav_items:
            bg = SIDEBAR_ACTIVE if active else SIDEBAR_BG
            ctk.CTkButton(
                sidebar,
                text=text,
                font=("Montserrat UI Semibold" if active else "Montserrat UI", 13),
                text_color="#FFFFFF",
                fg_color=bg,
                hover_color=SIDEBAR_HOVER,
                corner_radius=0,
                height=42,
                anchor="center",
            ).pack(fill="x", pady=(0, 1))

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

        # Loading spinner label
        self.loading_label = ctk.CTkLabel(
            p_info,
            text="",
            font=("Montserrat UI", 12),
            text_color=ACCENT_GREEN,
        )
        self.loading_label.pack(pady=4)
        self.loading_spinner = LoadingSpinner(self.loading_label)

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
        self.listbox.insert("end", *[f.name for f in sheets])

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

        # Custom title with buttons
        title_row = ctk.CTkFrame(p_cfg, fg_color="transparent")
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
        
        # Buttons on the right
        buttons_frame = ctk.CTkFrame(title_row, fg_color="transparent")
        buttons_frame.pack(side="right", padx=0)
        
        ctk.CTkButton(
            buttons_frame,
            text="Salvar Configuração",
            fg_color=ACCENT_GREEN,
            hover_color=ACCENT_GREEN_H,
            text_color="#FFFFFF",
            font=("Montserrat UI Semibold", 10),
            height=28,
            corner_radius=4,
            command=self._save_config,
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
            command=self._load_saved_config,
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
            command=self._load_default_config,
        ).pack(side="left", padx=4)
        
        divider(p_cfg)

        cfg_inner = ctk.CTkFrame(p_cfg, fg_color="transparent")
        cfg_inner.pack(fill="both", expand=True, padx=4, pady=(0, 10))
        cfg_inner.columnconfigure((0, 1, 2), weight=1)

        # Col 0 – sliders
        col0 = ctk.CTkFrame(cfg_inner, fg_color="transparent")
        col0.grid(row=0, column=0, sticky="nsew", padx=(8, 4))

        self.slider_precisao, self.entry_precisao = slider_row(
            col0,
            "Precisão de correspondência:",
            from_=0, to=100, default=85,
            tooltip="Define o quão rigoroso o algoritmo de correspondência agirá sobre as descrições dos itens. Quanto maior o valor, menor a chance de um item ser preenchido incorretamente, porém maior a chance de falsos negativos, onde itens válidos são rejeitados por não atingirem o limiar exigido.",
        )
        self.slider_velocidade, self.entry_velocidade = slider_row(
            col0,
            "Velocidade de preenchimento:",
            from_=0, to=100, default=50,
            tooltip="Define a velocidade de preenchimento da automação no sistema TransfereGov. Quanto maior o valor, mais rápido o preenchimento, porém mais instável a automação, aumentando o risco de falhas e interrupções.",
        )

        # Vertical separator
        ctk.CTkFrame(cfg_inner, width=1, fg_color=PANEL_BORDER).grid(
            row=0, column=1, sticky="ns", padx=4, pady=6
        )

        # Col 1 – small entries
        col1 = ctk.CTkFrame(cfg_inner, fg_color="transparent")
        col1.grid(row=0, column=1, sticky="nsew", padx=12)

        def small_labeled_entry(parent, label, width=90, tooltip=""):
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

        self.entry_attempts = small_labeled_entry(
            col1,
            "Tentativas por item:",
            tooltip="Define a quantidade de tentativas de preenchimento serão feitas por item caso o mesmo não seja encontrado no sistema.",
        )
        
        # "Reinicializações máximas" with checkbox
        f_restarts = ctk.CTkFrame(col1, fg_color="transparent")
        f_restarts.pack(fill="x", pady=6)

        label_restarts_row = ctk.CTkFrame(f_restarts, fg_color="transparent")
        label_restarts_row.pack(fill="x", padx=0, pady=(0, 4))

        ctk.CTkLabel(
            label_restarts_row,
            text="Reinicializações máximas:",
            font=("Montserrat UI", 11),
            text_color=TEXT_MID,
            anchor="w",
        ).pack(side="left")

        help_badge(label_restarts_row, "Define a quantidade de vezes a automação irá reiniciar caso o sistema falhe ou venha a cair.").pack(side="left", padx=(6, 0))

        entry_restarts_row = ctk.CTkFrame(f_restarts, fg_color="transparent")
        entry_restarts_row.pack(fill="x")

        self.entry_restarts = ctk.CTkEntry(
            entry_restarts_row,
            width=90,
            height=28,
            fg_color=FIELD_BG,
            border_color=FIELD_BORDER,
            border_width=1,
            corner_radius=4,
            font=("Montserrat UI", 11),
            text_color=TEXT_DARK,
        )
        self.entry_restarts.pack(side="left")

        def on_restarts_checkbox_change():
            if self.var_use_restarts.get():
                self.entry_restarts.configure(state="normal")
            else:
                self.entry_restarts.delete(0, "end")
                self.entry_restarts.configure(state="disabled")

        ctk.CTkCheckBox(
            entry_restarts_row,
            text="Usar limite",
            variable=self.var_use_restarts,
            command=on_restarts_checkbox_change,
            font=("Montserrat UI", 10),
            text_color=TEXT_MID,
            fg_color=SIDEBAR_BG,
            hover_color=SIDEBAR_HOVER,
            checkmark_color="#FFFFFF",
            border_color=FIELD_BORDER,
        ).pack(side="left", padx=(12, 0))

        # Vertical separator
        ctk.CTkFrame(cfg_inner, width=1, fg_color=PANEL_BORDER).grid(
            row=0, column=2, sticky="ns", padx=4, pady=6
        )

        # Col 2 – checkbox + badge
        col2 = ctk.CTkFrame(cfg_inner, fg_color="transparent")
        col2.grid(row=0, column=2, sticky="nsew", padx=12)

        cb_row = ctk.CTkFrame(col2, fg_color="transparent")
        cb_row.pack(anchor="w", pady=10)

        ctk.CTkCheckBox(
            cb_row,
            text="Tentar realizar login\nautomaticamente",
            variable=self.var_auto_login,
            font=("Montserrat UI", 11),
            text_color=TEXT_MID,
            fg_color=SIDEBAR_BG,
            hover_color=SIDEBAR_HOVER,
            checkmark_color="#FFFFFF",
            border_color=FIELD_BORDER,
        ).pack(side="left")

        help_badge(cb_row, "Tenta realizar o login no Gov automaticamente. Atenção: Essa função pode não funcionar corretamente.").pack(side="left", padx=(10, 0))

        # Bottom footer with "Iniciar Preenchimento" button
        footer_frame = ctk.CTkFrame(p_cfg, fg_color="transparent")
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
            command=self._start_filling,
        ).pack(side="right", anchor="e")

    # ── Footer with message display ────────────────────────────────────────────
    def _build_footer(self):
        footer = ctk.CTkFrame(self, fg_color=PANEL_BG, height=120, corner_radius=0)
        footer.pack(fill="x", side="bottom", padx=14, pady=(0, 14))
        footer.pack_propagate(False)

        # Border on top
        ctk.CTkFrame(footer, height=1, fg_color=PANEL_BORDER).pack(fill="x", pady=(0, 8))

        # Message display with scrollbar
        msg_frame = ctk.CTkFrame(footer, fg_color=LISTBOX_BG, border_width=1, border_color=FIELD_BORDER, corner_radius=4)
        msg_frame.pack(fill="both", expand=True, padx=0, pady=(0, 8))
        msg_frame.columnconfigure(0, weight=1)
        msg_frame.rowconfigure(0, weight=1)

        self.message_display = tk.Text(
            msg_frame,
            bg=LISTBOX_BG,
            fg=TEXT_DARK,
            font=("Montserrat UI", 10),
            relief="flat",
            bd=0,
            highlightthickness=0,
            wrap="word",
            height=4,
            state="disabled",  # Make it read-only
        )
        self.message_display.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        scrollbar = ctk.CTkScrollbar(msg_frame, command=self.message_display.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.message_display.configure(yscrollcommand=scrollbar.set)

        # Configure text tags for different message types
        self.message_display.tag_config("success", foreground="#4A7C59")
        self.message_display.tag_config("error", foreground="#8B3A3A")
        self.message_display.tag_config("info", foreground="#2D4A5A")
        self.message_display.tag_config("warning", foreground="#D4A574")

    def show_message(self, message: str, msg_type: str = "info"):
        """Display a message in the GUI message area.
        msg_type: 'success', 'error', 'info', 'warning'
        """
        if self.message_display is None:
            return

        # Enable text widget for editing
        self.message_display.config(state="normal")
        
        # Add timestamp
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Add message with tag
        self.message_display.insert("end", f"[{timestamp}] {message}\n", msg_type)
        
        # Disable text widget again
        self.message_display.config(state="disabled")
        
        # Auto-scroll to bottom
        self.message_display.see("end")
        self.update()

    # ── Helpers ───────────────────────────────────────────────────────────────
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
            ctk.CTkButton(
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
            ).pack(side="left", padx=(4, 0))

        return entry

    # ── Button callbacks ──────────────────────────────────────────────────────
    def _select_sheet(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        name = self.listbox.get(sel[0])
        path = Path("Sheets").resolve() / name
        self.entry_dir.delete(0, "end")
        self.entry_dir.insert(0, str(path))
        self._load_sheet_info(str(path))

    def _load_sheet_info(self, path: str):
        """Load sheet info in a background thread."""
        def load_thread():
            try:
                import pandas as pd
                df        = pd.read_excel(path)
                total     = len(df)
                mask      = df.iloc[:, 4].notna() & (df.iloc[:, 4] != 0)
                filled    = int(mask.sum())
                remaining = total - filled

                # Schedule UI update on main thread
                self.after(0, lambda: self._update_sheet_info(total, filled, remaining))
            except Exception as e:
                self.after(0, lambda: self._update_sheet_info_error(str(e)))
        
        # Show loading spinner and start thread
        self.loading_spinner.start()
        thread = threading.Thread(target=load_thread, daemon=True)
        thread.start()
    
    def _update_sheet_info(self, total, filled, remaining):
        """Update UI with loaded sheet info."""
        self.var_total.set(str(total))
        self.var_filled.set(str(filled))
        self.var_remaining.set(str(remaining))
        self.var_inits.set("0")
        self.var_errors.set("0")
        self.loading_spinner.stop()
    
    def _update_sheet_info_error(self, error_msg):
        """Update UI when sheet loading fails."""
        self.var_total.set("Erro")
        self.var_filled.set("—")
        self.var_remaining.set("—")
        self.show_message(f"Erro ao carregar planilha: {error_msg}", "error")
        self.loading_spinner.stop()

    def _remove_selection(self):
        sel = self.listbox.curselection()
        if sel:
            self.listbox.delete(sel[0])

    def _start_filling(self):
        """Validate inputs and start the filling process."""
        # Validation
        errors = []
        
        if not self.entry_num.get().strip():
            errors.append("• Número do Instrumento é obrigatório")
        
        if not self.entry_dir.get().strip():
            errors.append("• Diretório da planilha é obrigatório")
        
        if not self.entry_precisao.get().strip():
            errors.append("• Precisão de correspondência é obrigatória")
        
        if not self.entry_velocidade.get().strip():
            errors.append("• Velocidade de preenchimento é obrigatória")
        
        if not self.entry_attempts.get().strip():
            errors.append("• Tentativas por item é obrigatória")
        
        if self.var_use_restarts.get() and not self.entry_restarts.get().strip():
            errors.append("• Reinicializações máximas é obrigatória (desmarque se não usar limite)")
        
        if errors:
            error_msg = "Preencha todos os campos obrigatórios:\n\n" + "\n".join(errors)
            self.show_message(error_msg, "error")
            return
        
        # Prepare configuration
        config = {
            "instrumento": self.entry_num.get().strip(),
            "planilha_path": self.entry_dir.get().strip(),
            "precisao": float(self.entry_precisao.get()),
            "velocidade": float(self.entry_velocidade.get()),
            "tentativas": int(self.entry_attempts.get()),
            "reinicializacoes": int(self.entry_restarts.get()) if self.var_use_restarts.get() else None,
            "usar_limite_reinicializacoes": self.var_use_restarts.get(),
        }
        
        msg_lines = [
            "✓ Iniciando preenchimento com as seguintes configurações:",
            f"  → Instrumento: {config['instrumento']}",
            f"  → Planilha: {config['planilha_path']}",
            f"  → Precisão: {config['precisao']}",
            f"  → Velocidade: {config['velocidade']}",
            f"  → Tentativas: {config['tentativas']}",
        ]
        if config['usar_limite_reinicializacoes']:
            msg_lines.append(f"  → Reinicializações máximas: {config['reinicializacoes']}")
        else:
            msg_lines.append(f"  → Reinicializações: Ilimitado")
        
        self.show_message("\n".join(msg_lines), "success")
        
        # Call main.py with the configuration
        self._call_main(config)

    def _call_main(self, config: dict):
        import sys
        import importlib.util
        import io
        from contextlib import redirect_stdout, redirect_stderr
        
        try:
            # Load main.py as a module
            spec = importlib.util.spec_from_file_location("main", "main.py")
            main_module = importlib.util.module_from_spec(spec)
            
            sys.modules['main'] = main_module
            spec.loader.exec_module(main_module)
            
            main_module.PRE_INSTRUMENTO = config['instrumento']
            main_module.PLANILHA_PATH = config['planilha_path']
            main_module.SIMILARITY_THRESHOLD = 1 - (config['precisao'] / 100)
            main_module.MAX_TRIES = config['tentativas']
            main_module.MAX_RESTARTS = config['reinicializacoes'] if config['usar_limite_reinicializacoes'] else None
            
            slider_value = config['velocidade']
            main_module.VELOCIDADE_MULTIPLICADOR = (100 - slider_value) / 100 * 0.9 + 0.1
            
            main_module.RELATORIO_PATH = main_module.get_relatorio_path()
            
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                main_module.run_filling()
            
            # Display captured output in GUI
            stdout_output = stdout_capture.getvalue()
            stderr_output = stderr_capture.getvalue()
            
            if stdout_output:
                for line in stdout_output.strip().split('\n'):
                    if line.strip():
                        self.show_message(line, "info")
            
            if stderr_output:
                for line in stderr_output.strip().split('\n'):
                    if line.strip():
                        self.show_message(line, "error")
            
            self.show_message("✓ Preenchimento concluído!", "success")
        except Exception as e:
            error_msg = f"✗ Erro ao executar preenchimento: {e}"
            self.show_message(error_msg, "error")
            import traceback
            traceback.print_exc()

    # ── Configuration Management ──────────────────────────────────────────────
    def _save_config(self):
        """Save current configuration to JSON file."""
        try:
            # Validate and get values with defaults
            instrumento = self.entry_num.get() or ""
            planilha_path = self.entry_dir.get() or ""
            precisao = self.entry_precisao.get() or "85"
            velocidade = self.entry_velocidade.get() or "50"
            tentativas = self.entry_attempts.get() or "3"
            reinicializacoes = self.entry_restarts.get() or "5" if self.var_use_restarts.get() else "0"
            
            config = {
                "instrumento": instrumento,
                "planilha_path": planilha_path,
                "precisao_correspondencia": int(precisao),
                "velocidade_preenchimento": int(velocidade),
                "tentativas_por_item": int(tentativas),
                "reinicializacoes_maximas": int(reinicializacoes),
                "usar_limite_reinicializacoes": self.var_use_restarts.get(),
                "tentar_login_automaticamente": self.var_auto_login.get(),
            }
            
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=4)
            
            self.show_message("✓ Configuração salva com sucesso!", "success")
        except Exception as e:
            self.show_message(f"✗ Erro ao salvar configuração: {e}", "error")

    def _load_config(self):
        """Load configuration from JSON file on startup."""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r") as f:
                    config = json.load(f)
                
                # Wait for widgets to be created before loading
                self.after(100, lambda: self._apply_config(config))
            except Exception as e:
                self.show_message(f"Erro ao carregar configuração: {e}", "warning")

    def _load_saved_config(self):
        """Load saved configuration from JSON file."""
        if not CONFIG_FILE.exists():
            self.show_message("✗ Nenhuma configuração salva encontrada!", "error")
            return
        
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
            
            self._apply_config(config)
            self.show_message("✓ Configuração carregada com sucesso!", "success")
        except Exception as e:
            self.show_message(f"✗ Erro ao carregar configuração: {e}", "error")

    def _load_default_config(self):
        """Load default configuration."""
        self._apply_config(DEFAULT_CONFIG)
        self.show_message("✓ Configuração padrão carregada!", "success")

    def _apply_config(self, config: dict):
        """Apply configuration values to the UI."""
        try:
            # Only apply if widgets are initialized
            if self.entry_precisao is None:
                return
            
            # Load instrumento and planilha_path
            self.entry_num.delete(0, "end")
            self.entry_num.insert(0, config.get("instrumento", DEFAULT_CONFIG["instrumento"]))
            
            self.entry_dir.delete(0, "end")
            self.entry_dir.insert(0, config.get("planilha_path", DEFAULT_CONFIG["planilha_path"]))

            if self.entry_dir:
                self._load_sheet_info(self.entry_dir.get())
            
            self.entry_precisao.delete(0, "end")
            self.entry_precisao.insert(0, str(config.get("precisao_correspondencia", DEFAULT_CONFIG["precisao_correspondencia"])))
            self.slider_precisao.set(float(self.entry_precisao.get()))
            
            self.entry_velocidade.delete(0, "end")
            self.entry_velocidade.insert(0, str(config.get("velocidade_preenchimento", DEFAULT_CONFIG["velocidade_preenchimento"])))
            self.slider_velocidade.set(float(self.entry_velocidade.get()))
            
            self.entry_attempts.delete(0, "end")
            self.entry_attempts.insert(0, str(config.get("tentativas_por_item", DEFAULT_CONFIG["tentativas_por_item"])))
            
            use_limit = config.get("usar_limite_reinicializacoes", DEFAULT_CONFIG["usar_limite_reinicializacoes"])
            self.var_use_restarts.set(use_limit)
            
            if use_limit:
                self.entry_restarts.configure(state="normal")
                self.entry_restarts.delete(0, "end")
                self.entry_restarts.insert(0, str(config.get("reinicializacoes_maximas", DEFAULT_CONFIG["reinicializacoes_maximas"])))
            else:
                self.entry_restarts.delete(0, "end")
                self.entry_restarts.configure(state="disabled")
            
            self.var_auto_login.set(config.get("tentar_login_automaticamente", DEFAULT_CONFIG["tentar_login_automaticamente"]))
        except Exception as e:
            self.show_message(f"Erro ao aplicar configuração: {e}", "warning")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = LicitaBotApp()
    app.mainloop()