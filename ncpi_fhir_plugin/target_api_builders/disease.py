"""
Builds FHIR Phenotype 

Phenotypes attach to patients via "subject" and capture:
    disease_id  (when available - along with disease_description)
    phenotype_description
    affected_status (via extension)

HPO Absent/Present will reference the 

"""

from ncpi_fhir_plugin.common import CONCEPT, constants
from ncpi_fhir_plugin.target_api_builders.ncpi_patient import Patient
from ncpi_fhir_plugin.shared import join

affected_status_lookup = {
    constants.AFFECTED_STATUS.AFFECTED: {
        "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
        "code": "confirmed",
        "display": "Confirmed"
    },
    constants.AFFECTED_STATUS.UNAFFECTED: {
        "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
        "code": "refuted",
        "display": "Refuted"
    },
    constants.AFFECTED_STATUS.POSSIBLY_AFFECTED: {
        "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
        "code": "provisional",
        "display": "Provisional"
    },
}

class Disease:
    class_name = "disease"
    resource_type = "Condition"
    target_id_concept = CONCEPT.DIAGNOSIS.TARGET_SERVICE_ID

    @staticmethod
    def build_key(record):
        # For now, I'm assuming that family+id are necessary to be unique, but that may not be true
        assert None is not record[CONCEPT.PARTICIPANT.ID]
        assert None is not record[CONCEPT.STUDY.ID]
        assert None is not record[CONCEPT.DIAGNOSIS.NAME]
        assert None is not record[CONCEPT.FAMILY.ID]
        assert None is not record[CONCEPT.DIAGNOSIS.DESCRIPTION] and record[CONCEPT.DIAGNOSIS.DESCRIPTION].strip() != ""
        return record.get(CONCEPT.DIAGNOSIS.UNIQUE_KEY) or join(
            record[CONCEPT.STUDY.ID],
            record[CONCEPT.FAMILY.ID],
            record[CONCEPT.PARTICIPANT.ID],
            record[CONCEPT.DIAGNOSIS.NAME],
        )

    @staticmethod
    def build_entity(record, key, get_target_id_from_record):
        study_id = record[CONCEPT.STUDY.ID]
        family_id = record[CONCEPT.FAMILY.ID]
        study_name = record[CONCEPT.STUDY.NAME]
        disease_id = record[CONCEPT.DIAGNOSIS.DISEASE_ID]
        disease_name = record.get(CONCEPT.DIAGNOSIS.NAME)
        disease_description = record.get(CONCEPT.DIAGNOSIS.DESCRIPTION)
        disease_system = record.get(CONCEPT.DIAGNOSIS.SYSTEM)
        age_onset = record.get(CONCEPT.DIAGNOSIS.AGE_ONSET)
        affected_status = record[CONCEPT.DIAGNOSIS.AFFECTED_STATUS]
        pheno_description = record[CONCEPT.PHENOTYPE.DESCRIPTION]
        alternate_disease_ids = record[CONCEPT.DIAGNOSIS.DISEASE_ALTERNATE_IDS]

        entry_note = []
        if pheno_description:
            entry_note.append(pheno_description + ". ")

        if alternate_disease_ids:
            entry_note.append(f"Other Disease IDs: {alternate_disease_ids}")

        entity = {
            "resourceType": Disease.resource_type,
            "id": get_target_id_from_record(Disease, record),
            "meta": {
                "profile": [
                    f"http://fhir.ncpi-project-forge.io/StructureDefinition/ncpi-disease"
                ]
            },
            "identifier": [
                {
                    "system": "urn:ncpi:unique-string",
                    "value": join(Disease.resource_type, study_name, key),
                }
            ],
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                            "code": "encounter-diagnosis",
                            "display": "Encounter Diagnosis",
                        }
                    ]
                }
            ],
            "code": {"text": disease_description},
            "subject": {
                "reference": f"Patient/{get_target_id_from_record(Patient, record)}"
            },
        }

        if disease_id:
            entity['code']['coding'] = [
            {
                'system': disease_system,
                'code': disease_id,
                'display': disease_name
            }
            ]

        if affected_status and affected_status != "Unknown":
            entity['verificationStatus'] = {
                "coding": [
                   affected_status_lookup[affected_status]
                ],
                'text': affected_status
            }
        if age_onset:
            entity['onsetAge'] = {
                "value": int(age_onset),
                "unit": "a",
                "system": "http://unitsofmeasure.org",
                "code": "years",
                
            }

        if len(entry_note) > 0:
            entity['note'] = [
                { 'text' : " ".join(entry_note) }
            ]
        return entity
