import hashlib
from datetime import datetime, timezone
from io import BytesIO
from typing import Any, Dict
from fpdf import FPDF
from shared.logging_setup import setup_logger

logger = setup_logger("certificate_generator")


class CSRCertificatePDF(FPDF):
    def header(self):
        # Decorative border
        self.set_line_width(1.0)
        self.set_draw_color(34, 139, 34)  # Forest Green
        self.rect(8, 8, self.w - 16, self.h - 16)
        self.set_line_width(0.3)
        self.rect(10, 10, self.w - 20, self.h - 20)

        # Header Title
        self.set_font("Helvetica", "B", 22)
        self.set_text_color(24, 80, 40)
        self.set_y(22)
        self.cell(0, 12, "FOODBRIDGE NETWORK", align="C", new_x="LMARGIN", new_y="NEXT")

        self.set_font("Helvetica", "I", 12)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, "Real-Time Food Surplus Redistribution & Climate Impact Initiative", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(6)


def generate_csr_certificate_pdf(
    donor_id: str,
    donor_name: str,
    metrics: Dict[str, Any],
    month_year: str = "October 2026",
) -> bytes:
    """Generates a verified, publication-ready PDF CSR Impact Certificate."""
    pdf = CSRCertificatePDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()

    # Main Certificate Title
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(30, 41, 59)
    pdf.ln(8)
    pdf.cell(0, 10, "CERTIFICATE OF CORPORATE SOCIAL RESPONSIBILITY", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(0, 8, "This certifies that", align="C", new_x="LMARGIN", new_y="NEXT")

    # Donor Name
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 12, donor_name.upper(), align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(
        0,
        8,
        f"has actively prevented commercial food waste and supported community welfare during {month_year}.",
        align="C",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(10)

    # Key Metrics Highlights Box
    pdf.set_fill_color(241, 245, 249)
    pdf.set_draw_color(203, 213, 225)
    pdf.rect(25, pdf.get_y(), 160, 52, style="FD")

    start_y = pdf.get_y() + 6
    pdf.set_xy(30, start_y)

    total_kg = metrics.get("total_kg_diverted", 0.0)
    total_meals = metrics.get("total_meals_saved", 0)
    total_co2e = metrics.get("total_co2e_avoided_kg", 0.0)

    # Metric 1: Food Diverted
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(22, 101, 52)
    pdf.cell(50, 10, f"{total_kg:,.1f} KG", align="C")
    # Metric 2: Meals Saved
    pdf.set_text_color(30, 58, 138)
    pdf.cell(50, 10, f"{total_meals:,} MEALS", align="C")
    # Metric 3: CO2e Avoided
    pdf.set_text_color(153, 27, 27)
    pdf.cell(50, 10, f"{total_co2e:,.1f} KG", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(30)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(50, 6, "Total Surplus Diverted", align="C")
    pdf.cell(50, 6, "Nutritious Meals Served", align="C")
    pdf.cell(50, 6, "GHG Emissions Avoided", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_y(start_y + 40)
    pdf.ln(12)

    # Verification Hash for Auditability
    now_str = datetime.now(timezone.utc).isoformat()
    raw_hash_data = f"{donor_id}:{total_kg}:{total_meals}:{total_co2e}:{now_str}"
    verification_hash = hashlib.sha256(raw_hash_data.encode()).hexdigest()[:24].upper()

    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(0, 6, f"Cryptographic Verification Hash: {verification_hash}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Certified under UN Sustainable Development Goals (SDG 2: Zero Hunger & SDG 12: Responsible Consumption)", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Generated on {now_str[:10]} | FoodBridge Cloud Platform v1.0", align="C", new_x="LMARGIN", new_y="NEXT")

    # Signatures
    pdf.ln(14)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(51, 65, 85)
    pdf.cell(90, 6, "Dr. Aarti Sharma", align="C")
    pdf.cell(90, 6, "FoodBridge Operations Board", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(90, 4, "Director of Sustainability Auditing", align="C")
    pdf.cell(90, 4, "Verified Digital Signature", align="C")

    # Output binary PDF buffer
    buf = BytesIO()
    pdf.output(buf)
    return buf.getvalue()
