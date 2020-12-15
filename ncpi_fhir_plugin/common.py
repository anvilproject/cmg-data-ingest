# Constants and concepts that deviate from the KF ingest library, but are 
# required by the NCPI model

# We are using the KF ingest library, but it doesn't support 100% of the fields
# that we expect to need. This will modify both the concept map and the 
# constant values
from kf_lib_data_ingest.common import constants
from kf_lib_data_ingest.common.concept_schema import (
    CONCEPT, 
    PropertyMixin, 
    concept_property_set, 
    compile_schema
)

# For now, I'm going to just append the values to CONCEPT and constants that
# I want to work with. We'll figure out the proper way to add these into 
# the actual library at a later date. 
CONCEPT.DBGAP_STUDY_ID = 'DBGAP_STUDY_ID'
CONCEPT.DBGAP_ID = 'PARTICIPANT|DBGAP_ID'
CONCEPT.PARTICIPANT.DBGAP_SAMPLE_ID = 'PARTICIPANT|SAMPLE|DBGAP_ID'
CONCEPT.PARTICIPANT.ANCESTRY_DETAIL = 'PARTICIPANT|ANCESTRY_DETAIL'
CONCEPT.PARTICIPANT.AGE_AT_LAST_OBSERVATION = 'PARTICIPANT|AGE_AT_LAST_OBSERVATION'
CONCEPT.DIAGNOSIS.DESCRIPTION = 'DIAGNOSIS|DESCRIPTION'
CONCEPT.DIAGNOSIS.DISEASE_ID = 'DIAGNOSIS|DISEASE_ID'
CONCEPT.DIAGNOSIS.DISEASE_ALTERNATE_IDS = 'DIAGNOSIS|DISEASE_ALTERNATE_IDS'
CONCEPT.DIAGNOSIS.AGE_ONSET = 'DIAGNOSIS|AGE_ONSET'
CONCEPT.DIAGNOSIS.AFFECTED_STATUS = 'DIAGNOSIS|AFFECTED_STATUS'
CONCEPT.DIAGNOSIS.SYSTEM = 'DIAGNOSIS|SYSTEM'
CONCEPT.DIAGNOSIS.PHENOTYPES_PRESENT = 'DIAGNOSIS|PHENOTYPES_PRESENT'
CONCEPT.DIAGNOSIS.PHENOTYPES_ABSENT = 'DIAGNOSIS|PHENOTYPES_ABSENT'
CONCEPT.PHENOTYPE.DESCRIPTION = 'DIAGNOSIS|PHENOTYPE|DESCRIPTION'
CONCEPT.BIOSPECIMEN.AFFECTED_STATUS = 'BIOSPECIMEN|TISSUE_AFFECTED_STATUS'
CONCEPT.BIOSPECIMEN.DBGAP_ID = 'BIOSPECIMEN|DBGAP_ID'
CONCEPT.SEQUENCING.ASSAY = 'SEQUENCING|ASSAY'
CONCEPT.SEQUENCING.CAPTURE_REGION = 'SEQUENCING|CAPTURE_REGION'
CONCEPT.SEQUENCING.ALIGNMENT_METHOD = 'SEQUENCING|ALIGNMENT_METHOD'
CONCEPT.SEQUENCING.DATA_PROC_PIPELINE = 'SEQUENCING|DATA_PROC_PIPELINE'
CONCEPT.SEQUENCING.FUNCTIONAL_EQUIVALENCE_PIPELINE = 'SEQUENCING|FUNCTIONAL_EQUIVALENCE_PIPELINE'
CONCEPT.SEQUENCING.DRS_URI = 'SEQUENCING|DRS_URI'

class SampleProvider(PropertyMixin):
    NAME = None
    class SUBJECT(PropertyMixin):
        CONSENT = None
        STATUS = None

CONCEPT.STUDY.PROVIDER = SampleProvider
class TissueStatus(PropertyMixin):
    NAME = "BIOSPECIMEN|TISSUE|AFFECTED_STATUS"

class AffectedStatus(PropertyMixin):
    AFFECTED = "Affected"
    UNAFFECTED = "Unaffected"
    POSSIBLY_AFFECTED = "Possibly affected"

CONCEPT.BIOSPECIMEN.TISSUE_AFFECTED_STATUS = TissueStatus   
CONCEPT.BIOSPECIMEN.TISSUE_TYPE_NAME = "BIOSPECIMEN|TISSUE_TYPE|NAME"
#constants.SPECIMEN.TISSUE_TYPE.AFFECTED = "Affected"
#constants.SPECIMEN.TISSUE_TYPE.UNAFFECTED = "Unaffected"
#constants.SPECIMEN.TISSUE_TYPE.POSSIBLY_AFFECTED = "Possibly affected"
constants.AFFECTED_STATUS = AffectedStatus
constants.PHENOTYPE.OBSERVED.PRESENT = "Present"
constants.PHENOTYPE.OBSERVED.ABSENT = "Absent"

class DISCOVERY(PropertyMixin):
    class GENE(PropertyMixin):
        GENE_CLASS = None
        GENE_CODE = None        # Human readable gene 'symbol'
        GENE_SYSTEM = None      # Used in FHIR for system id, so URL/URI for terminology source

    class VARIANT(PropertyMixin):
        INHERITANCE = None
        ZYGOSITY = None
        GENOME_BUILD = None

        CHROM = None
        POS = None
        REF = None
        ALT = None
        HGVSC = None
        HGVSP = None
        TRANSCRIPT = None
        SV_NAME = None
        SV_TYPE = None
        SIGNIFICANCE = None

        class VARIANT_REPORT(PropertyMixin):
            VARIANTS = None


CONCEPT.DISCOVERY = DISCOVERY

class DiscoveryConstants:
    class GENE:
        class GENE_CLASS:
            KNOWN = "Known"
            Tier1 = "Tier1"
            Tier2 = "Tier2"
    class VARIANT:
        class CHROMOSOME:
            CHR1 = 'Chr1'
            CHR2 = 'Chr2'
            CHR3 = 'Chr3'
            CHR4 = 'Chr4'
            CHR5 = 'Chr5'
            CHR6 = 'Chr6'
            CHR7 = 'Chr7'
            CHR8 = 'Chr8'
            CHR9 = 'Chr9'
            CHR10 = 'Chr10'
            CHR11 = 'Chr11'
            CHR12 = 'Chr12'
            CHR13 = 'Chr13'
            CHR14 = 'Chr14'
            CHR15 = 'Chr15'
            CHR16 = 'Chr16'
            CHR17 = 'Chr17'
            CHR18 = 'Chr18'
            CHR19 = 'Chr19'
            CHR20 = 'Chr20'
            CHR21 = 'Chr21'
            CHR22 = 'Chr22'
            CHRX = 'ChrX'
            CHRY = 'ChrY'  
        class ZYGOSITY:
            HETEROZYGOUS = "Heterozygous"
            HOMOZYGOUS = "Homozygous"
            HEMIZYGOUS = "Hemizygous"
            HETEROPLASMIC = "Heteroplasmic"
            HOMOPLASMIC = "Homoplasmic"
        class GENOME_BUILD:
            NCBI34 = "NCBI34"
            NCBI35 = "NCBI35"
            NCBI36 = "NCBI36"
            GRCh37 = "GRCh37"
            GRCh38 = "GRCh38"
        class SV_TYPE:
            DELETION = "Deletion"
            DUPLICATION = "Duplication"
            MULTIALLELIC_CNV = "Multiallelic CNV"
            INSERTION = "Insertion"
            INVERSION = "Inversion"
            COMPLEX_SVS = "Complex SVs"
        class SIGNIFICANCE:
            BENIGN = "Benign"
            LIKELY_BENIGN = "Likely benign"
            UNCERTAIN_SIGNIFICANCE = "Uncertain significance"
            SUSPECTED_PATHOGENIC = "Suspectedpathogenic"
            LIKELY_PATHOGENIC = "Likely pathogenic"
            PATHOGENIC = "Pathogenic"
        class INHERITANCE:
            DE_NOVO = "de novo"
            AUTOSOMAL_RECESSIVE_HOMOZYGOUS = "Autosomal recessive (homozygous)"
            AUTOSOMAL_RECESSIVE_COMPOUND_HETERO = "Autosomal recessive (compound heterozygous)"
            AUTOSOMAL_DOMINANT = "Autosomal dominant"
            X_LINKED = "X-linked"
            MITOCHONDRIAL = "Mitochondrial"
            Y_LINKED = "Y-linked"
            CONTIGUOUS_GENE_SYNDROME = "Contiguous gene syndrome"
            SOMATIC_MOSAICISM = "Somatic mosaicism"
constants.DISCOVERY = DiscoveryConstants
concept_property_set=compile_schema()

#https://fhir.loinc.org/ValueSet/LL381-5    -- Zygosity
#https://fhir.loinc.org/ValueSet/LL1040-6   -- Genome Builds
#https://loinc.org/LL4033-8/                -- structure variant types

#   CONCEPT.DISCOVERY.VARIANT.SV_TYPE.MULTIALLELIC_CNV: '',
LOINC_LOOKUP = {
    constants.DISCOVERY.VARIANT.ZYGOSITY.HETEROZYGOUS: 'LA6706-1',
    constants.DISCOVERY.VARIANT.ZYGOSITY.HOMOZYGOUS: 'LA6705-3',
    constants.DISCOVERY.VARIANT.ZYGOSITY.HEMIZYGOUS: 'LA6707-9',
    constants.DISCOVERY.VARIANT.ZYGOSITY.HETEROPLASMIC: 'LA6703-8',
    constants.DISCOVERY.VARIANT.ZYGOSITY.HOMOPLASMIC: 'LA6704-6',
    constants.DISCOVERY.VARIANT.GENOME_BUILD.NCBI34: 'LA14032-9',
    constants.DISCOVERY.VARIANT.GENOME_BUILD.NCBI35: 'LA14031-1',
    constants.DISCOVERY.VARIANT.GENOME_BUILD.NCBI36: 'LA14030-3',
    constants.DISCOVERY.VARIANT.GENOME_BUILD.GRCh37: 'LA14029-5',
    constants.DISCOVERY.VARIANT.GENOME_BUILD.GRCh38: 'LA26806-2',
    constants.DISCOVERY.VARIANT.SV_TYPE.DELETION: 'LA6692-3',
    constants.DISCOVERY.VARIANT.SV_TYPE.DUPLICATION: 'LA6686-5',
    constants.DISCOVERY.VARIANT.SV_TYPE.INSERTION: 'LA6687-3',
    constants.DISCOVERY.VARIANT.SV_TYPE.INVERSION: 'LA6689-9',
    constants.DISCOVERY.VARIANT.SV_TYPE.COMPLEX_SVS: 'LA26330-3',
    constants.DISCOVERY.VARIANT.SIGNIFICANCE.BENIGN: 'LA6675-8',
    constants.DISCOVERY.VARIANT.SIGNIFICANCE.LIKELY_BENIGN: 'LA6674-1', # Presumed Benign
    constants.DISCOVERY.VARIANT.SIGNIFICANCE.UNCERTAIN_SIGNIFICANCE: 'LA6682-4', #Unknown Significance
    constants.DISCOVERY.VARIANT.SIGNIFICANCE.SUSPECTED_PATHOGENIC: 'LA6669-1',  # Exactly how does suspected and likely differ?
    constants.DISCOVERY.VARIANT.SIGNIFICANCE.LIKELY_PATHOGENIC: 'LA6669-1',
    constants.DISCOVERY.VARIANT.SIGNIFICANCE.PATHOGENIC: 'LA6668-3',
    constants.DISCOVERY.VARIANT.CHROMOSOME.CHR1: 'LA21254-0',
    constants.DISCOVERY.VARIANT.CHROMOSOME.CHR2: 'LA21255-7',
    constants.DISCOVERY.VARIANT.CHROMOSOME.CHR3: 'LA21256-5',
    constants.DISCOVERY.VARIANT.CHROMOSOME.CHR4: 'LA21257-3',
    constants.DISCOVERY.VARIANT.CHROMOSOME.CHR5: 'LA21258-1',
    constants.DISCOVERY.VARIANT.CHROMOSOME.CHR6: 'LA21259-9',
    constants.DISCOVERY.VARIANT.CHROMOSOME.CHR7: 'LA21260-7',
    constants.DISCOVERY.VARIANT.CHROMOSOME.CHR8: 'LA21261-5',
    constants.DISCOVERY.VARIANT.CHROMOSOME.CHR9: 'LA21262-3',
    constants.DISCOVERY.VARIANT.CHROMOSOME.CHR10: 'LA21263-1',
    constants.DISCOVERY.VARIANT.CHROMOSOME.CHR11: 'LA21264-9',
    constants.DISCOVERY.VARIANT.CHROMOSOME.CHR12: 'LA21265-6',
    constants.DISCOVERY.VARIANT.CHROMOSOME.CHR13: 'LA21266-4',
    constants.DISCOVERY.VARIANT.CHROMOSOME.CHR14: 'LA21267-2',
    constants.DISCOVERY.VARIANT.CHROMOSOME.CHR15: 'LA21268-0',
    constants.DISCOVERY.VARIANT.CHROMOSOME.CHR16: 'LA21269-8',
    constants.DISCOVERY.VARIANT.CHROMOSOME.CHR17: 'LA21270-6',
    constants.DISCOVERY.VARIANT.CHROMOSOME.CHR18: 'LA21271-4',
    constants.DISCOVERY.VARIANT.CHROMOSOME.CHR19: 'LA21272-2',
    constants.DISCOVERY.VARIANT.CHROMOSOME.CHR20: 'LA21273-0',
    constants.DISCOVERY.VARIANT.CHROMOSOME.CHR21: 'LA21274-8',
    constants.DISCOVERY.VARIANT.CHROMOSOME.CHR22: 'LA21275-5',
    constants.DISCOVERY.VARIANT.CHROMOSOME.CHRX: 'LA21276-3',
    constants.DISCOVERY.VARIANT.CHROMOSOME.CHRY: 'LA21277-1'
}
def add_loinc_coding(value, name = None):
    loinc_code = LOINC_LOOKUP[value]
    if name is None:
        name = value

    return {
        "coding": [ 
            {
                "system": "http://loinc.org",
                "code": loinc_code,
                "display": value
            }
        ],
        "text": name
    }

terminology = {
    # https://www.hl7.org/fhir/valueset-observation-interpretation.html
    "interpretation_status" : {
        constants.AFFECTED_STATUS.UNAFFECTED: 
        {
            "coding": [ 
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                    "code": "NEG",
                    "display": "Unaffected"
                }
            ],
            "text": "Unaffected"
        },
        constants.AFFECTED_STATUS.AFFECTED: {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                    "code": "POS",
                    "display": "Affected",
                }
            ],
            "text": "Affected"
        },
        constants.PHENOTYPE.OBSERVED.NO: 
        {
            "coding": [ 
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                    "code": "NEG",
                    "display": "Absent"
                }
            ],
            "text": "Absent"
        },
        constants.PHENOTYPE.OBSERVED.YES: {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                    "code": "POS",
                    "display": "Present",
                }
            ],
            "text": "Present"
        },
    }
}
