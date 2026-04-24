import json
from pathlib import Path

from logic.sheet_loader import load_log_info, load_sheet_info

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

def save_config(app):
    """Save current configuration to JSON file."""
    try:
        # Validate and get values with defaults
        instrumento = app.entry_num.get() or ""
        planilha_path = app.entry_dir.get() or ""
        precisao = app.entry_precisao.get() or "85"
        velocidade = app.entry_velocidade.get() or "50"
        tentativas = app.entry_attempts.get() or "3"
        reinicializacoes = app.entry_restarts.get() or "5" if app.var_use_restarts.get() else "0"
        
        config = {
            "instrumento": instrumento,
            "planilha_path": planilha_path,
            "precisao_correspondencia": int(precisao),
            "velocidade_preenchimento": int(velocidade),
            "tentativas_por_item": int(tentativas),
            "reinicializacoes_maximas": int(reinicializacoes),
            "usar_limite_reinicializacoes": app.var_use_restarts.get(),
            "tentar_login_automaticamente": app.var_auto_login.get(),
        }
        
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
        
        app.show_message("✓ Configuração salva com sucesso!", "success")
    except Exception as e:
        app.show_message(f"✗ Erro ao salvar configuração: {e}", "error")

def load_config(app):
    """Load configuration from JSON file on startup."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
            
            # Wait for widgets to be created before loading
            app.after(100, lambda: app._apply_config(config))
        except Exception as e:
            app.show_message(f"Erro ao carregar configuração: {e}", "warning")

def load_saved_config(app):
    """Load saved configuration from JSON file."""
    if not CONFIG_FILE.exists():
        app.show_message("✗ Nenhuma configuração salva encontrada!", "error")
        return
    
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        
        app._apply_config(config)
        app.show_message("✓ Configuração carregada com sucesso!", "success")
    except Exception as e:
        app.show_message(f"✗ Erro ao carregar configuração: {e}", "error")

def load_default_config(app):
    """Load default configuration."""
    app._apply_config(DEFAULT_CONFIG)
    app.show_message("✓ Configuração padrão carregada!", "success")

def apply_config(app, config: dict):
    """Apply configuration values to the UI."""
    try:
        # Only apply if widgets are initialized
        if app.entry_precisao is None:
            return
        
        # Load instrumento and planilha_path
        app.entry_num.delete(0, "end")
        app.entry_num.insert(0, config.get("instrumento", DEFAULT_CONFIG["instrumento"]))
        
        app.entry_dir.delete(0, "end")
        app.entry_dir.insert(0, config.get("planilha_path", DEFAULT_CONFIG["planilha_path"]))


        if app.entry_dir:
            load_sheet_info(app, app.entry_dir.get())

        if app.entry_num:
            load_log_info(app, app.entry_num.get())
        
        app.entry_precisao.delete(0, "end")
        app.entry_precisao.insert(0, str(config.get("precisao_correspondencia", DEFAULT_CONFIG["precisao_correspondencia"])))
        app.slider_precisao.set(float(app.entry_precisao.get()))
        
        app.entry_velocidade.delete(0, "end")
        app.entry_velocidade.insert(0, str(config.get("velocidade_preenchimento", DEFAULT_CONFIG["velocidade_preenchimento"])))
        app.slider_velocidade.set(float(app.entry_velocidade.get()))
        
        app.entry_attempts.delete(0, "end")
        app.entry_attempts.insert(0, str(config.get("tentativas_por_item", DEFAULT_CONFIG["tentativas_por_item"])))
        
        use_limit = config.get("usar_limite_reinicializacoes", DEFAULT_CONFIG["usar_limite_reinicializacoes"])
        app.var_use_restarts.set(use_limit)
        
        if use_limit:
            app.entry_restarts.configure(state="normal")
            app.entry_restarts.delete(0, "end")
            app.entry_restarts.insert(0, str(config.get("reinicializacoes_maximas", DEFAULT_CONFIG["reinicializacoes_maximas"])))
        else:
            app.entry_restarts.delete(0, "end")
            app.entry_restarts.configure(state="disabled")
        
        app.var_auto_login.set(config.get("tentar_login_automaticamente", DEFAULT_CONFIG["tentar_login_automaticamente"]))
    except Exception as e:
        app.show_message(f"Erro ao aplicar configuração: {e}", "warning")
