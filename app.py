import customtkinter as ctk
from tkinter import filedialog
import tkinter as tk
from pathlib import Path
from ui.constants import *
from ui.widgets import *
from logic.config_manager import *
from logic.sheet_loader import *
from ui.panels.instrumento import build_instrumento
from ui.panels.info import build_info


# ── Appearance ────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# ══════════════════════════════════════════════════════════════════════════════
#  Main App
# ══════════════════════════════════════════════════════════════════════════════
class LicitaBotApp(ctk.CTk):
    _save_config = save_config
    _load_config = load_config
    _apply_config = apply_config
    _load_saved_config = load_saved_config
    _load_default_config = load_default_config 

    _load_sheet_info = load_sheet_info
    _update_sheet_info = update_sheet_info

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
        main.pack(fill="both", expand=True)

        main.columnconfigure(0, weight=3)
        main.columnconfigure(1, weight=2)
        main.rowconfigure(0, weight=0)
        main.rowconfigure(1, weight=0)
        main.rowconfigure(2, weight=1)

        build_instrumento(self, main)
        build_info(self, main)
        build_sheets(self, main)
        build_configuracoes(self, main)

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

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = LicitaBotApp()
    app.mainloop()