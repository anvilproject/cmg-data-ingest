"""
Adds family relationship links between Patient resources from rows of tabular
participant family data.
"""
import pandas as pd

from ncpi_fhir_plugin.common import constants, CONCEPT, add_family_encoding, DEGENDERFICATION
from ncpi_fhir_plugin.shared import join, make_identifier
from ncpi_fhir_plugin.target_api_builders.ncpi_patient import Patient
from ncpi_fhir_plugin.target_api_builders import TargetBase

import pdb

class PatientRelation(TargetBase):
    class_name = "family_relationship"
    resource_type = "Observation"
    target_id_concept = CONCEPT.FAMILY_RELATIONSHIP.TARGET_SERVICE_ID

    @classmethod
    def get_key_components(cls, record, get_target_id_from_record):
        # These are required for the variant
        assert None is not record[CONCEPT.PARTICIPANT.ID]
        assert None is not record[CONCEPT.PARTICIPANT.RELATIONSHIP_TO_PROBAND]
        assert record[CONCEPT.PARTICIPANT.RELATIONSHIP_TO_PROBAND].strip() != ""
        assert None is not record[CONCEPT.PARTICIPANT.PROBAND_ID]
        assert record[CONCEPT.PARTICIPANT.PROBAND_ID].strip() != ""
        assert None is not record[CONCEPT.STUDY.NAME]
        assert record[CONCEPT.PARTICIPANT.ID] != record[CONCEPT.PARTICIPANT.PROBAND_ID]

        return {
            "identifier":  join(
                record[CONCEPT.STUDY.NAME],
                record[CONCEPT.PARTICIPANT.ID],
                record[CONCEPT.PARTICIPANT.RELATIONSHIP_TO_PROBAND],
                'to',
                record[CONCEPT.PARTICIPANT.PROBAND_ID]
            )
        }

    @classmethod
    def build_entity(cls, record, get_target_id_from_record):
        key = cls.get_key_components(record, get_target_id_from_record)['identifier']
        participant_id = record.get(CONCEPT.PARTICIPANT.ID)
        relationship = record.get(CONCEPT.PARTICIPANT.RELATIONSHIP_TO_PROBAND)
        relationship_raw = record.get(CONCEPT.PARTICIPANT.RELATIONSHIP_TO_PROBAND_RAW)
        proband = record.get(CONCEPT.PARTICIPANT.PROBAND_ID)
        study_id = record[CONCEPT.STUDY.NAME]

        proband_record = {
            CONCEPT.PARTICIPANT.ID: record[CONCEPT.PARTICIPANT.PROBAND_ID],
            CONCEPT.STUDY.NAME: record[CONCEPT.STUDY.NAME]
        }
        proband_id = get_target_id_from_record(Patient, proband_record)

        rel_struct = [add_family_encoding(relationship)]

        # Add in the gender neutral terms
        if relationship in DEGENDERFICATION:
            rel_struct = [add_family_encoding(DEGENDERFICATION[relationship]), rel_struct[0]]


        # Are patients limited to a single institution?
        # institution = record[CONCEPT.STUDY.PROVIDER.ID]

        entity = {
            "resourceType": PatientRelation.resource_type,
            "id": get_target_id_from_record(PatientRelation, record),
            "meta": {
                "profile": [
                    f"{constants.NCPI_DOMAIN}/ncpi-fhir-ig/StructureDefinition/family-relationship"
                ]
            },
            "identifier": [
                {
                    "system" : f"{cls.identifier_system}",
                    "value": key
                }
            ],
            "code": {
                "coding": [
                  {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
                    "code": "FAMMEMB",
                    "display": "family member"
                  }
                ],
                "text": "Family Relationship"
            },
            "status": "final",
            "subject" : {'reference': f"{Patient.resource_type}/{get_target_id_from_record(Patient, record)}"},
            "focus" : [{'reference' : f"{Patient.resource_type}/{proband_id}"}],
            "valueCodeableConcept": {
                "coding": rel_struct,
                "text": relationship_raw
            }
        }

        return entity
