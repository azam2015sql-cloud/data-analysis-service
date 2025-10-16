# visuals.py
import io
import base64

# Try to import heavy libs; if missing, provide safe stubs.
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns
    from wordcloud import WordCloud
    import arabic_reshaper
    from bidi.algorithm import get_display
    VISUALS_AVAILABLE = True
except Exception:
    VISUALS_AVAILABLE = False

def _png_bytes_to_b64(png_bytes):
    return base64.b64encode(png_bytes).decode("utf-8")

def create_visuals(df):
    """
    Returns a dict of visuals (name -> base64 PNG) or empty dict if visuals not available.
    """
    if not VISUALS_AVAILABLE:
        return {}

    visuals = {}
    try:
        # Histogram for the first numeric column
        import numpy as np
        num_cols = df.select_dtypes(include=[int, float]).columns.tolist()
        if num_cols:
            col = num_cols[0]
            plt.figure(figsize=(6,3))
            sns.histplot(df[col].dropna(), kde=False)
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight')
            plt.close()
            visuals['histogram'] = _png_bytes_to_b64(buf.getvalue())
    except Exception:
        pass

    return visuals
