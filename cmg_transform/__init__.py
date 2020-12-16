"""
This module contains the classes related to CMG data transformation. 
"""
import csv
from ncpi_fhir_plugin.common import CONCEPT, constants

def ParseDate(value):
    # 20160525  -- May need to test for "-" and "/" or other characters
    if len(value.strip()) == 8:
        year = value[0:4]
        month = value[4:6]
        day = value[6:]

        return f"{year}-{month}-{day}"
    return None


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

    _raw_chroms = [str(x) for x in range(1,23)] + ['X', 'Y']

    def CleanVar(constobj, rawval, default_to_empty=False):
        val = rawval

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
                if default_to_empty:
                    return ""

                if val in Transform._alt_transforms[constobj]:
                    return Transform._alt_transforms[constobj][val]
                # if this excepts, then we need to figure out what is going wrong
                # Eventually, this will become it's own exception which can be handled
                # nicely at the application layer
                raise e         
        return None

    def CleanSubjectId(var):
        # For now, just strip the character data from the strings
        return var