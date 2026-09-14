from .base import RegistryConnector


class MCAConnector(RegistryConnector):
    source, filename, identifier_field = "MCA", "mca.json", "cin"
