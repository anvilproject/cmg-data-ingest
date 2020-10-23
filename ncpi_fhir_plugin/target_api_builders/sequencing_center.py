"""
Builds FHIR Organization to represent sequencing center
"""
import pandas as pd
import sys
# from kf_lib_data_ingest.common.concept_schema import CONCEPT

"""
from ncpi_model_forge.ingest_plugin.target_api_builders.organization import (
    Organization,
)
from ncpi_model_forge.ingest_plugin.target_api_builders.practitioner import (
    Practitioner,
)"""
from ncpi_fhir_plugin.shared import join, make_identifier
from ncpi_fhir_plugin.common import constants, CONCEPT

class SequencingCenter:
    class_name = "sequencing_center"
    resource_type = "Organization"
    target_id_concept = CONCEPT.SEQUENCING.CENTER.TARGET_SERVICE_ID

    @staticmethod
    def build_key(record):
        assert None is not record[CONCEPT.SEQUENCING.CENTER.ID]

        return record.get(CONCEPT.SEQUENCING.CENTER.UNIQUE_KEY) or join(
            record[CONCEPT.SEQUENCING.CENTER.ID]
        )

    @staticmethod
    def build_entity(record, key, get_target_id_from_record):
        study_id = record[CONCEPT.STUDY.ID]
        study_name = record.get(CONCEPT.STUDY.NAME)
        seq_center = record.get(CONCEPT.SEQUENCING.CENTER.ID)

        entity = {
            "resourceType": SequencingCenter.resource_type,
            "id": make_identifier(seq_center),
            "meta": {
                "profile": [
                    "http://hl7.org/fhir/StructureDefinition/Organization"
                ]
            },
            "identifier": [
                {
                    "system": "urn:ncpi:unique-string",
                    "value": join(SequencingCenter.resource_type, key),
                },
            ],
            "name": seq_center,
            "active": True
        }

        return entity
