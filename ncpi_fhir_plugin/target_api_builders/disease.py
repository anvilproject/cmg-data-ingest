"""
Builds FHIR Phenotype 

Phenotypes attach to patients via "subject" and capture:
    disease_id  (when available - along with disease_description)
    phenotype_description
    affected_status (via extension)

HPO Absent/Present will reference the 

"""

from copy import deepcopy
from ncpi_fhir_plugin.common import CONCEPT, constants
from ncpi_fhir_plugin.target_api_builders.ncpi_patient import Patient
from ncpi_fhir_plugin.shared import join
from ncpi_fhir_plugin.target_api_builders import TargetBase

import pdb

affected_status_lookup = {
    constants.AFFECTED_STATUS.AFFECTED: {
        "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
        "code": "confirmed",
        "display": "Confirmed"
    },
    'Present': {
        "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
        "code": "confirmed",
        "display": "Confirmed"
    },
    constants.AFFECTED_STATUS.UNAFFECTED: {
        "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
        "code": "refuted",
        "display": "Refuted"
    },
    'Absent': {
        "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
        "code": "refuted",
        "display": "Refuted"       
    },
    constants.AFFECTED_STATUS.POSSIBLY_AFFECTED: {
        "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
        "code": "provisional",
        "display": "Provisional"
    },
    constants.AFFECTED_STATUS.UNKNOWN: {
        "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
        "code": "unconfirmed",
        "display": "Unconfirmed"
    }
}

class Disease(TargetBase):
    class_name = "disease"
    resource_type = "Condition"
    target_id_concept = CONCEPT.DIAGNOSIS.TARGET_SERVICE_ID

    @classmethod
    def get_key_components(cls, record, get_target_id_from_record):
        # These are required for the variant
        assert None is not record[CONCEPT.PARTICIPANT.ID]
        assert None is not record[CONCEPT.STUDY.NAME]
        assert None is not record[CONCEPT.DIAGNOSIS.NAME]
        assert None is not record[CONCEPT.FAMILY.ID]

        assert (None is not record.get(CONCEPT.DIAGNOSIS.DESCRIPTION) and record[CONCEPT.DIAGNOSIS.DESCRIPTION].strip() != "") or (None is not record.get(CONCEPT.DIAGNOSIS.DISEASE_CODE) and record.get(CONCEPT.DIAGNOSIS.DISEASE_CODE).strip() != "")

        if CONCEPT.DIAGNOSIS.DISEASE_CODE in record:
            return {
                "identifier":  join(
                    record[CONCEPT.STUDY.NAME],
                    record[CONCEPT.FAMILY.ID],
                    record[CONCEPT.PARTICIPANT.ID],
                    record[CONCEPT.DIAGNOSIS.DISEASE_CODE],
                )
            }
        else:
            return {
                "identifier":  join(
                    record[CONCEPT.STUDY.NAME],
                    record[CONCEPT.FAMILY.ID],
                    record[CONCEPT.PARTICIPANT.ID],
                    record[CONCEPT.DIAGNOSIS.NAME],
                )
            }

    @classmethod 
    def transform_records_list(cls, records_list):
        altered_records = []

        # We'll capture the rows associated with a single
        # disease_id and aggregate the codings as we encounter
        # them
        with_codings = {}

        for record in records_list:
            if CONCEPT.DIAGNOSIS.DISEASE_ID in record:
                id = join(
                    record[CONCEPT.STUDY.NAME],
                    record[CONCEPT.FAMILY.ID],
                    record[CONCEPT.PARTICIPANT.ID],
                    record[CONCEPT.DIAGNOSIS.NAME],
                )

                if id in with_codings:
                    with_codings[id]['CODE'].append({
                        'system': record.get(CONCEPT.DIAGNOSIS.SYSTEM),
                        'code': record.get(CONCEPT.DIAGNOSIS.DISEASE_CODE),
                        'display': record.get(CONCEPT.DIAGNOSIS.NAME)
                    })
                else:
                    with_codings[id] = deepcopy(record)
                    with_codings[id]['CODE'] = [{
                        'system': record.get(CONCEPT.DIAGNOSIS.SYSTEM),
                        'code': record.get(CONCEPT.DIAGNOSIS.DISEASE_CODE),
                        'display': record.get(CONCEPT.DIAGNOSIS.NAME)
                    }]

        for record in records_list:
            if CONCEPT.DIAGNOSIS.DISEASE_ID in record:
                id = join(
                    record[CONCEPT.STUDY.NAME],
                    record[CONCEPT.FAMILY.ID],
                    record[CONCEPT.PARTICIPANT.ID],
                    record[CONCEPT.DIAGNOSIS.NAME],
                )
                altered_records.append(with_codings[id])
                if altered_records.get(CONCEPT.DIAGNOSIS.DESCRIPTION).strip() == "":
                    altered_records[CONCEPT.DIAGNOSIS.DESCRIPTION] = record[CONCEPT.DIAGNOSIS.NAME]
            else:
                altered_records.append(record)
                if altered_records[-1].get(CONCEPT.DIAGNOSIS.DESCRIPTION).strip() == "":
                    altered_records[-1][CONCEPT.DIAGNOSIS.DESCRIPTION] = record[CONCEPT.DIAGNOSIS.NAME]
        return altered_records

    @classmethod
    def build_entity(cls, record, get_target_id_from_record):
        key = cls.get_key_components(record, get_target_id_from_record)['identifier']
        study_id = record[CONCEPT.STUDY.NAME]
        family_id = record[CONCEPT.FAMILY.ID]
        study_name = record[CONCEPT.STUDY.NAME]
        disease_id = record.get(CONCEPT.DIAGNOSIS.DISEASE_ID)
        diseae_code = record.get(CONCEPT.DIAGNOSIS.DISEASE_CODE)
        disease_name = record.get(CONCEPT.DIAGNOSIS.NAME)
        disease_description = record.get(CONCEPT.DIAGNOSIS.DESCRIPTION)
        disease_system = record.get(CONCEPT.DIAGNOSIS.SYSTEM)
        age_onset = record.get(CONCEPT.DIAGNOSIS.AGE_ONSET)
        affected_status = record[CONCEPT.PHENOTYPE.OBSERVED]
        pheno_description = record[CONCEPT.PHENOTYPE.DESCRIPTION]
        alternate_disease_ids = record.get(CONCEPT.DIAGNOSIS.DISEASE_ALTERNATE_IDS)

        if disease_name.strip() == "":
            pdb.set_trace()

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
                    f"{constants.NCPI_DOMAIN}/ncpi-fhir-ig/StructureDefinition/disease"
                ]
            },
            "identifier": [
                {
                    "system" : f"{cls.identifier_system}",
                    "value": key,
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
            entity['code']['coding'] = record.get('CODE')

        if affected_status and affected_status not in ["Unknown", constants.AFFECTED_STATUS.UNKNOWN]:
            entity['verificationStatus'] = {
                "coding": [
                   affected_status_lookup[affected_status]
                ],
                'text': affected_status
            }
        if age_onset:
            try:
                age = int(age_onset)
                entity['onsetAge'] = {
                    "value": int(age_onset),
                    "unit": "a",
                    "system": "http://unitsofmeasure.org",
                    "code": "years",
                }
            except:
                entity['onsetString'] = age_onset
                

        if len(entry_note) > 0:
            entity['note'] = [
                { 'text' : " ".join(entry_note) }
            ]
        return entity
