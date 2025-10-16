import pandas as pd
import re
from collections import Counter
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

# تحميل نموذج التحليل العاطفي العربي من Hugging Face
MODEL_NAME = "CAMeL-Lab/bert-base-arabic-camelbert-mix-sentiment"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
sentiment_pipeline = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)

# ------------------------
# 🔠 تحليل النصوص العامة
# ------------------------

def clean_text(text):
    """تنظيف النص من الرموز والعلامات."""
    if not isinstance(text, str):
        return ""
    text = re.sub(r"http\S+", "", text)  # إزالة الروابط
    text = re.sub(r"[^ء-يa-zA-Z\s]", " ", text)  # الإبقاء على الحروف فقط
    text = re.sub(r"\s+", " ", text).strip()
    return text

def get_top_words(series, top_n=20):
    """استخراج أكثر الكلمات تكرارًا في العمود النصي."""
    words = []
    for text in series.dropna().astype(str):
        text = clean_text(text)
        words.extend(text.split())
    counter = Counter(words)
    return dict(counter.most_common(top_n))

# ------------------------
# 😊 تحليل المشاعر
# ------------------------

def analyze_sentiment(series):
    """تحليل المشاعر للنصوص العربية باستخدام نموذج CAMeL-Lab."""
    texts = series.dropna().astype(str).tolist()
    if not texts:
        return {"positive": 0, "negative": 0, "neutral": 0}
    
    results = sentiment_pipeline(texts, truncation=True)
    
    pos, neg, neu = 0, 0, 0
    for r in results:
        label = r["label"].lower()
        if "pos" in label:
            pos += 1
        elif "neg" in label:
            neg += 1
        else:
            neu += 1

    total = pos + neg + neu
    return {
        "positive": pos,
        "negative": neg,
        "neutral": neu,
        "positive_ratio": round(pos / total, 3) if total else 0,
        "negative_ratio": round(neg / total, 3) if total else 0,
        "neutral_ratio": round(neu / total, 3) if total else 0,
    }
