import threading

def load_sheet_info(app, path: str):
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
            app.after(0, lambda: app._update_sheet_info(total, filled, remaining))
        except Exception as e:
            app.after(0, lambda: app._update_sheet_info_error(str(e)))
    
    # Show loading spinner and start thread
    app.loading_spinner.start()
    thread = threading.Thread(target=load_thread, daemon=True)
    thread.start()

def update_sheet_info(app, total, filled, remaining):
    """Update UI with loaded sheet info."""
    app.var_total.set(str(total))
    app.var_filled.set(str(filled))
    app.var_remaining.set(str(remaining))
    app.var_inits.set("0")
    app.var_errors.set("0")
    app.loading_spinner.stop()

def update_sheet_info_error(app, error_msg):
    """Update UI when sheet loading fails."""
    app.var_total.set("Erro")
    app.var_filled.set("—")
    app.var_remaining.set("—")
    app.show_message(f"Erro ao carregar planilha: {error_msg}", "error")
    app.loading_spinner.stop()
