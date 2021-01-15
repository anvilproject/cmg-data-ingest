
from ncpi_fhir_plugin.common import CONCEPT, constants
from cmg_transform import Transform, ParseDate
from term_lookup import pull_details, write_cache

class Sequencing:
    file_cols = ['seq_filename',
        'cram_path',
        'crai_path', 
        'vcf']

    # We need this in case the build isn't part of the discovery data
    genome_builds = {}      # sample_id => reference sequence

    def __init__(self, row, seq_centers, subj_id):
        self.sample_id = row.get('sample_id')

        # a few of Broad's sequence entries don't have sample information associated with the
        # sequence output...so, we have to extract it from the filename
        if self.sample_id is None:
            if 'cram_or_bam_path' in row:
                self.sample_id =  Transform.ExtractVar(row, 'cram_or_bam_path').split("/")[-1].split(".")[0]
            else:
                print("No sample IDs nor cram_or_bam_path")
                sys.exit(1)
        try:
            self.subject_id = Transform.CleanSubjectId(Transform.ExtractVar(row, 'subject_id')) 
        except KeyError:
            self.subject_id = subj_id[self.sample_id]
        self.seq_filenames = []     

        for col in Sequencing.file_cols:
            if col in row:
                # One of the broad's cmg datasets didn't have cram_path, but another had both
                # cram_path and cram_or_bam...and we dont' want dupes
                if row[col] not in self.seq_filenames:
                    self.seq_filenames.append(Transform.ExtractVar(row, col))

        #self.seq_file_type = self.seq_filename.split(".")[-1]
        if 'analyte_type' in row:
            self.analyte_type =Transform.ExtractVar(row, 'analyte_type')
        elif 'data_type' in row:
            self.analyte_type = Transform.ExtractVar(row, 'data_type')
        else:
            self.analyte_type = None

        self.sequencing_assay = Transform.ExtractVar(row, 'sequencing_assay')
        if 'data_type' in row:
            self.sequencing_assay = Transform.ExtractVar(row, 'data_type')
        else:
            self.sequencing_assay = None
        self.library_prep_kit_method = Transform.ExtractVar(row, 'library_prep_kit_method')
        self.exome_capture_platform = Transform.ExtractVar(row, 'exome_capture_platform')
        self.capture_region_bed_file = Transform.ExtractVar(row, 'capture_region_bed_file')
        self.reference_genome_build = Transform.ExtractVar(row, 'reference_genome_build')
        self.alignment_method = Transform.ExtractVar(row, 'alignment_method')
        self.data_processing_pipeline = Transform.ExtractVar(row, 'data_processing_pipeline')

        self.functional_equivalence_standard = None
        if 'functional_equivalence_standard' in row:
            self.functional_equivalence_standard = Transform.ExtractVar(row, 'functional_equivalence_standard', constants.COMMON)
        if 'date_data_generation' in row:
            self.date_data_generation = ParseDate(Transform.ExtractVar(row, 'date_data_generation'))
        elif 'release_date' in row:
            self.date_data_generation = ParseDate(Transform.ExtractVar(row, 'release_date'))

        self.seq_center = None

        if self.sample_id:
            self.seq_center = seq_centers.get(self.sample_id)

        # for now, our sequencing id is just the file prefix
        self.sequencing_id = None

        if len(self.seq_filenames) > 0:
            self.sequencing_id = ".".join(self.seq_filenames[0].split(".")[0:-1])

        if self.reference_genome_build is not None:
            Sequencing.genome_builds[self.sample_id] = self.reference_genome_build

    @classmethod
    def write_header(cls, writer):
        writer.writerow([
            CONCEPT.STUDY.NAME,
            CONCEPT.PARTICIPANT.ID,
            CONCEPT.SEQUENCING.ID,
            CONCEPT.SEQUENCING_GENOMIC_FILE.ID,
            CONCEPT.GENOMIC_FILE.FILE_FORMAT,
            CONCEPT.SEQUENCING.DRS_URI,
            CONCEPT.SEQUENCING.CENTER.ID,
            CONCEPT.BIOSPECIMEN.ID,
            CONCEPT.BIOSPECIMEN.ANALYTE,
            CONCEPT.SEQUENCING.ASSAY,
            CONCEPT.SEQUENCING.LIBRARY_NAME,
            CONCEPT.SEQUENCING.PLATFORM,
            CONCEPT.SEQUENCING.CAPTURE_REGION,
            CONCEPT.SEQUENCING.REFERENCE_GENOME,
            CONCEPT.SEQUENCING.ALIGNMENT_METHOD,
            CONCEPT.SEQUENCING.DATA_PROC_PIPELINE,
            CONCEPT.SEQUENCING.FUNCTIONAL_EQUIVALENCE_PIPELINE,
            CONCEPT.SEQUENCING.DATE
            ])

    def write_row(self, study_name, writer, drs_ids):
        for fn in self.seq_filenames:
            drs_uri = drs_ids.get(fn.split("/")[-1])

            file_type = fn.split(".")[-1]
            writer.writerow([
                study_name,
                self.subject_id,
                self.sequencing_id,
                fn,
                file_type,
                drs_uri,
                self.seq_center,
                self.sample_id,
                self.analyte_type,
                self.sequencing_assay,
                self.library_prep_kit_method,
                self.exome_capture_platform,
                self.capture_region_bed_file,
                self.reference_genome_build,
                self.alignment_method,
                self.data_processing_pipeline,
                self.functional_equivalence_standard,
                self.date_data_generation
            ])