import io
import base64
import pandas as pd
from fpdf import FPDF

# IMPORTANT: This path must match the one in visuals.py
ARABIC_FONT_PATH = './fonts/Amiri-Regular.ttf'

def create_excel_report(df, profile, analysis_summary, pivots, text_results):
    """Creates a multi-sheet Excel report."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Raw Data', index=False)
        
        # Summary Sheet
        summary_df = pd.DataFrame(analysis_summary).transpose()
        summary_df.to_excel(writer, sheet_name='Analysis Summary')

        # Pivot Sheets
        for name, pivot_df in pivots.items():
            pivot_df.to_excel(writer, sheet_name=name)
        
        # Text Analysis Sheet
        if text_results.get('top_words'):
            pd.DataFrame.from_dict(
                text_results['top_words'], orient='index', columns=['Frequency']
            ).to_excel(writer, sheet_name='Top Words')
            pd.DataFrame.from_dict(
                text_results['sentiment'], orient='index', columns=['Count']
            ).to_excel(writer, sheet_name='Sentiment')

    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode('utf-8')

class PDF(FPDF):
    def header(self):
        self.add_font('Amiri', '', ARABIC_FONT_PATH, uni=True)
        self.set_font('Amiri', '', 16)
        title = "تقرير تحليلي للبيانات"
        self.cell(0, 10, title, 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_pdf_report(analysis_summary, text_results):
    """Creates a summary PDF report in Arabic."""
    pdf = PDF()
    pdf.add_page()
    pdf.add_font('Amiri', '', ARABIC_FONT_PATH, uni=True)
    pdf.set_font('Amiri', '', 12)
    
    # Text results must be processed for RTL
    from bidi.algorithm import get_display
    import arabic_reshaper

    def write_rtl(text):
        reshaped_text = arabic_reshaper.reshape(text)
        bidi_text = get_display(reshaped_text)
        pdf.multi_cell(0, 10, bidi_text, 0, 'R')

    write_rtl("ملخص تحليل المشاعر:")
    sentiment = text_results.get('sentiment', {})
    if sentiment:
        write_rtl(f"إيجابي: {sentiment.get('positive_count', 0)}")
        write_rtl(f"سلبي: {sentiment.get('negative_count', 0)}")
        write_rtl(f"محايد: {sentiment.get('neutral_count', 0)}")
    
    pdf.ln(10)
    write_rtl("أكثر الكلمات تكرارًا:")
    top_words = text_results.get('top_words', {})
    if top_words:
        for word, count in list(top_words.items())[:10]:
            write_rtl(f"{word}: {count}")

    buf = io.BytesIO()
    pdf.output(buf)
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode('utf-8')
