import threading

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
