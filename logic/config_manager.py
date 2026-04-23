import json
from pathlib import Path

CONFIG_FILE = Path("config.json")

DEFAULT_CONFIG = {
    "instrumento": "",
    "planilha_path": "",
    "precisao_correspondencia": 85,
    "velocidade_preenchimento": 50,
    "tentativas_por_item": 3,
    "reinicializacoes_maximas": 5,
    "usar_limite_reinicializacoes": True,
    "tentar_login_automaticamente": False,
}

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
