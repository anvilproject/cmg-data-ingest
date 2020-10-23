"""
Builds FHIR ResearchSubject resources (http://www.hl7.org/fhir/researchsubject.html)

Links a Patient to a Study
"""
from ncpi_fhir_plugin.shared import join, make_identifier
from ncpi_fhir_plugin.common import constants, CONCEPT
from ncpi_fhir_plugin.target_api_builders.ncpi_patient import Patient
from ncpi_fhir_plugin.target_api_builders.research_study import ResearchStudy

class ResearchSubject:
    class_name = "research_subject"
    resource_type = "ResearchSubject"
    target_id_concept = CONCEPT.STUDY.PROVIDER.SUBJECT.TARGET_SERVICE_ID

    @staticmethod
    def build_key(record):
        assert None is not record[CONCEPT.STUDY.ID]
        assert None is not record[CONCEPT.PARTICIPANT.ID]

        return join(
            record[CONCEPT.STUDY.ID],
            record[CONCEPT.PARTICIPANT.ID]
        )
        
    @staticmethod
    def build_entity(record, key, get_target_id_from_record):
        study = record[CONCEPT.STUDY.ID]
        study_name = record.get(CONCEPT.STUDY.NAME)
        identity = join(
        	record[CONCEPT.STUDY.ID],
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
                    "system": "urn:kids-first:unique-string",
                    "value": join(ResearchSubject.resource_type, key),
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
