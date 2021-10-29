"""
Build tasks used to represent much of the act of sequencing data
from a specimen
"""
import pandas as pd
import sys

from ncpi_fhir_plugin.shared import join, make_identifier
from ncpi_fhir_plugin.common import constants, CONCEPT
from ncpi_fhir_plugin.target_api_builders.sequencing_center import SequencingCenter
from ncpi_fhir_plugin.target_api_builders.specimen import Specimen
from ncpi_fhir_plugin.target_api_builders.ncpi_patient import Patient
from ncpi_fhir_plugin.target_api_builders.sequencing_file import SequencingFile 
from ncpi_fhir_plugin.target_api_builders import (
    addReference,
    addValuestring,
    addValuebool)
from ncpi_fhir_plugin.target_api_builders import TargetBase
from ncpi_fhir_plugin.target_api_builders.sequencing_file_no_drs import SequencingFileNoDrs
import pdb


# Eventually, this needs to become sequencing_task, but doing so will require either
# purging the current tasks in the remote server or making some changes to the 
# cache db (basically renaming the tables))
class SequencingTask(TargetBase):
    class_name = "sequencing_data"
    resource_type = "Task"
    target_id_concept = CONCEPT.SEQUENCING.TARGET_SERVICE_ID

    @classmethod
    def get_key_components(cls, record, get_target_id_from_record):
        assert None is not record.get(CONCEPT.SEQUENCING.ID) and record.get(CONCEPT.SEQUENCING.ID).strip() != ""

        # I think it's safe to say that we'll need a DRS URI at this point
        # we may switch to an alternate approach at a later date, though
        assert None is not record.get(CONCEPT.SEQUENCING.DRS_URI)

        return {
            "identifier":  join(
                record[CONCEPT.SEQUENCING.ID]
            )
        }


    @classmethod
    def build_entity(cls, record, get_target_id_from_record):
        key = cls.get_key_components(record, get_target_id_from_record)['identifier']
        study_id = record[CONCEPT.STUDY.NAME]
        seq_filename = record.get(CONCEPT.SEQUENCING_GENOMIC_FILE.ID)
        seq_id = record.get(CONCEPT.SEQUENCING.ID)
        seq_center = record.get(CONCEPT.SEQUENCING.CENTER.ID)
        specimen = get_target_id_from_record(Specimen, record)
        analyte_type = record.get(CONCEPT.BIOSPECIMEN.ANALYTE)
        seq_assay = record.get(CONCEPT.SEQUENCING.ASSAY)
        library_prep = record.get(CONCEPT.SEQUENCING.LIBRARY_NAME)
        exome_platform = record.get(CONCEPT.SEQUENCING.PLATFORM)
        capture_region = record.get(CONCEPT.SEQUENCING.CAPTURE_REGION)
        reference_seq = record.get(CONCEPT.SEQUENCING.REFERENCE_GENOME)
        alignment_method = record.get(CONCEPT.SEQUENCING.ALIGNMENT_METHOD)
        data_proc_pipeline = record.get(CONCEPT.SEQUENCING.DATA_PROC_PIPELINE)
        functional_equivalence_standard = record.get(CONCEPT.SEQUENCING.FUNCTIONAL_EQUIVALENCE_PIPELINE)
        data_date_generation = record.get(CONCEPT.SEQUENCING.DATE)


        seq_file_id = get_target_id_from_record(SequencingFile, record)

        if seq_center.strip() == "":
            pdb.set_trace()
        if record[CONCEPT.SEQUENCING.DRS_URI].strip() == "":
            seq_file_id = get_target_id_from_record(SequencingFileNoDrs, record)


        # In the event that our specimen ID doesn't work, let's see if it's under
        # sample ID. This was used during some hurried push to get some messy 
        # data into a fhir server, so it's probably no longer necessary. But, will
        # need to be properly tested
        # TODO - Make sure this is still sensible
        if specimen is None:
            specimen = get_target_id_from_record(Specimen, {CONCEPT.BIOSPECIMEN.ID: record[CONCEPT.PARTICIPANT.ID]})

        status = 'completed'

        entity = {
            "resourceType": SequencingTask.resource_type,
            "id": get_target_id_from_record(SequencingTask, record),
            "meta": {
                "profile": [
                    f"http://hl7.org/fhir/StructureDefinition/{SequencingTask.resource_type}"
                ]
            },
            "identifier": [
                {
                    "system" : f"{cls.identifier_system}",
                    "value": key,
                },
            ],           "status": "complete",
            "description": "Generate sequence data for use by researchers",
            "focus": {
                "reference": f"{Specimen.resource_type}/{specimen}",
                "display" : "Specimen"
            },
            "owner" : {
                "reference": f"{SequencingCenter.resource_type}/{get_target_id_from_record(SequencingCenter, record)}",
                "display": seq_center
            },
            "intent": "order",
            "status": status,
            "output": [ 
                addReference("Sequence Data Filename", f"{SequencingFile.resource_type}/{seq_file_id}")
            ],
            "input": []
        }

        if specimen: 
            entity['input'].append(
                {
                    "type": {
                        "text": "Specimen"
                    },
                    "valueReference": {
                        "reference": f"{Specimen.resource_type}/{specimen}"
                    }
                }
            )

        #entity['output'].append(addValuestring("Sequence Filename", seq_filename))

        if analyte_type:
            entity['input'].append(addValuestring("Analyte Type", analyte_type))

        if library_prep:
            entity['input'].append(addValuestring("Library Prep Kit", library_prep))

        if exome_platform:
            entity['input'].append(addValuestring("Exome Capture Platform", exome_platform))

        if capture_region:
            entity['input'].append(addValuestring("Capture Region Bed File", capture_region))

        # So, what exactly is input vs output, because this is input to the alignment phase, but that isn't really
        # part of the act of sequencing
        """
        if reference_seq:
            entity['output'].append(addValuestring("Reference Genome Build", reference_seq))

        if alignment_method:
            entity['output'].append(addValuestring("Alignment Method", alignment_method))

        if data_proc_pipeline:
            entity['output'].append(addValuestring("Data Processing Pipeline", data_proc_pipeline))

        if functional_equivalence_standard:
            entity['output'].append(addValuebool("Functional Equivalence Standard", functional_equivalence_standard))
        """

        if data_date_generation:
            entity['authoredOn'] = data_date_generation

        return entity
