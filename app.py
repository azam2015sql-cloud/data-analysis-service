from flask import Flask, request, jsonify
from io_handler import read_data
from report import create_excel_report, create_pdf_report
import base64
import traceback
import tempfile
import os

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "<h3>✅ API is running</h3>", 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        # التحقق من وجود الملف
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        uploaded_file = request.files['file']
        df = read_data(uploaded_file)
        if df is None or df.empty:
            return jsonify({"error": "Invalid or empty file"}), 400

        # إنشاء تقارير مؤقتة
        with tempfile.TemporaryDirectory() as tmpdir:
            excel_path = os.path.join(tmpdir, "report.xlsx")
            pdf_path = os.path.join(tmpdir, "report.pdf")

            # توليد الملفات
            create_excel_report
            create_pdf_report


            # تحويل الملفات إلى base64
            with open(excel_path, "rb") as f:
                excel_b64 = base64.b64encode(f.read()).decode('utf-8')
            with open(pdf_path, "rb") as f:
                pdf_b64 = base64.b64encode(f.read()).decode('utf-8')

        # إرجاع الرد بشكل نظيف وواضح
        response = jsonify({
            "success": True,
            "report_excel": excel_b64,
            "report_pdf": pdf_b64
        })
        response.status_code = 200
        response.headers["Connection"] = "close"
        return response

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "trace": traceback.format_exc()
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False, threaded=True)
