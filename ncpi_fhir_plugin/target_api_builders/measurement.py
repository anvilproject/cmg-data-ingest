"""
Measurements - These represent clinical observations
"""


from ncpi_fhir_plugin.shared import join, make_identifier
from ncpi_fhir_plugin.common import CONCEPT, constants

from ncpi_fhir_plugin.target_api_builders.ncpi_patient import Patient
from ncpi_fhir_plugin.target_api_builders import TargetBase
from ncpi_fhir_plugin.target_api_builders.encounter import Encounter

import pdb

class Measurement(TargetBase):
    class_name = "measurement"
    resource_type = "Observation"
    target_id_concept = CONCEPT.STUDY.PROVIDER.SUBJECT.TARGET_SERVICE_ID

    @classmethod
    def get_key_components(cls, record, get_target_id_from_record):
        # These are required for the variant
        assert None is not record[CONCEPT.PARTICIPANT.ID]
        assert None is not record[CONCEPT.STUDY.NAME]

        return {
            "identifier":  join(
                record[CONCEPT.STUDY.NAME],
                record[CONCEPT.PARTICIPANT.ID],
                record[CONCEPT.PARTICIPANT.VISIT_NUMBER],
                record[CONCEPT.PARTICIPANT.MEASUREMENT.CODE]
            )
        }

    @classmethod
    def build_entity(cls, record, get_target_id_from_record):
        key = cls.get_key_components(record, get_target_id_from_record)['identifier']
        study_name = record[CONCEPT.STUDY.NAME]
        cls.report(study_name)
        visit_number = record[CONCEPT.PARTICIPANT.VISIT_NUMBER]
        measurement = record[CONCEPT.PARTICIPANT.MEASUREMENT.ID]
        units = record[CONCEPT.PARTICIPANT.MEASUREMENT.UNITS]
        units_system = record[CONCEPT.PARTICIPANT.MEASUREMENT.UNITS_SYSTEM]
        measurement_code = record[CONCEPT.PARTICIPANT.MEASUREMENT.CODE]
        measurement_name = record[CONCEPT.PARTICIPANT.MEASUREMENT.NAME]
        derived_from = record[CONCEPT.PARTICIPANT.MEASUREMENT.DERIVED_FROM]
        measurement_desc = record.get(CONCEPT.PARTICIPANT.MEASUREMENT.DESC)

        patient_id=get_target_id_from_record(Patient, record)
        if patient_id is None:
            pdb.set_trace()

        if measurement == 'NA':
            print("We have encountered NA for a measurement value. This should be mapped to None or whatever is suitable for the consortium preferences.")
            pdb.set_trace()
        if measurement_desc is None or measurement_desc.strip() == '':
            measurement_desc = measurement_name

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
                    "value": key
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
                "text": f"{measurement_desc}"
            },
            "subject": {
                "reference": f"Patient/{get_target_id_from_record(Patient, record)}"
            },

            "valueQuantity": {
                "value" : float(measurement),
                "unit" : units,
                "system": units_system
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
            encid = get_target_id_from_record(Encounter, record)
            if encid is None:
                pdb.set_trace()
            entity['encounter'] = {
                "reference": f"Encounter/{encid}"
            }

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
                                        "unit": "years",
                                        "system": "http://unitsofmeasure.org",
                                        "code": "a"
                                }

                            }]
                        }
                    ]
                }
            """
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
            """

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

