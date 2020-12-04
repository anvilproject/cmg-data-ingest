"""
Represents some of the disease specific aspsects associated with the variation, such as the inheritance.

"""

import sys

from ncpi_fhir_plugin.shared import join, make_identifier
from ncpi_fhir_plugin.common import constants, CONCEPT, add_loinc_coding
from ncpi_fhir_plugin.target_api_builders.specimen import Specimen
from ncpi_fhir_plugin.target_api_builders.discovery_variant import DiscoveryVariant

from fhirwood.reference import Reference
from fhirwood.coding import Coding
from fhirwood.identifier import Identifier

class DiscoveryImplication:
    class_name = "discovery_implication"
    resource_type = "Observation"
    target_id_concept = CONCEPT.DISCOVERY.VARIANT.TARGET_SERVICE_ID

    @staticmethod
    def build_key(record):
    	# These are required for the variant
        assert None is not record[CONCEPT.STUDY.ID]
        assert None is not record[CONCEPT.DISCOVERY.VARIANT.ID]
        assert None is not record[CONCEPT.BIOSPECIMEN.ID]
        assert None is not record[CONCEPT.DISCOVERY.VARIANT.INHERITANCE]

        return join(
            record[CONCEPT.STUDY.ID],
            record[CONCEPT.DISCOVERY.VARIANT.ID],
            record[CONCEPT.DISCOVERY.VARIANT.INHERITANCE]
        )

    @staticmethod
    def build_entity(record, key, get_target_id_from_record):
        study_id = record[CONCEPT.STUDY.ID]
        biospecimen_id = get_target_id_from_record(Specimen, record)
        subject_id = record[CONCEPT.PARTICIPANT.ID]
        variant_id = record[CONCEPT.DISCOVERY.VARIANT.ID]         
        inheritance = record[CONCEPT.DISCOVERY.VARIANT.INHERITANCE]

        signif = record[CONCEPT.DISCOVERY.VARIANT.SIGNIFICANCE]

        entity = {
            "resourceType": DiscoveryImplication.resource_type,
            "id": get_target_id_from_record(DiscoveryImplication, record),
            "meta": {
                "profile": [
                     f"http://hl7.org/fhir/StructureDefinition/{DiscoveryImplication.resource_type}"
                ]
            },
            "identifier": Identifier(
                    system="urn:ncpi:unique-string",
                    value=join(DiscoveryVariant.resource_type, key),
                    is_list=True).as_obj(),
            "status": "final",
            "category" : [ 
                {
                    "coding" : Coding(
                            system="http://terminology.hl7.org/CodeSystem/observation-category", 
                            code="laboratory", 
                            is_list=True).as_obj() 
                }
            ],
            "code":     {
                "coding": Coding(
                            system="http://hl7.org/fhir/uv/genomics-reporting/CodeSystem/tbd-codes",
                            code="diagnostic-implication",
                            display="Diagnostic Implication",
                            is_list=True).as_obj()
            },
            "specimen": Reference(
                            ref=f"{Specimen.resource_type}/{biospecimen_id}", 
                            display="Specimen").as_obj(),
            "derivedFrom": [ 
                Reference(ref=f"{DiscoveryVariant.resource_type}/{get_target_id_from_record(DiscoveryVariant, record)}").as_obj()
            ],
            "component": [ 
                {
                    "code" : {
                            "coding" : Coding(
                                    system="http://hl7.org/fhir/uv/genomics-reporting/CodeSystem/tbd-codes",
                                    code="mode-of-inheritance",
                                    display="mode-of-inheritance",
                                    is_list=True).as_obj()
                        },
                        "valueCodeableConcept" : {
                        "coding" : Coding(
                                system="http://ghr.nlm.nih.gov/primer/inheritance/inheritancepatterns",
                                code=inheritance,
                                display=inheritance,
                                is_list=True).as_obj()
                    }
                }
            ]
        }

        if signif:
            entity['component'].append(
                {
                    "code": {
                        "coding": Coding(
                                system="http://loinc.org",
                                code="53037-8",
                                display= "Genetic variation clinical significance [Imp]",
                                is_list=True).as_obj()
                    },
                    "valueCodeableConcept": add_loinc_coding(signif)
                }
            )

        # If we end up wanting to apply the clinvar url as an extension, it would be like this:
        # https://www.ncbi.nlm.nih.gov/clinvar/variation/{cvid}/#clinical-assertions
        # cvid is what we get when we probed the NIH for the hgsvc match

        return entity

