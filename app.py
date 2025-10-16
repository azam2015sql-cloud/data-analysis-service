import io
import tempfile
import pandas as pd
from flask import Flask, request, Response, jsonify
from werkzeug.utils import secure_filename
from analysis import analyze_data
from profiling import generate_profile
from pivots import create_pivot_tables
from report import generate_pdf_report
from io_handler import save_excel_report
from visuals import create_visuals

app = Flask(__name__)

# --------------------------------------------------
# 1. Health Check Endpoint
# --------------------------------------------------
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200


# --------------------------------------------------
# 2. Main Analysis Endpoint
# --------------------------------------------------
@app.route("/analyze", methods=["POST"])
def analyze_file():
    """
    يستقبل ملف Excel أو CSV، يعالجه، وينشئ تقريري PDF وExcel
    ثم يُرجعهما مباشرة داخل استجابة multipart/mixed متوافقة مع n8n.
    """
    if "file" not in request.files:
        return jsonify({"error": "الملف مفقود (form field 'file' مطلوب)"}), 400

    uploaded_file = request.files["file"]
    if uploaded_file.filename == "":
        return jsonify({"error": "اسم الملف فارغ"}), 400

    filename = secure_filename(uploaded_file.filename)
    ext = filename.split(".")[-1].lower()

    # تحميل الملف إلى DataFrame
    try:
        if ext == "csv":
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
    except Exception as e:
        return jsonify({"error": f"فشل في قراءة الملف: {str(e)}"}), 400

    # --------------------------------------------------
    # تحليل البيانات باستخدام الوحدات المساعدة
    # --------------------------------------------------
    try:
        analysis_result = analyze_data(df)
        profile_summary = generate_profile(df)
        pivots = create_pivot_tables(df)
        visuals = create_visuals(df)
    except Exception as e:
        return jsonify({"error": f"حدث خطأ أثناء تحليل البيانات: {str(e)}"}), 500

    # --------------------------------------------------
    # إنشاء التقارير PDF و Excel داخل الذاكرة
    # --------------------------------------------------
    try:
        # إنشاء ملف Excel داخل ذاكرة
        excel_buffer = io.BytesIO()
        save_excel_report(df, analysis_result, pivots, excel_buffer)
        excel_buffer.seek(0)

        # إنشاء تقرير PDF داخل ذاكرة مؤقتة
        pdf_buffer = io.BytesIO()
        generate_pdf_report(df, analysis_result, pivots, visuals, pdf_buffer)
        pdf_buffer.seek(0)
    except Exception as e:
        return jsonify({"error": f"فشل إنشاء الملفات: {str(e)}"}), 500

    # --------------------------------------------------
    # إعداد استجابة متعددة الملفات (multipart/mixed)
    # --------------------------------------------------
    boundary = "----DataBoundary"
    multipart_body = io.BytesIO()

    def add_part(file_bytes, filename, mime_type):
        multipart_body.write(f"--{boundary}\r\n".encode())
        multipart_body.write(
            f'Content-Disposition: form-data; name="{filename}"; filename="{filename}"\r\n'.encode()
        )
        multipart_body.write(f"Content-Type: {mime_type}\r\n\r\n".encode())
        multipart_body.write(file_bytes)
        multipart_body.write(b"\r\n")

    add_part(excel_buffer.read(), "report.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    add_part(pdf_buffer.read(), "report.pdf", "application/pdf")
    multipart_body.write(f"--{boundary}--\r\n".encode())
    multipart_body.seek(0)

    response = Response(
        multipart_body.read(),
        status=200,
        mimetype=f"multipart/mixed; boundary={boundary}"
    )
    return response


# --------------------------------------------------
# 3. Run locally (for debugging)
# --------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
