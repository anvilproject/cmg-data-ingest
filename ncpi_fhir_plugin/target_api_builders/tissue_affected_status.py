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


class TissueAffectedStatus:
    class_name = "tissue_affected_status"
    resource_type = "Observation"
    target_id_concept = CONCEPT.BIOSPECIMEN.TISSUE_AFFECTED_STATUS.TARGET_SERVICE_ID

    @staticmethod
    def build_key(record):
        subject_id = record.get(CONCEPT.PARTICIPANT.ID)
        sample_id = record.get(CONCEPT.BIOSPECIMEN.ID)
        status = record.get(CONCEPT.BIOSPECIMEN.TISSUE_AFFECTED_STATUS.NAME)
        assert None is not record[CONCEPT.PARTICIPANT.ID]
        assert None is not record[CONCEPT.BIOSPECIMEN.ID]
        assert None is not record[CONCEPT.BIOSPECIMEN.TISSUE_AFFECTED_STATUS.NAME] and record[CONCEPT.BIOSPECIMEN.TISSUE_AFFECTED_STATUS.NAME] != ""
        key = join(
            record[CONCEPT.PARTICIPANT.ID],
            record[CONCEPT.BIOSPECIMEN.ID],
            record[CONCEPT.BIOSPECIMEN.TISSUE_AFFECTED_STATUS.NAME]
        )

        return key

    @staticmethod
    def build_entity(record, key, get_target_id_from_record):
        study_id = record[CONCEPT.STUDY.ID]
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
                    "system": "urn:ncpi:unique-string",
                    "value": join(TissueAffectedStatus.resource_type, study_id, key),
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
