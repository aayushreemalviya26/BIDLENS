from .base import RegistryConnector


class StartupConnector(RegistryConnector):
    source, filename, identifier_field = "STARTUP", "startup.json", "recognition_number"
