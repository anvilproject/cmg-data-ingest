import pytest

def test_study_is_present_in_config(config, study_name):
	print(study_name)
	assert study_name in config.list_datasets(), "Verify that the study is present"
