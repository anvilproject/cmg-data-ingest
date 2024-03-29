"""
Builds FHIR Specimen resources (https://www.hl7.org/fhir/specimen.html)
from rows of tabular participant biospecimen adata.
"""
from ncpi_fhir_plugin.common import constants, CONCEPT
from ncpi_fhir_plugin.shared import join
from ncpi_fhir_plugin.target_api_builders.ncpi_patient import Patient
from ncpi_fhir_plugin.target_api_builders import TargetBase

# https://www.hl7.org/fhir/v2/0487/index.html
specimen_type = {
    constants.SPECIMEN.COMPOSITION.BLOOD: {
        "system": "http://terminology.hl7.org/CodeSystem/v2-0487",
        "code": "BLD",
        "display": "Whole blood",
    },
    constants.SPECIMEN.COMPOSITION.SALIVA: {
        "system": "http://terminology.hl7.org/CodeSystem/v2-0487",
        "code": "SAL",
        "display": "Saliva",
    },
    constants.SPECIMEN.COMPOSITION.TISSUE: {
        "system": "http://terminology.hl7.org/CodeSystem/v2-0487",
        "code": "TISS",
        "display": "Tissue",
    },
}

class Specimen(TargetBase):
    class_name = "specimen"
    resource_type = "Specimen"
    target_id_concept = CONCEPT.BIOSPECIMEN.TARGET_SERVICE_ID

    @classmethod
    def get_key_components(cls, record, get_target_id_from_record):
        assert None is not record[CONCEPT.BIOSPECIMEN.ID]

        return {
            "identifier":  join(
                record[CONCEPT.STUDY.NAME], 
                record[CONCEPT.BIOSPECIMEN.ID]
            )
        }

    @classmethod
    def build_entity(cls, record, get_target_id_from_record):
        key = cls.get_key_components(record, get_target_id_from_record)['identifier']
        study_id = record[CONCEPT.STUDY.NAME]
        biospecimen_id = record.get(CONCEPT.BIOSPECIMEN.ID)
        dbgap_id = record.get(CONCEPT.BIOSPECIMEN.DBGAP_ID)
        event_age_days = record.get(CONCEPT.BIOSPECIMEN.EVENT_AGE_DAYS)
        concentration_mg_per_ml = record.get(
            CONCEPT.BIOSPECIMEN.CONCENTRATION_MG_PER_ML
        )
        composition = record.get(CONCEPT.BIOSPECIMEN.COMPOSITION)
        volume_ul = record.get(CONCEPT.BIOSPECIMEN.VOLUME_UL)
        sample_source =record.get(CONCEPT.BIOSPECIMEN.TISSUE_TYPE)
        sample_source_name = record.get(CONCEPT.BIOSPECIMEN.TISSUE_TYPE_NAME)

        entity = {
            "resourceType": Specimen.resource_type,
            "id": get_target_id_from_record(Specimen, record),
            "meta": {
                "profile": [
                    "http://hl7.org/fhir/StructureDefinition/Specimen"
                ]
            },
            "identifier": [
                {
                    "system": f"http://ncpi-api-dataservice.kidsfirstdrc.org/biospecimens?study_id={study_id}&external_aliquot_id=",
                    "value": biospecimen_id,
                },
                {
                    "system" : f"{cls.identifier_system}",
                    "value": key,
                },
            ],
            "subject": {
                "reference": f"Patient/{get_target_id_from_record(Patient, record)}"
            },
        }
        if dbgap_id:
            entity["identifier"].append(
                {
                    "system": f"https://dbgap-api.ncbi.nlm.nih.gov/specimen",
                    "value": dbgap_id
                }

            )

        if event_age_days:
            entity.setdefault("extension", []).append(
                {
                    "url": "http://fhir.ncpi-project-forge.io/StructureDefinition/age-at-event",
                    "valueAge": {
                        "value": int(event_age_days),
                        "unit": "d",
                        "system": "http://unitsofmeasure.org",
                        "code": "days",
                    },
                }
            )
            entity.setdefault("extension", []).append(
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/cqf-relativeDateTime",
                    "extension": [{
                            "url": "target",
                            "valueReference": {
                                "reference": f"Patient/{get_target_id_from_record(BasicPatient, record)}"
                            }
                        }, {
                            "url": "targetPath",
                            "valueString": "birthDate"
                        }, {
                            "url": "relationship",
                            "valueCode":  "after" 
                        }, {
                            "url": "offset",
                            "valueDuration": {
                                "value": int(event_age_days),
                                "unit": "d",
                                "system": "http://unitsofmeasure.org",
                                "code": "days"
                        }

                    }]
                }
            )

        if sample_source_name:
            entity['collection'] = {
                "bodySite": {
                    "coding": [ 
                        {
                            "system": "https://uberon.github.io/",
                            "code": sample_source,
                            "display": sample_source_name
                        }
                    ],
                    "text": sample_source_name
                }
            }
        return entity
