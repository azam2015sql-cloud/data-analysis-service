import io
import base64
import pandas as pd
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

# محاولات استيراد آمنة
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
    """
    يستقبل ملف (CSV/XLSX)، ينشئ تقريري PDF وExcel
    ثم يُعيدهما داخل JSON بصيغة Base64 (جاهزة لـ n8n)
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

    # تحليل البيانات
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

    # إنشاء الملفات داخل الذاكرة
    try:
        # Excel
        excel_buffer = io.BytesIO()
        if save_excel_report:
            save_excel_report(df, analysis_result, pivots, excel_buffer)
        else:
            with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Data")
                pd.DataFrame(analysis_result).to_excel(writer, sheet_name="Summary")
        excel_buffer.seek(0)

        # PDF
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

    # تحويل الملفات إلى Base64
    report_excel_b64 = base64.b64encode(excel_buffer.read()).decode("utf-8")
    report_pdf_b64 = base64.b64encode(pdf_buffer.read()).decode("utf-8")

    # إرسال الرد بصيغة JSON
    return jsonify({
        "status": "success",
        "report_excel": report_excel_b64,
        "report_pdf": report_pdf_b64
    }), 200


# --------------------------------------------------
@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "service": "Data Analysis API",
        "status": "running",
        "endpoints": ["/health", "/analyze"]
    }), 200


# --------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
