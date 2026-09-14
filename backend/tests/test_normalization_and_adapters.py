from app.services.bidder_ai_adapter import BidderAIAdapter
from app.services.requirement_normalizer import RequirementNormalizer
from app.services.tender_ai_adapter import TenderAIAdapter


def test_tender_adapter_normalizes_and_not_found_is_not_applicable():
    raw = [
        {"query": "GST", "status": "found", "requirements": [{"page": 11, "requirement": "GSTIN Number"}]},
        {"query": "EPFO / ESIC", "status": "not_found", "requirements": []},
    ]
    output = TenderAIAdapter(normalizer=RequirementNormalizer()).normalize_output(raw)
    assert output[0]["operator"] == "EXACT_IDENTIFIER_MATCH"
    assert output[0]["source"]["page"] == 11
    assert output[1]["applicable"] is False
    assert output[1]["operator"] == "MANUAL_REVIEW"


def test_requirement_normalization_thresholds_and_turnover():
    raw = [{"query": "Make in India / Local Content", "status": "found", "requirements": [{"page": 7, "requirement": "Minimum 50% and 20% Local Content required for qualifying as Class 1 and Class 2"}]}, {"query": "Turnover", "status": "found", "requirements": [{"page": 9, "requirement": "Minimum Average Annual Turnover 2.62 Lakh"}]}]
    local, turnover = RequirementNormalizer().normalize(raw)
    assert local["operator"] == "LOCAL_CONTENT_CLASSIFICATION"
    assert local["metadata"] == {"class_1_threshold": 50.0, "class_2_threshold": 20.0}
    assert turnover["operator"] == "GREATER_THAN_OR_EQUAL"
    assert turnover["required_value"] == 262000
    assert turnover["name"] == "Minimum Bidder Turnover"
    assert local["name"] == "Make in India / Local Content"


def test_requirement_heading_is_clean_and_description_is_preserved():
    description = "Bidder must submit self-attested copy of valid GST registration certificate."
    output = RequirementNormalizer().normalize([{"query": "GST", "status": "found", "requirements": [{"page": 7, "requirement": description}]}])
    assert output[0]["name"] == "GST Registration"
    assert output[0]["description"] == description


def test_unsupported_requirement_stays_manual_review():
    output = RequirementNormalizer().normalize([{"query": "Custom", "status": "found", "requirements": [{"page": 1, "requirement": "Use an appropriate methodology"}]}])
    assert output[0]["operator"] == "MANUAL_REVIEW"


def test_bidder_adapter_keeps_classification_separate_from_evidence():
    documents = {"documents": [{"document_id": "DOC_1", "category": "GST", "confidence": .99, "pages": [1]}]}
    evidence = {"results": [{"requirement_id": "REQ001", "evidence_found": True, "evidence": [{"document_id": "DOC_1", "page": 1, "field": "GSTIN", "value": "07AACCB5566K1ZP", "evidence_text": "GSTIN 07AACCB5566K1ZP"}], "ambiguities": []}]}
    output = BidderAIAdapter().normalize_outputs(documents, evidence)
    assert "status" not in output["documents"][0]
    assert output["evidence"][0]["value"] == "07AACCB5566K1ZP"
