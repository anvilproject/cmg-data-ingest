#!/usr/bin/env python

"""This script just pulls variant codes from the output from the transformation and builds a FHIR CodeSystem for adding to the model. """

import sys
import csv

from ncpi_fhir_plugin import common
from pathlib import Path


# colnames: DISCOVERY|VARIANT|HGVSC , DISCOVERY|VARIANT|HGVSP
#           common.DISCOVERY.GENE.VARIANT.HGVSC
#           common.DISCOVERY.GENE.VARIANT.HGVSP
variants = set()

for filename in list(Path().glob("output/*/transformed/discovery_variant.tsv")):
    with open(filename, 'rt') as file:
      reader = csv.DictReader(file, delimiter='\t', quotechar='"')
      #print(reader.fieldnames)
      for row in reader:
          if row[common.DISCOVERY.VARIANT.HGVSC].strip() != "":
              variants.add(row[common.DISCOVERY.VARIANT.HGVSC].strip())
          if row[common.DISCOVERY.VARIANT.HGVSP].strip() != "":
              variants.add(row[common.DISCOVERY.VARIANT.HGVSP].strip())
concept = []
for var in sorted(list(variants)):
    concept.append(f"""  {{
    "code": "{var}",
    "display": "{var}"
  }}""")
concept_list = ",\n".join(concept)
print(f"""{{
  "resourceType": "CodeSystem",
  "id": "v3-hgvs",
  "text": {{
    "status": "generated",
    "div": "<div xmlns=\\"http://www.w3.org/1999/xhtml\\"><p>This code system http://varnomen.hgvs.org defines many codes, but they are not represented here</p></div>"
  }},
  "url": "http://varnomen.hgvs.org",
  "identifier": [
    {{
      "system": "urn:ietf:rfc:3986",
      "value": "urn:oid:2.16.840.1.113883.6.282"
    }}
  ],
  "version": "2.0.0",
  "name": "Hgvs",
  "title": "Human Genome Variation Society nomenclature",
  "status": "active",
  "experimental": false,
  "date": "2019-03-20T00:00:00-04:00",
  "publisher": "Human Genome Variation Society",
  "description": "HGVS nomenclatures are the guidelines for mutation nomenclature made by the Human Genome Variation Society.\\r\\n\\r\\nHGVS nomenclature can be used with the HL7 coded data type (code data type that accepts expression data, or a coded expression data type). This coded data type should be able to distinguish expressions in HGVS nomenclature from coded concepts. For example, in the HL7 messages specified according to the HL7 V2 Clinical Genomics Fully LOINC-Qualified Genetic Variation Model, HGVS nomenclature can be used to as the observation values for DNA sequence variations. For example, OBX|1|CWE|48004-6^DNA Sequence Variation^LN||c.1129C>T^^HGVS|\\r\\n\\r\\nVersioning information: The HGVS nomenclature for the description of sequence variants was last modified Feb 20, 2008. The HGVS nomenclature for the description of protein sequence variants was last modified May 12, 2007. The HGVS nomenclature for the description of DNA sequence variants was last modified June 15, 2007 The HGVS nomenclature for the description of RNA sequence variants was last modified May 12, 2007\\r\\n\\r\\nHGVS nomenclatures can be used freely by the public.",
  "content": "complete",
  "count": {len(concept)},
  "concept": [
  {concept_list}
  ]
}}""")
