from hhs.crypto import hashing

def escapeString(text):
    return "'" + str(text).replace("'", "''") + "'"

def serialize(literal):
    plain = ''

    keys = None
    o = None
    c = None
        
    if (type(literal) == dict):
        keys = list(literal.keys())
        keys.sort()
        o = '{'
        c = '}'
    elif (type(literal) == list):
        keys = range(0, len(literal))
        o = '['
        c = ']'

    if (keys != None):
        plain = o

        for key in keys:
            if literal[key] != None:
                plain = plain + escapeString(key) + ':' + serialize(literal[key]) + ','

        plain = plain + c
    elif (type(literal) == str):
        plain = escapeString(literal)
    elif (type(literal) == bool):
        plain = str(literal).lower()
    elif (type(literal) == float):
        if (literal.is_integer()):
            plain = str(int(literal))
        else:
            plain = str(literal)
    elif (type(literal) == int):
        plain = str(literal)
    else:
        raise Exception('Cannot serialize ' + str(literal) + ', its type ' + str(type(literal)) + ' is illegal for a literal.')

    return plain

sha = hashing.SHA()
rmd = hashing.RMD()

def forString(text, seed=None):

    if (seed == None):
        seed = ''

    firstPass  = sha.sha256base64('0a' + text + seed);
    secondPass = rmd.rmd160base64(text + firstPass); 

    return secondPass
def forValue(value, seed=None):
    text = serialize(value)
    
    return forString(text, seed)

def toHex(h):
    return codecs.encode(base64.b64decode(h), 'hex').decode('utf-8')
    
def fromHex(hexHash):
    return base64.b64encode(codecs.decode(hexHash, 'hex')).decode('utf-8')