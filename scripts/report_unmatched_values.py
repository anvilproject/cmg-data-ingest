#!/bin/env python

"""
Perform queries associated issues encountered during transformation process
"""

import sqlite3
import csv
from fhir_walk.config import DataConfig 
from argparse import ArgumentParser, FileType
from pathlib import Path

from cmg_transform.transformed import Report
from cmg_transform.change_logger import ChangeLog

if __name__ == "__main__":
    config = DataConfig.config()
    env_options = config.list_environments()
    ds_options = config.list_datasets()


    parser = ArgumentParser()
    parser.add_argument("-d", 
                "--dataset", 
                choices=['ALL'] + ds_options,
                default=['ALL'],
                help=f"Dataset config to be used",
                action='append')
    parser.add_argument("-m", "--min-missing", type=int, default=10, help='Filter out values with % missingness greater than this value')
    parser.add_argument("-o", "--out", default='output', help="Directory where the database is to be found")
    args = parser.parse_args()

    datasets = args.dataset 

    if 'ALL' in datasets:
        datasets = ds_options

    report_header = True
    for study in sorted(datasets):
        cur = ChangeLog.InitDB(args.out, study, purge_priors=False)

        report = Report(cur)

        report.summarize(study, args.min_missing, report_header)
        report_header =False
