import re
from collections import Counter

def clean_text(text):
    """تنظيف النص من الرموز والعلامات."""
    if not isinstance(text, str):
        return ""
    text = re.sub(r"http\S+", "", text)  # إزالة الروابط
    text = re.sub(r"[^ء-يa-zA-Z\s]", " ", text)  # إبقاء الحروف فقط
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
