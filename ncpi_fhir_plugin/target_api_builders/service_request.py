"""
In our context, ServiceRequests are used to associate a specimen to a "visit" (encounter)
"""


from ncpi_fhir_plugin.shared import join, make_identifier
from ncpi_fhir_plugin.common import CONCEPT, constants

from ncpi_fhir_plugin.target_api_builders.ncpi_patient import Patient
from ncpi_fhir_plugin.target_api_builders import TargetBase
from ncpi_fhir_plugin.target_api_builders.specimen import Specimen
from ncpi_fhir_plugin.target_api_builders.encounter import Encounter

import pdb

class ServiceRequest(TargetBase):
    class_name = "service_request"
    resource_type = "ServiceRequest"
    target_id_concept = CONCEPT.STUDY.PROVIDER.SUBJECT.TARGET_SERVICE_ID

    @classmethod
    def get_key_components(cls, record, get_target_id_from_record):
        # These are required for the variant
        assert None is not record[CONCEPT.PARTICIPANT.ID]
        assert None is not record[CONCEPT.STUDY.NAME]
        assert None is not record[CONCEPT.PARTICIPANT.VISIT_NUMBER]
        assert None is not record[CONCEPT.BIOSPECIMEN.ID]

        return {
            "identifier":  join(
                record[CONCEPT.STUDY.NAME],
                record[CONCEPT.PARTICIPANT.ID],
                record[CONCEPT.PARTICIPANT.VISIT_NUMBER],
                record[CONCEPT.BIOSPECIMEN.ID]
            )
        }

    @classmethod
    def build_entity(cls, record, get_target_id_from_record):
        key = cls.get_key_components(record, get_target_id_from_record)['identifier']
        study_name = record[CONCEPT.STUDY.NAME]
        cls.report(study_name)
        visit_number = record[CONCEPT.PARTICIPANT.VISIT_NUMBER]
        biospecimen_id = record.get(CONCEPT.BIOSPECIMEN.ID)

        patient_id=get_target_id_from_record(Patient, record)
        if patient_id is None:
            pdb.set_trace()

        age_at_obs = record[CONCEPT.PARTICIPANT.AGE_AT_EVENT]

        entity = {
            "resourceType": ServiceRequest.resource_type,
            "id": get_target_id_from_record(ServiceRequest, record),
            "identifier": [
                {
                    "system" : f"{cls.identifier_system}",
                    "value": key,
                }
            ],
            "status": "completed",
            "intent": "order",
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": '108252007',
                            "display": "Laboratory procedure"
                        }
                    ],
                    "text": "Draw Biospecimen"
                }
            ],
            "subject": {
                "reference": f"Patient/{get_target_id_from_record(Patient, record)}"
            },
            "encounter": {
                "reference": f"Encounter/{get_target_id_from_record(Encounter, record)}"
            },
            "specimen": [ 
                {
                    "reference": f"Specimen/{get_target_id_from_record(Specimen, record)}"
                }
            ]
        }



        return entity

