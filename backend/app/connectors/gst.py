from .base import RegistryConnector


class GSTConnector(RegistryConnector):
    source, filename, identifier_field = "GST", "gst.json", "gstin"
