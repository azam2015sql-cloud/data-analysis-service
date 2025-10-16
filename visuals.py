import io
import base64
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import arabic_reshaper
from bidi.algorithm import get_display

# IMPORTANT: Place an Arabic font like 'Amiri-Regular.ttf' in a 'fonts' directory
# You can get it from Google Fonts.
ARABIC_FONT_PATH = './fonts/Amiri-Regular.ttf'

def _save_plot_to_base64():
    """Saves the current matplotlib plot to a base64 string."""
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode('utf-8')

def plot_histogram(series, title=""):
    """Generates a histogram for a numeric series."""
    plt.figure(figsize=(8, 5))
    sns.histplot(series, kde=True)
    plt.title(f'Distribution of {title}')
    plt.xlabel(title)
    plt.ylabel('Frequency')
    return _save_plot_to_base64()

def plot_correlation_heatmap(df):
    """Generates a correlation heatmap for the numeric columns of a DataFrame."""
    numeric_df = df.select_dtypes(include=['number'])
    if numeric_df.shape[1] < 2:
        return None
    plt.figure(figsize=(10, 8))
    sns.heatmap(numeric_df.corr(), annot=True, cmap='coolwarm', fmt=".2f")
    plt.title('Correlation Heatmap')
    return _save_plot_to_base64()

def generate_wordcloud(top_words):
    """Generates a word cloud from a dictionary of words and frequencies."""
    if not top_words:
        return None
    
    # Reshape text for Arabic display
    reshaped_text_dict = {get_display(arabic_reshaper.reshape(k)): v for k, v in top_words.items()}

    wc = WordCloud(
        font_path=ARABIC_FONT_PATH,
        width=800,
        height=400,
        background_color='white'
    ).generate_from_frequencies(reshaped_text_dict)
    
    plt.figure(figsize=(12, 6))
    plt.imshow(wc, interpolation='bilinear')
    plt.axis('off')
    return _save_plot_to_base64()
