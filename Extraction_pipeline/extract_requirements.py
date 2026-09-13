import json
import ollama


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_PATH = "extracted/retrieved_chunks.json"
OUTPUT_PATH = "extracted/extracted_requirements.json"

MODEL_NAME = "qwen2.5:3b"


# ============================================================
# CATEGORY-SPECIFIC PROMPTS
# ============================================================

CATEGORY_INSTRUCTIONS = {

    "Udyam / MSME": """
Identify explicit Udyam/MSME requirements.

ACCEPT:
- Udyam registration
- Udyam certificate
- MSME registration/certificate
- MSE/MSME status where the tender requires proof or eligibility
- Udyam portal verification
- Proof of Micro, Small or Medium Enterprise status

IMPORTANT:
Extract the actual requirement stated in the tender.
Do not create generic requirements such as "MSME registration or proof"
if the tender does not explicitly say that.

Do not treat a general mention of MSE/MSME as a requirement unless the
tender actually imposes a condition, submission, verification, exemption,
or eligibility requirement.
""",

    "GST": """
Identify explicit GST-related requirements.

ACCEPT:
- GSTIN
- GSTIN Number
- GST registration
- GST certificate
- GST return
- GST compliance
- GST-related document or information
- Requirement to submit/provide GST details

IMPORTANT:
A requirement mentioning "GSTIN Number" IS a GST requirement even if
the word "registration" is not present.

For example:
"GSTIN Number of the bidder" -> FOUND.

Do not require the word "GST registration" specifically.

REJECT:
- PAN alone
- Income Tax alone
- Generic tax compliance
- Generic statutory compliance
- Generic financial information without GST reference
""",

    "PAN / Income Tax": """
Identify explicit PAN or Income Tax requirements.

ACCEPT:
- PAN
- PAN card
- PAN number
- Income Tax registration
- Income Tax return
- Income Tax compliance
- Income Tax certificate
- Submission of PAN or Income Tax documents

IMPORTANT:
If PAN is explicitly required, it is a valid requirement even when
Income Tax is not mentioned.

REJECT:
- GST alone
- Generic tax compliance
- Generic statutory compliance
""",

    "Make in India / Local Content": """
Identify explicit Make in India and local-content requirements.

ACCEPT:
- Make in India
- Local content percentage
- Minimum local content
- Local sourcing
- Domestic value addition
- Class I Local Supplier
- Class II Local Supplier
- Local supplier classification
- Domestic manufacturing/local-content conditions
- Make in India declaration

IMPORTANT:
Extract the complete requirement, including percentages or thresholds
when they are explicitly stated.

For example:
"Minimum 50% local content required for Class I Local Supplier"
should be extracted as the requirement.

Do not infer local-content requirements from a generic mention of
manufacturing or supplier.
""",

    "EPFO / ESIC": """
Identify explicit EPFO or ESIC requirements.

ACCEPT:
- EPFO
- Employees' Provident Fund
- Provident Fund registration
- Provident Fund contribution/compliance
- ESIC
- Employees' State Insurance
- ESIC registration
- ESIC contribution/compliance
- EPFO/ESIC certificate or document

IMPORTANT:
The requirement must explicitly refer to EPFO, ESIC, Provident Fund,
or Employees' State Insurance.

REJECT:
- Generic labour compliance
- Generic employee compliance
- Generic social-security compliance
- Generic statutory compliance
""",

    "Startup India": """
Identify explicit Startup India requirements.

ACCEPT:
- Startup India registration
- Startup India recognition
- Startup India certificate
- Startup eligibility
- Startup-specific exemption
- Startup-specific benefit
- DPIIT recognition when explicitly connected to startup recognition

IMPORTANT:
Extract the actual condition or requirement.

REJECT:
- Generic mention of startup
- Generic DPIIT reference without startup relevance
- Generic business registration
""",

    "NSIC": """
Identify explicit NSIC requirements.

ACCEPT:
- NSIC registration
- NSIC certificate
- NSIC eligibility
- NSIC registration proof
- NSIC-related exemption
- NSIC-related documentation

IMPORTANT:
The requirement must explicitly mention NSIC.

REJECT:
- Generic MSME requirement
- Generic MSE requirement
- Udyam registration unless NSIC is explicitly involved
""",

    "OEM Authorization": """
Identify explicit OEM or manufacturer authorization requirements.

ACCEPT:
- OEM authorization
- OEM authorization certificate
- OEM authorization letter
- OEM certificate
- Manufacturer authorization
- Manufacturer authorization letter
- Proof of authorization from OEM
- Authorization issued by the original equipment manufacturer

IMPORTANT:
Extract the actual authorization requirement stated in the tender.

REJECT:
- Merely mentioning manufacturer
- Manufacturer name
- Make and Model
- Brand name
- Product manufacturer information
- Technical specifications without authorization
""",

    "DigiLocker / Document Verification": """
Identify explicit DigiLocker or digital document verification requirements.

ACCEPT:
- DigiLocker
- DigiLocker document
- DigiLocker verification
- Submission through DigiLocker
- Digitally verified government documents
- Online government document verification
- Verification through an official digital document repository

IMPORTANT:
The tender must explicitly require or mention this type of document
submission or verification.

REJECT:
- Normal PDF upload
- Generic online submission
- Generic document verification
- Digital signature alone
""",

    "Blacklisting / Debarment": """
Identify explicit blacklisting, debarment, suspension, or banning
requirements.

ACCEPT:
- Bidder must not be blacklisted
- Bidder must not be debarred
- Declaration that bidder is not blacklisted
- Declaration that bidder is not debarred
- Blacklisting
- Debarment
- Suspension
- Banning
- Debarment-related eligibility condition

IMPORTANT:
Extract the complete condition when it is explicitly stated.

REJECT:
- Generic eligibility
- Generic poor performance
- Generic legal compliance
""",

    "BIS / DPIIT": """
Identify explicit BIS or DPIIT requirements.

ACCEPT:
- BIS certification
- BIS licence
- BIS registration
- BIS standard where compliance is explicitly required
- DPIIT recognition
- DPIIT certificate
- DPIIT registration
- DPIIT-related compliance

IMPORTANT:
The requirement must explicitly mention BIS or DPIIT.

REJECT:
- Generic quality certification
- Generic government certification
- Generic technical standard
- Generic certification without BIS/DPIIT reference
""",

    "Technical Specifications": """
Identify the actual technical specifications and technical requirements
of the product.

ACCEPT:
- Processor
- RAM
- Storage
- Operating system
- Display
- Dimensions
- Weight
- Capacity
- Performance
- Connectivity
- Ports
- Battery
- Camera
- Materials
- Features
- Technical standards
- Required make/model characteristics
- Any other explicit product specification

IMPORTANT:
Extract the ACTUAL technical requirement and its value whenever stated.

For example:
"16 GB DDR5 RAM"
"512 GB NVMe SSD"
"Intel Core i5 processor"

These are requirements.

DO NOT extract only generic statements such as:
- "technical specifications shall be submitted"
- "technical compliance statement shall be submitted"

unless no actual technical specification is present.

If the retrieved text contains an actual technical specification,
extract it.
""",

    "Tender-Specific Eligibility": """
Identify explicit bidder eligibility and qualification requirements.

ACCEPT:
- Minimum years of experience
- Minimum similar-work experience
- Minimum turnover
- Average annual turnover
- Financial eligibility
- Technical qualification
- Previous supply experience
- Required project history
- Similar project requirement
- Specific bidder qualification
- Required eligibility documents
- Specific eligibility thresholds
- Required number/value of previous contracts

IMPORTANT:
Extract the COMPLETE requirement.

For example, do NOT output:
"Minimum turnover"

Instead, if the tender states a value, output something like:
"Bidder must have a minimum average annual turnover of ₹X during the
last three financial years."

Do NOT output generic labels such as:
- "Minimum experience"
- "Minimum turnover"
- "Technical qualification"
- "Eligibility conditions"

unless that is literally all the tender says.

REJECT:
- Generic tender instructions
- Generic document submission
- General statements that do not establish bidder eligibility
""",

    "Other Statutory Compliance": """
Identify explicit statutory, regulatory, legal, government registration,
licence, certification, declaration, or compliance requirements that do
NOT belong to any of the other categories.

ACCEPT:
- Explicit statutory registration
- Explicit government licence
- Explicit regulatory certificate
- Explicit legal declaration
- Explicit regulatory compliance
- Other clearly named legal/government requirement

IMPORTANT:
Only extract requirements that are genuinely outside the other 13
categories.

Do NOT extract:
- GST
- PAN / Income Tax
- Udyam / MSME
- EPFO / ESIC
- Startup India
- NSIC
- OEM Authorization
- DigiLocker
- Blacklisting / Debarment
- BIS / DPIIT
- Make in India / Local Content
- Technical Specifications
- Tender-Specific Eligibility

Do not infer a statutory requirement from generic words such as
"statutory compliance" unless the actual specific requirement is stated.
"""
}


# ============================================================
# COMMON PROMPT
# ============================================================

def build_prompt(category, query, chunks):

    category_instruction = CATEGORY_INSTRUCTIONS.get(
        category,
        "Extract only explicit requirements relevant to this category."
    )

    chunks_text = ""

    for chunk in chunks:
        chunks_text += (
            f"\n--- CHUNK ---\n"
            f"Page: {chunk.get('page')}\n"
            f"Text:\n{chunk.get('text', '')}\n"
        )

    prompt = f"""
You are a government tender requirement extraction system.

CATEGORY:
{category}

QUERY:
{query}

The following text contains chunks retrieved from the tender using
semantic embedding similarity.

Your job is to verify whether these chunks contain an ACTUAL and EXPLICIT
requirement belonging specifically to the requested category.

CATEGORY-SPECIFIC RULES:
{category_instruction}

GENERAL RULES:

1. Use ONLY the provided tender text.

2. Do not use outside knowledge.

3. A requirement must be explicitly stated.

4. Do not infer requirements.

5. A keyword alone is not enough.

6. Ignore chunks that are relevant to another category.

7. Ignore generic statements that do not establish a specific requirement.

8. Do not invent:
   - values
   - percentages
   - dates
   - certificates
   - registrations
   - eligibility conditions
   - technical specifications

9. If multiple separate requirements are explicitly present, extract them.

10. If the same requirement appears multiple times without meaningful
    difference, return it only once.

11. Use the page number provided with the chunk.

12. If there is no explicit requirement for this category in the provided
    chunks, return status "not_found".

13. Do not treat the query itself as evidence.

14. Return ONLY valid JSON.

15. Prefer complete requirements over fragments.

16. Do not extract a general heading, label, or category name as a
requirement when the surrounding text contains the actual condition.

17. If a requirement has sub-points (a), (b), (c), extract the complete
parent requirement when the sub-points are simply details of that same
requirement. Extract sub-points separately only when they represent
independent requirements.

18. Do not extract the same requirement more than once, even if it appears
on multiple pages.

19. If the same requirement appears on multiple pages, keep the page where
the requirement is most clearly stated. Do not duplicate it merely because
the text was repeated.

20. Do not create generic requirements such as:
- "Minimum experience"
- "Minimum turnover"
- "Technical qualification"
- "Eligibility conditions"
- "MSME registration/certificate"

when the actual tender text provides a more specific condition.

21. Preserve important details such as:
- percentages
- monetary thresholds
- quantities
- time periods
- number of years
- number of orders
- required documents
- conditions

22. The extracted requirement should be understandable by itself without
needing the surrounding chunk.

23. Do not split one logically connected requirement into multiple
requirements merely because it contains multiple sentences.

24. Do not merge two genuinely independent requirements into one.

OUTPUT FORMAT:

If requirements are found:

{{
    "status": "found",
    "requirements": [
        {{
            "page": 0,
            "requirement": "..."
        }}
    ]
}}

If no requirement is found:

{{
    "status": "not_found",
    "requirements": []
}}

RETRIEVED TENDER TEXT:
{chunks_text}
"""

    return prompt


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("OLLAMA REQUIREMENT EXTRACTION")
    print("=" * 60)

    # --------------------------------------------------------
    # Load retrieved chunks
    # --------------------------------------------------------

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        retrieved_data = json.load(f)

    results = []

    # --------------------------------------------------------
    # Process each query
    # --------------------------------------------------------

    for index, item in enumerate(retrieved_data, start=1):

        query_id = item.get("query_id")
        category = item.get("category")
        query = item.get("query")
        chunks = item.get("results", [])

        print()
        print(f"[{index}/14] {query_id} - {category}")

        prompt = build_prompt(
            category,
            query,
            chunks
        )

        try:

            response = ollama.chat(
                model=MODEL_NAME,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                options={
                    "temperature": 0
                }
            )

            content = response["message"]["content"].strip()

            # ------------------------------------------------
            # Parse JSON
            # ------------------------------------------------

            extracted = json.loads(content)

            status = extracted.get("status", "not_found")
            requirements = extracted.get("requirements", [])

            # ------------------------------------------------
            # Clean output
            # ------------------------------------------------

            cleaned_requirements = []

            for requirement in requirements:

                cleaned_requirements.append({
                    "page": requirement.get("page"),
                    "requirement": requirement.get("requirement", "")
                })

            final_item = {
                "query": category,
                "status": status,
                "requirements": cleaned_requirements
            }

            results.append(final_item)

            print(f"Status: {status}")

            for req in cleaned_requirements:
                print(
                    f"  - Page {req['page']}: "
                    f"{req['requirement']}"
                )

        except Exception as e:

            print("ERROR:", e)

            results.append({
                "query": category,
                "status": "error",
                "requirements": []
            })

    # --------------------------------------------------------
    # Save final JSON
    # --------------------------------------------------------

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:

        json.dump(
            results,
            f,
            indent=4,
            ensure_ascii=False
        )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    found = sum(
        1 for item in results
        if item["status"] == "found"
    )

    not_found = sum(
        1 for item in results
        if item["status"] == "not_found"
    )

    errors = sum(
        1 for item in results
        if item["status"] == "error"
    )

    print()
    print("=" * 60)
    print("EXTRACTION COMPLETED")
    print("=" * 60)

    print("Total queries :", len(results))
    print("Found         :", found)
    print("Not found     :", not_found)
    print("Errors        :", errors)

    print()
    print("Output:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()