"""
Load discover values into the FHIR server

Variant -- http://hl7.org/fhir/uv/genomics-reporting/STU1/variant.html
    variant is ultimately derived from observation, but by way of all sort of genetic specific profiles

    specimen => Reference to Specimen (from structure definition, Finding)

    components:
        (From Finding profile http://hl7.org/fhir/uv/genomics-reporting/STU1/finding.html )
        gene studied ID:    (need code for each gene). Display will be the gene name
        cytogenic (chromosome) location:  is crhmosome
        ref-sequence-assembly: variang_genome_build

        (from Variant profile http://hl7.org/fhir/uv/genomics-reporting/STU1/variant.html )
        exact-start-end: pos
        ref-allele: ref
        alt-allele: alt
        allele-state:   zygosity
        dna-chg:        hgsvc
        dna-chg-type:   ?? May need this http://www.sequenceontology.org/

        amino-acid-chg: hgsvp
        amino-acid-chg-type     Wild type | Deletion | Duplication | Frameshift | Initiating Methionine | Insertion | Insertion and Deletion | Missense | Silent | Stop Codon Mutation  (https://r.details.loinc.org/AnswerList/LL380-7.html)
                -- Does this map to sv and and type?

        transcript-ref-seq ->   transcript  presumably system http://www.ncpi.nlm.nih.gov

        variant-inheritance -> inheritance_description?? They point to sequence ontology once again
        
DiagnosticImplication   http://hl7.org/fhir/uv/genomics-reporting/StructureDefinition/diagnostic-implication file:///E:/Downloads/full-ig%20(1)/site/Observation-obs-idh-ex.json.html
InheritedDiseasePathogenicity http://hl7.org/fhir/uv/genomics-reporting/inherited-disease-pathogenicity.html
    code:   -> significance (Pathogenic | Likely pathogenic | Uncertain significance | Likely benign | Benign)

    componet:
        associated-phenotype
        mode-of-inheritance: -> inheritance_description     (Autosomal dominant|Autosomal recessive|X-linked dominant|X-linked recessive|Y-linked|Codominant|Mitochondrial      )

"""

import sys

from ncpi_fhir_plugin.shared import join, make_identifier
from ncpi_fhir_plugin.common import constants, CONCEPT, add_loinc_coding
from ncpi_fhir_plugin.target_api_builders.specimen import Specimen

class DiscoveryVariant:
    class_name = "discovery_variant"
    resource_type = "Observation"
    target_id_concept = CONCEPT.DISCOVERY.VARIANT.TARGET_SERVICE_ID

    @staticmethod
    def build_key(record):
        assert None is not record[CONCEPT.PARTICIPANT.ID]
        assert None is not record[CONCEPT.STUDY.ID]
        assert None is not record[CONCEPT.DISCOVERY.VARIANT.ID]

        return record.get(CONCEPT.DISCOVERY.VARIANT.UNIQUE_KEY) or join(
            record[CONCEPT.STUDY.ID],
            record[CONCEPT.DISCOVERY.VARIANT.ID]
        )

    @staticmethod
    def build_entity(record, key, get_target_id_from_record):
        study_id = record[CONCEPT.STUDY.ID]
        biospecimen_id = get_target_id_from_record(Specimen, record)
        subject_id = record[CONCEPT.PARTICIPANT.ID]
        variant_id = record[CONCEPT.DISCOVERY.VARIANT.ID]         

        gene = record[CONCEPT.DISCOVERY.GENE.ID]        # HGNCID (or other)
        gene_code = record[CONCEPT.DISCOVERY.GENE.GENE_CODE] # The human readable gene 'symbol'
        gene_class = record[CONCEPT.DISCOVERY.GENE.GENE_CLASS]
        inheritance = record[CONCEPT.DISCOVERY.VARIANT.INHERITANCE]
        zygosity = record[CONCEPT.DISCOVERY.VARIANT.ZYGOSITY]
        genome_build = record[CONCEPT.DISCOVERY.VARIANT.GENOME_BUILD]
        chrom = record[CONCEPT.DISCOVERY.VARIANT.CHROM]
        pos = record[CONCEPT.DISCOVERY.VARIANT.POS]
        ref = record[CONCEPT.DISCOVERY.VARIANT.REF]
        alt = record[CONCEPT.DISCOVERY.VARIANT.ALT]
        hgvsc = record[CONCEPT.DISCOVERY.VARIANT.HGVSC]
        hgvsp = record[CONCEPT.DISCOVERY.VARIANT.HGVSP]
        transcript = record[CONCEPT.DISCOVERY.VARIANT.TRANSCRIPT]
        sv_name = record[CONCEPT.DISCOVERY.VARIANT.SV_NAME]
        sv_type = record[CONCEPT.DISCOVERY.VARIANT.SV_TYPE]

        entity = {
            "resourceType": DiscoveryVariant.resource_type,
            "id": get_target_id_from_record(DiscoveryVariant, record),
            "meta": {
                "profile": [
                     f"http://hl7.org/fhir/StructureDefinition/{DiscoveryVariant.resource_type}"
                ]
            },
            "identifier": [
                {
                    "system": "urn:ncpi:unique-string",
                    "value": join(DiscoveryVariant.resource_type, key),
                }
            ],
            "status": "final",
            "category" : [
                {
                    "coding" : [
                        {
                            "system" : "http://terminology.hl7.org/CodeSystem/observation-category",
                            "code" : "laboratory"
                        }
                    ]
                }
            ],
            "code":     {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "69548-6",
                        "display": "Genetic variant assessment"
                    }
                ]
            },
            "valueCodeableConcept" : {
                "coding" : [
                    {
                        "system" : "http://loinc.org",
                        "code" : "LA9633-4",
                        "display" : "Present"
                    }
                ]
            },
            "method" : {
                "coding" : [
                    {
                        "system" : "http://loinc.org",
                        "code" : "LA26398-0",
                        "display" : "Sequencing"
                    }
                ]
            },
            "specimen": {
                "reference": f"{Specimen.resource_type}/{biospecimen_id}",
                "display" : "Specimen"
            },
            "component": [ ]
        }

        if gene:
            entity["component"].append(
                {
                    "code": {
                        "coding" : [
                            {
                                "system": "http://loinc.org",
                                "code": "48018-6",
                                "display": "Gene studied ID"
                            }
                        ]
                    },
                    "valueCodeableConcept": {
                        "coding": [
                            {
                                "system": f"https://www.ncbi.nlm.nih.gov/gene",
                                "code": gene,
                                "display" : gene_code
                            }
                        ]
                    }
                }
            )

        if chrom:
            entity['component'].append(
                {
                    "code" : {
                        "coding" : [
                            {
                                "system" : "http://loinc.org",
                                "code" : "48001-2",
                                "display" : "Cytogenetic (chromosome) location"
                            }
                        ]
                    },
                    "valueCodeableConcept" : add_loinc_coding(chrom)
                }
            )

        if pos:
            if "-" in pos:
                rangevals = pos.split("-")
                value_range = {
                    "low": {
                        "value": int(rangevals[0])
                    },
                    "high": {
                        "value" : int(rangevals[1])
                    }
                }
            else:
                value_range = {
                    "low": {
                        "value": int(pos)
                    }
                }
            entity['component'].append(
                {
                    "code" : {
                    "coding" : [
                        {
                            "system" : "http://hl7.org/fhir/uv/genomics-reporting/CodeSystem/tbd-codes",
                            "code" : "exact-start-end",
                            "display" : "Variant exact start and end"
                        }
                    ]
                },
                    "valueRange" : value_range
                }
            )
        if ref:
            entity['component'].append(
                {
                    "code" : {
                        "coding" : [
                            {
                                "system" : "http://loinc.org",
                                "code" : "69547-8",
                                "display" : "Genomic ref allele [ID]"
                            }
                        ]
                    },
                    "valueString" : ref
                }
            )

        if alt:
            entity['component'].append(
                {
                    "code" : {
                        "coding" : [
                            {
                                "system" : "http://loinc.org",
                                "code" : "69551-0",
                                "display" : "Genomic alt allele [ID]"
                            }
                        ]
                    },
                    "valueString" : alt
                }
            )
        if zygosity:
            entity['component'].append(
                {
                    "code" : {
                        "coding" : [
                            {
                                "system" : "http://loinc.org",
                                "code" : "53034-5",
                                "display" : "Allelic state"
                            }
                        ]
                    },
                    "valueCodeableConcept" : add_loinc_coding(zygosity)
                }
            )
        if genome_build:
            entity['component'].append(
                {
                    "code" : {
                        "coding" : [
                            {
                                "system" : "http://loinc.org",
                                "code" : "62374-4",
                                "display" : "Human reference sequence assembly version"
                            }
                        ]
                    },
                    "valueCodeableConcept" : add_loinc_coding(genome_build)
                }
            )            

        if transcript:
            entity['component'].append(
                {
                    "code" : {
                        "coding" : [
                            {
                                "system" : "http://loinc.org",
                                "code" : "51958-7",
                                "display" : "Transcript reference sequence [ID]"
                            }
                        ]
                    },
                    "valueCodeableConcept" : {
                        "coding" : [
                            {
                                "system" : "http://www.ncbi.nlm.nih.gov/refseq",
                                "code" : transcript,
                                "display" : transcript
                            }
                        ]
                    }
                }
            )

        if hgvsc:
            entity['component'].append(
                {
                    "code" : {
                        "coding" : [
                            {
                                "system" : "http://loinc.org",
                                "code" : "48004-6",
                                "display" : "DNA change (c.HGVS)"
                            }
                        ]
                    },
                    "valueCodeableConcept" : {
                        "coding" : [
                            {
                                "system" : "http://varnomen.hgvs.org",
                                "code" : f"{hgvsc}",
                                "display" : f"{hgvsc}"
                            }
                        ]
                    }
                }
            )
        if hgvsp:
            entity['component'].append(
                {
                    "code" : {
                        "coding" : [
                            {
                                "system" : "http://loinc.org",
                                "code" : "48005-3",
                                "display" : "Amino acid change (pHGVS)"
                            }
                        ]
                    },
                    "valueCodeableConcept" : {
                        "coding" : [
                            {
                                "system" : "http://varnomen.hgvs.org",
                                "code" : hgvsp,
                                "display" : hgvsp
                            }
                        ]
                    }
                }
            )

        if sv_type:
            entity['component'].append(
                {
                    "code" : {
                        "coding" : [
                            {
                                "system" : "http://loinc.org",
                                "code" : "48006-1",
                                "display" : "Amino acid change type"
                            }
                        ]
                    },
                    "valueCodeableConcept" : add_loinc_coding(sv_type, sv_name)
                }
            )
        return entity
