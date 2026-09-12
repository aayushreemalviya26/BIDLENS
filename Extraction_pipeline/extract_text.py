import pdfplumber
import json
import os
import pypdfium2 as pdfium

from ocr_engine import extract_with_ocr


pdf_path = "data/tender.pdf"
output_path = "extracted/tender_pages.json"

pages = []

with pdfplumber.open(pdf_path) as pdf:

    # Open the same PDF with PDFium only for OCR rendering
    pdfium_pdf = pdfium.PdfDocument(pdf_path)

    print("Number of pages:", len(pdf.pages))

    for page_number, page in enumerate(pdf.pages, start=1):

        print(f"\nProcessing page {page_number}...")

        # --------------------------------------------------
        # STEP 1: Try normal PDFPlumber text extraction
        # --------------------------------------------------

        text = (page.extract_text() or "").strip()

        if text:

            # ----------------------------------------------
            # NORMAL DIGITAL PDF
            # ----------------------------------------------

            print("  PDFPlumber text found.")
            print("  Using PDFPlumber extraction.")

            tables = page.extract_tables()

            extraction_method = "pdfplumber"

        else:

            # ----------------------------------------------
            # SCANNED / IMAGE-ONLY PAGE
            # ----------------------------------------------

            print("  PDFPlumber found no text.")
            print("  Running OCR...")

            ocr_result = extract_with_ocr(
                pdfium_pdf,
                page_number
            )

            text = ocr_result["text"]

            # Do NOT trust PDFPlumber tables on an OCR page
            tables = []

            extraction_method = "ocr"

            print("  OCR completed.")
            print(
                "  OCR confidence:",
                ocr_result.get("ocr_confidence")
            )

        # --------------------------------------------------
        # STEP 2: Create COMMON page structure
        # --------------------------------------------------

        page_data = {
            "page": page_number,
            "text": text,
            "tables": tables
        }

        pages.append(page_data)

    pdfium_pdf.close()


# ----------------------------------------------------------
# STEP 3: Save exactly the same output format as before
# ----------------------------------------------------------

os.makedirs("extracted", exist_ok=True)

with open(output_path, "w", encoding="utf-8") as f:

    json.dump(
        pages,
        f,
        indent=4,
        ensure_ascii=False
    )


print("\nExtraction completed.")
print("Saved to:", output_path)