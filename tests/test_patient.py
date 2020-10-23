import pytest

from csv import DictReader

from ncpi_fhir_plugin.target_api_builders.ncpi_patient import (
    administrative_gender,
    omb_race_category,
    omb_ethnicity_category
)
from ncpi_fhir_plugin.common import (
    constants,
    CONCEPT
)

race_alternates = {
    constants.COMMON.UNKNOWN: 'Unknown'
}

def test_patient_details(study, transformed_dir):
    subjects = transformed_dir / 'subject.tsv'
    assert subjects.exists(), "Subject file exists?"

    patients = study.Patients()

    with subjects.open() as f:
        reader = DictReader(f, delimiter='\t')

        for line in reader:
            subject_id = line['PARTICIPANT|ID']
            assert subject_id in patients, f"Did we get the subject ({subject_id}) from the server?"
            subject = patients[subject_id]
            assert subject_id == subject.subject_id 
            assert f"{subject.study}|{subject_id}" == subject.research_subject_id
            assert subject.sex == administrative_gender[line['PARTICIPANT|GENDER']], "Verify the patient's sex"
            if line['PARTICIPANT|RACE'] in race_alternates:
                assert subject.race == race_alternates[line['PARTICIPANT|RACE']]
            else:
                assert subject.race == line['PARTICIPANT|RACE'], "Patient's race match?"
            assert subject.eth == line['PARTICIPANT|ETHNICITY'], "Patient's eth match?"

            # We don't bother with this if there isn't an ID present
            if line[CONCEPT.DBGAP_ID] != "":
                assert subject.dbgap_id == line[CONCEPT.DBGAP_ID], "DBGAP id"
                assert subject.dbgap_study_id == line[CONCEPT.DBGAP_STUDY_ID], f'DBGap Study ID for {subject_id}'


