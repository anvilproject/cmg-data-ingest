def addReference(value_name, value_ref):
    return {
        "type": {
            "text": value_name
        },
        "valueReference": {
            "reference": value_ref
        }
    }

def addValuestring(value_name, value):
    return {
                "type": {
                    "text": value_name
                },
                "valueString": value
            }        
def addValuebool(value_name, value):
    return {
                "type": {
                    "text": value_name
                },
                "valueBoolean": value
            }

class Component:
    def addValuestring(value_name, value):
        return {
                    "code": {
                        "text": value_name
                    },
                    "valueString": value
                }        
    def addValuebool(value_name, value):
        return {
                    "code": {
                        "text": value_name
                    },
                    "valueBoolean": value
                }