
from ncpi_fhir_plugin.common import CONCEPT, constants
from cmg_transform import Transform
from term_lookup import pull_details, write_cache

class Patient:
    def __init__(self, row, family_lkup, proband_relationships):
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
