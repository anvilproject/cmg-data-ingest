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
from ncpi_fhir_plugin.target_api_builders.group import Group
from copy import deepcopy
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
    def transform_records_list(cls, records_list):
        '''
        Transforms the given record list into the form needed for this
        class's build_key and build_entity methods.

        :param records_list: list of records coming from the Transform stage
        :type records_list: list of dicts
        :return: list of reformatted records needed by this class's build_key
            and build_entity methods
        :rtype: list of dicts
        '''

        altered_records = {}
        for row in records_list:
            key = join(
                row[CONCEPT.STUDY.NAME]
            )
            if key not in altered_records:
                altered_records[key] = deepcopy(row)
                altered_records[key][CONCEPT.STUDY.GROUP.NAME] = set()

            altered_records[key][CONCEPT.STUDY.GROUP.NAME].add(row[CONCEPT.STUDY.GROUP.NAME])

        new_record_list = []
        for k in altered_records.keys():
            new_record_list.append(altered_records[k])
            new_record_list[-1][CONCEPT.STUDY.GROUP.NAME] = list(new_record_list[-1][CONCEPT.STUDY.GROUP.NAME])
        
        return new_record_list

    @classmethod
    def build_entity(cls, record, get_target_id_from_record):
        key = cls.get_key_components(record, get_target_id_from_record)['identifier']
        study_id = record[CONCEPT.STUDY.NAME]
        study_name = record.get(CONCEPT.STUDY.NAME)
        study_title = study_name

        if CONCEPT.STUDY.TITLE in record and record[CONCEPT.STUDY.TITLE].strip() != "":
            study_title = record.get(CONCEPT.STUDY.TITLE)

        attribution = record.get(CONCEPT.STUDY.ATTRIBUTION)
        short_name = record.get(CONCEPT.STUDY.SHORT_NAME)
        status = record.get(CONCEPT.STUDY.RELEASE_STATUS)

        unmatched_ids = []
        group_refs = []
        for group in record.get(CONCEPT.STUDY.GROUP.NAME):
            fake_row = {
                CONCEPT.STUDY.NAME: study_name,
                CONCEPT.STUDY.GROUP.NAME: group
            }
            group_id = get_target_id_from_record(Group, fake_row)
            if group_id is not None:
                group_refs.append(f"Group/{group_id}")
            else:
                unmatched_ids.append(id)
        if len(unmatched_ids) > 0:
            print(sorted(unmatched_ids))
            print("Unmatched IDs for Research Study enrollment")

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
            "title": study_title,
            "status": status
        }

        if attribution:
            entity["identifier"].append({"value": attribution})

        if len(group_refs) > 0:
            entity['enrollment'] = []

            for group in group_refs:
                entity['enrollment'].append({
                    "reference": group
                })
        # I don't know if we will be using this
        if short_name:
            entity["extension"].append(
                {
                    "url": "http://fhir.ncpi-project-forge.io/StructureDefinition/display-name",
                    "valueString": short_name,
                }
            )


        return entity
