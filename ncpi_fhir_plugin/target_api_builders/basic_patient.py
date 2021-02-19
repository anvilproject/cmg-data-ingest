"""
Emerge has a very small demographic footprint. Rather than make the NCPI 
patient more complex, I figure we can just have a baby demo for the 
emerge project 
"""

from ncpi_fhir_plugin.common import constants, CONCEPT
from ncpi_fhir_plugin.shared import join
from ncpi_fhir_plugin.target_api_builders import TargetBase
from ncpi_fhir_plugin.target_api_builders.ncpi_patient import omb_ethnicity_category, omb_race_category, administrative_gender
from colorama import init,Fore,Back,Style
init()

import pdb

class BasicPatient(TargetBase):
    class_name = "basic_patient"
    resource_type = "Patient"
    target_id_concept = CONCEPT.PARTICIPANT.TARGET_SERVICE_ID

    @classmethod
    def get_key_components(cls, record, get_target_id_from_record):
        #pdb.set_trace()
        # These are required for the variant
        assert None is not record[CONCEPT.PARTICIPANT.ID]
        assert None is not record[CONCEPT.STUDY.ID]
        return {
            "identifier":  join(
                record[CONCEPT.STUDY.ID],
                record[CONCEPT.PARTICIPANT.ID]
            )
        }

    @classmethod
    def build_entity(cls, record, get_target_id_from_record):
        key = cls.get_key_components(record, get_target_id_from_record)['identifier']

        study_id = record[CONCEPT.STUDY.ID]
        cls.report(study_id)
        participant_id = record.get(CONCEPT.PARTICIPANT.ID)
        ethnicity = record.get(CONCEPT.PARTICIPANT.ETHNICITY)
        race = record.get(CONCEPT.PARTICIPANT.RACE)
        gender = record.get(CONCEPT.PARTICIPANT.GENDER)
        year_of_birth = record.get(CONCEPT.PARTICIPANT.YEAR_OF_BIRTH)

        unique_id = get_target_id_from_record(BasicPatient, record)
        entity = {
            "resourceType": BasicPatient.resource_type,
            "id": get_target_id_from_record(BasicPatient, record),
            "meta": {
                "profile": [
                    f"http://hl7.org/fhir/StructureDefinition/{BasicPatient.resource_type}"
                ]
            },
            "identifier": [
                {
                    "system": f"https://ncpi-api-dataservice.kidsfirstdrc.org/participants?study_id={study_id}&external_id=",
                    "value": participant_id,
                },
                {
                    "system" : f"{cls.identifier_system}",
                    "value": key,
                }
            ]
        }
 
        if ethnicity:
            if omb_ethnicity_category.get(ethnicity):
                entity.setdefault("extension", []).append(
                    {
                        "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity",
                        "extension": [
                            omb_ethnicity_category[ethnicity],
                            {"url": "text", "valueString": ethnicity},
                        ],
                    }
                )

        if race:
            if omb_race_category.get(race):
                entity.setdefault("extension", []).append(
                    {
                        "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race",
                        "extension": [
                            omb_race_category[race],
                            {"url": "text", "valueString": race},
                        ],
                    }
                )

        if gender:
            if administrative_gender.get(gender):
                entity["gender"] = administrative_gender[gender]

        if year_of_birth:
            entity['birthDate'] = year_of_birth
            
        return entity
