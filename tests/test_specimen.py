import pytest

from csv import DictReader

from ncpi_fhir_plugin.common import (
    constants,
    CONCEPT
)

def test_specimen_details(study, transformed_dir):
    specimen_file = transformed_dir / 'specimen.tsv'
    assert specimen_file.exists(), "Subject file exists?"

    # At this time, we have to go through subjects to get to specimen.
    # That may be an issue, since you have to go through research subject to 
    # get to the patient...so, the number of layers does start getting a bit
    # deep. 
    patients = study.Patients()

    with specimen_file.open() as f:
        reader = DictReader(f, delimiter='\t')

        for line in reader:
            subject_id = line[CONCEPT.PARTICIPANT.ID]
            sample_id = line[CONCEPT.BIOSPECIMEN.ID]
            assert subject_id in patients, f"Did we get the subject ({subject_id}) from the server?"
            subject = patients[subject_id]
            assert subject_id == subject.subject_id, "Make sure subject IDs do match"
            specimens = subject.specimens()
            assert sample_id in specimens
            specimen = specimens[sample_id]
            assert specimen.subject_id == f"Patient/{subject.id}", "Verify that the patient's id is correct"
            if line[CONCEPT.BIOSPECIMEN.TISSUE_TYPE] != "":
	            assert specimen.body_site[0] == line[CONCEPT.BIOSPECIMEN.TISSUE_TYPE]
	            assert specimen.body_site[1] == line[CONCEPT.BIOSPECIMEN.TISSUE_TYPE_NAME]
	            assert specimen.dbgap_id == line[CONCEPT.BIOSPECIMEN.DBGAP_ID]



