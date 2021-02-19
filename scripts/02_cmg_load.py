#!/usr/bin/env python

import sys
import logging
from pathlib import Path
from time import sleep

from yaml import load, FullLoader
from kf_lib_data_ingest.common.io import read_df
from kf_lib_data_ingest.etl.load.load import LoadStage

from fhir_walk.config import DataConfig 
from fhir_walk.fhir_host import FhirHost
import ncpi_fhir_plugin.fhir_plugin as fhir # import SetAuthorization, remote_authorization

import pdb

from argparse import ArgumentParser, FileType

if __name__ == "__main__":
    all_loadable_classes = [
        "patient", 
        "research_study", 
        "research_subject", 
        "family_relationship",
        "specimen",
        "disease",
        "human_phenotype",
        "tissue_affected_status",
        "sequencing_center",
        "sequencing_file",
        "sequencing_file_no_drs",
        "sequencing_data",           # This will eventually change to sequencing_task
        "discovery_variant",
        "discovery_implication",
        "discovery_report"
    ]
    """ For now, we'll leave these off. None of those fields mapped well anyway
        "sequencing_file_info"  """
    config = DataConfig.config()
    env_options = config.list_environments()
    ds_options = config.list_datasets()
    parser = ArgumentParser()
    parser.add_argument("-e", 
                "--env", 
                choices=env_options, 
                default='dev', 
                help=f"Remote configuration to be used")
    parser.add_argument("-d", 
                "--dataset", 
                choices=ds_options + ['ALL'],
                default=[],
                help=f"Dataset config to be used",
                action='append')
    parser.add_argument("-o", "--out", default='output')
    parser.add_argument("-m", 
                "--modules-to-load", 
                choices=all_loadable_classes, 
                default=[], 
                action='append',
                help=f"Which module(s) should be loaded? Default is all of them")
    args = parser.parse_args()

    list_of_class_names_to_load = args.modules_to_load
    if len(list_of_class_names_to_load) == 0:
        list_of_class_names_to_load = all_loadable_classes

    fhir_host = config.set_host(args.env)
    datasets = args.dataset 
    if len(datasets) == 0:
        datasets.append('FAKE-CMG')
    elif "ALL" in datasets:
        datasets = ds_options

    path_to_my_target_service_plugin = "ncpi_fhir_plugin/fhir_plugin.py"
    target_service_base_url = fhir_host.target_service_url
 
    for study_id in sorted(datasets):
        print(f"Loading '{study_id}'")
        logging.basicConfig(filename=f'{args.out}/{study_id}-{args.env}-load.log',
                                filemode='w',
                                format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                                datefmt='%H:%M:%S',
                                level=logging.DEBUG)


        input_file_dir = f"{args.out}/{study_id}/transformed"
        path_to_cache_storage_directory = Path(f"{input_file_dir}/{args.env}")
        path_to_cache_storage_directory.mkdir(parents=True, exist_ok=True)

        specimens = read_df(f'{input_file_dir}/specimen.tsv')
        subjects = read_df(f'{input_file_dir}/subject.tsv')
        disease = read_df(f'{input_file_dir}/disease.tsv')
        hpo = read_df(f'{input_file_dir}/hpo.tsv')
        sequencing_data = read_df(f'{input_file_dir}/sequencing.tsv')

        basic_reports = {
            "default": subjects,
            'research_study': specimens,
            'research_subject': specimens,
            'tissue_affected_status': specimens,
            'sequencing_center': specimens,
            "family_relationship": subjects,
            "disease": disease,
            "specimen": specimens,
            'human_phenotype': hpo,
            'sequencing_file': sequencing_data,
            'sequencing_file_no_drs': sequencing_data,
            'sequencing_data': sequencing_data,
            "sequencing_file_info": sequencing_data,           
        }
        offs = {    
        }
        if Path(f"{input_file_dir}/discovery_variant.tsv").is_file():
            discovery_variant = read_df(f"{input_file_dir}/discovery_variant.tsv") 

            basic_reports['discovery_variant'] = discovery_variant
            basic_reports["discovery_implication"] = discovery_variant

        if Path(f"{input_file_dir}/discovery_report.tsv").is_file():
            discovery_report = read_df(f"{input_file_dir}/discovery_report.tsv")

            basic_reports["discovery_report"] = discovery_report
        #pdb.set_trace()
        outcome = LoadStage(
            path_to_my_target_service_plugin,
            target_service_base_url,
            list_of_class_names_to_load,
            study_id,
            str(path_to_cache_storage_directory)
        ).run(basic_reports)

