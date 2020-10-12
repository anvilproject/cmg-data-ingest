# Example JSON files from current cmg's FHIR plugin for the KF Ingest Library

## examples/disease.json
For CMG, we are represent the disease which is the focus of the research for which the subject was enrolled using Condition. 

## The Subject is represented via the base Profile, Patient. 
examples/patient.json

## Family structure is recorded as a series of Observations in which the Subject is the Patient being observed and *focus* is the related party (the proband). So, if the relationship being described is "Mother", the Subject is the Mother, and the Focus is the child.
examples/father.json
examples/mother.json

## HPOs are collected to describe the patient's observed phenotypes and may be annotated as either Present or Absent. 
examples/hpo.json

## ResearchStudy allows us to associate Patients with a Particular study by way of ResearchStudy and ResearchSubject. There can be only one entry for the Patient (and thus, ResearchSubject) in a given study. 
examples/research_study.json
examples/research_subject.json

## Sequence data is represented as the Task of sequencing the blood/saliva/tissue, the output of that task (DocumentReference) And details about that document are "observed" via an Observation. 
examples/sequencing_file_info.json
examples/sequencing_file.json
examples/sequencing_task.json

## Specimen is currently captured by way of the standard Specimen Profile
examples/specimen.json
