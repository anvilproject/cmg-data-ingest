#!/usr/bin/env python

import sys
from os import getenv, remove
import logging
from pathlib import Path
from time import sleep

from yaml import safe_load
from kf_lib_data_ingest.common.io import read_df
from kf_lib_data_ingest.etl.load.load import LoadStage
from ncpi_fhir_client.fhir_client import FhirClient

import ncpi_fhir_plugin as fhir # import SetAuthorization, remote_authorization

import pdb

from argparse import ArgumentParser, FileType

if __name__ == "__main__":
    #   "family_relationship",
    all_loadable_classes = [
        "patient", 
        "consent",
        "group",
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

    hostsfile = Path(getenv("FHIRHOSTS", 'fhir_hosts'))
    config = safe_load(hostsfile.open("rt"))
    
    env_options = config.keys()
    parser = ArgumentParser()
    parser.add_argument("-e", 
                "--env", 
                choices=env_options, 
                default='dev', 
                help=f"Remote configuration to be used")
    parser.add_argument("-d", 
                "--dataset", 
                type=FileType('rt'),
                help=f"Dataset config to be used",
                action='append')
    parser.add_argument("-o", "--out", default='output')
    parser.add_argument("-m", 
                "--modules-to-load", 
                choices=all_loadable_classes, 
                default=[], 
                action='append',
                help=f"Which module(s) should be loaded? Default is all of them")
    parser.add_argument("-b", 
                "--write-bundle",
                action='store_true',
                help="Optionally write a bundle file")
    parser.add_argument("-p",
                "--purge-ids",
                action='store_true',
                help="Purge the ID cache. Use only the database has been rebuilt and it's contents look different from when this was last run.")
    args = parser.parse_args()

    list_of_class_names_to_load = args.modules_to_load
    if len(list_of_class_names_to_load) == 0:
        list_of_class_names_to_load = all_loadable_classes

    #pdb.set_trace()
    fhir_host = FhirClient(config[args.env])
    fhir.set_fhir_server(fhir_host)
    
    datasets = args.dataset 

    path_to_my_target_service_plugin = "ncpi_fhir_plugin/fhir_plugin.py"
    target_service_base_url = fhir_host.target_service_url
 
    for dsfile in datasets:
        study = safe_load(dsfile)
        study_id = study['study_id']
        study_name = study['study_name'].replace(' ', '_')
        study_title = study['study_title']

        print(f"Loading '{study_id}'")
        log_filename = f"{args.out}/{study_name}-{args.env}-load.log"
        print(f"Logfile: {log_filename}")

        # This clears out previous logging entities so we can determine what and where to log
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        logging.basicConfig(filename=log_filename,
                                filemode='wt',
                                format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                                datefmt='%H:%M:%S',
                                level=logging.DEBUG)

        logging.info(f"Does this work? We tried to write to a file named {log_filename}")
        fhir_host.init_log()
        input_file_dir = f"{args.out}/{study_name}/transformed"
        path_to_cache_storage_directory = Path(f"{input_file_dir}/{args.env}")
        path_to_cache_storage_directory.mkdir(parents=True, exist_ok=True)

        if args.purge_ids:
            cache_file = f"{path_to_cache_storage_directory}/LoadStage/localhost_8000_{study_id}_uid_cache.db"
            print(f"Purging local cache: {cache_file}")
            remove(cache_file)

        if args.write_bundle:
            fhir_host.init_bundle(f"{args.out}/{study_id}-{args.env}.json", study_id)

        specimens = read_df(f'{input_file_dir}/specimen.tsv')
        consents = read_df(f'{input_file_dir}/consent_groups.tsv')
        subjects = read_df(f'{input_file_dir}/subject.tsv')
        disease = read_df(f'{input_file_dir}/disease.tsv')
        hpo = read_df(f'{input_file_dir}/hpo.tsv')
        sequencing_data = read_df(f'{input_file_dir}/sequencing.tsv')
        
        basic_reports = {
            "default": subjects,
            'research_study': consents,
            'consent': consents,
            'group': consents,
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

        outcome = LoadStage(
            path_to_my_target_service_plugin,
            target_service_base_url,
            list_of_class_names_to_load,
            study_id,
            str(path_to_cache_storage_directory)
        ).run(basic_reports)

        fhir_host.close_bundle()