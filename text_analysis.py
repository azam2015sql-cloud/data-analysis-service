import re
from collections import Counter
from nltk.corpus import stopwords
from camel_tools.sentiment import SentimentAnalyzer

# Initialize sentiment analyzer (can be slow, initialize once)
sa = SentimentAnalyzer.pretrained()

def clean_arabic_text(text):
    """Cleans Arabic text from punctuation, numbers, and tashkeel."""
    if not isinstance(text, str):
        return ""
    # Remove tashkeel, non-Arabic letters/numbers, and punctuation
    text = re.sub(r'[^\u0600-\u06FF\s]', '', text)
    text = re.sub(r'(\w)\1{2,}', r'\1', text) # Remove elongated characters
    return text.strip()

def get_top_words(series, top_n=20):
    """Finds the most frequent words in an Arabic text series."""
    # Ensure NLTK stopwords are downloaded
    try:
        arabic_stopwords = set(stopwords.words('arabic'))
    except:
        return {"error": "NLTK stopwords for Arabic not found. Please download them."}

    cleaned_series = series.dropna().apply(clean_arabic_text)
    words = ' '.join(cleaned_series).split()
    
    filtered_words = [word for word in words if word not in arabic_stopwords and len(word) > 2]
    
    return dict(Counter(filtered_words).most_common(top_n))

def analyze_sentiment(series):
    """Analyzes sentiment for a series of Arabic texts."""
    # CAMeL Tools expects a list of strings
    sentences = series.dropna().tolist()
    if not sentences:
        return {}
        
    # Predict sentiment (positive, negative, neutral)
    sentiments = sa.predict(sentences)
    sentiment_counts = Counter(sentiments)
    
    return {
        "positive_count": sentiment_counts.get('positive', 0),
        "negative_count": sentiment_counts.get('negative', 0),
        "neutral_count": sentiment_counts.get('neutral', 0),
        "total_analyzed": len(sentences)
    }
