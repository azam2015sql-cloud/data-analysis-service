# report.py
import io
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def create_excel_report(df: pd.DataFrame, profile: dict, pivots: dict) -> bytes:
    """
    Return bytes of an Excel file (xlsx) created in-memory.
    """
    buf = io.BytesIO()
    # use openpyxl/xlsxwriter (pandas will choose engine)
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Data")
        # Summary sheet: simple transpose of profile (if exists)
        if profile:
            try:
                summary_df = pd.DataFrame(profile)
                summary_df.to_excel(writer, sheet_name="Profile")
            except Exception:
                # fallback: minimal info
                pd.DataFrame({"note": ["profile generation failed"]}).to_excel(writer, sheet_name="Profile")
        else:
            pd.DataFrame({"note": ["no profile generated"]}).to_excel(writer, sheet_name="Profile")
        # Pivots sheet
        if pivots:
            try:
                # pivots expected as dict of name -> DataFrame
                for name, table in pivots.items():
                    try:
                        if isinstance(table, pd.DataFrame):
                            table.to_excel(writer, sheet_name=str(name)[:31])
                        else:
                            pd.DataFrame({'value': [str(table)]}).to_excel(writer, sheet_name=str(name)[:31])
                    except Exception:
                        pass
            except Exception:
                pass
    buf.seek(0)
    return buf.read()

def create_pdf_report(df: pd.DataFrame, profile: dict, pivots: dict, visuals: dict) -> bytes:
    """
    Return bytes of a simple PDF report created with reportlab.
    visuals: dict of name -> PNG base64 or raw bytes (optional)
    """
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, height - 50, "Data Analysis Report")
    c.setFont("Helvetica", 10)
    c.drawString(40, height - 70, f"Rows: {len(df)}  Columns: {len(df.columns)}")

    y = height - 100

    # add a small profile summary if exists
    if profile:
        try:
            items = list(profile.items())[:10]
            for k, v in items:
                line = f"{k}: {v}"
                c.drawString(40, y, line[:100])
                y -= 14
                if y < 80:
                    c.showPage()
                    y = height - 50
        except Exception:
            pass
    else:
        c.drawString(40, y, "No profile generated.")
        y -= 20

    # simple pivots listing
    if pivots:
        c.drawString(40, y, "Pivots summary:")
        y -= 14
        try:
            for name, val in list(pivots.items())[:5]:
                c.drawString(50, y, f"- {name}")
                y -= 12
                if y < 80:
                    c.showPage()
                    y = height - 50
        except Exception:
            pass

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()
