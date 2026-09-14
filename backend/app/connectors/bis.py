from .base import RegistryConnector


class BISConnector(RegistryConnector):
    source, filename, identifier_field = "BIS", "bis.json", "license_number"
