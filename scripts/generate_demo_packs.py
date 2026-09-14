from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from io import BytesIO
import shutil

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.pdfgen import canvas
from pypdf import PdfReader, PdfWriter


ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demo_files"
DISCLAIMER = "SYNTHETIC DOCUMENT — FOR PROTOTYPE TESTING ONLY"


def make_pdf(path: Path, title: str, fields: list[tuple[str, str]], note: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Disclaimer", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=10, textColor=HexColor("#A13D33"), alignment=1, spaceAfter=14))
    styles.add(ParagraphStyle(name="DocTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=18, textColor=HexColor("#2B2523"), spaceAfter=16))
    styles.add(ParagraphStyle(name="BodySmall", parent=styles["BodyText"], fontSize=9, leading=13, textColor=HexColor("#5C554D")))
    doc = SimpleDocTemplate(str(path), pagesize=A4, leftMargin=22 * mm, rightMargin=22 * mm, topMargin=18 * mm, bottomMargin=18 * mm, title=title, author="BidLens Prototype")
    story = [Paragraph(DISCLAIMER, styles["Disclaimer"]), Paragraph(title, styles["DocTitle"])]
    data = [[Paragraph(f"<b>{label}</b>", styles["BodySmall"]), Paragraph(value, styles["BodySmall"])] for label, value in fields]
    table = Table(data, colWidths=[52 * mm, 100 * mm], hAlign="LEFT")
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, -1), HexColor("#F5F1EB")), ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#D8D0C7")), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    story.append(table)
    if note:
        story += [Spacer(1, 10 * mm), Paragraph(note, styles["BodySmall"])]
    story += [Spacer(1, 15 * mm), Paragraph("This document is fictional, uses invented identifiers, and is not issued by any government or certification body.", styles["BodySmall"])]
    doc.build(story)


def pack(company: dict, local_content: int, omit_service: bool = False, auth_name: str | None = None) -> dict[str, tuple[str, list[tuple[str, str]], str]]:
    name, bidder_id = company["name"], company["bidder_id"]
    authorization_name = auth_name or name
    common = [("Registered Bidder", name), ("Bidder ID", bidder_id), ("Tender", "GEM/2026/B/7910945")]
    docs = {
        "Company_Profile.pdf": ("Certificate of Incorporation and Company Profile", common + [("CIN", company["cin"]), ("Legal status", "Active private limited company"), ("Registered office", company["address"])], "The registered bidder identity used throughout this pack is stated above."),
        "GST_Registration.pdf": ("GST Registration Certificate", common + [("GSTIN", company["gst"]), ("Legal Name", name), ("Registration Status", "ACTIVE")], "Synthetic GST evidence for connector matching."),
        "PAN_Card.pdf": ("PAN Card and Income Tax Identity", common + [("PAN", company["pan"]), ("Name on PAN", name), ("Status", "VALID")], "Synthetic PAN evidence for connector matching."),
        "Udyam_Certificate.pdf": ("Udyam Registration Certificate", common + [("Udyam Registration Number", company["udyam"]), ("Enterprise Name", name), ("Enterprise Type", "SMALL"), ("Registration Status", "ACTIVE")], "Synthetic Udyam evidence for connector matching."),
        "Bidder_Turnover_Certificate.pdf": ("Bidder Turnover Certificate", common + [("Average Annual Turnover", "INR 8,500,000"), ("Period", "FY 2022-23, FY 2023-24, FY 2024-25"), ("Entity", name)], "Average annual bidder turnover is certified as INR 8,500,000."),
        "OEM_Turnover_Certificate.pdf": ("OEM Turnover Certificate", common + [("OEM", company["oem"]), ("Average Annual Turnover", "INR 18,000,000"), ("Period", "FY 2022-23, FY 2023-24, FY 2024-25")], "Average annual OEM turnover is certified as INR 18,000,000."),
        "Experience_Credentials.pdf": ("Similar Experience Credentials", common + [("Experience Period", "10 financial years"), ("Similar Supplies", "Desktop computers and workstation supply, installation and commissioning"), ("Qualifying Order", "One completed order valued at INR 3,000,000"), ("Completion Status", "SATISFACTORY")], "Documentary evidence of qualifying similar supply/work experience."),
        "Past_Performance.pdf": ("Past Performance Certificate", common + [("Completed Contracts", "7"), ("On-time Completion", "100%"), ("Customer Rating", "Satisfactory")], "Past performance is stated as satisfactory."),
        "OEM_Authorization.pdf": ("OEM Authorization Certificate", common + [("OEM Name", company["oem"]), ("Authorized Bidder", authorization_name), ("Authorization Scope", "Supply, installation and warranty support for offered desktop computers"), ("Authorization Status", "VALID")], "The OEM authorizes only the entity named in the Authorized Bidder field."),
        "Local_Content_Declaration.pdf": ("Make in India Local Content Declaration", common + [("Percentage of Local Content", f"{local_content}%"), ("Supplier Classification", "Class I local supplier" if local_content >= 50 else ("Class II local supplier" if local_content >= 20 else "Non-local supplier")), ("Place of Value Addition", "India"), ("Declaration Status", "FILED")], f"The offered product contains {local_content}% local content."),
        "ISO_9001_Certificate.pdf": ("ISO 9001 Quality Management System Certificate", common + [("Standard", "ISO 9001:2015"), ("Certificate Number", company["iso"]), ("Validity", "2030-12-31"), ("Status", "VALID")], "Synthetic quality-management evidence; not issued by an accreditation body."),
        "BIS_Technical_Compliance.pdf": ("BIS Licence and Technical Compliance Certificate", common + [("BIS Licence Number", company["bis"]), ("Standard", "IS 13252 (Part 1):2010"), ("Product", "Desktop Computer"), ("Registry Status", "VALID")], "Synthetic BIS identifier designed for the local mock connector."),
        "Blacklisting_Declaration.pdf": ("Non-Blacklisting and Non-Debarment Declaration", common + [("Blacklisting Status", "NOT BLACKLISTED"), ("Debarment Status", "NOT DEBARRED"), ("Declaration Date", "2026-09-01")], "Entity declares it is not suspended, banned, blacklisted, or debarred."),
        "Financial_Standing.pdf": ("Financial Standing Certificate", common + [("Net Worth", "INR 12,000,000"), ("Net Worth Status", "POSITIVE"), ("Insolvency Status", "NOT INSOLVENT")], "Positive net worth and sound financial standing are declared."),
        "Service_Centre_Details.pdf": ("Service Centre Details", common + [("Service Centre", company["service"]), ("Support Window", "8x5 onsite support"), ("Response Time", "Next business day")], "Local service support is available for the contract period."),
        "Malicious_Code_Declaration.pdf": ("Malicious Code and Software Integrity Declaration", common + [("Malicious Code", "ABSENT"), ("Backdoors", "ABSENT"), ("Integrity Verification", "PASSED")], "The offered equipment and software are declared free from malicious code and backdoors."),
        "BoQ_Compliance.pdf": ("Bill of Quantities and Technical Specification Sheet", common + [("Item", "Desktop Computer"), ("Quantity", "20"), ("Processor", "64-bit x86, 8 cores"), ("Memory", "16 GB"), ("Storage", "512 GB SSD"), ("Compliance", "OFFERED AS SPECIFIED")], "Line-item BoQ response for the offered product."),
    }
    if omit_service:
        docs.pop("Service_Centre_Details.pdf")
    return docs


def make_combined_orange(folder: Path) -> Path:
    """Build one combined submission with stable original-file page references."""
    output = DEMO / "bidders" / "orange_tech_combined" / "Orange_Tech_Complete_Bid.pdf"
    output.parent.mkdir(parents=True, exist_ok=True)
    writer = PdfWriter()

    front = BytesIO()
    cover = canvas.Canvas(front, pagesize=A4)
    for title, body in [
        ("Orange Tech Complete Bid", "Synthetic combined bidder submission for GEM/2026/B/7910945"),
        ("Submission Index", "Certificates and declarations follow in the order supplied by the bidder."),
        ("Bidder Declaration", "All documents in this combined PDF relate to Orange Tech Systems Private Limited."),
    ]:
        cover.setFont("Helvetica-Bold", 18)
        cover.drawString(55, 780, title)
        cover.setFont("Helvetica", 10)
        cover.drawString(55, 750, DISCLAIMER)
        cover.drawString(55, 720, body)
        cover.showPage()
    cover.save()
    front.seek(0)
    for page in PdfReader(front).pages:
        writer.add_page(page)

    final_docs = {"GST_Registration.pdf", "PAN_Card.pdf", "Udyam_Certificate.pdf"}
    for pdf in sorted(path for path in folder.glob("*.pdf") if path.name not in final_docs):
        for page in PdfReader(pdf).pages:
            writer.add_page(page)

    # Stable combined-file demo positions: GST 18-19, PAN 20, Udyam 21-22.
    for filename, copies in [("GST_Registration.pdf", 2), ("PAN_Card.pdf", 1), ("Udyam_Certificate.pdf", 2)]:
        source_page = PdfReader(folder / filename).pages[0]
        for _ in range(copies):
            writer.add_page(source_page)

    with output.open("wb") as destination:
        writer.write(destination)
    return output


def main() -> None:
    companies = [
        ({"slug": "orange_tech", "name": "Orange Tech Systems Private Limited", "bidder_id": "OTS-001", "cin": "U62099HR2020PTC123456", "gst": "29AAECO1234K1Z8", "pan": "AAECO1234K", "udyam": "UDYAM-HR-05-0012345", "bis": "BIS-SYN-2026-001", "iso": "ISO-SYN-OTS-9001", "oem": "Orange Compute Devices Private Limited", "address": "Gurugram, Haryana", "service": "Gurugram Support Centre"}, 55, False, None),
        ({"slug": "bharat_compute", "name": "Bharat Compute Solutions Private Limited", "bidder_id": "BCS-002", "cin": "U62099DL2019PTC234567", "gst": "07AAECB2345M1Z6", "pan": "AAECB2345M", "udyam": "UDYAM-DL-07-0067890", "bis": "BIS-SYN-2026-002", "iso": "ISO-SYN-BCS-9001", "oem": "Bharat Compute Manufacturing Private Limited", "address": "New Delhi, Delhi", "service": "Delhi NCR Support Centre"}, 15, False, None),
        ({"slug": "securebyte", "name": "SecureByte Systems Private Limited", "bidder_id": "SBS-003", "cin": "U62099KA2021PTC345678", "gst": "29AAECS3456N1Z4", "pan": "AAECS3456N", "udyam": "UDYAM-KA-03-0076543", "bis": "BIS-SYN-2026-003", "iso": "ISO-SYN-SBS-9001", "oem": "SecureByte Device Labs Private Limited", "address": "Bengaluru, Karnataka", "service": ""}, 55, True, "SecureByte Technology Solutions Private Limited"),
    ]
    for company, local, omit_service, auth_name in companies:
        folder = DEMO / "bidders" / company["slug"]
        folder.mkdir(parents=True, exist_ok=True)
        for filename, (title, fields, note) in pack(company, local, omit_service, auth_name).items():
            make_pdf(folder / filename, title, fields, note)
        with ZipFile(DEMO / f"{company['slug']}_bidder_pack.zip", "w", ZIP_DEFLATED) as archive:
            for pdf in sorted(folder.glob("*.pdf")):
                archive.write(pdf, arcname=pdf.name)

    make_combined_orange(DEMO / "bidders" / "orange_tech")

    mutation_company = companies[1][0]
    mutation_doc = pack(mutation_company, 35)["Local_Content_Declaration.pdf"]
    make_pdf(DEMO / "mutations" / "bharat_35" / "Local_Content_Declaration.pdf", *mutation_doc)
    tender_folder = DEMO / "tender"
    tender_folder.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "Extraction_pipeline" / "data" / "tender.pdf", tender_folder / "GEM_2026_B_7910945.pdf")


if __name__ == "__main__":
    main()
