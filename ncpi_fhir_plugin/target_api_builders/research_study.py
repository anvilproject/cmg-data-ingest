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

class ResearchStudy:
    class_name = "research_study"
    resource_type = "ResearchStudy"
    target_id_concept = CONCEPT.STUDY.TARGET_SERVICE_ID

    @staticmethod
    def build_key(record):
        assert None is not record[CONCEPT.STUDY.ID]

        return record.get(CONCEPT.STUDY.UNIQUE_KEY) or join(
            record[CONCEPT.STUDY.ID]
        )

    @staticmethod
    def build_entity(record, key, get_target_id_from_record):
        study_id = record[CONCEPT.STUDY.ID]
        study_name = record.get(CONCEPT.STUDY.NAME)
        attribution = record.get(CONCEPT.STUDY.ATTRIBUTION)
        short_name = record.get(CONCEPT.STUDY.SHORT_NAME)
        status = record.get(CONCEPT.STUDY.RELEASE_STATUS)

        if status is None:
            status = 'completed'

        entity = {
            "resourceType": ResearchStudy.resource_type,
            "id": make_identifier(study_id),
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
                    "system": "urn:ncpi:unique-string",
                    "value": join(ResearchStudy.resource_type, key),
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
