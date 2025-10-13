# analysis.py
from flask import Flask, request, jsonify, abort
import pandas as pd
import io, base64, os, tempfile, logging
from fpdf import FPDF

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# ✅ قراءة مفتاح API من متغير البيئة
API_KEY = os.environ.get("ANALYSIS_API_KEY", "s3cr3t")


# ==================== حماية الوصول ====================
def require_api_key(req):
    key = req.headers.get("x-api-key") or req.args.get("api_key")
    if not key or key != API_KEY:
        abort(401, description="Unauthorized")


# ==================== اختبار الصحة ====================
@app.route("/health")
def health():
    return jsonify({"status": "ok"})


# ✅ إضافة endpoint رئيسي حتى لا يفشل Render في النشر
@app.route("/")
def index():
    return jsonify({
        "status": "running",
        "message": "Analysis API active and ready."
    })


# ==================== التحليل الرئيسي ====================
@app.route("/analyze", methods=["POST"])
def analyze():
    require_api_key(request)

    # التأكد من وجود ملف
    if "file" not in request.files:
        return jsonify({"error": "missing file"}), 400

    f = request.files["file"]
    action = (request.form.get("action") or "full_report").strip().lower()
    name = (f.filename or "").lower()

    # قراءة الملف
    try:
        if name.endswith(".csv"):
            df = pd.read_csv(f)
        elif name.endswith(".xlsx") or name.endswith(".xls"):
            df = pd.read_excel(f)
        else:
            return jsonify({"error": "unsupported file format"}), 400
    except Exception as e:
        return jsonify({"error": f"cannot read file: {e}"}), 400

    # تنفيذ التقرير الكامل
    if action == "full_report":
        desc = df.describe(include="all").transpose()
        missing = (df.isnull().sum() / max(len(df), 1)).to_dict()

        # ===== إنشاء PDF مؤقت =====
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            pdf_path = tmp.name

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(0, 10, "Data Analysis Report", ln=True)
        pdf.set_font("helvetica", "", 11)
        pdf.multi_cell(0, 8, f"Rows: {len(df)} | Columns: {df.shape[1]}")
        pdf.multi_cell(0, 8, f"Missing ratios: {missing}")
        pdf.output(pdf_path)

        with open(pdf_path, "rb") as p:
            pdf_bytes = p.read()
        os.remove(pdf_path)

        # ===== إنشاء Excel داخل الذاكرة =====
        excel_buf = io.BytesIO()
        with pd.ExcelWriter(excel_buf, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Raw Data")
            desc.to_excel(writer, sheet_name="Stats")
        excel_buf.seek(0)

        return jsonify({
            "report_pdf": base64.b64encode(pdf_bytes).decode(),
            "report_excel": base64.b64encode(excel_buf.getvalue()).decode()
        })

    # في حال لم يكن هناك action معروف
    return jsonify({"error": "unknown action"}), 400


# ==================== نقطة التشغيل ====================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
