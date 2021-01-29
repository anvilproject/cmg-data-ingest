"""
Builds FHIR ResearchSubject resources (http://www.hl7.org/fhir/researchsubject.html)

Links a Patient to a Study
"""
from ncpi_fhir_plugin.shared import join, make_identifier
from ncpi_fhir_plugin.common import constants, CONCEPT
from ncpi_fhir_plugin.target_api_builders.ncpi_patient import Patient
from ncpi_fhir_plugin.target_api_builders.research_study import ResearchStudy
from ncpi_fhir_plugin.target_api_builders import TargetBase

class ResearchSubject(TargetBase):
    class_name = "research_subject"
    resource_type = "ResearchSubject"
    target_id_concept = CONCEPT.STUDY.PROVIDER.SUBJECT.TARGET_SERVICE_ID

    @classmethod
    def get_key_components(cls, record, get_target_id_from_record):
        # These are required for the variant
        assert None is not record[CONCEPT.STUDY.NAME]
        assert None is not record[CONCEPT.PARTICIPANT.ID]

        return {
            "identifier":  join(
                record[CONCEPT.STUDY.NAME],
                record[CONCEPT.PARTICIPANT.ID]
            )
        }
        
    @classmethod
    def build_entity(cls, record, get_target_id_from_record):
        key = cls.get_key_components(record, get_target_id_from_record)['identifier']
        study = record[CONCEPT.STUDY.NAME]
        study_name = record.get(CONCEPT.STUDY.NAME)
        identity = join(
        	record[CONCEPT.STUDY.NAME],
            record[CONCEPT.PARTICIPANT.ID]
        )

        study_id = get_target_id_from_record(ResearchStudy, record)

        entity = {
            "resourceType": ResearchSubject.resource_type,
            "id": get_target_id_from_record(ResearchSubject, record),
            "meta": {
                "profile": [
                    "http://hl7.org/fhir/StructureDefinition/ResearchSubject"
                ]
            },
            "identifier": [
                {
                    "system": f"https://ncpi-api-dataservice.kidsfirstdrc.org/research_subjects?study_id={study_id}&external_id=",
                    "value": identity,
                },
                {
                    "system" : f"{cls.identifier_system}",
                    "value": key,
                }
            ],
            "status": "on-study",
            "individual": {
                "reference": f"Patient/{get_target_id_from_record(Patient, record)}"
            },
            "study": {
            	"reference": f"ResearchStudy/{get_target_id_from_record(ResearchStudy, record)}"
            }
        }

        return entity
