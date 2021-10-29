"""
Measurements - These represent clinical observations
"""


from ncpi_fhir_plugin.shared import join, make_identifier
from ncpi_fhir_plugin.common import CONCEPT, constants

from ncpi_fhir_plugin.target_api_builders.ncpi_patient import Patient
from ncpi_fhir_plugin.target_api_builders import TargetBase

import pdb

class Encounter(TargetBase):
    class_name = "encounter"
    resource_type = "Encounter"
    target_id_concept = CONCEPT.PARTICIPANT.TARGET_SERVICE_ID

    @classmethod
    def get_key_components(cls, record, get_target_id_from_record):
        # These are required for the variant
        assert None is not record[CONCEPT.PARTICIPANT.ID]
        assert None is not record[CONCEPT.STUDY.NAME]
        assert None is not record[CONCEPT.PARTICIPANT.VISIT_NUMBER]

        return {
            "identifier":  join(
                record[CONCEPT.STUDY.NAME],
                record[CONCEPT.PARTICIPANT.ID],
                record[CONCEPT.PARTICIPANT.VISIT_NUMBER]
            )
        }

    @classmethod
    def build_entity(cls, record, get_target_id_from_record):
        key = cls.get_key_components(record, get_target_id_from_record)['identifier']
        study_name = record[CONCEPT.STUDY.NAME]
        cls.report(study_name)
        visit_id = record[CONCEPT.PARTICIPANT.VISIT_NUMBER]

        patient_id=get_target_id_from_record(Patient, record)
        if patient_id is None:
            pdb.set_trace()

        age_at_obs = record[CONCEPT.PARTICIPANT.AGE_AT_EVENT]

        entity = {
            "resourceType": Encounter.resource_type,
            "id": get_target_id_from_record(Encounter, record),
            "meta": {
                "profile": [
                     f"http://hl7.org/fhir/StructureDefinition/{Encounter.resource_type}"
                ]
            },
            "identifier": [
                {
                    "system" : f"{cls.identifier_system}",
                    "value": key,
                }
            ],
            "status": "finished",
            "class":     {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "AMB",
                "display": "Ambulatory"
            },
            "subject": {
                "reference": f"Patient/{get_target_id_from_record(Patient, record)}"
            },

        }


        """
        relationship has to be from: http://hl7.org/fhir/R4/valueset-action-relationship-type.html
        """
        if age_at_obs:
            entity['period'] = {
                "_start" :  {
                    "extension": [
                        {
                            "url": "http://hl7.org/fhir/StructureDefinition/cqf-relativeDateTime",
                            "extension": [{
                                    "url": "target",
                                    "valueReference": {
                                        "reference": f"Patient/{get_target_id_from_record(Patient, record)}"
                                    }
                                }, {
                                    "url": "targetPath",
                                    "valueString": "birthDate"
                                }, {
                                    "url": "relationship",
                                    "valueCode":  "after" 
                                }, {
                                    "url": "offset",
                                    "valueDuration": {
                                        "value": float(age_at_obs),
                                        "unit": "a",
                                        "system": "http://unitsofmeasure.org",
                                        "code": "years"
                                }

                            }]
                        }
                    ]
                }
            }
        return entity

