#!/usr/bin/env python

"""get details about SNVs from NIH website"""

# They do enumerate these with incremental changes, so we should periodically verify that it is still
# the most recent version

import requests
import collections
import re
from csv import DictReader, DictWriter, writer
from time import sleep
from pathlib import Path 
from datetime import datetime

url = "https://clinicaltables.nlm.nih.gov/api/variants/v4/search?terms="
cache_path = Path(__file__).resolve().parent

class VarCache:
    fn = cache_path / "variant_cache.csv"

    # This is a big part, capturing those that don't match what we are trying to find
    miss = cache_path / "variant_missing.csv"

    # How long do we keep these failed matches around? 
    max_missing_age = 30
    def __init__(self):
        self.data = {}
        self.missing = {}

        if VarCache.fn.is_file():
            with open(VarCache.fn, 'rt') as f:
                reader = DictReader(f, delimiter=',', quotechar='"')

                for line in reader:
                    self.data[line['VariantID']] = Variant(line)

        if VarCache.miss.is_file():
            now = datetime.now()
            with open(VarCache.miss, 'rt') as f:
                reader = DictReader(f, delimiter=',', quotechar='"')

                for line in reader:
                    # If the age of missing is greater than the maximum, we'll 
                    # try again if it's encountered
                    origin = datetime.fromtimestamp(float(line['date']))
                    if (now - origin).days < VarCache.max_missing_age:
                        self.missing[line['name']] = float(line['date'])
                    else:
                        print(str(origin))
                        print((now - origin).days)
                        print(VarCache.max_missing_age)
                        print((now - origin).days > VarCache.max_missing_age)
                        print(f"Ignoring 'missing' {line['name']} entry due to age expirey")


    def add_missing(self, name):
        self.missing[name] = datetime.now().timestamp()

    def add_variant(self, name, var):
        self.data[name] = var 

    def get_variant(self, name):
        if name in self.data:
            return self.data[name]

        if name in self.missing:
            return -1
        return None

    def commit(self):
        with open(VarCache.fn, 'wt') as f:
            wrt = DictWriter(f, delimiter=',', quotechar='"', fieldnames=Variant.header)
            wrt.writeheader()
            for id in sorted(self.data.keys()):
                wrt.writerow(self.data[id].as_obj())

        with open(VarCache.miss, 'wt') as f:
            wrt = writer(f, delimiter=',', quotechar='"')
            wrt.writerow(['name', 'date'])

            for id in sorted(self.missing.keys()):
                wrt.writerow([id, self.missing[id]])

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
    header = ['Name', 'VariantID', 'GeneSymbol', 'Type', 'dbSNP', 'Chromosome', 'GenomicLocation', 'PhenotypeIDS', 'PhenotypeList', 'phenotype']
    cache = None
    def __init__(self, data):
        self.name = data['Name']
        self.variant_id = data['VariantID']
        self.gene_symbol = data['GeneSymbol']
        self.type = data['Type']
        self.dbSnp = data['dbSNP']
        self.chr = data['Chromosome']
        self.pos = data['GenomicLocation']

        self.phenotypes = collections.defaultdict(list)
        self.phenotype_ids = data['PhenotypeIDS']
        for pheno in data['PhenotypeIDS'].split(","):
            for ph in pheno.split(";"):
                entry = PhenoID(ph)

                self.phenotypes[entry.onto].append(entry)

        self.raw_pheno = data['PhenotypeList']
        self.phenotype = data['phenotype']

    def printme(self):
        print(f"{self.name} [{self.chr}:{self.pos}] ({self.dbSnp}) -- {self.variant_id} -- {self.gene_symbol} : {self.raw_pheno}")
        print(f"{self.phenotypes}")

    def as_obj(self):
        return {
            'Name' : self.name,
            'VariantID' : self.variant_id,
            'GeneSymbol' : self.gene_symbol,
            'Type' : self.type,
            'dbSNP' : self.dbSnp,
            'Chromosome' : self.chr,
            'GenomicLocation' : self.pos,
            'PhenotypeIDS' : self.phenotype_ids,
            'PhenotypeList': self.raw_pheno,
            'phenotype': self.phenotype
        }
Variant.cache = VarCache()
header = "VariantID,Type,dbSNP,GeneSymbol,Name,Chromosome,GenomicLocation,PhenotypeList,phenotype,phenotypes,PhenotypeIDS,VariationID,AminoAcidChange,RefSeqID".split(",")
def get_variant(hgvsc, transcript):
    # We can't rely on the versions matching. 
    trscpt = transcript.split(".")[0]

    var = Variant.cache.get_variant(hgvsc)

    # If the name has already been identified as missing, just abort
    if var == -1:
        return None

    # Return cached entity
    if var is not None:
        return var

    try:
        query = f"{url}{trscpt} {hgvsc}&maxList=500&df={','.join(header)}"
        response = requests.get(query)
        sleep(1)
    # Some queries regularly fail
    except:
        print(f"There was a problem getting the variant information for {hgvsc}")
        response = None


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
                var = Variant(values)
                Variant.cache.add_variant(hgvsc, var)

                return var
        if count > 0:
            print(f"We found {count} records, for the hgsvc, but none matched the transcript")

        # Make a note about missing data so we don't requery it for a certain amount of time
        Variant.cache.add_missing(hgvsc)

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

    # Since __del__ is weird, let's just force it
    Variant.cache.commit()