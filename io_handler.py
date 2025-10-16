# io_handler.py
import pandas as pd

def read_data(file_storage):
    filename = (file_storage.filename or "").lower()
    if filename.endswith(".csv"):
        return pd.read_csv(file_storage)
    elif filename.endswith(".xls") or filename.endswith(".xlsx"):
        return pd.read_excel(file_storage)
    else:
        # Try reading as excel as a fallback
        try:
            return pd.read_excel(file_storage)
        except Exception:
            raise ValueError("Unsupported file type. Use CSV or XLSX.")
