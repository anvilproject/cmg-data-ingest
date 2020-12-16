import csv
from ncpi_fhir_plugin.common import CONCEPT, constants
from cmg_transform import Transform
from genenames import Gene
from variant_details import get_variant

from cmg_transform.sequencing import Sequencing

class DiscoveryVariant:
    genome_builds = {
        'hs37d5': 'GRCh37',
        'GRCh38DH': 'GRCh38'
    }
    def __init__(self, row):
        self.id = Transform.CleanSubjectId(row['subject_id']) # Transform.CleanSubjectId(row['subject_id'])
        self.sample_id = row['sample_id']
        self.gene = row['gene']
        self.gene_class = row['gene_class']
        self.gene_code = self.gene
        self.zygosity = row['zygosity']

        # Some of the genes are done weirdly, so we'll try and fix them now:
        if ":" in self.gene:
            self.gene, tier = self.gene.split(":")
            if self.gene_class == "Candidate":
                self.gene_class = f"{tier} - Candidate"

        if 'variant_genome_build' in row:
            self.ref_seq = row['variant_genome_build']
        else:
            self.ref_seq = DiscoveryVariant.genome_builds[Sequencing.genome_builds[self.sample_id]]
        self.chrom = Transform.CleanVar(constants.DISCOVERY.VARIANT.CHROMOSOME, row['chrom'])
        self.pos = row['pos']
        self.ref = row['ref']
        self.alt = row['alt']
        self.hgvsc = row['hgvsc']
        self.hgvsp = row['hgvsp']
        self.transcript = row['transcript']
        self.sv_name = row['sv_name']
        self.sv_type = row['sv_type']
        self.significance = row['significance']
        self.variant_id = f"{self.chrom}|{self.pos}|{self.ref}|{self.alt}"

        if self.gene:
            gene = Gene.get_gene(self.gene)
            if gene:
                self.gene_code = gene.id

        # if we do get a variant, the ID can be used to construct a URL for clinvar entry, which 
        # may be quite informative
        if self.variant_id is None:
            print(f"Get Variant returned nothing: {self.hgvsc} : {self.hgvsp} : {self.transcript}")
            sys.exit(1)
        self.variant = get_variant(self.hgvsc, self.transcript)

        self.inheritance = row['inheritance_description']

    def add_variant_ids(self, variant_lkup):
        variant_lkup[self.id].append(f"{self.variant_id}+{self.sample_id}")
        if self.inheritance and self.inheritance.strip() != "":
            variant_lkup[self.id].append(f"{self.variant_id}+{self.sample_id}+{self.inheritance}")

    def writerow(self, writer, study_name):
        writer.writerow([
            self.id,
            study_name,
            self.sample_id,
            self.variant_id,
            self.gene,
            self.gene_class,
            self.gene_code,
            self.ref_seq,
            self.chrom,
            self.pos,
            self.ref,
            self.alt,
            self.zygosity,
            self.hgvsc,
            self.hgvsp,
            self.transcript,
            self.sv_name,
            self.sv_type,
            self.significance,
            self.inheritance
        ])

    @classmethod
    def writeheader(cls, writer):
        writer.writerow([
            CONCEPT.PARTICIPANT.ID,
            CONCEPT.STUDY.ID,
            CONCEPT.BIOSPECIMEN.ID,
            CONCEPT.DISCOVERY.VARIANT.ID,
            CONCEPT.DISCOVERY.GENE.ID,
            CONCEPT.DISCOVERY.GENE.GENE_CLASS,
            CONCEPT.DISCOVERY.GENE.GENE_CODE,
            CONCEPT.DISCOVERY.VARIANT.GENOME_BUILD,
            CONCEPT.DISCOVERY.VARIANT.CHROM,
            CONCEPT.DISCOVERY.VARIANT.POS,
            CONCEPT.DISCOVERY.VARIANT.REF,
            CONCEPT.DISCOVERY.VARIANT.ALT,
            CONCEPT.DISCOVERY.VARIANT.ZYGOSITY,
            CONCEPT.DISCOVERY.VARIANT.HGVSC,
            CONCEPT.DISCOVERY.VARIANT.HGVSP,
            CONCEPT.DISCOVERY.VARIANT.TRANSCRIPT,
            CONCEPT.DISCOVERY.VARIANT.SV_NAME,
            CONCEPT.DISCOVERY.VARIANT.SV_TYPE,
            CONCEPT.DISCOVERY.VARIANT.SIGNIFICANCE,
            CONCEPT.DISCOVERY.VARIANT.INHERITANCE    
        ])