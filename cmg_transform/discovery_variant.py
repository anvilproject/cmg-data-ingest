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
        if "subject_id" not in row:
            print(sorted(row.keys()))
        self.id = Transform.CleanSubjectId(row['subject_id']) # Transform.CleanSubjectId(row['subject_id'])
        self.sample_id = row['sample_id']
        self.gene = Transform.ExtractVar(row, 'gene')
        self.gene_class = Transform.ExtractVar(row, 'gene_class')
        self.gene_code = self.gene
        self.zygosity = Transform.ExtractVar(row, 'zygosity')

        # Some of the genes are done weirdly, so we'll try and fix them now:
        if self.gene is not None and ":" in self.gene:
            self.gene, tier = self.gene.split(":")
            if self.gene_class == "Candidate":
                self.gene_class = f"{tier} - Candidate"

        if 'variant_genome_build' in row:
            self.ref_seq = Transform.ExtractVar(row, 'variant_genome_build', constants.DISCOVERY.VARIANT.GENOME_BUILD, default_to_empty=True)
        else:
            if self.sample_id in Sequencing.genome_builds:
                self.ref_seq = DiscoveryVariant.genome_builds[Sequencing.genome_builds[self.sample_id]]
            else:
                self.ref_seq = None
        self.chrom = Transform.ExtractVar(row, 'chrom', constants.DISCOVERY.VARIANT.CHROMOSOME, default_to_empty=True)
        self.pos = Transform.ExtractVar(row, 'pos')
        self.ref = Transform.ExtractVar(row, 'ref')
        self.alt = Transform.ExtractVar(row, 'alt')
        self.hgvsc = Transform.ExtractVar(row, 'hgvsc')
        self.hgvsp = Transform.ExtractVar(row, 'hgvsp')
        self.transcript = Transform.ExtractVar(row, 'transcript')
        self.sv_name = Transform.ExtractVar(row, 'sv_name')
        self.sv_type = Transform.ExtractVar(row, 'sv_type')
        self.significance = Transform.ExtractVar(row, 'significance', constants.DISCOVERY.VARIANT.SIGNIFICANCE)
        self.variant_id = None
        if self.chrom is not None:
            self.variant_id = f"{self.chrom}|{self.pos}|{self.ref}|{self.alt}"


        if self.gene:
            try:
                gene = Gene.get_gene(self.gene)
                if gene:
                    self.gene_code = gene.id
            except:
                print(f"There was an issue pulling variant details data down for, {self.gene}")

        # if we do get a variant, the ID can be used to construct a URL for clinvar entry, which 
        # may be quite informative
        if self.chrom is not None and self.variant_id is None:
            print(f"Get Variant returned nothing: {self.hgvsc} : {self.hgvsp} : {self.transcript}")
            sys.exit(1)

        if self.hgvsc is not None and self.transcript is not None:
            self.variant = get_variant(self.hgvsc, self.transcript)

        self.inheritance = Transform.ExtractVar(row, 'inheritance_description')

    def add_variant_ids(self, variant_lkup):
        if self.variant_id is not None:
            variant_lkup[self.id].append(f"{self.variant_id}+{self.sample_id}")
            if self.inheritance and self.inheritance.strip() != "":
                variant_lkup[self.id].append(f"{self.variant_id}+{self.sample_id}+{self.inheritance}")

    def writerow(self, writer, study_name):
        """Returns True if there was a variant written to file"""
        if self.variant_id is not None:
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
            return True
        return False

    @classmethod
    def writeheader(cls, writer):
        writer.writerow([
            CONCEPT.PARTICIPANT.ID,
            CONCEPT.STUDY.NAME,
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