# analysis.py
from flask import Flask, request, jsonify, abort
import pandas as pd
import io, base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from fpdf import FPDF
import os

app = Flask(__name__)

# SECURITY: ضع مفتاح API هنا أو في ENVIRONMENT variable على Render
API_KEY = os.environ.get("ANALYSIS_API_KEY", "change_this_to_a_strong_key")

def require_api_key(req):
    key = req.headers.get("x-api-key") or req.args.get("api_key")
    if not key or key != API_KEY:
        abort(401, description="Unauthorized")

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status":"ok"})

@app.route("/analyze", methods=["POST"])
def analyze():
    require_api_key(request)
    if 'file' not in request.files:
        return jsonify({"error":"missing file field"}), 400

    file = request.files['file']
    action = request.form.get('action', 'descriptive')
    filename = (file.filename or "").lower()

    # read file
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif filename.endswith('.xls') or filename.endswith('.xlsx'):
            df = pd.read_excel(file)
        else:
            return jsonify({'error':'unsupported file format'}), 400
    except Exception as e:
        return jsonify({'error': f'cannot read file: {str(e)}'}), 400

    try:
        if action == 'descriptive':
            desc = df.describe(include='all').transpose().to_dict()
            return jsonify({"descriptive": desc})

        if action == 'kpi':
            # sample KPIs: top5 each categorical column, missing ratios, simple growth if Month/Sales exist
            top5 = {}
            for col in df.select_dtypes(include=['object','category']).columns:
                try:
                    top5[col] = df[col].value_counts().head(5).to_dict()
                except:
                    top5[col] = {}
            missing_ratio = (df.isnull().sum() / max(len(df),1)).to_dict()
            growth_rate = None
            if 'Month' in df.columns and 'Sales' in df.columns:
                try:
                    growth_rate = float(df.groupby('Month')['Sales'].sum().pct_change().mean())
                except:
                    growth_rate = None
            return jsonify({"top5": top5, "missing_ratio": missing_ratio, "avg_growth_rate": growth_rate})

        if action == 'charts':
            # create charts for first numeric column (as example)
            nums = df.select_dtypes(include=['number']).columns.tolist()
            if not nums:
                return jsonify({"error":"no numeric columns for chart"}), 400
            col = nums[0]
            buf = io.BytesIO()
            plt.figure(figsize=(6,4))
            df[col].hist(bins=30)
            plt.title(col)
            plt.tight_layout()
            plt.savefig(buf, format='png')
            plt.close()
            buf.seek(0)
            img_b64 = base64.b64encode(buf.getvalue()).decode()
            return jsonify({"chart_base64": img_b64, "chart_for_column": col})

        if action == 'full_report':
            # descriptive
            desc = df.describe(include='all').transpose()
            missing_ratio = (df.isnull().sum() / max(len(df),1)).to_dict()

            # create PDF
            pdf_buf = io.BytesIO()
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, "تقرير تحليلي للبيانات", ln=True)
            pdf.set_font("Arial", '', 12)
            pdf.multi_cell(0, 8, f"عدد السجلات: {len(df)} | الأعمدة: {df.shape[1]}")
            pdf.ln(2)
            pdf.multi_cell(0, 8, "نسبة القيم المفقودة لكل عمود:")
            pdf.multi_cell(0, 8, str(missing_ratio))
            pdf.output(pdf_buf)
            pdf_buf.seek(0)

            # create Excel in-memory
            excel_buf = io.BytesIO()
            with pd.ExcelWriter(excel_buf, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Raw Data', index=False)
                desc.to_excel(writer, sheet_name='Descriptive Stats')
            excel_buf.seek(0)

            return jsonify({
                "report_pdf": base64.b64encode(pdf_buf.getvalue()).decode(),
                "report_excel": base64.b64encode(excel_buf.getvalue()).decode()
            })

        return jsonify({"error":"unknown action"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
