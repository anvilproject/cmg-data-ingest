import pytest

from collections import defaultdict
from csv import DictReader
from fhir_walk.model.variants import Variant, VariantReport

from ncpi_fhir_plugin.common import (
            constants,
            CONCEPT
)


def test_variant_details(config, study, transformed_dir):
    host = config.get_host()
    variant_file = transformed_dir / 'discovery_variant.tsv'
    assert variant_file.exists(), "Discovery variant file exists?"

    patients = study.Patients()

    with variant_file.open() as f:
        reader = DictReader(f, delimiter='\t')

        # subject_id => [Objects/id ]  for each variant 
        variant_refs = defaultdict(set)

        for line in reader:
            subject_id = line[CONCEPT.PARTICIPANT.ID]
            specimen_id = line[CONCEPT.BIOSPECIMEN.ID]
            variant_id = line[CONCEPT.DISCOVERY.VARIANT.ID]
            gene_id = line[CONCEPT.DISCOVERY.GENE.ID]
            gene_class = line[CONCEPT.DISCOVERY.GENE.GENE_CLASS]
            gene_code = line[CONCEPT.DISCOVERY.GENE.GENE_CODE]
            genome_build = line[CONCEPT.DISCOVERY.VARIANT.GENOME_BUILD]
            chrom = line[CONCEPT.DISCOVERY.VARIANT.CHROM]
            pos = line[CONCEPT.DISCOVERY.VARIANT.POS]
            ref = line[CONCEPT.DISCOVERY.VARIANT.REF]
            alt = line[CONCEPT.DISCOVERY.VARIANT.ALT]
            zygosity = line[CONCEPT.DISCOVERY.VARIANT.ZYGOSITY]
            hgvsc = line[CONCEPT.DISCOVERY.VARIANT.HGVSC]
            hgvsp = line[CONCEPT.DISCOVERY.VARIANT.HGVSP]
            transcript = line[CONCEPT.DISCOVERY.VARIANT.TRANSCRIPT]
            sv_name = line[CONCEPT.DISCOVERY.VARIANT.SV_NAME]
            sv_type = line[CONCEPT.DISCOVERY.VARIANT.SV_TYPE]
            significance = line[CONCEPT.DISCOVERY.VARIANT.SIGNIFICANCE]
            inheritance = line[CONCEPT.DISCOVERY.VARIANT.INHERITANCE]

            subject = patients[subject_id]
            specimens = subject.specimens()
            specimen = specimens[specimen_id]

            variants = Variant.VariantsBySpecimen(specimen.id, host)
            id = f"Observation|{study.id}|{specimen_id}|{subject_id}|{variant_id}"

            print(f"The Specimen ID {specimen.id} -- {len(variants)} variants returned")
            #print(f"The variant ID {variant.id}")

            assert(id in variants)
            variant = variants[id]

            variant_refs[subject.id].add(f"Observation/{variant.id}")

            if chrom:
                assert variant.chrom == chrom

            if pos:
                assert variant.pos == pos

            if ref:
                assert variant.ref_allele == ref

            if alt:
                assert variant.alt_allele == alt 

            if zygosity:
                assert variant.zygosity == zygosity

            if genome_build:
                assert variant.ref_seq == genome_build 

            if transcript:
                assert variant.transcript == transcript

            if hgvsc:
                assert variant.hgvsc == hgvsc

            if hgvsp:
                assert variant.hgvsp == hgvsp

            if sv_type:
                assert variant.sv_type == sv_type

            if gene_code:
                assert variant.gene.coding == gene_code

            if inheritance:
                assert variant.inheritance == inheritance

            if significance:
                assert variant.significance == significance

        for patient_id in patients:
            patient = patients[patient_id]
            reports = VariantReport.VariantReportsBySubject(patient.id, host)

            report_ids = set()
            print(reports)

            for rep in reports:
                print(rep.id)

            if len(variant_refs[patient.id]) > 0:
                for var in reports[0].result:
                    report_ids.add(f"Observation/{var.id}")

                assert len(reports)==1
                print(report_ids)
                print(variant_refs[patient.id])
                assert report_ids == variant_refs[patient.id]

