# analysis.py (optimized and non-blocking)
from flask import Flask, request, jsonify, abort
import pandas as pd
import io, base64, os, tempfile, logging
from fpdf import FPDF

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# ✅ قراءة المفتاح من متغير البيئة (افتراضيًا "s3cr3t")
API_KEY = os.environ.get("ANALYSIS_API_KEY", "s3cr3t")

def require_api_key(req):
    """تحقق من صحة مفتاح API من جميع الاحتمالات الممكنة"""
    key = (
        req.headers.get("x-api-key")
        or req.headers.get("X-Api-Key")
        or req.headers.get("ANALYSIS_API_KEY")
        or req.headers.get("analysis_api_key")
        or req.args.get("api_key")
    )
    if not key or key != API_KEY:
        abort(401, description="Unauthorized: Invalid or missing API key")

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

@app.route("/analyze", methods=["POST"])
def analyze():
    # ✅ التحقق من المفتاح قبل أي شيء
    require_api_key(request)

    if "file" not in request.files:
        return jsonify({"error": "missing file"}), 400

    f = request.files["file"]
    action = request.form.get("action", "full_report").strip().lower()
    name = (f.filename or "").lower()

    try:
        if name.endswith(".csv"):
            df = pd.read_csv(f)
        elif name.endswith(".xlsx") or name.endswith(".xls"):
            df = pd.read_excel(f)
        else:
            return jsonify({"error": "unsupported file format"}), 400
    except Exception as e:
        return jsonify({"error": f"cannot read file: {e}"}), 400

    if action == "full_report":
        desc = df.describe(include="all").transpose()
        missing = (df.isnull().sum() / max(len(df), 1)).to_dict()

        # ===== إنشاء تقرير PDF =====
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

        # ===== إنشاء Excel في الذاكرة =====
        excel_buf = io.BytesIO()
        with pd.ExcelWriter(excel_buf, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Raw Data")
            desc.to_excel(writer, sheet_name="Stats")
        excel_buf.seek(0)

        # ===== إرجاع النتائج Base64 =====
        return jsonify({
            "report_pdf": base64.b64encode(pdf_bytes).decode(),
            "report_excel": base64.b64encode(excel_buf.getvalue()).decode()
        })

    # في حالة لم يُعرف نوع الإجراء
    return jsonify({"error": "unknown action"}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
