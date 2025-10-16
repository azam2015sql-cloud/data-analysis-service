import os
from flask import Flask, request, jsonify, abort

# Import our custom modules
from io_handler import read_data
from profiling import profile_dataframe
from analysis import analyze_numeric, analyze_datetime, analyze_categorical
from text_analysis import get_top_words, analyze_sentiment
from visuals import plot_histogram, plot_correlation_heatmap, generate_wordcloud
from pivots import generate_smart_pivots
from report import create_excel_report, create_pdf_report

app = Flask(__name__)

# Security: Use environment variables on Render
API_KEY = os.environ.get("ANALYSIS_API_KEY", "change_this_to_a_strong_key")

def require_api_key(req):
    key = req.headers.get("x-api-key")
    if not key or key != API_KEY:
        abort(401, description="Unauthorized: Missing or invalid API Key.")

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/analyze", methods=["POST"])
def analyze_endpoint():
    require_api_key(request)
    
    if 'file' not in request.files:
        return jsonify({"error": "Missing 'file' field"}), 400

    file = request.files['file']
    try:
        df = read_data(file)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    # Main analysis pipeline
    try:
        # 1. Profiling
        profile = profile_dataframe(df)
        
        # 2. Analysis per column
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

        # 3. Text Analysis (on the first text column found)
        text_results = {}
        if text_columns:
            text_series = df[text_columns[0]]
            top_words = get_top_words(text_series)
            sentiment = analyze_sentiment(text_series)
            text_results = {"top_words": top_words, "sentiment": sentiment}

        # 4. Visualizations
        visuals = {}
        numeric_cols = [k for k, v in profile.items() if v == 'numeric']
        if numeric_cols:
            visuals['histogram_first_numeric'] = plot_histogram(df[numeric_cols[0]], title=numeric_cols[0])
            visuals['correlation_heatmap'] = plot_correlation_heatmap(df)
        if text_results.get('top_words'):
            visuals['wordcloud'] = generate_wordcloud(text_results['top_words'])
            
        # 5. Pivot Tables
        pivots = generate_smart_pivots(df, profile)

        # 6. Reporting
        final_reports = {
            'excel_report_b64': create_excel_report(df, profile, analysis_summary, pivots, text_results),
            'pdf_report_b64': create_pdf_report(analysis_summary, text_results)
        }

        # 7. Construct final response
        return jsonify({
            "status": "success",
            "profile": profile,
            "reports": final_reports,
            "visuals_b64": visuals
        })

    except Exception as e:
        # Log the full error for debugging
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An internal error occurred during analysis."}), 500

if __name__ == "__main__":
    # Ensure fonts directory exists
    if not os.path.exists('fonts'):
        os.makedirs('fonts')
        print("Created 'fonts' directory. Please add an Arabic TTF font (e.g., Amiri-Regular.ttf) there.")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
