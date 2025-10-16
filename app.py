import os
import matplotlib
matplotlib.use("Agg")  # استخدام backend خفيف لتجنب استهلاك الذاكرة في Render

from flask import Flask, request, jsonify, abort

# استيراد الوحدات المساعدة
from io_handler import read_data
from profiling import profile_dataframe
from analysis import analyze_numeric, analyze_datetime, analyze_categorical
from text_analysis import get_top_words  # بدون تحليل مشاعر
from visuals import plot_histogram, plot_correlation_heatmap, generate_wordcloud
from pivots import generate_smart_pivots
from report import create_excel_report, create_pdf_report

app = Flask(__name__)

# 🔐 مفتاح API للأمان
API_KEY = os.environ.get("ANALYSIS_API_KEY", "change_this_to_a_strong_key")


def require_api_key(req):
    """التحقق من مفتاح API."""
    key = req.headers.get("x-api-key")
    if not key or key != API_KEY:
        abort(401, description="Unauthorized: Missing or invalid API Key.")


@app.route("/health", methods=["GET"])
def health():
    """فحص صحة الخدمة."""
    return jsonify({"status": "ok"})


@app.route("/analyze", methods=["POST"])
def analyze_endpoint():
    """نقطة تحليل البيانات الرئيسية."""
    require_api_key(request)

    # التحقق من وجود ملف
    if 'file' not in request.files:
        return jsonify({"error": "Missing 'file' field"}), 400

    file = request.files['file']
    try:
        df = read_data(file)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    try:
        # 1️⃣ تحليل مبدئي لتحديد أنواع الأعمدة
        profile = profile_dataframe(df)

        # 2️⃣ تحليل الأعمدة حسب نوعها
        analysis_summary = {}
        text_columns = []
        for col, col_type in profile.items():
            if col_type == 'numeric':
                analysis_summary[col] = analyze_numeric(df[col])
            elif col_type == 'datetime':
                analysis_summary[col] = analyze_datetime(df[col])
            elif col_type == 'categorical':
                analysis_summary[col] = analyze_categorical(df[col])
            elif col_type == 'text':
                text_columns.append(col)

        # 3️⃣ تحليل نصي (الكلمات الأكثر تكرارًا فقط)
        text_results = {}
        if text_columns:
            text_series = df[text_columns[0]]
            top_words = get_top_words(text_series)
            text_results = {"top_words": top_words}
        else:
            text_results = {}

        # 4️⃣ توليد الرسوم البيانية
        visuals = {}
        numeric_cols = [k for k, v in profile.items() if v == 'numeric']
        if numeric_cols:
            visuals['histogram_first_numeric'] = plot_histogram(
                df[numeric_cols[0]], title=numeric_cols[0]
            )
            visuals['correlation_heatmap'] = plot_correlation_heatmap(df)

        if text_results.get('top_words'):
            visuals['wordcloud'] = generate_wordcloud(text_results['top_words'])

        # 5️⃣ توليد الجداول المحورية
        pivots = generate_smart_pivots(df, profile)

        # 6️⃣ إنشاء التقارير النهائية
        final_reports = {
            'excel_report_b64': create_excel_report(
                df, profile, analysis_summary, pivots, text_results
            ),
            'pdf_report_b64': create_pdf_report(analysis_summary, text_results),
        }

        # 7️⃣ إعادة النتيجة
        return jsonify({
            "status": "success",
            "profile": profile,
            "analysis_summary": analysis_summary,
            "visuals_b64": visuals,
            "reports": final_reports
        })

    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return jsonify({"error": "An internal error occurred during analysis."}), 500


if __name__ == "__main__":
    # التأكد من وجود مجلد الخطوط
    if not os.path.exists('fonts'):
        os.makedirs('fonts')
        print("⚠️ Created 'fonts' directory. Please add Amiri-Regular.ttf font.")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
