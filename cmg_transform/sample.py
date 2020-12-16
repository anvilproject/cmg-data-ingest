
from ncpi_fhir_plugin.common import CONCEPT, constants
from cmg_transform import Transform
from term_lookup import pull_details, write_cache

tissue_type_replacements = {
    "whole blood": "UBERON:0000178"
}

class Sample:
    # We have some data that has been broken into 2 sets of files, which 
    # we have to merge. Rather than deal with it outside, we'll just
    # skip rows where the sample ID has already been opserved
    observed = set()
    def __init__(self, row, family_lkup, subid_lkup):
        self.id = Transform.CleanSubjectId(row['subject_id']) #Transform.CleanSubjectId(row['subject_id'])
        self.fam_id = family_lkup[self.id]
        self.sample_id = row['sample_id']
        self.dbgap_sample_id = row['dbgap_sample_id']
        self.sample_source = row['sample_source']

        if 'sequencing_center' in row:
            self.sample_provider = row['sequencing_center']
        else:
            self.sample_provider = row['sample_provider']

        self.tissue_affected_status = Transform.CleanVar(constants.PHENOTYPE.OBSERVED, row.get('tissue_affected_status'))
        
        if self.sample_source in tissue_type_replacements:
            self.sample_source = tissue_type_replacements[self.sample_source]
        sample_details = pull_details(self.sample_source)
        self.sample_source_name = None
        if sample_details:
            self.sample_source_name = sample_details.name

        subid_lkup[self.sample_id] = self.id
        Sample.observed.add(self.sample_id)

    @classmethod
    def write_default_header(cls, writer):
        writer.writerow([
            CONCEPT.FAMILY.ID,
            CONCEPT.PARTICIPANT.ID,
            CONCEPT.BIOSPECIMEN.ID,
            CONCEPT.BIOSPECIMEN.DBGAP_ID,
            CONCEPT.STUDY.NAME,
            CONCEPT.SEQUENCING.CENTER.ID,
            CONCEPT.BIOSPECIMEN.TISSUE_TYPE,
            CONCEPT.BIOSPECIMEN.TISSUE_TYPE_NAME,
            CONCEPT.BIOSPECIMEN.TISSUE_AFFECTED_STATUS
            ])

    def write_row(self, study_name, writer):
        sample_source = self.sample_source
        sample_source_name = self.sample_source_name

        if sample_source_name is None or sample_source_name.strip() == "":
            sample_source = None
            sample_source_name = None
        # FHIR Doesn't like empty names, so if we couldn't find
        # the appropriate code, we have to skip it for now
        writer.writerow([
            self.fam_id,
            self.id,
            self.sample_id,
            self.dbgap_sample_id,
            study_name,
            self.sample_provider, 
            sample_source,
            sample_source_name,
            self.tissue_affected_status
        ])