"""
This module contains the classes related to CMG data transformation. 
"""
import csv
from ncpi_fhir_plugin.common import CONCEPT, constants
from csv import DictReader
from collections import defaultdict
from cmg_transform.change_logger import ChangeLog

def ParseDate(value):
    # 20160525  -- May need to test for "-" and "/" or other characters
    if len(value.strip()) == 8:
        year = value[0:4]
        month = value[4:6]
        day = value[6:]

        return f"{year}-{month}-{day}"
    return None


def strip(val):
    if val is not None:
        return val.strip()
    return val
# 
# TODO
# To attempt to reach the deadline, I'm just jamming in anything that doesn't fit
# Some of these really do need to be handled more carefully

class Transform:
    # If it's a valid entry, but not one in the constant's list, then we will 
    # attempt to convert it to one that will be supported by our fhir server's 
    # model configuration

    # KF Constant class  => { expected => transformed }
    _alt_transforms = {
        constants.PHENOTYPE.OBSERVED : {
            "Affected": constants.PHENOTYPE.OBSERVED.YES,
            "Unaffected": constants.PHENOTYPE.OBSERVED.NO,
            '': '',
            'Unknown': '',
        },
        constants.RACE : {
            "Black or African American" : constants.RACE.BLACK,
            "American Indian or Alaskan Native": constants.RACE.NATIVE_AMERICAN,
            "Unknown": constants.COMMON.UNKNOWN,
            'Other': constants.COMMON.OTHER,
            '': None
        },
        constants.GENDER : {
            "Intersex": constants.COMMON.OTHER,
            "Unknown" : "unknown"
        },
        constants.AFFECTED_STATUS : {
            '' : "",
            "Unknown": constants.COMMON.UNKNOWN,
            'Other': constants.COMMON.OTHER
        },
        constants.COMMON: {
            "yes" : "true",
            "no" : "false"
        },
        constants.RELATIONSHIP: {
            "mother's cousin #2": ''
        }
    }

    _missing = set(['-'])

    _field_map = {}

    # The map is a 1 to one replacement     SUBSTR != YES
    _data_map = defaultdict(dict)

    # The transform is a text substitution. SUBSTR == YES
    _data_transform = defaultdict(dict)

    _raw_chroms = [str(x) for x in range(1,23)] + ['X', 'Y']

    _cur_filename = None
    _linenumber = 0

    def ExtractVar(row, fieldname, constobj=None, default_to_empty=False):
        curval = strip(row.get(fieldname))

        newval = Transform.GetValue(row, fieldname)
        if constobj is not None:
            newval = Transform.CleanVar(constobj, newval, default_to_empty)
        """    
        if constobj is None:
            newval = Transform.GetValue(row, fieldname)
        else:
            newval = Transform.CleanVar(constobj, curval, default_to_empty)
        """
        # log the extraction
        ChangeLog._instance.add_transformation(
                                                Transform._cur_filename, 
                                                fieldname, 
                                                Transform._linenumber, 
                                                curval, 
                                                newval)

        return newval

    def CleanDataVar(constobj, row, fieldname, default_to_empty=False):
        val = Transform.GetValue(row, fieldname)

        return Transform.CleanVar(constobj, val, default_to_empty)

    def GetValue(row, fieldname):
        val = strip(row.get(fieldname))

        if fieldname in Transform._data_map:
            if val in Transform._data_map[fieldname]:
                return Transform._data_map[fieldname][val]

        if fieldname in Transform._data_transform:
            for err in Transform._data_transform[fieldname].keys():
                if err in val:
                    return val.replace(err, Transform._data_transform[fieldname][err]).strip()

        return Transform.Value(val)

    def Value(val):
        """Since we get some weird stuff that probably means "missing", we'll just strip that out"""
        if val not in Transform._missing:
            return val
        return ""

    def CleanVar(constobj, rawval, default_to_empty=False):
        val = rawval

        if val is None or val.strip() == "":
            return None

        # For the CMG datasets I've seen, chromosomes are bare numbers/letters
        # this doesn't make for very useful constant variable names and we 
        # do want to enforce constants and provide something clear for the
        # display parameter
        if constobj == constants.DISCOVERY.VARIANT.CHROMOSOME:
            if val in Transform._raw_chroms:
                val = f"Chr{val}"

        # Definitely want to get rid of whitespace
        if val is not None:
            propname = val.strip().upper().replace(" ", "_")
            try:
                # This is just a way to verify that our data conforms to constants
                # If it works, then we have our value. We'll take the extracted value
                # so that case coming in doesn't have to match
                propname = getattr(constobj, propname)
                return propname
            except AttributeError as e:
                if constobj in Transform._alt_transforms:
                    if val in Transform._alt_transforms[constobj]:
                        return Transform._alt_transforms[constobj][val]

                if default_to_empty:
                    return ""
                # if this excepts, then we need to figure out what is going wrong
                # Eventually, this will become it's own exception which can be handled
                # nicely at the application layer
                raise e         
        return None

    def CleanSubjectId(var):
        # For now, just strip the character data from the strings
        return var

    def LoadFieldMap(filename):
        if filename is not None:
            with open(filename, 'rt') as f:
                reader = DictReader(f, delimiter=',', quotechar='"')

                for line in reader:
                    Transform._field_map[line['CURRENT']] = line['EXPECTED']

    def LoadDataMap(filename):
        if filename is not None:
            with open(filename, 'rt') as f:
                reader = DictReader(f, delimiter=',', quotechar='"')

                for line in reader:
                    if line['SUBSTR'] == "YES":
                        Transform._data_transform[line['FIELD_NAME']][line['ALTERNATIVE']] = line['EXPECTED']
                    else:
                        Transform._data_map[line['FIELD_NAME']][line['ALTERNATIVE']] = line['EXPECTED']


    def GetReader(csv_file, delimiter=','):
        reader = csv.DictReader(csv_file, delimiter=delimiter, quotechar='"')

        fieldnames = []
        for colname in reader.fieldnames:
            if colname in Transform._field_map:
                fieldnames.append(Transform._field_map[colname])
                print(f"Transforming {csv_file.name}:{colname} into {Transform._field_map[colname]}")
            else:
                fieldnames.append(colname)

        reader.fieldnames = fieldnames
        return reader