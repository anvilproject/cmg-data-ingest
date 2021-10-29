#!/usr/bin/env python

import csv
from os import getenv

from yaml import safe_load
from argparse import ArgumentParser, FileType
from pathlib import Path
from collections import defaultdict
import cmg_transform.tools
from cmg_transform.tools.term_lookup import pull_details, write_cache, remote_calls

from ncpi_fhir_plugin.common import CONCEPT, constants

from cmg_transform.tools.variant_details import Variant

from cmg_transform import Transform, InvalidID
from cmg_transform.discovery_variant import DiscoveryVariant
from cmg_transform.disease import Disease
from cmg_transform.patient import Patient
from cmg_transform.sequencing import Sequencing 
from cmg_transform.consent import ConsentGroup
from cmg_transform.specimen import Specimen

from cmg_transform.change_logger import ChangeLog

import pdb

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

    study_title = dataset['study_title']
    study_id = dataset['study_id']

    study_group = ConsentGroup(study_name, study_title=study_title, study_id=study_id, group_name=f"{study_name}-complete", consent_name=None)

    # We'll dump consents for each group as they are parsed then the entire study
    fconsent = open(output /"consent_groups.tsv", 'wt')
    wconsent = csv.writer(fconsent, delimiter='\t', quotechar='"')
    ConsentGroup.write_default_header(wconsent)

    with open(output / "subject.tsv", 'wt') as subf, \
            open(output / "disease.tsv", 'wt') as disf, \
            open(output / "hpo.tsv", 'wt') as hpof, \
            open(output / "specimen.tsv", 'wt') as specf, \
            open(output / "sequencing.tsv", 'wt') as seqf, \
            open(output / "discovery_variant.tsv", 'wt') as discf, \
            open(output / "discovery_report.tsv", 'wt') as disrf:

        wsubject = csv.writer(subf, delimiter='\t', quotechar='"')
        Patient.write_default_header(wsubject)

        wdisease = csv.writer(disf, delimiter='\t', quotechar='"')
        Disease.write_header(wdisease)

        whpo = csv.writer(hpof, delimiter='\t', quotechar='"')
        Disease.hpo_write_header(whpo)

        wspecemin = csv.writer(specf, delimiter='\t', quotechar='"')        
        Specimen.write_default_header(wspecemin)

        wsequencing = csv.writer(seqf, delimiter='\t', quotechar='"')
        Sequencing.write_header(wsequencing)

        wdisc_var = csv.writer(discf, delimiter='\t', quotechar='"')
        DiscoveryVariant.writeheader(wdisc_var)

        wdisc_rep = csv.writer(disrf, delimiter='\t', quotechar='"')
        wdisc_rep.writerow([
                CONCEPT.STUDY.NAME,
                CONCEPT.PARTICIPANT.ID,
                CONCEPT.DISCOVERY.VARIANT.ID
        ])
        for consent_name in dataset['consent-groups'].keys():
            consent = dataset['consent-groups'][consent_name]
            # We need a way to point back to the family when we parse our specimen file
            family_lkup = {}

            # There is currently no reference to the proband from parent rows, so we 
            # need to define that. 
            proband_relationships = defaultdict(dict)           # parent_id => "relationship" => proband_id 

            if 'field_map' in consent:
                Transform.LoadFieldMap(consent['field_map'])
                print(Transform._field_map)

            if 'data_map' in consent:
                Transform.LoadDataMap(consent['data_map'])
                print(Transform._data_map)
                print(Transform._data_transform)

            if 'invalid-ids' in consent:
                Transform.LoadInvalidIDs(consent['invalid-ids'])
                print(Transform._invalid_ids)

            consent_group = ConsentGroup(study_name, study_title=study_title, study_id=study_id, group_name=consent_name, consent_name=consent_name)

            drs_ids = {}
            if 'drs' in consent:
                with open(consent['drs'], 'rt') as file:
                    reader = csv.DictReader(file, delimiter='\t', quotechar='"')

                    for row in reader:
                        locals = dict(zip(row['filenames'].split(","), row['object_id'].split(",")))
                        for fn in locals.keys():
                            drs_ids[fn] = locals[fn]

            diseases = []
            with open(consent['subject'], 'rt', encoding='utf-8-sig') as file:
                Transform._cur_filename = 'subject'
                try:
                    reader = Transform.GetReader(file, delimiter=delim)
                except:
                    pdb.set_trace()
                    print(f"There was an issue with loading data from the file, {consent['subject']}")
                    reader = Transform.GetReader(file, delimiter=delim)

                peeps = []
                Transform._linenumber = 1
                for line in reader:
                    Transform._linenumber += 1
                    p = Patient(line, family_lkup, proband_relationships)
                    peeps.append(p)

                    d = Disease(line, family_lkup)
                    diseases.append(d)
                # Just in case the pedigree data isn't in order
                for p in peeps:
                    p.write_default(study_name, wsubject, proband_relationships)

            # Diseases
            for d in diseases:
                d.writerow(study_name, wdisease)
            
            # Human Phenotypes
            for d in diseases:
                d.hpo_writerow(study_name, whpo)

            seq_centers = {}        # Capture the sequencing centers to add to 
                                    # our sequencing output
            subj_id = {}            # There are some datasets where there is no
                                    # subject ID in the sequencing file
            with open(consent['sample'], 'rt', encoding='utf-8-sig') as file:
                Transform._cur_filename = 'sample'
                reader = Transform.GetReader(file, file_type='sample', delimiter=delim)

                Transform._linenumber = 1
                for line in reader:
                    try:
                        Transform.CheckForBadIDs(line)
                        Transform._linenumber += 1
                        # We skip over samples that exist twice--a side effect
                        # of concatting wgs onto the the wes data
                        if line['sample_id'] not in Specimen.observed:
                            s = Specimen(line, consent_name, family_lkup, subj_id)
                            if s.sample_provider:
                                seq_centers[s.sample_id] = s.sample_provider
                            consent_group.add_patient(s.id, s.sample_provider)
                            study_group.add_patient(s.id, s.sample_provider, fail_on_seq_center=False)
                            s.write_row(study_name, wspecemin)
                    except InvalidID as error:
                        print(repr(error))
                consent_group.write_data(wconsent)
                
            with open(consent['sequencing'], 'rt', encoding='utf-8-sig') as file:
                reader = Transform.GetReader(file, file_type='sequencing', delimiter=delim)
                
                Transform._linenumber = 1
                for row in reader:
                    try:
                        Transform.CheckForBadIDs(row)
                        Transform._linenumber += 1
                        seq = Sequencing(row, seq_centers, subj_id)
                        seq.write_row(study_name, wsequencing, drs_ids)
                    except InvalidID as error:
                        print(repr(error))
            if "discovery" in consent:
                with open(consent['discovery'], 'rt', encoding='utf-8-sig') as file:
                    Transform._cur_filename = 'discovery'
                    reader = Transform.GetReader(file, delimiter=delim)

                    # subject_id => [variant_id, ...]
                    variants = defaultdict(list)
                    Transform._linenumber = 1
                    for row in reader:
                        Transform._linenumber += 1
                        var = DiscoveryVariant(row)
                        if var.writerow(wdisc_var, study_name):
                            var.add_variant_ids(variants)

                    for id in variants.keys():
                        wdisc_rep.writerow([study_name, id, "::".join(variants[id])])
    study_group.write_data(wconsent)
    fconsent.close()

if __name__ == "__main__":
    # Some files may end up going in a directory corresponding to the environment
    hostsfile = Path(getenv("FHIRHOSTS", 'fhir_hosts'))
    config = safe_load(hostsfile.open("rt"))

    parser = ArgumentParser()
    parser.add_argument("-d", 
                "--dataset", 
                type=FileType('rt'),
                help=f"Dataset config to be used",
                action='append')
    parser.add_argument("-o", "--out", default='output')
    args = parser.parse_args()

    for dsfile in sorted(args.dataset):
        study = safe_load(dsfile)
        study_name = study['study_name'].replace(' ', '_')
        dirname = Path(f"{args.out}/{study_name}/transformed")
        dirname.mkdir(parents=True, exist_ok=True)
        ChangeLog.InitDB(args.out, study_name, purge_priors=True)

        Run(dirname, study_name, study)

    # Write the term cache to file since the API can sometimes be unresponsive
    write_cache()

    print(f"Total calls to remote api {remote_calls}")

    # Make sure the cache is saved
    Variant.cache.commit()
    ChangeLog.Close()