#!/usr/bin/env python

"""Pull the details about a gene symbol from genenames.org """

import requests
import collections
import re

import pprint
import sys

from time import sleep

url = "http://rest.genenames.org/fetch/symbol"
alt_url = "http://rest.genenames.org/search"

class Gene:
    cache = {}
    def __init__(self, data_chunk):
        self.id = data_chunk['hgnc_id']
        self.symbol = data_chunk['symbol']
        self.name = data_chunk['name']
        self.omim_id = data_chunk['omim_id']
        self.orphanet = None 
        if 'orphanet' in data_chunk:
            self.orphanet = data_chunk['orphanet']
        self.pubmed = data_chunk['pubmed_id']
        self.refseq = data_chunk['refseq_accession']
        self.status = data_chunk['status']
        self.gene_group = None 

        if 'gene_group' in data_chunk:
            self.gene_group = data_chunk['gene_group']
        self.aliases = []

        if 'alias_symbol' in data_chunk:
            self.aliases = data_chunk['alias_symbol']

    def __repr__(self):
        return f"{self.symbol}:{self.name} - {self.id}"

    @classmethod
    def get_gene(cls, symbol):
        if symbol not in Gene.cache:
            query = f"{url}/{symbol}"
            response = requests.get(query, headers={"content-type":"JSON", "accept":"application/json"})

            sleep(0.3)
            if response:
                result = response.json()
                if result:
                    genes = []

                    for doc in result['response']['docs']:
                        genes.append(Gene(doc))
                    
                    if len(genes) > 1:
                        print(f"Unexpectedly encountered more than one gene and not sure how to proceed: {genes}")
                        sys.exit(1)

                    if len(genes) > 0:
                        Gene.cache[symbol] = genes[0]

        if symbol in Gene.cache:
            return Gene.cache[symbol]

        # Let's consider that it may be an alias
        query = f"{alt_url}/{symbol}"
        response = requests.get(query, headers={"content-type":"JSON", "accept":"application/json"})
        sleep(0.3)
        if response:
            result = response.json()
            print(pprint.pprint(result))
            for alt in result['response']['docs']:
                gene = Gene.get_gene(alt['symbol'])
                if gene:
                    Gene.cache[symbol] = gene
                    return gene
        print("Ugh. Still nothing!")            
        sys.exit(1)


if __name__=="__main__":
    gene = Gene.get_gene(sys.argv[1])
