#!/usr/bin/env python

"""get details about SNVs from NIH website"""

# They do enumerate these with incremental changes, so we should periodically verify that it is still
# the most recent version
url = "https://clinicaltables.nlm.nih.gov/api/variants/v4/search?terms="
import requests
import collections
import re

class PhenoID:
    system_sources = {
        re.compile("(?P<onto>MedGen)[.:](?P<code>[A-Z]+[0-9]+)", re.I): "http://www.ncbi.nlm.nih.gov/medgen",
        re.compile("(?P<onto>ORPHA)[.:](?P<code>[A-Z][0-9]+)", re.I): "http://www.orpha.net",
        re.compile("(?P<onto>OMIM)[.:](?P<code>[A-Z][0-9]+)", re.I): "http://www.omim.org"
    }    

    def __init__(self, entry):

        self.onto = None
        self.code = None
        self.system = None

        for ex in PhenoID.system_sources.keys():
            g = ex.search(entry)

            if g is not None:
                self.onto = g.group('onto')
                self.code = g.group('code')
                self.system = PhenoID.system_sources[ex]

    def __str__(self):
        return f"{self.onto}.{self.code} : {self.system}"

    def __repr__(self):
        return f"{self.onto}.{self.code} : {self.system}"


class Variant:
    def __init__(self, data):
        self.name = data['Name']
        self.variant_id = data['VariantID']
        self.gene_symbol = data['GeneSymbol']
        self.type = data['Type']
        self.dbSnp = data['dbSNP']
        self.chr = data['Chromosome']
        self.pos = data['GenomicLocation']

        self.phenotypes = collections.defaultdict(list)
        for pheno in data['PhenotypeIDS'].split(","):
            for ph in pheno.split(";"):
                entry = PhenoID(ph)

                self.phenotypes[entry.onto].append(entry)

        self.raw_pheno = data['PhenotypeList']
        self.phenotype = data['phenotype']

    def printme(self):
        print(f"{self.name} [{self.chr}:{self.pos}] ({self.dbSnp}) -- {self.variant_id} -- {self.gene_symbol} : {self.raw_pheno}")
        print(f"{self.phenotypes}")

header = "VariantID,Type,dbSNP,GeneSymbol,Name,Chromosome,GenomicLocation,PhenotypeList,phenotype,phenotypes,PhenotypeIDS,VariationID,AminoAcidChange,RefSeqID".split(",")
def get_variant(hgvsc, transcript):
    # We can't rely on the versions matching. 
    trscpt = transcript.split(".")[0]

    query = f"{url}{trscpt} {hgvsc}&maxList=500&df={','.join(header)}"
    response = requests.get(query)

    if response:
        result = response.json()
        id = result[0]
        lst = result[1]
        # 3rd is always none
        data = result[3]
        count = 0
        for chunk in data:
            count += 1
            values = dict(zip(header, chunk))

            if values['RefSeqID'].split(".")[0] == trscpt:
                return Variant(values)
        if count > 0:
            print(f"We found {count} records, for the hgsvc, but none matched the transcript")

if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("-t", 
                "--transcript", 
                required=True,
                help=f"The trascript associated with the hgsvc")
    parser.add_argument("-c", 
                "--hgsvc",  
                required=True,
                help=f"The variation hgsvc")
    args = parser.parse_args()

    var = get_variant(args.hgsvc, args.transcript)
    if var:
        var.printme()
    else:
        print("Your query returned no results")