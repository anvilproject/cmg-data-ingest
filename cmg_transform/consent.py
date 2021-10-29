
from ncpi_fhir_plugin.common import CONCEPT, constants
from cmg_transform import Transform
#from term_lookup import pull_details, write_cache
import pdb
import sys

class ConsentGroup:
    def __init__(self, study_name, study_id, study_title, group_name, consent_name, release_status='completed'):
        self.study_name = study_name
        self.study_id = study_id
        self.study_title = study_title
        self.group_name = group_name
        self.consent_name = consent_name
        self.release_status = release_status
        self.seq_center = None
        self.ids = set()

    def add_patient(self, participant_id, seq_center, fail_on_seq_center=True):
        self.ids.add(participant_id)
        if self.seq_center is None or self.seq_center.strip() == "":
            self.seq_center = seq_center
        else:
            # I'm not entirely sure how reliable the sequencing center will be across the entire study...
            if not fail_on_seq_center and seq_center.strip() != "":
                assert(self.seq_center == seq_center)

    @classmethod
    def write_default_header(cls, writer):
        #pdb.set_trace()
        writer.writerow([
            CONCEPT.PARTICIPANT.ID,
            CONCEPT.STUDY.NAME,
            CONCEPT.STUDY.TITLE,
            CONCEPT.SEQUENCING.CENTER.ID,
            CONCEPT.STUDY.RELEASE_STATUS,
            CONCEPT.STUDY.GROUP.NAME,
            CONCEPT.STUDY.GROUP.URL,
            CONCEPT.STUDY.GROUP.CONSENT_NAME
        ])

    def write_data(self, writer):
        if self.seq_center is None:
            pdb.set_trace()
        assert(self.seq_center is not None)
        for id in self.ids:
            writer.writerow([
                id,
                self.study_name,
                self.study_title, 
                self.seq_center,
                self.release_status,
                self.group_name,
                f"https://www.ncbi.nlm.nih.gov/projects/gap/group-identifier/{self.study_id}",
                self.consent_name
            ])
    
