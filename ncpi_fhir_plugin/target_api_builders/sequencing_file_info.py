"""Observation describing the output from a sequencing task"""

from ncpi_fhir_plugin.shared import join, make_identifier
from ncpi_fhir_plugin.common import constants, CONCEPT
from ncpi_fhir_plugin.target_api_builders.sequencing_center import SequencingCenter
from ncpi_fhir_plugin.target_api_builders.specimen import Specimen
from ncpi_fhir_plugin.target_api_builders.ncpi_patient import Patient
from ncpi_fhir_plugin.target_api_builders.sequencing_task import SequencingTask
from ncpi_fhir_plugin.target_api_builders.sequencing_file import SequencingFile
from ncpi_fhir_plugin.target_api_builders import Component
from ncpi_fhir_plugin.target_api_builders import TargetBase

class SequencingFileInfo(TargetBase):
    class_name = "sequencing_file_info"
    resource_type = "Observation"
    target_id_concept = CONCEPT.SEQUENCING.TARGET_SERVICE_ID

    @classmethod
    def get_key_components(cls, record, get_target_id_from_record):
        # These are required for the variant
        assert None is not record[CONCEPT.SEQUENCING.ID]

        return {
            "identifier":  join("SEQ|FILE|INFO", record[CONCEPT.SEQUENCING.ID])
        }

    @classmethod
    def build_entity(cls, record, get_target_id_from_record):
        key = cls.get_key_components(record, get_target_id_from_record)['identifier']
        study_id = record[CONCEPT.STUDY.NAME]
        seq_filename = record.get(CONCEPT.SEQUENCING_GENOMIC_FILE.ID)
        seq_id = record.get(CONCEPT.SEQUENCING.ID)
        file_format = record.get(CONCEPT.GENOMIC_FILE.FILE_FORMAT)
        seq_center = record.get(CONCEPT.SEQUENCING.CENTER.ID)
        specimen = get_target_id_from_record(Specimen, record)
        reference_seq = record.get(CONCEPT.SEQUENCING.REFERENCE_GENOME)
        alignment_method = record.get(CONCEPT.SEQUENCING.ALIGNMENT_METHOD)
        data_proc_pipeline = record.get(CONCEPT.SEQUENCING.DATA_PROC_PIPELINE)
        functional_equivalence_standard = {"true": True, "false": False, None: None}[record.get(CONCEPT.SEQUENCING.FUNCTIONAL_EQUIVALENCE_PIPELINE)]

        entity = {
            "resourceType": SequencingFileInfo.resource_type,
            "id": get_target_id_from_record(SequencingFileInfo, record),
            "meta": {
                "profile": [
                    f"http://hl7.org/fhir/StructureDefinition/{SequencingFileInfo.resource_type}"
                ]
            },     
            "identifier": [
                {
                    "system" : f"{cls.identifier_system}",
                    "value": key,
                },
            ],       
            "status": "final",
            "code": {
                "text": "sequence_file_info"
            },
            "subject": {
            	"reference": f"Patient/{get_target_id_from_record(Patient, record)}",
            	"display" : f"{record.get(CONCEPT.PARTICIPANT.ID)}"
            },
            "focus": [
            	{
	            	"reference": f"{SequencingFile.resource_type}/{get_target_id_from_record(SequencingFile, record)}",
	            	"display": "Sequence Data Filename"
	            }
            ],
        	"component": [
        	]
        }

        if reference_seq:
            entity['component'].append(Component.addValuestring("Reference Genome Build", reference_seq))

        if alignment_method:
            entity['component'].append(Component.addValuestring("Alignment Method", alignment_method))

        if data_proc_pipeline:
            entity['component'].append(Component.addValuestring("Data Processing Pipeline", data_proc_pipeline))

        if functional_equivalence_standard:
            entity['component'].append(Component.addValuebool("Functional Equivalence Standard", functional_equivalence_standard))

        return entity