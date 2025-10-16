import pandas as pd
import io

def read_data(file_storage):
    """
    Reads a file storage object (CSV or Excel) into a pandas DataFrame.
    """
    filename = (file_storage.filename or "").lower()
    try:
        if filename.endswith('.csv'):
            return pd.read_csv(file_storage)
        elif filename.endswith('.xls') or filename.endswith('.xlsx'):
            return pd.read_excel(file_storage)
        else:
            raise ValueError("Unsupported file format. Please use CSV or XLSX.")
    except Exception as e:
        raise ValueError(f"Could not read the file: {str(e)}")
