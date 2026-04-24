import pandas as pd
import threading
from pathlib import Path

def load_sheet_info(app, path: str):
    """Load sheet row counts in background thread."""
    def thread():
        try:
            df = pd.read_excel(path)
            total = len(df)
            app.after(0, lambda: update_sheet_info(app, total))
        except Exception as e:
            app.after(0, lambda: update_error(app, str(e)))

    app.loading_spinner.start()
    threading.Thread(target=thread, daemon=True).start()

def load_log_info(app, instrumento: str):
    """Load filled/inits/errors from the log file for this instrumento."""
    def thread():
        try:
            log_path = Path("Logs") / f"relatorio_execucao-{instrumento}.xlsx"
            
            if not log_path.exists():
                app.after(0, lambda: _update_log_info(app, 0, 0, 0))
                return
            
            df = pd.read_excel(log_path)
            
            filled    = len(df[df["Status"] == "OK"])
            errors    = len(df[df["Status"].isin(["ERRO", "SKIPPED"])])
            inits     = int(df["Inicializacoes"].iloc[-1]) if "Inicializacoes" in df.columns else 0
            
            app.after(0, lambda: _update_log_info(app, filled, inits, errors))
        except Exception as e:
            app.after(0, lambda: app.show_message(f"Erro ao carregar log: {e}", "warning"))

    threading.Thread(target=thread, daemon=True).start()

def update_sheet_info(app, total):
    app.var_total.set(str(total))
    app.loading_spinner.stop()

def _update_log_info(app, filled, inits, errors):
    app.var_filled.set(str(filled))
    app.var_remaining.set(str(int(app.var_total.get() or 0) - filled))
    app.var_inits.set(str(inits))
    app.var_errors.set(str(errors))

def update_error(app, msg):
    app.var_total.set("Erro")
    app.show_message(f"Erro ao carregar planilha: {msg}", "error")
    app.loading_spinner.stop()

def load_sheets():
    sheets_dir = Path("Sheets")
    if not sheets_dir.exists():
        return []
    return [f for f in sheets_dir.iterdir() if f.suffix in (".xlsx", ".xls")]