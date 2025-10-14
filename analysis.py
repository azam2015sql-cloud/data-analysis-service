# analysis.py (universal version, stable for Render)
from flask import Flask, request, jsonify, abort
import pandas as pd
import io, os, json, tempfile, logging, base64
from fpdf import FPDF

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# 🔐 مفتاح API من Render Environment Variable
API_KEY = os.environ.get("ANALYSIS_API_KEY", "s3cr3t")

def require_api_key(req):
    key = req.headers.get("x-api-key") or req.args.get("api_key")
    if not key or key != API_KEY:
        abort(401, description="Unauthorized - invalid or missing API key")

@app.route("/")
def home():
    return jsonify({"status": "running", "message": "Analyzer API is live ✅"})

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

@app.route("/analyze", methods=["POST"])
def analyze():
    require_api_key(request)

    # تحقق من وجود ملف
    if "file" not in request.files:
        return jsonify({"error": "Missing file"}), 400

    file = request.files["file"]
    action = request.form.get("action", "full_report").strip().lower()
    filename = (file.filename or "uploaded_file").lower()

    # 🧠 قراءة أنواع الملفات المختلفة
    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(file, encoding="utf-8", on_bad_lines="skip")
        elif filename.endswith(".xlsx") or filename.endswith(".xls"):
            df = pd.read_excel(file)
        elif filename.endswith(".json"):
            data = json.load(file)
            df = pd.json_normalize(data)
        elif filename.endswith(".txt"):
            content = file.read().decode("utf-8", errors="ignore")
            df = pd.DataFrame({"text": content.splitlines()})
        else:
            # محاولة تلقائية عبر pandas
            df = pd.read_csv(file, encoding="utf-8", on_bad_lines="skip")
    except Exception as e:
        return jsonify({"error": f"Cannot read file: {e}"}), 400

    # ✅ التحليل
    try:
        desc = df.describe(include="all").transpose()
        missing = (df.isnull().sum() / max(len(df), 1)).to_dict()
    except Exception as e:
        desc = pd.DataFrame()
        missing = {}
        logging.warning(f"Data analysis warning: {e}")

    # === إنشاء PDF مؤقت في /tmp ===
    pdf_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", dir="/tmp")
    pdf_path = pdf_file.name
    pdf_file.close()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "Universal Data Analysis Report", ln=True)
    pdf.set_font("helvetica", "", 11)
    pdf.multi_cell(0, 8, f"Rows: {len(df)} | Columns: {df.shape[1]}")
    pdf.multi_cell(0, 8, f"Missing ratios: {json.dumps(missing, indent=2)}")
    pdf.output(pdf_path)

    with open(pdf_path, "rb") as p:
        pdf_bytes = p.read()
    os.remove(pdf_path)

    # === إنشاء Excel في الذاكرة ===
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Raw Data")
        desc.to_excel(writer, sheet_name="Stats")
    excel_buffer.seek(0)

    return jsonify({
        "report_pdf": base64.b64encode(pdf_bytes).decode(),
        "report_excel": base64.b64encode(excel_buffer.getvalue()).decode(),
        "summary": {
            "rows": len(df),
            "columns": list(df.columns),
            "missing_ratios": missing
        }
    })

@app.errorhandler(500)
def handle_500(e):
    logging.exception("Internal server error: %s", e)
    return jsonify({"error": "Internal server error", "details": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
