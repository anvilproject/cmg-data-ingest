"""
Wrapper of sorts for the complete genomics diagnostic report
"""
import sys

from ncpi_fhir_plugin.shared import join, make_identifier
from ncpi_fhir_plugin.common import constants, CONCEPT
from ncpi_fhir_plugin.target_api_builders.specimen import Specimen
from ncpi_fhir_plugin.target_api_builders.discovery_variant import DiscoveryVariant
from ncpi_fhir_plugin.target_api_builders.discovery_implication import DiscoveryImplication
from ncpi_fhir_plugin.target_api_builders.ncpi_patient import Patient

class DiscoveryReport:
    class_name = "discovery_report"
    resource_type = "DiagnosticReport"
    target_id_concept = CONCEPT.DISCOVERY.VARIANT.VARIANT_REPORT.TARGET_SERVICE_ID

    @staticmethod
    def build_key(record):
        # These are required for the variant
        assert None is not record[CONCEPT.STUDY.ID]
        assert None is not record[CONCEPT.PARTICIPANT.ID]
        assert None is not record[CONCEPT.DISCOVERY.VARIANT.ID]
        print(f"ASDF: {record[CONCEPT.STUDY.ID]} {record[CONCEPT.PARTICIPANT.ID]}")

        the_key = record.get(CONCEPT.DISCOVERY.VARIANT.VARIANT_REPORT.TARGET_SERVICE_ID) or join(
            record[CONCEPT.STUDY.ID],
            record[CONCEPT.PARTICIPANT.ID]
        )

        print(f"And the key is: {the_key}\n\n")
        return record.get(CONCEPT.DISCOVERY.VARIANT.VARIANT_REPORT.TARGET_SERVICE_ID) or join(
            record[CONCEPT.STUDY.ID],
            record[CONCEPT.PARTICIPANT.ID]
        )

    @staticmethod
    def build_entity(record, key, get_target_id_from_record):
        study_id = record[CONCEPT.STUDY.ID]
        patient_id = record[CONCEPT.PARTICIPANT.ID]
        print(f"{study_id}|{patient_id} -- {record[CONCEPT.DISCOVERY.VARIANT.ID]}")

        print(f"Getting the ID FOR {study_id}|{patient_id} -> {get_target_id_from_record(DiscoveryReport, record)}")

        entity = {
            "resourceType": DiscoveryReport.resource_type,
            "id": get_target_id_from_record(DiscoveryReport, record),
            "meta": {
                "profile": [
                     f"http://hl7.org/fhir/StructureDefinition/{DiscoveryReport.resource_type}"
                ]
            },
            "identifier": [
                {
                    "system": "urn:ncpi:unique-string",
                    "value": join(DiscoveryReport.resource_type, key),
                }
            ],
            "status": "final",
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "81247-9",
                        "display": "Master HL7 genetic variant reporting panel"
                    }
                ]
            },
            "subject": {
                "reference": f"Patient/{get_target_id_from_record(Patient, record)}"
            },
            "result": [

            ]
        }

        for variant in record[CONCEPT.DISCOVERY.VARIANT.ID].split("::"):
            components = variant.split("+")
            variant_id = components[0]
            biospecimen_id=  components[1]
            significance = None

            fake_row = {
                CONCEPT.STUDY.ID: study_id,
                CONCEPT.PARTICIPANT.ID: patient_id,
                CONCEPT.BIOSPECIMEN.ID: biospecimen_id,
                CONCEPT.DISCOVERY.VARIANT.ID: variant_id
            }

            di = None
            dv = None
            if len(components) > 2:
                fake_row[CONCEPT.DISCOVERY.VARIANT.INHERITANCE] = components[2]
                di = get_target_id_from_record(DiscoveryImplication, fake_row)
            else:
                dv = get_target_id_from_record(DiscoveryVariant, fake_row)

            if dv:
                entity['result'].append({
                    "reference": f"Observation/{dv}"
                })

            if di:
                entity['result'].append({
                    "reference": f"Observation/{di}"
                })

        return entity