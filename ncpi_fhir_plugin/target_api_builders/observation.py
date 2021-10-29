"""
Observation - These represent basic observations
"""


from ncpi_fhir_plugin.shared import join, make_identifier
from ncpi_fhir_plugin.common import CONCEPT, constants

from ncpi_fhir_plugin.target_api_builders.ncpi_patient import Patient
from ncpi_fhir_plugin.target_api_builders import TargetBase
from ncpi_fhir_plugin.target_api_builders.encounter import Encounter

import pdb

class Observation(TargetBase):
    class_name = "observation"
    resource_type = "Observation"
    target_id_concept = CONCEPT.STUDY.PROVIDER.SUBJECT.TARGET_SERVICE_ID

    @classmethod
    def get_key_components(cls, record, get_target_id_from_record):
        #pdb.set_trace()
        # These are required for the variant
        assert None is not record[CONCEPT.PARTICIPANT.ID]
        assert None is not record[CONCEPT.STUDY.NAME]
        assert None is not record[CONCEPT.PARTICIPANT.OBSERVATION.ID]

        return {
            "identifier":  join(
                record[CONCEPT.STUDY.NAME],
                record[CONCEPT.PARTICIPANT.ID],
                record[CONCEPT.PARTICIPANT.OBSERVATION.ID]
            )
        }

    @classmethod
    def build_entity(cls, record, get_target_id_from_record):
        key = cls.get_key_components(record, get_target_id_from_record)['identifier']
        study_name = record[CONCEPT.STUDY.NAME]
        cls.report(study_name)
        observation_id = record.get(CONCEPT.PARTICIPANT.OBSERVATION.ID)
        observation_name = record.get(CONCEPT.PARTICIPANT.OBSERVATION.NAME)
        observation_system = record.get(CONCEPT.PARTICIPANT.OBSERVATION.SYSTEM)
        observation_desc = record.get(CONCEPT.PARTICIPANT.OBSERVATION.DESCRIPTION)
        observation_value = record.get(CONCEPT.PARTICIPANT.OBSERVATION.VALUE)
        #visit_id = record.get(CONCEPT.PARTICIPANT.VISIT_NUMBER)
        derived_from = record.get(CONCEPT.PARTICIPANT.MEASUREMENT.DERIVED_FROM)

        patient_id=get_target_id_from_record(Patient, record)
        if patient_id is None:
            pdb.set_trace()

        if observation_desc is None or observation_desc.strip() == '':
            observation_desc = observation_name

        age_at_obs = record.get(CONCEPT.PARTICIPANT.AGE_AT_EVENT)

        entity = {
            "resourceType": Observation.resource_type,
            "id": get_target_id_from_record(Observation, record),
            "meta": {
                "profile": [
                     f"http://hl7.org/fhir/StructureDefinition/{Observation.resource_type}"
                ]
            },
            "identifier": [
                {
                    "system" : f"{cls.identifier_system}",
                    "value": key,
                }
            ],
            "status": "final",
            "code":     {
                "text": f"{observation_desc}"
            },
            "subject": {
                "reference": f"Patient/{get_target_id_from_record(Patient, record)}"
            },

        }

        if observation_value is not None:
            entity['valueString'] = observation_value

        # We may actually have a true coding to work with...
        if observation_system is not None and observation_system.strip() != "":
            entity['code']['coding'] = [
                {
                    "system": observation_system,
                    "code": observation_id,
                    "display": observation_name
                }
            ]

        """if visit_id:
            entity['encounter'] = {
                "reference": f"Encounter/{get_target_id_from_record(Encounter, record)}"
            }
        """

        """
        relationship has to be from: http://hl7.org/fhir/R4/valueset-action-relationship-type.html
        """
        if age_at_obs:
            entity['_effectiveDateTime'] = {
                    "extension": [
                        {
                            "url": "http://hl7.org/fhir/StructureDefinition/cqf-relativeDateTime",
                            "extension": [{
                                    "url": "target",
                                    "valueReference": {
                                        "reference": f"Patient/{get_target_id_from_record(BasicPatient, record)}"
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

        other_ids = []

        if derived_from:
            # We should be able to handle spotty parents, but also skip it
            # altogether if they simply don't exist
            derived_refs = []
            for other in derived_from.split("|"):
                fake_row = {
                    CONCEPT.STUDY.ID: study_name,
                    CONCEPT.PARTICIPANT.ID: record[CONCEPT.PARTICIPANT.ID],
                    CONCEPT.PARTICIPANT.VISIT_NUMBER: visit_number,
                    CONCEPT.PARTICIPANT.MEASUREMENT.CODE: other             
                }
                other_id = get_target_id_from_record(Measurement, fake_row)
                if other_id:
                    other_ids.append(other_id)
                    derived_refs.append({
                        'reference': f"Observation/{other_id}"
                    })


            if len(derived_refs) > 0:
                entity['derivedFrom'] = derived_refs

        return entity

