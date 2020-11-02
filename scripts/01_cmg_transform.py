#!/usr/bin/env python

"""
    Simply translate the flat CMG data into tables ready for push to fhir server
"""

import csv
from ncpi_fhir_plugin.common import CONCEPT, constants

from pathlib import Path
import collections
import sys

from yaml import load, FullLoader

from term_lookup import pull_details, write_cache
import term_lookup
from fhir_walk.config import DataConfig 

from argparse import ArgumentParser, FileType

def ParseDate(value):
    # 20160525  -- May need to test for "-" and "/" or other characters
    if len(value.strip()) == 8:
        year = value[0:4]
        month = value[4:6]
        day = value[6:]

        return f"{year}-{month}-{day}"
    return None


# subject_id    paternal_id maternal_id twin_id proband_relationship    sex affected_status hpo_present hpo_absent  age_of_onset    congenital_status   age_at_last_observation prior_testing   family_id   ancestry    ancestry_detail disease_id  phenotype_description   disease_description phenotype_group project_id  solve_state dbgap_submission    dbgap_study_id  dbgap_subject_id    multiple_datasets   pmid_id
# fd-sub1   fd-sub2 fd-sub3     Proband Male    Affected    HP:0000076|HP:0000126|HP:0000218|HP:0000276|HP:0000297|HP:0000391|HP:0000508|HP:0000535|HP:0000545|HP:0000637|HP:0000736|HP:0000752|HP:0000767|HP:0000960|HP:0001162|HP:0001265|HP:0001385|HP:0001647|HP:0001845|HP:0002019|HP:0002020|HP:0002342|HP:0002558|HP:0002650|HP:0003186|HP:0003191|HP:0003429|HP:0008577|HP:0008689|HP:0009765|HP:0010297|HP:0011330|HP:0012804|HP:0003468|HP:0000481|HP:0002616|HP:0000606|HP:0010485           Congenital onset        SNP Array|MLL2|KDM6A    fd-fam1 White   Italian OMIM:108120|ORPHA:1147                  Unsolved    No  phs000711       No  


# Useful constants:
# constantsANTS.RELATIONSHIP

# TODO
# To attempt to reach the deadline, I'm just jamming in anything that doesn't fit
# Some of these really do need to be handled more carefully

class Transform:
    # If it's a valid entry, but not one in the constant's list, then we will 
    # attempt to convert it to one that will be supported by our fhir server's 
    # model configuration

    # KF Constant class  => { expected => transformed }
    _alt_transforms = {
        constants.PHENOTYPE.OBSERVED : {
            "Affected": constants.PHENOTYPE.OBSERVED.YES,
            "Unaffected": constants.PHENOTYPE.OBSERVED.NO,
            '': '',
            'Unknown': '',
        },
        constants.RACE : {
            "Black or African American" : constants.RACE.BLACK,
            "American Indian or Alaskan Native": constants.RACE.NATIVE_AMERICAN,
            "Unknown": constants.COMMON.UNKNOWN,
            'Other': constants.COMMON.OTHER,
            '': None
        },
        constants.GENDER : {
            "Intersex": constants.COMMON.OTHER,
            "Unknown" : "unknown"
        },
        constants.AFFECTED_STATUS : {
            '' : "",
            "Unknown": constants.COMMON.UNKNOWN,
            'Other': constants.COMMON.OTHER
        },
        constants.COMMON: {
            "yes" : "true",
            "no" : "false"
        },
        constants.RELATIONSHIP: {
            "mother's cousin #2": ''
        }
    }


    def CleanVar(constobj, val, default_to_empty=False):
        # Definitely want to get rid of whitespace

        if val is not None:
            propname = val.strip().upper().replace(" ", "_")
            try:
                # This is just a way to verify that our data conforms to constants
                # If it works, then we have our value. We'll take the extracted value
                # so that case coming in doesn't have to match
                propname = getattr(constobj, propname)
                return propname
            except AttributeError as e:
                if default_to_empty:
                    return ""

                if val in Transform._alt_transforms[constobj]:
                    return Transform._alt_transforms[constobj][val]
                # if this excepts, then we need to figure out what is going wrong
                # Eventually, this will become it's own exception which can be handled
                # nicely at the application layer
                raise e         
        return None

    def CleanSubjectId(var):
        # For now, just strip the character data from the strings
        return var
        #return var.replace("fd-sub", "")

class Disease:
    def __init__(self, row, family_lkup):
        self.id = Transform.CleanSubjectId(row['subject_id']) # Transform.CleanSubjectId(row['subject_id'])
        self.fam_id = family_lkup[self.id]
        # For now, we are going to assert that we got only a single disease_id (or none)
        self.disease_id = row['disease_id'].split("|")

        # When we get more than one disease id, all but the primary (first?) will go here
        # and should end up in the fhir record's note
        self.alternate_diseases = []
        self.alternate_disease_names = ""


        self.disease_description = row['disease_description']
        self.disease_name = self.disease_description
        self.disease_system = None
        self.phenotype_description = row['phenotype_description']

        self.get_disease_details(row)
        
        self.hpo_present = row['hpo_present'].split("|")
        self.hpo_absent = row['hpo_absent'].split("|")
        self.affected_status = row['affected_status']
        self.age_of_onset = row['age_of_onset']

    def get_disease_details(self, row):
        primary_id = None
        primary_details = None
        alternate_details = []
        # For now, we'll ignore row. We may introduce another source for name's
        if self.disease_id is not None:
            valid_ids = []
            for id in self.disease_id:
                details = pull_details(id)

                if details:
                    if primary_id is None:
                        primary_id=id
                        primary_details = details
                    else:
                        alternate_details.append(f"{id} ( {details.name} )")
                    valid_ids.append(id)

        if primary_id is None:
            term_lookup.broken_terms[id] = row['disease_description']
            return None
        self.disease_id = valid_ids
        self.disease_name = primary_details.name
        self.disease_system = primary_details.system
        self.alternate_disease_names = " | ".join(alternate_details)

    @classmethod
    def hpo_write_header(cls, writer):
        """HPOs as part of disease are vestiges of a previous modelling idea I had, but probably won't be necessary"""
        writer.writerow([
            CONCEPT.FAMILY.ID,
            CONCEPT.PARTICIPANT.ID,
            CONCEPT.STUDY.NAME,
            CONCEPT.PHENOTYPE.HPO_ID,
            CONCEPT.PHENOTYPE.NAME,
            CONCEPT.PHENOTYPE.OBSERVED])

    def hpo_writerow(self, study_name, writer):
        for hpo in self.hpo_present:
            if hpo is not None and hpo != "":
                details = pull_details(hpo)
                if details is not None:
                    writer.writerow([
                        self.fam_id, 
                        self.id, 
                        study_name,
                        hpo,
                        details.name,
                        constants.PHENOTYPE.OBSERVED.PRESENT
                    ])
                else:
                    print(f"Unrecognized HPO Term: {hpo}")
        for hpo in self.hpo_absent:
            if hpo is not None and hpo != "":
                details = pull_details(hpo)
                if details is not None:
                    writer.writerow([
                        self.fam_id, 
                        self.id, 
                        study_name,
                        hpo,
                        details.name,
                        constants.PHENOTYPE.OBSERVED.ABSENT
                    ])
                else:
                    print(f"Unrecognized HPO Term: {hpo}")

    @classmethod
    def write_header(cls, writer):
        writer.writerow([
            CONCEPT.FAMILY.ID,
            CONCEPT.PARTICIPANT.ID,
            CONCEPT.STUDY.NAME,
            CONCEPT.DIAGNOSIS.DISEASE_ID,
            CONCEPT.DIAGNOSIS.DESCRIPTION,
            CONCEPT.DIAGNOSIS.SYSTEM,
            CONCEPT.DIAGNOSIS.NAME,
            CONCEPT.DIAGNOSIS.AGE_ONSET,
            CONCEPT.DIAGNOSIS.AFFECTED_STATUS,
            CONCEPT.DIAGNOSIS.DISEASE_ALTERNATE_IDS,
            CONCEPT.PHENOTYPE.DESCRIPTION
            ])

    def writerow(self, study_name, writer):
        if len(self.disease_id) > 0:
            writer.writerow([
                self.fam_id,
                self.id,
                study_name,
                self.disease_id[0],
                self.disease_description,
                self.disease_system,
                self.disease_name,
                self.age_of_onset,
                self.affected_status,
                self.alternate_disease_names,
                self.phenotype_description
            ])
tissue_type_replacements = {
    "whole blood": "UBERON:0000178"
}
class Sample:
    # We have some data that has been broken into 2 sets of files, which 
    # we have to merge. Rather than deal with it outside, we'll just
    # skip rows where the sample ID has already been opserved
    observed = set()
    def __init__(self, row, family_lkup, subid_lkup):
        #print(row.keys())
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

class Sequencing:
    file_cols = ['seq_filename',
        'cram_path',
        'crai_path', 
        'vcf']

    def __init__(self, row, seq_centers, subj_id):
        self.sample_id = row.get('sample_id')

        # a few of Broad's sequence entries don't have sample information associated with the
        # sequence output...so, we have to extract it from the filename
        if self.sample_id is None:
            if 'cram_or_bam_path' in row:
                self.sample_id = row['cram_or_bam_path'].split("/")[-1].split(".")[0]
            else:
                print("No sample IDs nor cram_or_bam_path")
                sys.exit(1)
        try:
            self.subject_id = Transform.CleanSubjectId(row['subject_id']) #Transform.CleanSubjectId(row['subject_id'])
        except KeyError:
            self.subject_id = subj_id[self.sample_id]
        self.seq_filenames = []     

        for col in Sequencing.file_cols:
            if col in row:
                # One of the broad's cmg datasets didn't have cram_path, but another had both
                # cram_path and cram_or_bam...and we dont' want dupes
                if row[col] not in self.seq_filenames:
                    self.seq_filenames.append(row[col])

        #self.seq_file_type = self.seq_filename.split(".")[-1]
        if 'analyte_type' in row:
            self.analyte_type = row.get('analyte_type')
        elif 'data_type' in row:
            self.analyte_type = row.get('data_type')
        else:
            self.analyte_type = None

        self.sequencing_assay = row.get('sequencing_assay')
        if 'data_type' in row:
            self.sequencing_assay = row['data_type']
        else:
            self.sequencing_assay = None
        self.library_prep_kit_method = row.get('library_prep_kit_method')
        self.exome_capture_platform = row.get('exome_capture_platform')
        self.capture_region_bed_file = row.get('capture_region_bed_file')
        self.reference_genome_build = row.get('reference_genome_build')
        self.alignment_method = row.get('alignment_method')
        self.data_processing_pipeline = row.get('data_processing_pipeline')

        self.functional_equivalence_standard = None
        if 'functional_equivalence_standard' in row:
            self.functional_equivalence_standard = Transform.CleanVar(constants.COMMON, row['functional_equivalence_standard'])
        if 'date_data_generation' in row:
            self.date_data_generation = ParseDate(row['date_data_generation'])
        elif 'release_date' in row:
            self.date_data_generation = ParseDate(row['release_date'])

        self.seq_center = None

        if self.sample_id:
            self.seq_center = seq_centers.get(self.sample_id)

        # for now, our sequencing id is just the file prefix
        self.sequencing_id = None

        if len(self.seq_filenames) > 0:
            self.sequencing_id = ".".join(self.seq_filenames[0].split(".")[0:-1])

    @classmethod
    def write_header(cls, writer):
        writer.writerow([
            CONCEPT.STUDY.NAME,
            CONCEPT.PARTICIPANT.ID,
            CONCEPT.SEQUENCING.ID,
            CONCEPT.SEQUENCING_GENOMIC_FILE.ID,
            CONCEPT.GENOMIC_FILE.FILE_FORMAT,
            CONCEPT.SEQUENCING.DRS_URI,
            CONCEPT.SEQUENCING.CENTER.ID,
            CONCEPT.BIOSPECIMEN.ID,
            CONCEPT.BIOSPECIMEN.ANALYTE,
            CONCEPT.SEQUENCING.ASSAY,
            CONCEPT.SEQUENCING.LIBRARY_NAME,
            CONCEPT.SEQUENCING.PLATFORM,
            CONCEPT.SEQUENCING.CAPTURE_REGION,
            CONCEPT.SEQUENCING.REFERENCE_GENOME,
            CONCEPT.SEQUENCING.ALIGNMENT_METHOD,
            CONCEPT.SEQUENCING.DATA_PROC_PIPELINE,
            CONCEPT.SEQUENCING.FUNCTIONAL_EQUIVALENCE_PIPELINE,
            CONCEPT.SEQUENCING.DATE
            ])

    def write_row(self, study_name, writer, drs_ids):
        for fn in self.seq_filenames:
            drs_uri = drs_ids.get(fn.split("/")[-1])

            file_type = fn.split(".")[-1]
            writer.writerow([
                study_name,
                self.subject_id,
                self.sequencing_id,
                fn,
                file_type,
                drs_uri,
                self.seq_center,
                self.sample_id,
                self.analyte_type,
                self.sequencing_assay,
                self.library_prep_kit_method,
                self.exome_capture_platform,
                self.capture_region_bed_file,
                self.reference_genome_build,
                self.alignment_method,
                self.data_processing_pipeline,
                self.functional_equivalence_standard,
                self.date_data_generation
            ])

class Patient:
    def __init__(self, row, family_lkup, proband_relationships):
        # print(row.keys())
        self.id = Transform.CleanSubjectId(row['subject_id'])  # Transform.CleanSubjectId(row['subject_id'])
        self.project_id = row['project_id']
        self.fam_id = row['family_id']
        self.mat_id = Transform.CleanSubjectId(row['maternal_id'])
        self.pat_id = Transform.CleanSubjectId(row['paternal_id'])
        self.twin_id = Transform.CleanSubjectId(row['twin_id'])
        self.dbgap_study_id = row['dbgap_study_id']
        self.dbgap_id = row['dbgap_subject_id']
        self.age_at_last_observation = row['age_at_last_observation']

        if self.mat_id is not None:
            proband_relationships[self.mat_id] = self.id

        if self.pat_id is not None:
            proband_relationships[self.pat_id] = self.id

        if self.twin_id is not None:
            proband_relationships[self.twin_id] = self.id

        # I'm hopeful that everything should be in constantsANTS.RELATIONSHIP
        self.proband_relationship = Transform.CleanVar(constants.RELATIONSHIP, row['proband_relationship'], True)

        self.sex = Transform.CleanVar(constants.GENDER, row['sex'])

        self.affected_status = Transform.CleanVar(constants.AFFECTED_STATUS, row['affected_status'])

        # Right now, this constant object is limited to W|I|B|A|P|M so we will probably need to work on it
        self.race = constants.COMMON.UNKNOWN
        if row['ancestry'] != "Hispanic or Latino":
            self.race = Transform.CleanVar(constants.RACE , row['ancestry'])
            self.eth = None
        else:
            self.eth = constants.ETHNICITY.HISPANIC
        self.ancestry_detail = row['ancestry_detail']

        family_lkup[self.id] = self.fam_id


    @classmethod
    def write_default_header(self, writer):
        writer.writerow([
            CONCEPT.STUDY.ID,
            CONCEPT.FAMILY.ID,
            CONCEPT.PARTICIPANT.MOTHER_ID,
            CONCEPT.PARTICIPANT.FATHER_ID,
            CONCEPT.PARTICIPANT.ID,
            CONCEPT.PARTICIPANT.PROBAND_ID,
            CONCEPT.PARTICIPANT.RELATIONSHIP_TO_PROBAND,
            CONCEPT.PARTICIPANT.GENDER,
            CONCEPT.PARTICIPANT.RACE,
            CONCEPT.PARTICIPANT.ETHNICITY,
            CONCEPT.PARTICIPANT.ANCESTRY_DETAIL,
            CONCEPT.PARTICIPANT.AGE_AT_LAST_OBSERVATION,
            CONCEPT.DBGAP_STUDY_ID,
            CONCEPT.DBGAP_ID
            ]
        )
    def write_default(self, study, writer, proband_relationships):
        proband_id = None
        proband_relationship = None
        if self.id in proband_relationships:
            proband_id = proband_relationships[self.id]
            proband_relationship = self.proband_relationship
        writer.writerow([
            study, 
            self.fam_id,
            self.mat_id,
            self.pat_id,
            self.id,
            proband_id,
            proband_relationship,
            self.sex,
            self.race,
            self.eth,
            self.ancestry_detail,
            self.age_at_last_observation,
            self.dbgap_study_id,
            self.dbgap_id ]
        )

# Theoretically, there will be a sample_provider and a sample_source coming from the
# data. In Terra, that doesn't always seem true, but I suspect that those assumed based
# on the dataset (sample_provider would be whomever generated the data and the source
# is part of the filename, at least for broad's contributions to terra. We may need
# to tolerate that...)

def Run(output, study_name, dataset, delim=None):
    if "delim" not in dataset:
        delim = "\t"
    else:
        delim = dataset['delim']

    # We need a way to point back to the family when we parse our specimen file
    family_lkup = {}

    # There is currently no reference to the proband from parent rows, so we 
    # need to define that. 
    proband_relationships = collections.defaultdict(dict)           # parent_id => "relationship" => proband_id 

    drs_ids = {}
    if 'drs' in dataset:
        with open(dataset['drs'], 'rt') as file:
            reader = csv.DictReader(file, delimiter='\t', quotechar='"')

            for row in reader:
                locals = dict(zip(row['filenames'].split(","), row['object_id'].split(",")))
                for fn in locals.keys():
                    drs_ids[fn] = locals[fn]

    diseases = []
    with open(dataset['subject'], 'rt') as file:
        reader = csv.DictReader(file, delimiter=delim, quotechar='"')

        with open(output / "subject.tsv", 'wt') as outf:
            writer = csv.writer(outf, delimiter='\t', quotechar='"')
            Patient.write_default_header(writer)

            peeps = []

            for line in reader:
                p = Patient(line, family_lkup, proband_relationships)
                peeps.append(p)

                d = Disease(line, family_lkup)
                diseases.append(d)
            # Just in case the pedigree data isn't in order
            for p in peeps:
                p.write_default(study_name, writer, proband_relationships)

        with open(output / "disease.tsv", 'wt') as outf:
            writer = csv.writer(outf, delimiter='\t', quotechar='"')
            Disease.write_header(writer)

            for d in diseases:
                d.writerow(study_name, writer)
        with open(output / "hpo.tsv", 'wt') as outf:
            writer = csv.writer(outf, delimiter='\t', quotechar='"')
            Disease.hpo_write_header(writer)

            for d in diseases:
                d.hpo_writerow(study_name, writer)

    seq_centers = {}        # Capture the sequencing centers to add to 
                            # our sequencing output
    subj_id = {}            # There are some datasets where there is no
                            # subject ID in the sequencing file
    with open(dataset['sample'], 'rt') as file:
        reader = csv.DictReader(file, delimiter=delim, quotechar='"')
        with open(output / "specimen.tsv", 'wt') as outf:
            writer = csv.writer(outf, delimiter='\t', quotechar='"')
            Sample.write_default_header(writer)

            for line in reader:
                # We skip over samples that exist twice--a side effect
                # of concatting wgs onto the the wes data
                if line['sample_id'] not in Sample.observed:
                    s = Sample(line, family_lkup, subj_id)
                    if s.sample_provider:
                        seq_centers[s.sample_id] = s.sample_provider
                    s.write_row(study_name, writer)

    with open(dataset['sequencing'], 'rt') as file:
        reader = csv.DictReader(file, delimiter=delim, quotechar='"')
        
        with open(output / "sequencing.tsv", 'wt') as outf:
            writer = csv.writer(outf, delimiter='\t', quotechar='"')
            Sequencing.write_header(writer)

            for row in reader:
                seq = Sequencing(row, seq_centers, subj_id)
                seq.write_row(study_name, writer, drs_ids)

if __name__ == "__main__":
    config = DataConfig.config()
    env_options = config.list_environments()
    ds_options = config.list_datasets()

    parser = ArgumentParser()
    parser.add_argument("-e", 
            "--env", 
            choices=env_options, 
            default='dev', 
            help=f"Remote configuration to be used")
    parser.add_argument("-d", 
                "--dataset", 
                choices=ds_options,
                default=[],
                help=f"Dataset config to be used",
                action='append')
    parser.add_argument("-o", "--out", default='output')
    args = parser.parse_args()
    datasets = args.dataset 
    if len(datasets) == 0:
        datasets.append('FAKE-CMG')

    for study in sorted(datasets):
        dirname = Path(f"{args.out}/{study}/transformed")
        dirname.mkdir(parents=True, exist_ok=True)
        Run(dirname, study, config.get_dataset(study))

    # Write the term cache to file since the API can sometimes be unresponsive
    write_cache()

    print(f"Total calls to remote api {term_lookup.remote_calls}")