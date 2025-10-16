import pandas as pd

def generate_smart_pivots(df, profile, max_pivots=5):
    """
    Generates smart pivot tables based on column profiles.
    Prioritizes categorical/datetime dimensions against numeric values.
    """
    pivots = {}
    numeric_cols = [k for k, v in profile.items() if v == 'numeric']
    cat_cols = [k for k, v in profile.items() if v == 'categorical' or v == 'datetime']

    if not numeric_cols or not cat_cols:
        return pivots

    count = 0
    for dim_col in cat_cols:
        # Avoid creating pivots for high-cardinality dimensions
        if df[dim_col].nunique() > 50:
            continue
            
        for val_col in numeric_cols:
            if count >= max_pivots:
                break
            try:
                pivot_df = pd.pivot_table(
                    df, 
                    index=dim_col, 
                    values=val_col, 
                    aggfunc='sum' # or 'mean'
                ).round(2)
                
                # Truncate long sheet names
                sheet_name = f'Pivot_{dim_col[:10]}_vs_{val_col[:10]}'
                pivots[sheet_name] = pivot_df
                count += 1
            except Exception:
                continue # Skip if pivot fails
        if count >= max_pivots:
            break
            
    return pivots
