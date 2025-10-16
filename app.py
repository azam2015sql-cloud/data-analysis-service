import io
import tempfile
import pandas as pd
from flask import Flask, request, Response, jsonify
from werkzeug.utils import secure_filename

# محاولات الاستيراد الآمنة
try:
    from analysis import analyze_data
except ImportError:
    analyze_data = None

try:
    from profiling import generate_profile
except ImportError:
    generate_profile = None

try:
    from pivots import create_pivot_tables
except ImportError:
    create_pivot_tables = None

try:
    from report import generate_pdf_report
except ImportError:
    generate_pdf_report = None

try:
    from io_handler import save_excel_report
except ImportError:
    save_excel_report = None

try:
    from visuals import create_visuals
except ImportError:
    create_visuals = None


app = Flask(__name__)

# --------------------------------------------------
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200


# --------------------------------------------------
@app.route("/analyze", methods=["POST"])
def analyze_file():
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
    # تحليل البيانات (بديل ذكي في حال غياب الدالة)
    # --------------------------------------------------
    try:
        if analyze_data:
            analysis_result = analyze_data(df)
        else:
            analysis_result = df.describe(include="all").to_dict()

        profile_summary = generate_profile(df) if generate_profile else {}
        pivots = create_pivot_tables(df) if create_pivot_tables else {}
        visuals = create_visuals(df) if create_visuals else {}
    except Exception as e:
        return jsonify({"error": f"خطأ أثناء تحليل البيانات: {str(e)}"}), 500

    # --------------------------------------------------
    # إنشاء ملفات Excel وPDF في الذاكرة
    # --------------------------------------------------
    try:
        excel_buffer = io.BytesIO()
        if save_excel_report:
            save_excel_report(df, analysis_result, pivots, excel_buffer)
        else:
            with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Data")
                pd.DataFrame(analysis_result).to_excel(writer, sheet_name="Summary")
        excel_buffer.seek(0)

        pdf_buffer = io.BytesIO()
        if generate_pdf_report:
            generate_pdf_report(df, analysis_result, pivots, visuals, pdf_buffer)
        else:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            c = canvas.Canvas(pdf_buffer, pagesize=A4)
            c.setFont("Helvetica", 12)
            c.drawString(100, 800, "📊 تقرير التحليل الآلي للبيانات")
            c.drawString(100, 770, f"عدد الصفوف: {len(df)}")
            c.drawString(100, 750, f"عدد الأعمدة: {len(df.columns)}")
            c.showPage()
            c.save()
        pdf_buffer.seek(0)
    except Exception as e:
        return jsonify({"error": f"فشل إنشاء الملفات: {str(e)}"}), 500

    # --------------------------------------------------
    # إرجاع استجابة متعددة الملفات (multipart/mixed)
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
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
