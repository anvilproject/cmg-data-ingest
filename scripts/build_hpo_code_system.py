#!/usr/bin/env python

"""This script just pulls HPO codes from the output from the transformation and builds a FHIR CodeSystem for adding to the model. """

import sys
import csv

from pathlib import Path
import networkx
import obonet

obo_path = Path(__file__).resolve().parent

"""
Parse the obo file pulled from the internet and build a complete code system for all HP Codes. This script is nolonger used because the code systems were taking too long for the CI tests to complete their tests.
"""

hp_codes = {}

filename = obo_path / "hp-full.obo"

graph = obonet.read_obo(filename, ignore_obsolete=False)

nodes = graph.nodes(data=True)

for (id, data) in nodes:
    if id[0:2] == "HP":
        hp_codes[id] = data.get('name')

    if 'alt_id' in data:
        for aid in data['alt_id']:
            if aid not in hp_codes and aid[0:2] == "HP":
                hp_codes[aid] = data.get('name')

codes = []
for code in sorted(hp_codes.keys()):
    codes.append("    {" + f"""
  "code" : "{code}",
  "display": "{hp_codes[code]}"
""" + "    }")


with open("CodeSystem-hp.json", 'wt') as f:
    f.write("""{
  "resourceType": "CodeSystem",
  "id": "hp",
  "url": "http://purl.obolibrary.org/obo/hp.owl",
  "version": "http://purl.obolibrary.org/obo/hp/releases/2020-03-27/hp.owl",
  "name": "http://purl.obolibrary.org/obo/hp.owl",
  "title": "Human Phenotype Ontology",
  "status": "draft",
  "experimental": false,
  "description": "Please see license of HPO at http://www.human-phenotype-ontology.org",
  "valueSet": "http://fhir.ncpi-project-forge.io/ValueSet/phenotype-codes",
  "hierarchyMeaning": "is-a",
  "compositional": false,
  "versionNeeded": false,
  "content": "complete",
  "count": """ + str(len(codes)) + """,
  "filter": [
    {
      "code": "root",
      "operator": [
        "="
      ],
      "value": "True or false."
    },
    {
      "code": "deprecated",
      "operator": [
        "="
      ],
      "value": "True or false."
    },
    {
      "code": "imported",
      "operator": [
        "="
      ],
      "value": "True or false"
    }
  ],
  "property": [
    {
      "code": "parent",
      "description": "Parent codes.",
      "type": "code"
    },
    {
      "code": "imported",
      "description": "Indicates if the concept is imported from another code system.",
      "type": "boolean"
    },
    {
      "code": "root",
      "description": "Indicates if this concept is a root concept (i.e. Thing is equivalent or a direct parent)",
      "type": "boolean"
    },
    {
      "code": "deprecated",
      "description": "Indicates if this concept is deprecated.",
      "type": "boolean"
    }
  ],
  "concept": [
""" + ','.join(codes) + """
  ]
}
""")

