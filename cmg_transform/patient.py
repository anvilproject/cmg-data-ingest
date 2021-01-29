
from ncpi_fhir_plugin.common import CONCEPT, constants, GENDERFICATION
from cmg_transform import Transform
from term_lookup import pull_details, write_cache

import sys

class Patient:
    def __init__(self, row, family_lkup, proband_relationships):
        #print(row.keys())
        self.id = Transform.CleanSubjectId(row['subject_id'])  # Transform.CleanSubjectId(row['subject_id'])
        self.project_id = Transform.ExtractVar(row, 'project_id')
        self.fam_id = Transform.ExtractVar(row, 'family_id')
        self.mat_id = Transform.CleanSubjectId(Transform.ExtractVar(row, 'maternal_id'))
        self.pat_id = Transform.CleanSubjectId(Transform.ExtractVar(row, 'paternal_id'))
        self.twin_id = Transform.CleanSubjectId(Transform.ExtractVar(row, 'twin_id'))
        self.dbgap_study_id = Transform.ExtractVar(row, 'dbgap_study_id')
        self.dbgap_id = Transform.ExtractVar(row, 'dbgap_subject_id')
        self.age_at_last_observation = Transform.ExtractVar(row, 'age_at_last_observation')
        self.is_proband = False

        if self.mat_id is not None:
            proband_relationships[self.mat_id] = self.id

        if self.pat_id is not None:
            proband_relationships[self.pat_id] = self.id

        if self.twin_id is not None:
            proband_relationships[self.twin_id] = self.id

        try:
            # I'm hopeful that everything should be in constantsANTS.RELATIONSHIP
            self.proband_relationship = Transform.ExtractVar(row, 'proband_relationship', constants.RELATIONSHIP, True)
            if self.proband_relationship == '' and row['proband_relationship'] != "":
                print(f"'{row['proband_relationship']}'' -- '{Transform.GetValue(row, 'proband_relationship')}'")

            self.is_proband = self.proband_relationship == constants.RELATIONSHIP.PROBAND

            self.proband_relationship_raw = Transform.GetValue(row, 'proband_relationship')
        except:
            print("No proband present")
            print(sorted(row.keys()))
            print(row)
            sys.exit(1)
        self.sex = Transform.ExtractVar(row, 'sex', constants.GENDER)

        self.affected_status = Transform.ExtractVar(row, 'affected_status', constants.AFFECTED_STATUS)

        # Right now, this constant object is limited to W|I|B|A|P|M so we will probably need to work on it

        self.ancestry_detail = Transform.ExtractVar(row, 'ancestry_detail')
        self.race = constants.COMMON.UNKNOWN
        if Transform.ExtractVar(row, 'ancestry') != "Hispanic or Latino":
            self.race = Transform.ExtractVar(row, 'ancestry', constants.RACE)
            self.eth = None
        else:
            self.eth = constants.ETHNICITY.HISPANIC

            # In case the detail field is missing, we'll stash what we found in the 
            # ancestry field there (untransformed)
            if self.ancestry_detail.strip() == "":
                self.ancestry_detail = Transform.ExtractVar(row, 'ancestry')

        family_lkup[self.id] = self.fam_id

        # Go ahead and annotate the proband for the family. This will only work if the family_id for the 
        # member matches the proband's ID...but...such is the way of the world
        if self.is_proband:
            proband_relationships[self.fam_id] = self.id

        # Let's assign gendered family member relationships where it makes sense
        if self.sex in GENDERFICATION:
            if self.proband_relationship in GENDERFICATION[self.sex]:
                #print(f"--> {self.proband_relationship} {GENDERFICATION[self.sex][self.proband_relationship]}")
                self.proband_relationship = GENDERFICATION[self.sex][self.proband_relationship]


    @classmethod
    def write_default_header(self, writer):
        writer.writerow([
            CONCEPT.STUDY.NAME,
            CONCEPT.FAMILY.ID,
            CONCEPT.PARTICIPANT.MOTHER_ID,
            CONCEPT.PARTICIPANT.FATHER_ID,
            CONCEPT.PARTICIPANT.ID,
            CONCEPT.PARTICIPANT.PROBAND_ID,
            CONCEPT.PARTICIPANT.IS_PROBAND,
            CONCEPT.PARTICIPANT.RELATIONSHIP_TO_PROBAND,
            CONCEPT.PARTICIPANT.RELATIONSHIP_TO_PROBAND_RAW,
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
        proband_relationship = self.proband_relationship
        if self.id in proband_relationships:
            proband_id = proband_relationships[self.id]
            proband_relationship = self.proband_relationship
        if self.proband_relationship_raw == '':
            self.proband_relationship_raw = proband_relationship

        # Go ahead and provide a proband_id for those that we can manage
        if proband_id is None and self.fam_id in proband_relationships:
            proband_id=proband_relationships[self.fam_id]

        writer.writerow([
            study, 
            self.fam_id,
            self.mat_id,
            self.pat_id,
            self.id,
            proband_id,
            self.is_proband,
            proband_relationship,
            self.proband_relationship_raw,
            self.sex,
            self.race,
            self.eth,
            self.ancestry_detail,
            self.age_at_last_observation,
            self.dbgap_study_id,
            self.dbgap_id ]
        )
