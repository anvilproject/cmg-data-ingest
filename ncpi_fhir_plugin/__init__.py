__version__ = "0.1.0"

_fhir_server = None

def set_fhir_server(host):
    global _fhir_server

    _fhir_server = host

def get_fhir_server():
    return _fhir_server