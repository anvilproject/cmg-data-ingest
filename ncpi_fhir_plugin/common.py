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

class AffectedStatus:
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

concept_property_set=compile_schema()

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
