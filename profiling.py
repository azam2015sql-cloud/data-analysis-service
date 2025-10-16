import pandas as pd

def profile_dataframe(df):
    """
    Profiles a DataFrame to identify column types: 
    numeric, datetime, categorical, or text.
    """
    profile = {}
    for col in df.columns:
        dtype = df[col].dtype
        unique_ratio = df[col].nunique() / len(df) if len(df) > 0 else 0

        # Attempt to convert to datetime
        try:
            pd.to_datetime(df[col], errors='raise')
            profile[col] = 'datetime'
            continue
        except (ValueError, TypeError):
            pass

        if pd.api.types.is_numeric_dtype(dtype):
            profile[col] = 'numeric'
        elif pd.api.types.is_object_dtype(dtype):
            # Heuristic for categorical vs. text
            if unique_ratio < 0.5 and df[col].nunique() < 100:
                profile[col] = 'categorical'
            else:
                profile[col] = 'text'
        else:
            profile[col] = 'other'
            
    return profile
