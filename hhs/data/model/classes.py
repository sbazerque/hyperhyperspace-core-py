knownClasses = {}

def register(name, clazz):
    
    another = knownClasses.get(name)
    if another == None:
        knownClasses[name] = clazz
    elif another != clazz:
        raise Exception('Attempting to register two different instances of class ' + name + '.')

def lookup(name):
    return knownClasses.get(name)