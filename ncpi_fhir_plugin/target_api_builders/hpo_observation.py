"""
Builds FHIR HPO (Observation) entries

Links a Patient, Study, Disease with HPO (which is either present or absent)
"""

from ncpi_fhir_plugin.shared import join, make_identifier
from ncpi_fhir_plugin.common import CONCEPT, constants

from ncpi_fhir_plugin.target_api_builders.ncpi_patient import Patient
from ncpi_fhir_plugin.target_api_builders.disease import Disease
from ncpi_fhir_plugin.target_api_builders import TargetBase

from copy import deepcopy
import pdb

# https://www.hl7.org/fhir/valueset-observation-interpretation.html
interpretation = {
    constants.PHENOTYPE.OBSERVED.ABSENT: [{
        "coding": [ 
            {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                "code": "NEG",
                "display": "Negative"
            }
        ],
        "text": "Absent"
    }],
    constants.PHENOTYPE.OBSERVED.PRESENT: [{
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                "code": "POS",
                "display": "Positive",
            }
        ],
        "text": "Present"
    }],
}

observation_code = {
    constants.PHENOTYPE.OBSERVED.PRESENT: {
        "coding": [
            {
                "system": "http://snomed.info/sct",
                "code": "373573001",
                "display": "Clinical finding present (situation)"
            }
        ],
        "text": "Phenotype Present"
    },   
    constants.PHENOTYPE.OBSERVED.ABSENT: {
        "coding": [
            {
                "system": "http://snomed.info/sct",
                "code": "373572006",
                "display": "Clinical finding absent (situation)"
            }
        ],
        "text": "Phenotype Absent"
    }
}

affected_status_lookup = {
    constants.PHENOTYPE.OBSERVED.PRESENT: {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                "code": "confirmed",
                "display": "Confirmed"
            }
        ],
        "text": 'Phenotype Present'
    },
    constants.PHENOTYPE.OBSERVED.ABSENT: {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                "code": "refuted",
                "display": "Refuted"
            }
        ],
        "text": "Phenotype Absent"
    }
}

class HumanPhenotype(TargetBase):
    class_name = "human_phenotype"
    resource_type = "Condition"
    target_id_concept = CONCEPT.STUDY.PROVIDER.SUBJECT.TARGET_SERVICE_ID

    @classmethod
    def get_key_components(cls, record, get_target_id_from_record):
        # These are required for the variant
        #pdb.set_trace()

        assert None is not record[CONCEPT.PARTICIPANT.ID]
        assert None is not record[CONCEPT.STUDY.NAME]
        assert None is not record[CONCEPT.PHENOTYPE.ID] and record.get(CONCEPT.PHENOTYPE.ID).strip() != ""
        assert None is not record[CONCEPT.PHENOTYPE.OBSERVED]
        assert None is not record.get(CONCEPT.DIAGNOSIS.DISEASE_CODE) and record.get(CONCEPT.DIAGNOSIS.DISEASE_CODE).strip() != ""

        return {
            "identifier":  join(
                record[CONCEPT.STUDY.NAME],
                record[CONCEPT.PARTICIPANT.ID],
                record[CONCEPT.PHENOTYPE.ID],
                record[CONCEPT.PHENOTYPE.OBSERVED]
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
            if CONCEPT.PHENOTYPE.ID in record and record[CONCEPT.PHENOTYPE.ID].strip() != "":
                id = join(
                    record[CONCEPT.STUDY.NAME],
                    record[CONCEPT.PARTICIPANT.ID],
                    record[CONCEPT.PHENOTYPE.ID],
                    record[CONCEPT.PHENOTYPE.OBSERVED]
                )

                display = record.get(CONCEPT.DIAGNOSIS.NAME)
                if display is None or display.strip() == "":
                    display = record.get(CONCEPT.DIAGNOSIS.DESCRIPTION)
                if id in with_codings:
                    #pdb.set_trace()
                    with_codings[id]['CODE'].append({
                        'display': display
                    })
                    system =  record.get(CONCEPT.DIAGNOSIS.SYSTEM)
                    code = record.get(CONCEPT.DIAGNOSIS.DISEASE_CODE)
                    if system is not None and system.strip() != "":
                        with_codings[id]['CODE'][-1]['system'] = system
                    if code is not None and code.strip() != "":
                        with_codings[id]['CODE'][-1]['code'] = code

                else:
                    #pdb.set_trace()
                    with_codings[id] = deepcopy(record)
                    with_codings[id]['CODE'] = [{
                        'display': display
                    }]
                    system =  record.get(CONCEPT.DIAGNOSIS.SYSTEM)
                    code = record.get(CONCEPT.DIAGNOSIS.DISEASE_CODE)

                    if system is not None and system.strip() != "":
                        with_codings[id]['CODE'][-1]['system'] = system

                    if code is not None and code.strip() != "":
                        with_codings[id]['CODE'][-1]['code'] = code


        for record in records_list:
            if CONCEPT.PHENOTYPE.ID in record and record[CONCEPT.PHENOTYPE.ID].strip() != "":
                id = join(
                record[CONCEPT.STUDY.NAME],
                record[CONCEPT.PARTICIPANT.ID],
                record[CONCEPT.PHENOTYPE.ID],
                record[CONCEPT.PHENOTYPE.OBSERVED]
            )
                altered_records.append(with_codings[id])
            else:
                altered_records.append(record)
        return altered_records

    @classmethod
    def build_entity(cls, record, get_target_id_from_record):
        key = cls.get_key_components(record, get_target_id_from_record)['identifier']
        family_id = record[CONCEPT.FAMILY.ID]
        study_name = record[CONCEPT.STUDY.NAME]
        hpo_id = record[CONCEPT.PHENOTYPE.ID]
        pheno_name = record[CONCEPT.DIAGNOSIS.NAME] #record[CONCEPT.PHENOTYPE.NAME]
        if pheno_name.strip() == "":
            pheno_name = record.get(CONCEPT.DIAGNOSIS.DESCRIPTION)
        observed = record[CONCEPT.PHENOTYPE.OBSERVED]

        entity = {
            "resourceType": HumanPhenotype.resource_type,
            "id": get_target_id_from_record(HumanPhenotype, record),
            "meta": {
                "profile": [
                      f"{constants.NCPI_DOMAIN}/ncpi-fhir-ig/StructureDefinition/phenotype"
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
            "code":     {
                "coding": record['CODE'],
                "text": pheno_name
            },
            "subject": {
                "reference": f"Patient/{get_target_id_from_record(Patient, record)}"
            },
            "verificationStatus": affected_status_lookup[observed]
        }

        return entity

