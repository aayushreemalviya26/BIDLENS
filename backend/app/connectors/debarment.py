from .base import RegistryConnector


class DebarmentConnector(RegistryConnector):
    source, filename, identifier_field = "DEBARMENT", "debarment.json", "identifier"

    def lookup(self, identifier: str, bidder_name: str | None = None) -> dict:
        result = super().lookup(identifier, None)
        if result["registry_record"] and str(result["registry_record"].get("status", "")).upper() in {"ACTIVE", "LISTED", "DEBARRED"}:
            result.update(status="LISTED", matched=False, discrepancies=["Entity appears in the simulated debarment registry"])
        else:
            result.update(status="CLEAR", matched=True, discrepancies=[])
        return result
