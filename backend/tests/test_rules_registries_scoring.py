from pathlib import Path
from types import SimpleNamespace

from app.connectors import GSTConnector, PANConnector, UdyamConnector
from app.services.compliance_engine import ComplianceEngine
from app.services.scoring_service import ScoringService


REGISTRY_DIR = Path(__file__).resolve().parents[1] / "mock_registry"


def requirement(operator, value=None, applicable=True, approved=True, metadata=None):
    return SimpleNamespace(operator=operator, required_value=value, applicable=applicable, approved=approved, rule_metadata=metadata or {})


def evidence(value=None, field="Value", found=True, ambiguities=None):
    return SimpleNamespace(value=value, field=field, evidence_found=found, ambiguities_json=ambiguities or [])


def verification(matched):
    return SimpleNamespace(matched=matched)


def test_mock_gst_pan_and_udyam_verification():
    name = "Bharat Power Control Systems Pvt. Ltd."
    assert GSTConnector(REGISTRY_DIR).lookup("07AACCB5566K1ZP", name)["matched"]
    assert PANConnector(REGISTRY_DIR).lookup("PAN AACCB5566K", name)["matched"]
    assert UdyamConnector(REGISTRY_DIR).lookup("UDYAM-DL-07-0055412", name)["matched"]


def test_entity_mismatch_is_reported():
    result = GSTConnector(REGISTRY_DIR).lookup("07AACCB5566K1ZP", "Another Company")
    assert result["matched"] is False
    assert "Entity mismatch" in result["discrepancies"][0]


def test_threshold_and_missing_evidence_rules():
    engine = ComplianceEngine()
    assert engine.evaluate(requirement("GREATER_THAN_OR_EQUAL", 100), [evidence("125")])["status"] == "COMPLIANT"
    assert engine.evaluate(requirement("GREATER_THAN_OR_EQUAL", 100), [evidence(None, found=False)])["status"] == "NEEDS_REVIEW"


def test_local_content_classification():
    result = ComplianceEngine().evaluate(requirement("LOCAL_CONTENT_CLASSIFICATION", metadata={"class_1_threshold": 50, "class_2_threshold": 20}), [evidence("55%", "local content percentage")])
    assert result["status"] == "COMPLIANT"
    assert "Class 1" in result["reason"]


def test_registry_rule_and_not_applicable():
    engine = ComplianceEngine()
    assert engine.evaluate(requirement("EXACT_IDENTIFIER_MATCH"), [evidence("ABC", "GSTIN")], verification(False))["status"] == "NON_COMPLIANT"
    assert engine.evaluate(requirement("NOT_EXISTS"), [])["status"] == "COMPLIANT"
    assert engine.evaluate(requirement("EXISTS", applicable=False), [])["status"] == "NOT_APPLICABLE"


def test_transparent_score_and_risk():
    checks = [SimpleNamespace(required="MANDATORY", effective_status="COMPLIANT"), SimpleNamespace(required="MANDATORY", effective_status="NON_COMPLIANT")]
    score, risk, overall = ScoringService().calculate(checks)
    assert score == 50
    assert (risk, overall) == ("HIGH", "NON_COMPLIANT")
