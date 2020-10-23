"""
This module is translated into an instance of
kf_lib_data_ingest.etl.configuration.target_api_config.TargetAPIConfig which is
used by the Kids First Ingest Library's load stage to populate instances of
target model entities (i.e. participants, diagnoses, etc) with data from the
extracted concepts before those instances are loaded into the target service.

Reference: https://github.com/kids-first/kf-lib-data-ingest

See docstrings in kf_lib_data_ingest.etl.configuration.target_api_config for
more details on the requirements for format and content.
"""
import inspect 

import os
from pprint import pformat

from requests import RequestException

from ncpi_fhir_utility.client import FhirApiClient

from ncpi_fhir_plugin.target_api_builders.ncpi_patient import Patient
from ncpi_fhir_plugin.target_api_builders.research_subject import ResearchSubject
from ncpi_fhir_plugin.target_api_builders.research_study import ResearchStudy
from ncpi_fhir_plugin.target_api_builders.patient_relationship import PatientRelation
from ncpi_fhir_plugin.target_api_builders.specimen import Specimen 
from ncpi_fhir_plugin.target_api_builders.disease import Disease
from ncpi_fhir_plugin.target_api_builders.hpo_observation import HumanPhenotype
from ncpi_fhir_plugin.target_api_builders.tissue_affected_status import TissueAffectedStatus 
from ncpi_fhir_plugin.target_api_builders.sequencing_center import SequencingCenter
from ncpi_fhir_plugin.target_api_builders.sequencing_file import SequencingFile
from ncpi_fhir_plugin.target_api_builders.sequencing_task import SequencingTask 
from ncpi_fhir_plugin.target_api_builders.sequencing_file_info import SequencingFileInfo
from ncpi_fhir_plugin import common

from fhir_walk.fhir_host import FhirHost

import traceback

all_targets = [
    Patient,
    PatientRelation,
    ResearchStudy,
    ResearchSubject,
    SequencingCenter,
    Specimen,
    Disease,
    HumanPhenotype,
    TissueAffectedStatus,
    SequencingFile,
    SequencingTask,
    SequencingFileInfo 
]
#print(inspect.getsource(Patient.build_entity))
clients = {}

def submit(host, entity_class, body):
    global fhir_server
    #print(fhir_server)
    # default to...dev environment
    fhir_server = FhirHost.host()

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

    # print(cheaders)

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
