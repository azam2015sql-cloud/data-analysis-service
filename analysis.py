import pandas as pd
from sklearn.preprocessing import StandardScaler

def analyze_numeric(series):
    """Analyzes a numeric series for descriptive stats and outliers."""
    desc = series.describe()
    
    # Outlier detection using IQR
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    outliers = series[(series < (Q1 - 1.5 * IQR)) | (series > (Q3 + 1.5 * IQR))]
    
    return {
        "stats": desc.to_dict(),
        "outliers_count": len(outliers),
        "missing_ratio": series.isnull().sum() / len(series) if len(series) > 0 else 0
    }

def analyze_datetime(series):
    """Analyzes a datetime series for trends."""
    series = pd.to_datetime(series)
    return {
        "range_start": str(series.min()),
        "range_end": str(series.max()),
        "missing_ratio": series.isnull().sum() / len(series) if len(series) > 0 else 0
    }

def analyze_categorical(series):
    """Analyzes a categorical series for frequency distribution."""
    counts = series.value_counts()
    percentages = series.value_counts(normalize=True)
    
    # Pareto analysis (Top 80% contributors)
    pareto = percentages.cumsum()
    pareto_threshold = pareto[pareto <= 0.8].index.tolist()
    
    return {
        "top_5_counts": counts.head(5).to_dict(),
        "top_5_percentages": percentages.head(5).to_dict(),
        "pareto_categories": pareto_threshold,
        "unique_values": series.nunique()
    }
