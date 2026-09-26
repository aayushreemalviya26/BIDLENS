import importlib.util
from pathlib import Path

module_path = Path(__file__).resolve().parents[2] / "Bidder_doc/evidence.py"
spec = importlib.util.spec_from_file_location("bidder_evidence_test", module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_numeric_fact_is_retained_even_below_tender_threshold():
    result = {"required_document_type": "MII_LOCAL_CONTENT", "retrieved_chunks": [{"document_id": "LOCAL", "page": 10, "category": "MII_LOCAL_CONTENT", "text": "Percentage of Local Content\n15%"}]}
    facts = module.deterministic_fallback(result)
    assert facts[0]["value"] == "15" and facts[0]["page"] == 10
    result["retrieved_chunks"][0]["text"] = "Percentage of Local Content\n35%"
    assert module.deterministic_fallback(result)[0]["value"] == "35"


def test_llm_page_corrected_only_from_actual_retrieved_evidence():
    result = {"retrieved_chunks": [{"document_id": "LOCAL", "page": 10, "text": "Percentage of Local Content 15%"}]}
    extracted = {"evidence": [{"document_id": "LOCAL", "page": 1, "value": "15%", "evidence_text": "Percentage of Local Content 15%"}], "ambiguities": []}
    grounded = module.ground_evidence(extracted, result)
    assert grounded["evidence"][0]["page"] == 10
    assert grounded["evidence_found"]


def test_invented_or_ambiguous_source_does_not_get_a_page():
    result = {"retrieved_chunks": [{"document_id": "A", "page": 1, "text": "GST ACTIVE"}, {"document_id": "B", "page": 2, "text": "PAN ACTIVE"}]}
    for value in ("ACTIVE", "invented"):
        extracted = {"evidence": [{"document_id": "invented", "page": 9, "value": value}], "ambiguities": []}
        grounded = module.ground_evidence(extracted, result)
        assert not grounded["evidence_found"] and grounded["ambiguities"]
