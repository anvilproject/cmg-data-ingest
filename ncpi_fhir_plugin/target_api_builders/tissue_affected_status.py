"""
Builds FHIR Observation to reflect affected status for a tissue

code => Pos/NEG for affected status
Subject => Patient
focus => Condition associated with the status
specimen => relevant specimen

"""
from ncpi_fhir_plugin.common import constants, CONCEPT, terminology
from ncpi_fhir_plugin.shared import join
from ncpi_fhir_plugin.target_api_builders.ncpi_patient import Patient
from ncpi_fhir_plugin.target_api_builders.specimen import Specimen
from ncpi_fhir_plugin.target_api_builders import TargetBase


class TissueAffectedStatus(TargetBase):
    class_name = "tissue_affected_status"
    resource_type = "Observation"
    target_id_concept = CONCEPT.BIOSPECIMEN.TISSUE_AFFECTED_STATUS.TARGET_SERVICE_ID

    @classmethod
    def get_key_components(cls, record, get_target_id_from_record):
        assert None is not record[CONCEPT.PARTICIPANT.ID]
        assert None is not record[CONCEPT.BIOSPECIMEN.ID]
        assert None is not record[CONCEPT.BIOSPECIMEN.TISSUE_AFFECTED_STATUS.NAME] and record[CONCEPT.BIOSPECIMEN.TISSUE_AFFECTED_STATUS.NAME] != ""
        return {
            "identifier":  join(
                record[CONCEPT.PARTICIPANT.ID],
                record[CONCEPT.BIOSPECIMEN.ID],
                record[CONCEPT.BIOSPECIMEN.TISSUE_AFFECTED_STATUS.NAME]
            )
        }

    @classmethod
    def build_entity(cls, record, get_target_id_from_record):
        key = cls.get_key_components(record, get_target_id_from_record)['identifier']
        study_id = record[CONCEPT.STUDY.NAME]
        biospecimen_id = record.get(CONCEPT.BIOSPECIMEN.ID)
        subject_id = record.get(CONCEPT.PARTICIPANT.ID)
        tissue_affected_status = record[CONCEPT.BIOSPECIMEN.TISSUE_AFFECTED_STATUS.NAME]

        entity = {
            "resourceType": TissueAffectedStatus.resource_type,
            "id": get_target_id_from_record(TissueAffectedStatus, record),
            "meta": {
                "profile": [
                    f"http://hl7.org/fhir/StructureDefinition/{TissueAffectedStatus.resource_type}"
                ]
            },
            "identifier": [
                {
                    "system" : f"{cls.identifier_system}",
                    "value": key,
                },
            ],
            "status": "preliminary",
            "subject": {
                "reference": f"Patient/{get_target_id_from_record(Patient, record)}"
            },
            "specimen": {
                "reference": f"Specimen/{get_target_id_from_record(Specimen, record)}"
            },
            "code" : terminology['interpretation_status'][tissue_affected_status],
        }
        return entity
