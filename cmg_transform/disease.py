import csv
from ncpi_fhir_plugin.common import CONCEPT, constants
from cmg_transform import Transform
from term_lookup import pull_details, write_cache
import term_lookup

class Disease:
    def __init__(self, row, family_lkup):
        self.id = Transform.CleanSubjectId(row['subject_id']) # Transform.CleanSubjectId(row['subject_id'])
        self.fam_id = family_lkup[self.id]
        # For now, we are going to assert that we got only a single disease_id (or none)
        self.disease_id = Transform.ExtractVar(row, 'disease_id').split("|")

        # When we get more than one disease id, all but the primary (first?) will go here
        # and should end up in the fhir record's note
        self.alternate_diseases = []
        self.alternate_disease_names = ""


        self.disease_description = Transform.ExtractVar(row, 'disease_description')
        self.disease_name = self.disease_description
        self.disease_system = None
        self.phenotype_description = Transform.ExtractVar(row, 'phenotype_description')

        self.get_disease_details(row)
        
        self.hpo_present = Transform.ExtractVar(row, 'hpo_present').split("|")
        self.hpo_absent = Transform.ExtractVar(row, 'hpo_absent').split("|")
        self.affected_status = Transform.ExtractVar(row, 'affected_status')
        self.age_of_onset = Transform.ExtractVar(row, 'age_of_onset')

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
            term_lookup.broken_terms[id] = Transform.ExtractVar(row, 'disease_description')
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
            if hpo is not None and hpo != "" and hpo != "-":
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
            if hpo is not None and hpo != "" and hpo != "-":
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

