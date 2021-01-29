"""
Builds FHIR Patient resources (https://www.hl7.org/fhir/patient.html) from rows
of tabular participant data.
"""

# These two are slightly modified from the regular kf versions, so we'll use those
# instead of the KF versions
from ncpi_fhir_plugin.common import constants, CONCEPT
from ncpi_fhir_plugin.shared import join
from ncpi_fhir_plugin.target_api_builders import TargetBase

import pdb

# https://hl7.org/fhir/us/core/ValueSet-omb-ethnicity-category.html
omb_ethnicity_category = {
    constants.ETHNICITY.HISPANIC: {
        "url": "ombCategory",
        "valueCoding": {
            "system": "urn:oid:2.16.840.1.113883.6.238",
            "code": "2135-2",
            "display": "Hispanic or Latino",
        },
    },
    constants.ETHNICITY.NON_HISPANIC: {
        "url": "ombCategory",
        "valueCoding": {
            "system": "urn:oid:2.16.840.1.113883.6.238",
            "code": "2186-5",
            "display": "Not Hispanic or Latino",
        },
    },
    constants.COMMON.OTHER: {
        'url': 'http://terminology.hl7.org/CodeSystem/v3-NullFlavor',
        'valueCoding': {
            'system': "http://terminology.hl7.org/CodeSystem/v3-NullFlavor",
            'code': 'OTH',
            'display': 'Other'
        },
    },
    constants.COMMON.UNKNOWN: {
        'url': 'http://terminology.hl7.org/CodeSystem/v3-NullFlavor',
        'valueCoding': {
            'system': "http://terminology.hl7.org/CodeSystem/v3-NullFlavor",
            'code': 'UNK',
            'display': 'Unknown'
        },
    }
}

# https://hl7.org/fhir/us/core/ValueSet-omb-race-category.html
omb_race_category = {
    constants.RACE.NATIVE_AMERICAN: {
        "url": "ombCategory",
        "valueCoding": {
            "system": "urn:oid:2.16.840.1.113883.6.238",
            "code": "1002-5",
            "display": "American Indian or Alaska Native",
        },
    },
    constants.RACE.ASIAN: {
        "url": "ombCategory",
        "valueCoding": {
            "system": "urn:oid:2.16.840.1.113883.6.238",
            "code": "2028-9",
            "display": "Asian",
        },
    },
    constants.RACE.BLACK: {
        "url": "ombCategory",
        "valueCoding": {
            "system": "urn:oid:2.16.840.1.113883.6.238",
            "code": "2054-5",
            "display": "Black or African American",
        },
    },
    constants.RACE.PACIFIC: {
        "url": "ombCategory",
        "valueCoding": {
            "system": "urn:oid:2.16.840.1.113883.6.238",
            "code": "2076-8",
            "display": "Native Hawaiian or Other Pacific Islander",
        },
    },
    constants.RACE.WHITE: {
        "url": "ombCategory",
        "valueCoding": {
            "system": "urn:oid:2.16.840.1.113883.6.238",
            "code": "2106-3",
            "display": "White",
        },
    },
    constants.COMMON.OTHER: {
        'url': 'http://terminology.hl7.org/CodeSystem/v3-NullFlavor',
        'valueCoding': {
            'system': "http://terminology.hl7.org/CodeSystem/v3-NullFlavor",
            'code': 'OTH',
            'display': 'Other'
        },
    },
    constants.COMMON.UNKNOWN: {
        'url': 'http://terminology.hl7.org/CodeSystem/v3-NullFlavor',
        'valueCoding': {
            'system': "http://terminology.hl7.org/CodeSystem/v3-NullFlavor",
            'code': 'UNK',
            'display': 'Unknown'
        },
    },
}

species_dict = {
    constants.SPECIES.DOG: {
        "url": "http://fhir.ncpi-project-forge.io/StructureDefinition/species",
        "valueCodeableConcept": {
            "coding": [
                {
                    "system": "http://fhir.ncpi-project-forge.io/CodeSystem/species",
                    "code": "448771007",
                    "display": "Canis lupus subspecies familiaris",
                }
            ],
            "text": constants.SPECIES.DOG,
        },
    },
    constants.SPECIES.HUMAN: {
        "url": "http://fhir.ncpi-project-forge.io/StructureDefinition/species",
        "valueCodeableConcept": {
            "coding": [
                {
                    "system": "http://fhir.ncpi-project-forge.io/CodeSystem/species",
                    "code": "337915000",
                    "display": "Homo sapiens",
                }
            ],
            "text": constants.SPECIES.HUMAN,
        },
    },
}

# http://hl7.org/fhir/R4/codesystem-administrative-gender.html
administrative_gender = {
    constants.GENDER.MALE: "male",
    constants.GENDER.FEMALE: "female",
    constants.COMMON.OTHER: "other",
    constants.COMMON.UNKNOWN: "unknown",
}


class Patient(TargetBase):
    class_name = "patient"
    resource_type = "Patient"
    target_id_concept = CONCEPT.PARTICIPANT.TARGET_SERVICE_ID

    @classmethod
    def get_key_components(cls, record, get_target_id_from_record):
        # These are required for the variant
        assert None is not record[CONCEPT.PARTICIPANT.ID]

        return {
            "identifier":  join(
                record[CONCEPT.PARTICIPANT.ID]
            )
        }

    @classmethod
    def build_entity(cls, record, get_target_id_from_record):
        key = cls.get_key_components(record, get_target_id_from_record)['identifier']

        study_id = record[CONCEPT.STUDY.NAME]
        participant_id = record.get(CONCEPT.PARTICIPANT.ID)
        ethnicity = record.get(CONCEPT.PARTICIPANT.ETHNICITY)
        race = record.get(CONCEPT.PARTICIPANT.RACE)
        ancestry = race + ":" + record.get(CONCEPT.PARTICIPANT.ANCESTRY_DETAIL)
        species = record.get(CONCEPT.PARTICIPANT.SPECIES)
        gender = record.get(CONCEPT.PARTICIPANT.GENDER)
        dbgap_study_id = record.get(CONCEPT.DBGAP_STUDY_ID)
        dbgap_id = record.get(CONCEPT.DBGAP_ID)
        age_at_last_observation = record.get(CONCEPT.PARTICIPANT.AGE_AT_LAST_OBSERVATION)
        #print(f">>> {get_target_id_from_record}")

        unique_id = get_target_id_from_record(Patient, record)
        entity = {
            "resourceType": Patient.resource_type,
            "id": get_target_id_from_record(Patient, record),
            "meta": {
                "profile": [
                    f"http://hl7.org/fhir/StructureDefinition/{Patient.resource_type}"
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

        if dbgap_id:
            entity["identifier"].append(
                {
                    "system": f"https://dbgap-api.ncbi.nlm.nih.gov/participants?study_id={dbgap_study_id}&external_id=",
                    "value": dbgap_id
                }

            )
 
        if ethnicity:
            if omb_ethnicity_category.get(ethnicity):
                entity.setdefault("extension", []).append(
                    {
                        "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity",
                        "extension": [
                            omb_ethnicity_category[ethnicity],
                            {"url": "text", "valueString": ancestry},
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
                            {"url": "text", "valueString": ancestry},
                        ],
                    }
                )

        if species:
            if species_dict.get(species):
                entity.setdefault("extension", []).append(species_dict[species])

        if gender:
            if administrative_gender.get(gender):
                entity["gender"] = administrative_gender[gender]

        if age_at_last_observation:
            # For now, we'll just use float, but we could switch over to 
            # months if there is a good reason.
            try:
                value = float(age_at_last_observation)
                code = "a"
                display = "years"
            except:
                display = "months"
                code = "mo"
                value = 12 * float(age_at_last_observation)

            entity.setdefault("extension", []).append(
                {
                    "url": "http://fhir.ncpi-project-forge.io/StructureDefinition/age-at-event",
                    "valueAge": {
                        "value": value,
                        "unit": code,
                        "system": "http://unitsofmeasure.org",
                        "code": display,
                    },
                }
            )
            
        return entity
