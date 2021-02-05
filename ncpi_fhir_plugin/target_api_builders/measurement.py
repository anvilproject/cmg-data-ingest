"""
Measurements - These represent clinical observations
"""


from ncpi_fhir_plugin.shared import join, make_identifier
from ncpi_fhir_plugin.common import CONCEPT, constants

from ncpi_fhir_plugin.target_api_builders.basic_patient import BasicPatient
from ncpi_fhir_plugin.target_api_builders import TargetBase

import pdb

class Measurement(TargetBase):
    class_name = "measurement"
    resource_type = "Observation"
    target_id_concept = CONCEPT.STUDY.PROVIDER.SUBJECT.TARGET_SERVICE_ID

    @classmethod
    def get_key_components(cls, record, get_target_id_from_record):
        # These are required for the variant
        assert None is not record[CONCEPT.PARTICIPANT.ID]
        assert None is not record[CONCEPT.STUDY.ID]

        return {
            "identifier":  join(
                record[CONCEPT.STUDY.ID],
                record[CONCEPT.PARTICIPANT.ID],
                record[CONCEPT.PARTICIPANT.VISIT_NUMBER],
                record[CONCEPT.PARTICIPANT.MEASUREMENT.CODE]
            )
        }

    @classmethod
    def build_entity(cls, record, get_target_id_from_record):
        key = cls.get_key_components(record, get_target_id_from_record)['identifier']
        study_name = record[CONCEPT.STUDY.ID]
        cls.report(study_name)
        visit_number = record[CONCEPT.PARTICIPANT.VISIT_NUMBER]
        measurement = record[CONCEPT.PARTICIPANT.MEASUREMENT.ID]
        units = record[CONCEPT.PARTICIPANT.MEASUREMENT.UNITS]
        measurement_code = record[CONCEPT.PARTICIPANT.MEASUREMENT.CODE]
        measurement_name = record[CONCEPT.PARTICIPANT.MEASUREMENT.NAME]
        derived_from = record[CONCEPT.PARTICIPANT.MEASUREMENT.DERIVED_FROM]

        age_at_obs = record[CONCEPT.PARTICIPANT.AGE_AT_EVENT]

        # We can append codes other than LOINC 
        alt_codes = record[CONCEPT.PARTICIPANT.MEASUREMENT.ALT_CODES]

        entity = {
            "resourceType": Measurement.resource_type,
            "id": get_target_id_from_record(Measurement, record),
            "meta": {
                "profile": [
                     f"http://hl7.org/fhir/StructureDefinition/{Measurement.resource_type}"
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
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": measurement_code,
                        "display": measurement_name
                    }
                ],
                "text": f"{measurement_name}"
            },
            "subject": {
                "reference": f"Patient/{get_target_id_from_record(BasicPatient, record)}"
            },

            "valueQuantity": {
                "value" : float(measurement),
                "unit" : units
            }
        }

        for code in alt_codes.split("|"):
            system, code = code.split("^^")

            entity['code']['coding'].append(
                {
                    "system": system,
                    "code": code,
                    "display": measurement_name
                }
            )

        if visit_number:
            entity.setdefault("extension", []).append(
                {
                    "url": "http://fhir.ncpi-project-forge.io/StructureDefinition/visit-number",
                    "valueInteger":  int(visit_number)
                })

        if age_at_obs:
            entity.setdefault("extension", []).append(
                {
                    "url": "http://fhir.ncpi-project-forge.io/StructureDefinition/age-at-event",
                    "valueAge": {
                        "value": float(age_at_obs),
                        "unit": "a",
                        "system": "http://unitsofmeasure.org",
                        "code": "years",
                    }
                }
            )

        other_ids = []

        if derived_from:
            #pdb.set_trace()
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
                #print(fake_row)
                other_id = get_target_id_from_record(Measurement, fake_row)
                #print(other_id)
                if other_id:
                    other_ids.append(other_id)
                    derived_refs.append({
                        'reference': f"Observation/{other_id}"
                    })


            if len(derived_refs) > 0:
                entity['derivedFrom'] = derived_refs

        #print(f"{record[CONCEPT.PARTICIPANT.ID]} {measurement_name} {measurement_code}@{visit_number} :: {','.join(other_ids)} ")
        return entity

