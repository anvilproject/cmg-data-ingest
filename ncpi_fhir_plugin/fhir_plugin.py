"""
This module is translated into an instance of
kf_lib_data_ingest.etl.configuration.target_api_config.TargetAPIConfig which is
used by the Kids First Ingest Library's load stage to populate instances of
target model entities (i.e. participants, diagnoses, etc) with data from the
extracted concepts before those instances are loaded into the target service.

Reference: https://github.com/kids-first/kf-lib-data-ingest

See docstrings in kf_lib_data_ingest.etl.configuration.target_api_config for
more details on the requirements for format and content.
"""
import inspect 

import os


from ncpi_fhir_utility.client import FhirApiClient

from ncpi_fhir_plugin.target_api_builders.ncpi_patient import Patient
from ncpi_fhir_plugin.target_api_builders.basic_patient import BasicPatient
from ncpi_fhir_plugin.target_api_builders.research_subject import ResearchSubject
from ncpi_fhir_plugin.target_api_builders.research_study import ResearchStudy
from ncpi_fhir_plugin.target_api_builders.consent import Consent
from ncpi_fhir_plugin.target_api_builders.group import Group
from ncpi_fhir_plugin.target_api_builders.patient_relationship import PatientRelation
from ncpi_fhir_plugin.target_api_builders.specimen import Specimen 
from ncpi_fhir_plugin.target_api_builders.disease import Disease
from ncpi_fhir_plugin.target_api_builders.hpo_observation import HumanPhenotype
from ncpi_fhir_plugin.target_api_builders.tissue_affected_status import TissueAffectedStatus 
from ncpi_fhir_plugin.target_api_builders.sequencing_center import SequencingCenter
from ncpi_fhir_plugin.target_api_builders.sequencing_file import SequencingFile
from ncpi_fhir_plugin.target_api_builders.sequencing_file_no_drs import SequencingFileNoDrs
from ncpi_fhir_plugin.target_api_builders.sequencing_task import SequencingTask 
from ncpi_fhir_plugin.target_api_builders.sequencing_file_info import SequencingFileInfo
from ncpi_fhir_plugin.target_api_builders.discovery_variant import DiscoveryVariant
from ncpi_fhir_plugin.target_api_builders.discovery_implication import DiscoveryImplication 
from ncpi_fhir_plugin.target_api_builders.discovery_report import DiscoveryReport 
from ncpi_fhir_plugin.target_api_builders.measurement import Measurement
from ncpi_fhir_plugin.target_api_builders.encounter import Encounter
from ncpi_fhir_plugin.target_api_builders.service_request import ServiceRequest
from ncpi_fhir_plugin.target_api_builders.condition import Condition
from ncpi_fhir_plugin.target_api_builders.observation import Observation

from ncpi_fhir_plugin import common

from fhir_walk.fhir_host import FhirHost

import traceback

all_targets = [
    Patient,
    BasicPatient,
    Consent,
    Group,
    ResearchStudy,
    ResearchSubject,
    PatientRelation,
    SequencingCenter,
    Specimen,
    Disease,
    Encounter,
    ServiceRequest,
    HumanPhenotype,
    TissueAffectedStatus,
    SequencingFile,
    SequencingFileNoDrs,
    SequencingTask,
    SequencingFileInfo,
    DiscoveryVariant,
    DiscoveryImplication,
    DiscoveryReport,
    Measurement,
    Observation,
    Condition
]

LOADER_VERSION = 2
