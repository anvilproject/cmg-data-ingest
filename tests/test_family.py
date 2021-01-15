import pytest

from csv import DictReader

from ncpi_fhir_plugin.common import (
    constants,
    CONCEPT
)

def test_specimen_details(study, transformed_dir):
    subject_file = transformed_dir / 'subject.tsv'
    assert subject_file.exists(), "Subject file exists?"

    # At this time, we have to go through subjects to get to specimen.
    # That may be an issue, since you have to go through research subject to 
    # get to the patient...so, the number of layers does start getting a bit
    # deep. 
    patients = study.Patients()

    with subject_file.open() as f:
        reader = DictReader(f, delimiter='\t')

        for line in reader:
            subject_id = line[CONCEPT.PARTICIPANT.ID]
            proband_id = line.get(CONCEPT.PARTICIPANT.PROBAND_ID)
            relationship = line.get(CONCEPT.PARTICIPANT.RELATIONSHIP_TO_PROBAND)

            assert subject_id in patients, f"Did we get the subject ({subject_id}) from the server?"
            subject = patients[subject_id]
            assert subject_id == subject.subject_id, "Make sure subject IDs do match"

            # We have a limited number of relationships of interest
            if relationship and proband_id != "":
            	proband = patients[proband_id]
            	parents = proband.parents()
            	if relationship == constants.RELATIONSHIP.MOTHER:
            		parent = parents['MTH']
            		assert subject_id == parent.subject_id, "Verify that the mother's ID matches"
            	elif relationship == constants.RELATIONSHIP.FATHER:
            		parent = parents['FTH']
            		assert subject_id == parent.subject_id, "Verify that the father's ID matches"


            # So, to get mom or dad (currently, the only ones we support at this time) you 
            # have to ask the child for his/her parents. 

