import pytest


from csv import DictReader

from ncpi_fhir_plugin.common import (
            constants,
            CONCEPT
)


def test_disease_details(study, transformed_dir):
    disease_file = transformed_dir / 'disease.tsv'
    assert disease_file.exists(), "Disease file exists?"

    # At this time, we have to go through subjects to get to specimen.
    # That may be an issue, since you have to go through research subject to 
    # get to the patient...so, the number of layers does start getting a bit
    # deep. 
    patients = study.Patients()

    with disease_file.open() as f:
        reader = DictReader(f, delimiter='\t')

        for line in reader:
            subject_id = line[CONCEPT.PARTICIPANT.ID]
            disease_id = line[CONCEPT.DIAGNOSIS.DISEASE_ID]
            disease_desc = line[CONCEPT.DIAGNOSIS.DESCRIPTION]

            assert subject_id in patients, f"Did we get the subject ({subject_id}) from the server?"
            subject = patients[subject_id]
            assert subject_id == subject.subject_id, "Make sure subject IDs do match"

            # We have issues with some folks not having disease ids
            if None is not line[CONCEPT.DIAGNOSIS.DESCRIPTION] and line[CONCEPT.DIAGNOSIS.DESCRIPTION].strip() != "":
                diseases = subject.diseases()
                assert disease_id in diseases

                disease = diseases[disease_id]
                assert disease.code == disease_id




