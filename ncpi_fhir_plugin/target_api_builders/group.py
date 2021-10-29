"""
Builds the FHIR representation for groups 
"""
from ncpi_fhir_plugin.target_api_builders import TargetBase
from ncpi_fhir_plugin.shared import join, make_identifier
from ncpi_fhir_plugin.common import constants, CONCEPT
from ncpi_fhir_plugin.target_api_builders.ncpi_patient import Patient
from copy import deepcopy

import pdb

class Group(TargetBase):
    class_name = "group"
    resource_type = "Group"
    target_id_concept = CONCEPT.STUDY.GROUP.TARGET_SERVICE_ID

    @classmethod
    def get_key_components(cls, record, get_target_id_from_record):
        # These are required for the group
        assert None is not record[CONCEPT.STUDY.NAME]
        assert None is not record[CONCEPT.STUDY.GROUP.NAME]

        return {
            "identifier": join(
                record[CONCEPT.STUDY.NAME],
                record[CONCEPT.STUDY.GROUP.NAME]
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
        new_record = deepcopy(records_list[0])
        paricipant_ids = set()
        for row in records_list:
            key = join(
                row[CONCEPT.STUDY.NAME],
                row[CONCEPT.STUDY.GROUP.NAME]
            )
            if key not in altered_records:
                altered_records[key] = deepcopy(row)
                altered_records[key][CONCEPT.PARTICIPANT.ID] = set()

            altered_records[key][CONCEPT.PARTICIPANT.ID].add(row[CONCEPT.PARTICIPANT.ID])

        new_record_list = []
        for k in altered_records.keys():
            new_record_list.append(altered_records[k])
            new_record_list[-1][CONCEPT.PARTICIPANT.ID] = list(new_record_list[-1][CONCEPT.PARTICIPANT.ID])
        
        return new_record_list

    @classmethod
    def build_entity(cls, record, get_target_id_from_record):
        key = cls.get_key_components(record, get_target_id_from_record)['identifier']
        study_id = record[CONCEPT.STUDY.NAME]
        group_url = record[CONCEPT.STUDY.GROUP.URL]
        group_name = record[CONCEPT.STUDY.GROUP.NAME]
        #pdb.set_trace()

        patients = []
        fake_row = {
            CONCEPT.PARTICIPANT.ID: "",
            CONCEPT.STUDY.NAME: record[CONCEPT.STUDY.NAME]
        }

        unmatched_ids = []
        #pdb.set_trace()
        # We'll need patient references for each of our participants
        for id in record[CONCEPT.PARTICIPANT.ID]:
            fake_row[CONCEPT.PARTICIPANT.ID] = id
            patient_id = get_target_id_from_record(Patient, fake_row)
            if patient_id is not None:
                patients.append(f"Patient/{patient_id}")
            else:
                unmatched_ids.append(id)
        if len(unmatched_ids) > 0:
            print(sorted(unmatched_ids))
            print("^ Unmatched IDs")
            pdb.set_trace()
        entity = {
            "resourceType": cls.resource_type,
            "id": get_target_id_from_record(cls, record),
            "identifier": [ 
                {
                    "system": group_url,
                    "value": group_name
                },
                {
                    "system" : f"{cls.identifier_system}",
                    "value": key,
                }
            ],
            "type": "person",
            "actual": True,
            "name": group_name,
            'quantity': len(patients),
            "member": []
        }

        for patient in patients:
            entity['member'].append({
                "entity": {
                    "reference": patient
                }
            })

        return entity

