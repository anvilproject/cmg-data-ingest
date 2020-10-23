import pytest
from fhir_walk.model.research_study import ResearchStudy
from csv import DictReader

def test_research_study(config, study_name):
	host = config.get_host()
	studies = ResearchStudy.Studies(host)
	assert study_name in studies, "Make sure the dataset is present on the server"

def test_research_study_title(study, transformed_dir):
	specimens = transformed_dir / 'specimen.tsv'
	assert specimens.exists(), "Specimen file exists?"

	with specimens.open() as f:
		reader = DictReader(f, delimiter='\t')
		
		# The way the transformation works, all of the specimen in a given file will have
		# the same study name
		line = reader.__next__()
		assert line['STUDY|NAME'] == study.title, "Is the title correct?"

