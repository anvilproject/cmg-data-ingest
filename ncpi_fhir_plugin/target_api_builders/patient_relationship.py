"""
Adds family relationship links between Patient resources from rows of tabular
participant family data.
"""
import pandas as pd

from ncpi_fhir_plugin.common import constants, CONCEPT, add_family_encoding, DEGENDERFICATION
from ncpi_fhir_plugin.shared import join, make_identifier
from ncpi_fhir_plugin.target_api_builders.ncpi_patient import Patient

import pdb

class PatientRelation:
    class_name = "family_relationship"
    resource_type = "Observation"
    target_id_concept = CONCEPT.FAMILY_RELATIONSHIP.TARGET_SERVICE_ID

    @staticmethod
    def build_key(record):
        assert None is not record[CONCEPT.PARTICIPANT.ID]
        assert None is not record[CONCEPT.PARTICIPANT.RELATIONSHIP_TO_PROBAND]
        assert record[CONCEPT.PARTICIPANT.RELATIONSHIP_TO_PROBAND].strip() != ""
        assert None is not record[CONCEPT.PARTICIPANT.PROBAND_ID]
        assert record[CONCEPT.PARTICIPANT.PROBAND_ID].strip() != ""
        assert None is not record[CONCEPT.STUDY.ID]
        assert record[CONCEPT.PARTICIPANT.ID] != record[CONCEPT.PARTICIPANT.PROBAND_ID]

        return join(
            record[CONCEPT.STUDY.ID],
            record[CONCEPT.PARTICIPANT.ID],
            record[CONCEPT.PARTICIPANT.RELATIONSHIP_TO_PROBAND],
            record[CONCEPT.PARTICIPANT.PROBAND_ID]
        )

    @staticmethod
    def build_entity(record, key, get_target_id_from_record):
        participant_id = record.get(CONCEPT.PARTICIPANT.ID)
        relationship = record.get(CONCEPT.PARTICIPANT.RELATIONSHIP_TO_PROBAND)
        relationship_raw = record.get(CONCEPT.PARTICIPANT.RELATIONSHIP_TO_PROBAND_RAW)
        proband = record.get(CONCEPT.PARTICIPANT.PROBAND_ID)
        study_id = record[CONCEPT.STUDY.ID]
        proband_id = get_target_id_from_record(Patient, {CONCEPT.PARTICIPANT.ID: record[CONCEPT.PARTICIPANT.PROBAND_ID]})
        #pdb.set_trace()
        rel_struct = [add_family_encoding(relationship)]

        # Add in the gender neutral terms
        if relationship in DEGENDERFICATION:
            rel_struct = [add_family_encoding(DEGENDERFICATION[relationship]), rel_struct[0]]


        # Are patients limited to a single institution?
        # institution = record[CONCEPT.STUDY.PROVIDER.ID]

        entity = {
            "resourceType": PatientRelation.resource_type,
            "id": make_identifier(PatientRelation.resource_type, participant_id, relationship, 'to', proband),
            "meta": {
                "profile": [
                    "http://fhir.ncpi-project-forge.io/StructureDefinition/ncpi-family-relationship"
                ]
            },
            "code": {
                "coding": [
                  {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
                    "code": "FAMMEMB",
                    "display": "Family"
                  }
                ],
                "text": "Family relationship"
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
