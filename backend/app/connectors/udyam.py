from .base import RegistryConnector


class UdyamConnector(RegistryConnector):
    source, filename, identifier_field = "UDYAM", "udyam.json", "udyam_number"
