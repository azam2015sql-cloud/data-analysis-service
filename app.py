# app.py
import os
import io
import base64
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

# محليات المشروع (آمنة: استدعاء في try-except داخل هذه الوحدة)
from io_handler import read_data

# دوال التقرير (مستعملة داخل المشروع)
from report import create_excel_report, create_pdf_report

# محاولات لاستدعاء وحدات غير ضرورية (stubs handled in their modules)
try:
    from profiling import profile_dataframe
except Exception:
    def profile_dataframe(df): return {}

try:
    from pivots import generate_smart_pivots
except Exception:
    def generate_smart_pivots(df): return {}

try:
    from visuals import create_visuals
except Exception:
    def create_visuals(df): return {}

# النصي: نُوقِف الاعتماد على تحليل المشاعر الثقيل:
# text_analysis.py موجود كـ stub يعيد نتائج فارغة

app = Flask(__name__)

API_KEY = os.environ.get("ANALYSIS_API_KEY", "change_this_to_a_strong_key")

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200

@app.route("/analyze", methods=["POST"])
def analyze_file():
    """
    Accepts multipart/form-data with file field name 'file'.
    Returns JSON:
      {
        "status":"success",
        "report_excel": "<base64>",
        "report_pdf": "<base64>"
      }
    """
    # Security: optional API key header
    expected_key = os.environ.get("ANALYSIS_API_KEY")
    header_key = request.headers.get("x-api-key")
    if expected_key:
        if header_key != expected_key:
            return jsonify({"error": "Unauthorized"}), 401

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded. Field 'file' is required."}), 400

    uploaded_file = request.files["file"]
    if uploaded_file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    filename = secure_filename(uploaded_file.filename)
    try:
        # read_data will raise on unsupported formats
        df = read_data(uploaded_file)
    except Exception as e:
        return jsonify({"error": f"Failed reading file: {str(e)}"}), 400

    try:
        # lightweight analysis pipeline
        profile = profile_dataframe(df)
        pivots = generate_smart_pivots(df)
        visuals = create_visuals(df)

        # Create Excel and PDF in-memory
        excel_bytes = create_excel_report(df, profile, pivots)
        pdf_bytes = create_pdf_report(df, profile, pivots, visuals)

        # encode to base64 for JSON transport to n8n
        excel_b64 = base64.b64encode(excel_bytes).decode("utf-8")
        pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")

        return jsonify({
            "status": "success",
            "report_excel": excel_b64,
            "report_pdf": pdf_b64
        }), 200

    except Exception as e:
        # Return error + traceback for debugging (optional)
        import traceback as _tb
        return jsonify({"error": str(e), "trace": _tb.format_exc()}), 500


if __name__ == "__main__":
    # Bind to PORT provided by Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
