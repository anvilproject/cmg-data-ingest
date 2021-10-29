from fhir_walk.fhir_host import FhirHost
from fhirwood.identifier import Identifier
from pprint import pformat
from requests import RequestException
from ncpi_fhir_plugin import get_fhir_server
import sys
import pdb 
from colorama import init,Fore,Back,Style
init()



clients = {}
def submit(host, entity_class, body):
    fhir_server = get_fhir_server()
    clients[host] = clients.get(host) or fhir_server.client()

    # drop empty fields
    body = {k: v for k, v in body.items() if v not in (None, [], {})}

    headers = {}
    verb = "POST"
    api_path = f"{host}/{entity_class.resource_type}"
    if "id" in body:
        verb = "PUT"
        api_path = f"{api_path}/{body['id']}"

    if verb == "PATCH":
        # If we start trying to patch, then we need to look at making
        # sure the default content type doesn't clobber this one
        headers["Content-Type"] = cheaders["Content-Type"].replace(
            "application/fhir", "application/json-patch"
        )
    #pdb.set_trace()
    success, result = fhir_server.send_request(
        verb, api_path, body=body, headers=headers
    )

    if (
        (not success)
        and (verb == "PUT")
        and (
            "no resource with this ID exists"
            in result.get("response", {})
            .get("issue", [{}])[0]
            .get("diagnostics", "")
        )
    ):
        verb = "POST"
        api_path = f"{host}/{entity_class.resource_type}"
        success, result = fhir_server.send_request(
            verb, api_path, body=body, headers=headers
        )

    if success:
        return result["response"]["id"]
    else:
        print(pformat(body))
        raise RequestException(
            f"Sent {verb} request to {api_path}:\n{pformat(body)}"
            f"\nGot:\n{pformat(result)}"
        )
def submit_(host, entity_class, body):
    global fhir_server

    # default to...dev environment
    fhir_server = get_fhir_server()   #FhirHost.host()

    clients[host] = clients.get(host) or fhir_server.client()

    # drop empty fields
    body = {k: v for k, v in body.items() if v not in (None, [], {})}

    verb = "POST"
    api_path = f"{host}/{entity_class.resource_type}"
    if "id" in body:
        verb = "PUT"
        api_path = f"{api_path}/{body['id']}"

    cheaders = clients[host]._fhir_version_headers()
    if verb == "PATCH":
        cheaders["Content-Type"] = cheaders["Content-Type"].replace(
            "application/fhir", "application/json-patch"
        )

    if fhir_server.cookie:
        cheaders['cookie'] = fhir_server.cookie

    if fhir_server.google_identity:
        cheaders['Authorization'] = fhir_server.get_google_identity()

    pdb.set_trace()
    success, result = clients[host].send_request(
        verb, api_path, json=body, headers=cheaders
    )

    if (
        (not success)
        and (verb == "PUT")
        and (
            "no resource with this ID exists"
            in result.get("response", {})
            .get("issue", [{}])[0]
            .get("diagnostics", "")
        )
    ):
        verb = "POST"
        api_path = f"{host}/{entity_class.resource_type}"
        success, result = clients[host].send_request(
            verb, api_path, json=body, headers=cheaders
        )

    if success:
        return result["response"]["id"]
    else:
        print(pformat(body))
        raise RequestException(
            f"Sent {verb} request to {api_path}:\n{pformat(body)}"
            f"\nGot:\n{pformat(result)}"
        )


def addReference(value_name, value_ref):
    return {
        "type": {
            "text": value_name
        },
        "valueReference": {
            "reference": value_ref
        }
    }

def addValuestring(value_name, value):
    return {
                "type": {
                    "text": value_name
                },
                "valueString": value
            }        
def addValuebool(value_name, value):
    return {
                "type": {
                    "text": value_name
                },
                "valueBoolean": value
            }

def drop_none(body):
    return {k: v for k, v in body.items() if v is not None}


def not_none(val):
    assert val is not None
    return val

class TargetBase:   
    identifier_system = "urn:ncpi:unique-string"
    _reported_work = False

    @classmethod
    def query_target_ids(cls, host, key_components):
        #pdb.set_trace()
        ## We don't really need the host, because we keep that with our singleton server object
        host = host.strip("/")
        endpoint = cls.resource_type.strip("/")

        fhir_server = get_fhir_server()   #FhirHost.host()

        url = f"{endpoint}?identifier={cls.identifier_system}|{key_components['identifier']}"
        #pdb.set_trace()
        payload = fhir_server.get(url)

        id_list = set()

        for entity in payload.entries:
            if 'resource' in entity:
                id = entity['resource']['id']
                id_list.add(id)
        return list(id_list)

    @classmethod
    def submit(cls, host, body):
        return submit(host, cls, body)

    @classmethod
    def report(cls, study):
        if not cls._reported_work:
            sys.stderr.write(f"Processing {Fore.CYAN}{study}{Fore.RESET} -- {Fore.GREEN}{cls.__name__}{Fore.RESET}")
            cls._reported_work = True


    """ I think this will remain as is 
    @classmethod
    def build_entity(cls, record, get_target_id_from_record):
        return {
            **cls.get_key_components(record, get_target_id_from_record),
            **cls.get_secondary_components(record, get_target_id_from_record)
        }
    """

class Component:
    def addValuestring(value_name, value):
        return {
                    "code": {
                        "text": value_name
                    },
                    "valueString": value
                }        
    def addValuebool(value_name, value):
        return {
                    "code": {
                        "text": value_name
                    },
                    "valueBoolean": value
                }