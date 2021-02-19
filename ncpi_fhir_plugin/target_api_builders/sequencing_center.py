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
from ncpi_fhir_plugin.target_api_builders import TargetBase

class SequencingCenter(TargetBase):
    class_name = "sequencing_center"
    resource_type = "Organization"
    target_id_concept = CONCEPT.SEQUENCING.CENTER.TARGET_SERVICE_ID

    @classmethod
    def get_key_components(cls, record, get_target_id_from_record):
        # These are required for the variant
        assert None is not record[CONCEPT.SEQUENCING.CENTER.ID] and record[CONCEPT.SEQUENCING.CENTER.ID] != ""

        return {
            "identifier":  join(
                record[CONCEPT.SEQUENCING.CENTER.ID]
            )
        }

    @classmethod
    def build_entity(cls, record, get_target_id_from_record):
        key = cls.get_key_components(record, get_target_id_from_record)['identifier']
        study_name = record.get(CONCEPT.STUDY.NAME)
        seq_center = record.get(CONCEPT.SEQUENCING.CENTER.ID)

        entity = {
            "resourceType": SequencingCenter.resource_type,
            "id": get_target_id_from_record(SequencingCenter, record), #make_identifier(seq_center),
            "meta": {
                "profile": [
                    "http://hl7.org/fhir/StructureDefinition/Organization"
                ]
            },
            "identifier": [
                {
                    "system" : f"{cls.identifier_system}",
                    "value": key,
                },
            ],
            "name": seq_center,
            "active": True
        }

        return entity
