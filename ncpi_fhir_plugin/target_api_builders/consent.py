"""
Builds the FHIR representation for groups 
"""
from ncpi_fhir_plugin.target_api_builders import TargetBase
from ncpi_fhir_plugin.shared import join, make_identifier
from ncpi_fhir_plugin.common import constants, CONCEPT
from ncpi_fhir_plugin.target_api_builders.ncpi_patient import Patient
from copy import deepcopy

import pdb

class Consent(TargetBase):
    class_name = "consent"
    resource_type = "Consent"
    target_id_concept = CONCEPT.STUDY.GROUP.CONSENT_NAME


    @classmethod
    def get_key_components(cls, record, get_target_id_from_record):
        # These are required for the consent object

        assert None is not record[CONCEPT.STUDY.NAME]
        assert None is not record[CONCEPT.STUDY.GROUP.CONSENT_NAME] and record[CONCEPT.STUDY.GROUP.CONSENT_NAME].strip() != ""

        return {
            "identifier": join(
                record[CONCEPT.STUDY.NAME],
                record[CONCEPT.STUDY.GROUP.CONSENT_NAME]
            )
        }
    @classmethod
    def build_entity(cls, record, get_target_id_from_record):
        key = cls.get_key_components(record, get_target_id_from_record)['identifier']
        study_name = record[CONCEPT.STUDY.NAME]
        consent_name = record[CONCEPT.STUDY.GROUP.CONSENT_NAME]
        group_url = record[CONCEPT.STUDY.GROUP.URL]

        if consent_name == "":
            pdb.set_trace()

        entity = {
            "resourceType": cls.resource_type,
            "id": get_target_id_from_record(cls, record),
            "identifier": [
                {
                    "system": group_url,
                    "value": consent_name
                },
                {
                    "system" : f"{cls.identifier_system}",
                    "value": key,
                }
            ],
            "status": "inactive",
            "scope": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/consentscope",
                    "code": "research"
                }],
                "text": "Research"
            },
            "category": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/consentcategorycodes",
                    "code": "rsdid"
                }],
                "text": "rsdid"
            }],
            "policyRule": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/consentpolicycodes",
                    "code": "hipaa-research"
                }],
                "text": "Research"
            }
        }

        return entity
