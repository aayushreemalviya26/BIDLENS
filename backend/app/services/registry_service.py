from sqlalchemy.orm import Session

from app.connectors import BISConnector, DebarmentConnector, GSTConnector, MCAConnector, PANConnector, StartupConnector, UdyamConnector
from app.models import RegistryVerification


class RegistryService:
    CONNECTORS = {"GST": GSTConnector, "PAN": PANConnector, "UDYAM": UdyamConnector, "BIS": BISConnector, "STARTUP": StartupConnector, "DEBARMENT": DebarmentConnector, "MCA": MCAConnector}
    FIELD_SOURCES = {"gstin": "GST", "pan": "PAN", "udyam": "UDYAM", "bis": "BIS", "license": "BIS", "recognition": "STARTUP", "cin": "MCA"}

    def __init__(self, registry_dir=None):
        self.registry_dir = registry_dir

    def verify_evidence(self, db: Session, bidder, evidence: list) -> list[RegistryVerification]:
        db.query(RegistryVerification).filter_by(bidder_id=bidder.id).delete()
        created = []
        seen = set()
        for item in evidence:
            field = (item.field or "").casefold()
            source = next((value for token, value in self.FIELD_SOURCES.items() if token in field), None)
            if not source or not item.value:
                continue
            key = (source, self.CONNECTORS[source]._normalize_identifier(str(item.value)))
            if key in seen:
                continue
            seen.add(key)
            result = self.CONNECTORS[source](self.registry_dir).lookup(item.value, bidder.bidder_name)
            row = RegistryVerification(bidder_id=bidder.id, source=result["source"], identifier=result["identifier"], status=result["status"], matched=result["matched"], registry_record_json=result["registry_record"], discrepancies_json=result["discrepancies"])
            db.add(row)
            created.append(row)
        # Debarment is an entity-level due-diligence lookup, not an identifier
        # extracted from a certificate. Run it for every bidder without making
        # an absent tender requirement applicable to compliance scoring.
        result = self.CONNECTORS["DEBARMENT"](self.registry_dir).lookup(bidder.bidder_name, bidder.bidder_name)
        row = RegistryVerification(
            bidder_id=bidder.id,
            source=result["source"],
            identifier=result["identifier"],
            status=result["status"],
            matched=result["matched"],
            registry_record_json=result["registry_record"],
            discrepancies_json=result["discrepancies"],
        )
        db.add(row)
        created.append(row)
        db.flush()
        return created
