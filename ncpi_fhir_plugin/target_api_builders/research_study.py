"""
Builds FHIR ResearchStudy resources (https://www.hl7.org/fhir/researchstudy.html)
from rows of tabular study metadata.
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
import pdb

class ResearchStudy(TargetBase):
    class_name = "research_study"
    resource_type = "ResearchStudy"
    target_id_concept = CONCEPT.STUDY.TARGET_SERVICE_ID

    @classmethod
    def get_key_components(cls, record, get_target_id_from_record):
        # These are required for the variant
        assert None is not record[CONCEPT.STUDY.NAME]

        return {
            "identifier":  join(
                record[CONCEPT.STUDY.NAME]
            )
        }

    @classmethod
    def build_entity(cls, record, get_target_id_from_record):
        key = cls.get_key_components(record, get_target_id_from_record)['identifier']
        study_id = record[CONCEPT.STUDY.NAME]
        study_name = record.get(CONCEPT.STUDY.NAME)
        attribution = record.get(CONCEPT.STUDY.ATTRIBUTION)
        short_name = record.get(CONCEPT.STUDY.SHORT_NAME)
        status = record.get(CONCEPT.STUDY.RELEASE_STATUS)

        if status is None:
            status = 'completed'

        entity = {
            "resourceType": ResearchStudy.resource_type,
            "id": get_target_id_from_record(ResearchStudy, record),
            "meta": {
                "profile": [
                    "http://hl7.org/fhir/StructureDefinition/ResearchStudy"
                ]
            },
            "identifier": [
                {
                    "system": "https://ncpi-api-dataservice.kidsfirstdrc.org/studies?external_id=",
                    "value": study_id,
                },
                {
                    "system" : f"{cls.identifier_system}",
                    "value": key,
                },
            ],
            "title": study_name,
            "status": status
        }

        if attribution:
            entity["identifier"].append({"value": attribution})

        # I don't know if we will be using this
        if short_name:
            entity["extension"].append(
                {
                    "url": "http://fhir.ncpi-project-forge.io/StructureDefinition/display-name",
                    "valueString": short_name,
                }
            )


        return entity
