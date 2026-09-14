# import json
# from pathlib import Path

# import pdfplumber
# import pypdfium2 as pdfium
# import pytesseract


# # ============================================================
# # CONFIGURATION
# # ============================================================

# INPUT_FILE = Path("data/bidder.pdf")
# OUTPUT_FILE = Path("data/bidder_pages.json")

# BIDDER_ID = "B02"
# BIDDER_NAME = "Bharat Power Control Systems Pvt. Ltd."

# OCR_DPI = 200


# # ============================================================
# # TABLE HELPERS
# # ============================================================

# def table_to_text(table):
#     """
#     Convert one PDF table into deterministic text.

#     Example:

#     Name | Value
#     GSTIN | 07ABCDE1234F1Z5
#     """

#     if not table:
#         return ""

#     rows = []

#     for row in table:

#         if not row:
#             continue

#         cells = []

#         for cell in row:

#             if cell is None:
#                 cells.append("")
#             else:
#                 cells.append(
#                     str(cell).strip()
#                 )

#         rows.append(
#             " | ".join(cells)
#         )

#     return "\n".join(rows).strip()


# def tables_to_text(tables):

#     if not tables:
#         return ""

#     sections = []

#     for index, table in enumerate(tables, start=1):

#         text = table_to_text(table)

#         if text:

#             sections.append(
#                 f"[TABLE {index}]\n{text}"
#             )

#     return "\n\n".join(sections)


# # ============================================================
# # OCR
# # ============================================================

# def ocr_page(pdfium_pdf, page_number):

#     page = pdfium_pdf[
#         page_number - 1
#     ]

#     bitmap = page.render(
#         scale=OCR_DPI / 72
#     )

#     image = bitmap.to_pil()

#     text = pytesseract.image_to_string(
#         image
#     )

#     return text.strip()


# # ============================================================
# # TEXT CLEANING
# # ============================================================

# def normalize_text(text):

#     if not text:
#         return ""

#     text = text.replace(
#         "\x00",
#         " "
#     )

#     return text.strip()


# def has_text(text):

#     if not text:
#         return False

#     return bool(
#         text.strip()
#     )


# # ============================================================
# # MAIN
# # ============================================================

# def main():

#     if not INPUT_FILE.exists():

#         raise FileNotFoundError(
#             f"Bidder PDF not found: {INPUT_FILE}"
#         )

#     OUTPUT_FILE.parent.mkdir(
#         parents=True,
#         exist_ok=True
#     )

#     pages = []

#     print("=" * 60)
#     print("BIDDER PDF EXTRACTION")
#     print("=" * 60)

#     with pdfplumber.open(
#         INPUT_FILE
#     ) as pdf:

#         total_pages = len(pdf.pages)

#         print(
#             f"Total pages: {total_pages}"
#         )

#         # PDFium is used only if OCR is required.
#         pdfium_pdf = pdfium.PdfDocument(
#             str(INPUT_FILE)
#         )

#         try:

#             for page_number, page in enumerate(
#                 pdf.pages,
#                 start=1
#             ):

#                 print(
#                     f"\nProcessing page "
#                     f"{page_number}/{total_pages}"
#                 )

#                 # ------------------------------------------------
#                 # STEP 1: NORMAL PDF EXTRACTION
#                 # ------------------------------------------------

#                 text = (
#                     page.extract_text()
#                     or ""
#                 ).strip()

#                 tables = (
#                     page.extract_tables()
#                     or []
#                 )

#                 table_text = tables_to_text(
#                     tables
#                 )

#                 combined_text = text

#                 if table_text:

#                     if combined_text:
#                         combined_text += "\n\n"

#                     combined_text += table_text

#                 extraction_method = "pdfplumber"

#                 # ------------------------------------------------
#                 # STEP 2: OCR ONLY IF NO TEXT
#                 # ------------------------------------------------

#                 if not has_text(
#                     combined_text
#                 ):

#                     print(
#                         "  No extractable text."
#                     )

#                     print(
#                         "  Running OCR..."
#                     )

#                     ocr_text = ocr_page(
#                         pdfium_pdf,
#                         page_number
#                     )

#                     combined_text = ocr_text

#                     extraction_method = "ocr"

#                     # OCR page should not inherit
#                     # PDFPlumber tables.
#                     tables = []

#                     print(
#                         "  OCR completed."
#                     )

#                 else:

#                     print(
#                         "  PDFPlumber extraction used."
#                     )

#                 # ------------------------------------------------
#                 # PAGE OBJECT
#                 # ------------------------------------------------

#                 pages.append(
#                     {
#                         "page": page_number,
#                         "text": normalize_text(
#                             combined_text
#                         ),
#                         "tables": tables,
#                         "extraction_method":
#                             extraction_method
#                     }
#                 )

#         finally:

#             pdfium_pdf.close()

#     # ============================================================
#     # SAVE
#     # ============================================================

#     output = {
#         "bidder_id": BIDDER_ID,
#         "bidder_name": BIDDER_NAME,
#         "source_file": INPUT_FILE.name,
#         "total_pages": len(pages),
#         "pages": pages
#     }

#     with open(
#         OUTPUT_FILE,
#         "w",
#         encoding="utf-8"
#     ) as f:

#         json.dump(
#             output,
#             f,
#             indent=4,
#             ensure_ascii=False
#         )

#     print("\nExtraction completed.")
#     print(
#         "Saved to:",
#         OUTPUT_FILE
#     )


# if __name__ == "__main__":
#     main()

import json
from pathlib import Path

import pdfplumber
import pypdfium2 as pdfium
import pytesseract
from PIL import Image


INPUT = Path("data/bidder.pdf")
OUTPUT = Path("data/bidder_pages.json")

METADATA = Path("data/bidder_metadata.json")

OCR_DPI = 200


def clean_cell(value):
    if value is None:
        return ""
    return str(value).strip()


def bidder_metadata():
    if not METADATA.exists():
        return {"bidder_id": "UNSPECIFIED", "bidder_name": "Unspecified bidder"}
    return json.loads(METADATA.read_text(encoding="utf-8"))


def table_to_text(table):
    rows = []

    for row in table or []:
        cells = [clean_cell(cell) for cell in row]

        if any(cells):
            rows.append(" | ".join(cells))

    return "\n".join(rows)


def extract_tables_text(tables):
    sections = []

    for table_index, table in enumerate(tables or [], start=1):
        text = table_to_text(table)

        if text:
            sections.append(
                f"[TABLE {table_index}]\n{text}"
            )

    return "\n\n".join(sections)


def has_meaningful_text(text):
    return bool(text and text.strip())


def ocr_page(pdf, page_number):
    page = pdf[page_number - 1]

    bitmap = page.render(
        scale=OCR_DPI / 72
    )

    pil_image = bitmap.to_pil()

    text = pytesseract.image_to_string(
        pil_image,
        config="--psm 6"
    )

    return text.strip()


def main():

    if not INPUT.exists():
        raise FileNotFoundError(
            f"Input PDF not found: {INPUT}"
        )

    pages = []

    with pdfplumber.open(INPUT) as plumber_pdf:

        pdfium_pdf = pdfium.PdfDocument(str(INPUT))

        total_pages = len(plumber_pdf.pages)

        print(f"Number of pages: {total_pages}")

        for page_number, page in enumerate(
            plumber_pdf.pages,
            start=1
        ):

            text = (
                page.extract_text()
                or ""
            ).strip()

            tables = (
                page.extract_tables()
                or []
            )

            table_text = extract_tables_text(
                tables
            )

            combined_text = text

            if table_text:
                if combined_text:
                    combined_text += "\n\n"
                combined_text += table_text

            extraction_method = "pdfplumber"

            # IMPORTANT:
            # OCR only if PDF extraction produced no usable text.
            if not has_meaningful_text(combined_text):

                print(
                    f"Page {page_number}: "
                    "no extractable text → OCR"
                )

                ocr_text = ocr_page(
                    pdfium_pdf,
                    page_number
                )

                combined_text = ocr_text
                tables = []
                extraction_method = "ocr"

            pages.append({
                "bidder_id": bidder_metadata()["bidder_id"],
                "bidder_name": bidder_metadata()["bidder_name"],
                "page": page_number,
                "text": combined_text,
                "tables": tables,
                "extraction_method": extraction_method
            })

    output = {
        "bidder_id": bidder_metadata()["bidder_id"],
        "bidder_name": bidder_metadata()["bidder_name"],
        "source_file": INPUT.name,
        "total_pages": len(pages),
        "pages": pages
    }

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        OUTPUT,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            output,
            f,
            indent=4,
            ensure_ascii=False
        )

    print(
        f"Extraction completed → {OUTPUT}"
    )


if __name__ == "__main__":
    main()
