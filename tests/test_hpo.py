import pytest


from csv import DictReader

from ncpi_fhir_plugin.common import (
            constants,
            CONCEPT
)


def test_disease_details(study, transformed_dir):
    hpo_file = transformed_dir / 'hpo.tsv'
    assert hpo_file.exists(), "HPO file exists?"

    patients = study.Patients()

    line_number = 0
    with hpo_file.open() as f:
        reader = DictReader(f, delimiter='\t')

        for line in reader:
            line_number += 1
            subject_id = line[CONCEPT.PARTICIPANT.ID]
            phenotype_id = line[CONCEPT.PHENOTYPE.HPO_ID]
            phenotype_name = line[CONCEPT.PHENOTYPE.NAME]
            phenotype_observed = line[CONCEPT.PHENOTYPE.OBSERVED]

            assert subject_id in patients, f"Did we get the subject ({subject_id}) @ #{line_number} from the server? {len(patients)} patients returned"
            subject = patients[subject_id]
            pheno_present, pheno_absent = subject.phenotypes()

            if phenotype_observed == constants.PHENOTYPE.OBSERVED.PRESENT:
                assert phenotype_id in pheno_present, f"Make sure that the phenotype code is present (in present) for {subject_id} @ {line_number}"
                assert phenotype_name == pheno_present[phenotype_id].name 
            else:
                assert phenotype_id in pheno_absent, f"Make sure that the phenotype code '{phenotype_id}' is present (in absent) for {subject_id} | '{phenotype_observed}' @ {line_number}"
                assert phenotype_name == pheno_absent[phenotype_id].name 

