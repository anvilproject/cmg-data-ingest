#!/usr/bin/env python

import csv
from fhir_walk.config import DataConfig 
from argparse import ArgumentParser, FileType
from pathlib import Path
from collections import defaultdict
from term_lookup import pull_details, write_cache, remote_calls

from ncpi_fhir_plugin.common import CONCEPT, constants

from variant_details import Variant

from cmg_transform import Transform
from cmg_transform.discovery_variant import DiscoveryVariant
from cmg_transform.disease import Disease
from cmg_transform.patient import Patient
from cmg_transform.sample import Sample
from cmg_transform.sequencing import Sequencing 

from cmg_transform.change_logger import ChangeLog

# Theoretically, there will be a sample_provider and a sample_source coming from the
# data. In Terra, that doesn't always seem true, but I suspect that those assumed based
# on the dataset (sample_provider would be whomever generated the data and the source
# is part of the filename, at least for broad's contributions to terra. We may need
# to tolerate that...)

def Run(output, study_name, dataset, delim=None):
    if "delim" not in dataset:
        delim = "\t"
    else:
        delim = dataset['delim']

    # We need a way to point back to the family when we parse our specimen file
    family_lkup = {}

    # There is currently no reference to the proband from parent rows, so we 
    # need to define that. 
    proband_relationships = defaultdict(dict)           # parent_id => "relationship" => proband_id 

    if 'field_map' in dataset:
        Transform.LoadFieldMap(dataset['field_map'])
        print(Transform._field_map)

    if 'data_map' in dataset:
        Transform.LoadDataMap(dataset['data_map'])
        print(Transform._data_map)
        print(Transform._data_transform)

    drs_ids = {}
    if 'drs' in dataset:
        with open(dataset['drs'], 'rt') as file:
            reader = csv.DictReader(file, delimiter='\t', quotechar='"')

            for row in reader:
                locals = dict(zip(row['filenames'].split(","), row['object_id'].split(",")))
                for fn in locals.keys():
                    drs_ids[fn] = locals[fn]

    diseases = []
    with open(dataset['subject'], 'rt', encoding='utf-8-sig') as file:
        Transform._cur_filename = 'subject'
        reader = Transform.GetReader(file, delimiter=delim)

        print(f"The Patient: {dataset['subject']}")
        with open(output / "subject.tsv", 'wt') as outf:
            writer = csv.writer(outf, delimiter='\t', quotechar='"')
            Patient.write_default_header(writer)

            peeps = []
            Transform._linenumber = 1
            for line in reader:
                Transform._linenumber += 1
                #print(f"-- {line}")
                p = Patient(line, family_lkup, proband_relationships)
                peeps.append(p)

                d = Disease(line, family_lkup)
                diseases.append(d)
            # Just in case the pedigree data isn't in order
            for p in peeps:
                p.write_default(study_name, writer, proband_relationships)

        with open(output / "disease.tsv", 'wt') as outf:
            writer = csv.writer(outf, delimiter='\t', quotechar='"')
            Disease.write_header(writer)

            for d in diseases:
                d.writerow(study_name, writer)
        with open(output / "hpo.tsv", 'wt') as outf:
            writer = csv.writer(outf, delimiter='\t', quotechar='"')
            Disease.hpo_write_header(writer)

            for d in diseases:
                d.hpo_writerow(study_name, writer)

    seq_centers = {}        # Capture the sequencing centers to add to 
                            # our sequencing output
    subj_id = {}            # There are some datasets where there is no
                            # subject ID in the sequencing file
    with open(dataset['sample'], 'rt', encoding='utf-8-sig') as file:
        Transform._cur_filename = 'sample'
        reader = Transform.GetReader(file, delimiter=delim)

        with open(output / "specimen.tsv", 'wt') as outf:
            writer = csv.writer(outf, delimiter='\t', quotechar='"')
            Sample.write_default_header(writer)

            Transform._linenumber = 1
            for line in reader:
                Transform._linenumber += 1
                # We skip over samples that exist twice--a side effect
                # of concatting wgs onto the the wes data
                if line['sample_id'] not in Sample.observed:
                    s = Sample(line, family_lkup, subj_id)
                    if s.sample_provider:
                        seq_centers[s.sample_id] = s.sample_provider
                    s.write_row(study_name, writer)

    with open(dataset['sequencing'], 'rt', encoding='utf-8-sig') as file:
        Transform._cur_filename = 'sequencing'
        reader = Transform.GetReader(file, delimiter=delim)
        
        with open(output / "sequencing.tsv", 'wt') as outf:
            writer = csv.writer(outf, delimiter='\t', quotechar='"')
            Sequencing.write_header(writer)

            Transform._linenumber = 1
            for row in reader:
                Transform._linenumber += 1
                seq = Sequencing(row, seq_centers, subj_id)
                seq.write_row(study_name, writer, drs_ids)

    if "discovery" in dataset:
        with open(dataset['discovery'], 'rt', encoding='utf-8-sig') as file:
            Transform._cur_filename = 'discovery'
            reader = Transform.GetReader(file, delimiter=delim)

            # subject_id => [variant_id, ...]
            variants = defaultdict(list)
            with open(output / "discovery_variant.tsv", 'wt') as outf:
                writer = csv.writer(outf, delimiter='\t', quotechar='"')
                DiscoveryVariant.writeheader(writer)

                Transform._linenumber = 1
                for row in reader:
                    Transform._linenumber += 1
                    var = DiscoveryVariant(row)
                    var.writerow(writer, study_name)
                    var.add_variant_ids(variants)


            with open(output / "discovery_report.tsv", 'wt') as outf:
                writer = csv.writer(outf, delimiter='\t', quotechar='"')
                writer.writerow([
                        CONCEPT.STUDY.ID,
                        CONCEPT.PARTICIPANT.ID,
                        CONCEPT.DISCOVERY.VARIANT.ID
                ])

                for id in variants.keys():
                    writer.writerow([study, id, "::".join(variants[id])])

if __name__ == "__main__":
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
                choices=['ALL'] + ds_options,
                default=[],
                help=f"Dataset config to be used",
                action='append')
    parser.add_argument("-o", "--out", default='output')
    args = parser.parse_args()

    datasets = args.dataset 

    if 'ALL' in datasets:
        datasets = ds_options
        
    if len(datasets) == 0:
        datasets.append('FAKE-CMG')

    for study in sorted(datasets):
        ChangeLog.InitDB(args.out, study, purge_priors=True)

        dirname = Path(f"{args.out}/{study}/transformed")
        dirname.mkdir(parents=True, exist_ok=True)
        Run(dirname, study, config.get_dataset(study))

    # Write the term cache to file since the API can sometimes be unresponsive
    write_cache()

    print(f"Total calls to remote api {remote_calls}")

    # Make sure the cache is saved
    Variant.cache.commit()
    ChangeLog.Close()