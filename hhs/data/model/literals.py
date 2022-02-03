from hhs.data.model import hashing

#type Literal           = { hash: Hash, value: any, author?: Hash, signature?: string, dependencies: Array<Dependency> }
#type Dependency        = { path: string, hash: Hash, className: string, type: ('literal'|'reference') };

def getType(literal):
    return literal['value']['_type']

def getClassName(literal):
    return literal['value']['_class']

def getFields(literal):
    return literal['value']['_fields']

def getFlags(literal):
    return literal['value']['_flags']

# FIXME: I think this break custom hashes!!!!
# I think you cannot check the hash without deliteralizing the object.
def validateHash(literal):
    return literal.hash == hashing.forValue(literal.value)