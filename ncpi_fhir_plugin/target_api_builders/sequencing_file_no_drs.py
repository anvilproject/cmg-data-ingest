"""
Doc Resource associated with a file containing sequencing data."""
import pandas as pd
import sys

from ncpi_fhir_plugin.shared import join, make_identifier
from ncpi_fhir_plugin.common import constants, CONCEPT
from ncpi_fhir_plugin.target_api_builders.sequencing_center import SequencingCenter
from ncpi_fhir_plugin.target_api_builders.specimen import Specimen
from ncpi_fhir_plugin.target_api_builders.ncpi_patient import Patient

import pdb

class SequencingFileNoDrs:
    class_name = "sequencing_file_no_drs"
    resource_type = "DocumentReference"
    target_id_concept = CONCEPT.SEQUENCING.TARGET_SERVICE_ID

    @staticmethod
    def build_key(record):
        assert None is not record[CONCEPT.SEQUENCING.ID]
        assert None is record[CONCEPT.SEQUENCING.DRS_URI]

        return record.get(CONCEPT.SEQUENCING_GENOMIC_FILE.UNIQUE_KEY) or join(
            record[CONCEPT.SEQUENCING_GENOMIC_FILE.ID]
        )

    @staticmethod
    def build_entity(record, key, get_target_id_from_record):
        study_id = record[CONCEPT.STUDY.ID]
        seq_filename = record.get(CONCEPT.SEQUENCING_GENOMIC_FILE.ID)
        seq_id = record.get(CONCEPT.SEQUENCING.ID)
        file_format = record.get(CONCEPT.GENOMIC_FILE.FILE_FORMAT)
        seq_center = record.get(CONCEPT.SEQUENCING.CENTER.ID)
        specimen = get_target_id_from_record(Specimen, record)
        data_date_generation = record.get(CONCEPT.SEQUENCING.DATE)
        drs_uri = record.get(CONCEPT.SEQUENCING.DRS_URI)

        entity = {
            "resourceType": SequencingFile.resource_type,
            "id": get_target_id_from_record(SequencingFile, record),
            "meta": {
                "profile": [
                    f"http://hl7.org/fhir/StructureDefinition/{SequencingFileNoDrs.resource_type}"
                ]
            },            
            "status": "current",
            "author" : [
                {
                    "reference": f"{SequencingCenter.resource_type}/{seq_center}",
                    "display": seq_center
                }
            ],
            "subject": {
            	"reference": f"Patient/{get_target_id_from_record(Patient, record)}",
            	"display" : f"{record.get(CONCEPT.PARTICIPANT.ID)}"
            },

            "identifier": [
                {
                    "system": "urn:ncpi:unique-string",
                    "value": join("ncpi-drs-document-reference", seq_id),
                },
            ],
            "description": "production of sequence data",
        	"content": [
        		{
                    "attachment": {
                        "title": seq_filename
                    },
                    "format": {
                        "display": "Sequence Filename"
                    }
        		}
        	]
        }

        if data_date_generation:
            entity['date'] = data_date_generation + "T00:00:00+06:00"

        return entity
