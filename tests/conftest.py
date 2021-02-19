import pytest
from fhir_walk.config import DataConfig 
from fhir_walk.model.research_study import ResearchStudy

# We'll allow the user to change the config details via environment if they wish to 
# test more complicated data 
from os import getenv      
from pathlib import Path

#import pdb

"""Instantiate the fhir_walk host and starter details required for proper testing"""

@pytest.fixture
def env():
    return getenv('FHIR_CFG', 'dev')

@pytest.fixture
def study_name():
    return getenv('FHIR_STUDY', 'FAKE-CMG')

def get_config():
    return DataConfig.config(env=getenv('FHIR_CFG', 'dev'))

@pytest.fixture
def config():   
    return get_config()


@pytest.fixture
def study():
    config = get_config()
    return ResearchStudy.Studies(config.get_host())[getenv('FHIR_STUDY', 'FAKE-CMG')]

@pytest.fixture
def transformed_dir():
    return Path(f"{getenv('FHIR_OUT', 'output')}/{getenv('FHIR_STUDY', 'FAKE-CMG')}/transformed/")
