#!/bin/env python

"""
Perform queries associated issues encountered during transformation process
"""

from collections import defaultdict
import pdb 
import csv
import sys

class Variable:
    def __init__(self, cursor, variable_id, filename, varname):
        self.cur = cursor
        self.id = variable_id
        self.table = filename
        self.name = varname

class Report:
    def __init__(self, cursor, report_vars=None):
        """Optionally, limit variables to list in report_vars"""
        self.cur = cursor

        # Variables, hopefully where id-1 is the index 
        self.variables = []

        # Look up a variable by name
        self.vars_by_name = {}

        # filename => [vars found in file]
        self.filenames = defaultdict(list)

        for (varid, filename, name) in self.cur.execute(""" SELECT 
                                            variable_id, 
                                            filename, 
                                            name 
                                        FROM 
                                            variable_names
                                        ORDER BY
                                            variable_id"""):
            if report_vars is None or name in report_vars:
                var = Variable(self.cur, varid, filename, name)
                self.variables.append(var)
                self.vars_by_name[name] = var
                self.filenames[filename].append(var)

    def summarize(self, dataset_name, min_missing=10.0, print_header=True):
        class VarSummary:
            def __init__(self, var, total):
                self.var = var
                self.total = total

                # These should be set to reasonable values 
                self.missing = 0
                self.missed_values = defaultdict(int)
                self.transformed = 0

            @classmethod
            def header(cls, writer):
                writer.writerow(['Dataset', 'Filename', 'Colname', 'Total', '#Miss', '%Missing', 'Untransformed_Values'])

            def summary(self, writer, min_missing=10.0):
                values = []
                for missed in sorted(self.missed_values):
                    values.append(f"{missed}({self.missed_values[missed]})")
                missing_perc = float((self.missing * 100) / self.total)
                if missing_perc > min_missing:
                    writer.writerow([dataset_name,self.var.table, self.var.name, self.total, self.missing, "%.4f" % missing_perc] + values)

        summary_data = {}
        base_qry = """SELECT 
                        variable_id, 
                        count(DISTINCT line_number)
                    FROM 
                        transformations
                    WHERE 
                        dataset_name='{dataset_name}'
                    GROUP BY 
                        variable_id"""
        for (varid, total) in self.cur.execute(f""" SELECT 
                                            variable_id, 
                                            count(DISTINCT line_number)
                                        FROM 
                                            transformations
                                        WHERE 
                                            dataset_name='{dataset_name}'
                                        GROUP BY 
                                            variable_id"""):
            varid = varid -1
            summary_data[varid] = VarSummary(self.variables[varid], total)

        for (varid, val, total) in self.cur.execute(f"""SELECT
                                            variable_id, 
                                            orig_val,
                                            count(DISTINCT line_number)
                                        FROM 
                                            transformations
                                        WHERE 
                                            dataset_name='{dataset_name}' AND
                                            new_val == '' AND
                                            orig_val != ''
                                        GROUP BY 
                                            variable_id,
                                            orig_val"""):     
            varid = varid -1
            summary_data[varid].missing += total
            summary_data[varid].missed_values[val] = total

        for (varid, total) in self.cur.execute(f"""SELECT
                                            variable_id, 
                                            count(DISTINCT line_number)
                                        FROM 
                                            transformations
                                        WHERE 
                                            dataset_name='{dataset_name}' AND
                                            new_val != ''
                                        GROUP BY 
                                            variable_id"""):     
            varid = varid -1
            summary_data[varid].transformed = total
        writer = csv.writer(sys.stdout, delimiter=',', quotechar='"')

        if print_header:
            VarSummary.header(writer)
        for varid in sorted(summary_data.keys()):
            summary_data[varid].summary(writer, min_missing)



