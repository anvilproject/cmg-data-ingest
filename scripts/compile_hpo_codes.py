#!/usr/bin/env python

from argparse import ArgumentParser, FileType
import sys
import csv
from pathlib import Path
from json import load, dump

"""
Parse one or more TSV files as produced by the transform script to generate a comprehensive HP CodeSystem
"""

if __name__ == "__main__":
    files = list(Path().glob("output/*/transformed/hpo.tsv"))
    id_col = 'PHENOTYPE|HPO_ID'
    name_col = 'PHENOTYPE|NAME'

    print(f"{len(files)} HPO files found.")
    visited = set()
    # This is the core JSON object. We'll add to content and count
    meta = load(open("scripts/hpo.meta.json"))

    for dataset in files:
        with open(dataset, 'rt') as inf:
            reader = csv.DictReader(inf, delimiter='\t', quotechar='"')
            print(reader.fieldnames)
            for row in reader:
                codeval = row[id_col]

                if codeval.strip() != "" and codeval not in visited:
                    meta["concept"].append({
                        "code": row[id_col],
                        "display": row[name_col]
                        })
                    visited.add(codeval)
    meta['count'] = len(meta['concept'])

    outfilename = "CodeSystem-hp.json"
    with open(outfilename, 'wt') as outf:
        dump(meta, outf, indent=2)
       
