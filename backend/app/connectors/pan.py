import re

from .base import RegistryConnector


class PANConnector(RegistryConnector):
    source, filename, identifier_field = "PAN", "pan.json", "pan"

    @staticmethod
    def _normalize_identifier(value: str) -> str:
        match = re.search(r"[A-Z]{5}\d{4}[A-Z]", value.upper())
        return match.group(0) if match else RegistryConnector._normalize_identifier(value)
