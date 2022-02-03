from hhs.data.model.immutable import HashedLiteral, HashedObject, HashedSet, HashedMap, Context
from hhs.data.model import classes

class Wrapper(HashedObject):

    className = 'compat/Wrapper'

    def __init__(self, something=None):
        super(Wrapper, self).__init__()
        self.something = something

    def getClassName(self):
        return Wrapper.className

    def init(self):
        pass

    async def validate(self, references):
        return self.something != None

classes.register(Wrapper.className, Wrapper)

literals = ['a string', 123, 1.5, {'a': 'value'}, [1, 'two', 3]]
hashedLiterals = list(map(lambda x: HashedLiteral(x), literals))

def checkLiteralsInContext(ctx):
    for hashedLiteral in hashedLiterals:
        toCheck = ctx.objects.get(hashedLiteral.hash())

        if toCheck == None:
            print('-> HashedLiteral with hash ' + hashedLiteral.hash() + ' is missing')
            return False

        if not isinstance(toCheck, HashedLiteral):
            print('-> HashedLiteral with hash ' + hashedLiteral.hash() + ' is not a HashedLiteral instance.')
            return False

        if HashedObject.hashElement(toCheck.value) != HashedObject.hashElement(hashedLiteral.value):
            print('-> HashedLiteral with hash ' + hashedLiteral.hash() + ' is is expected to have value:')
            print(toCheck.value)
            print('-> but has value:')
            print(hashedLiteral.value)
            return False

    return True

checkLiterals = {
    'slug': 'hashing-01',
    'desc': 'HashedLiteral check',
    'gen': lambda: list(hashedLiterals),
    'check': checkLiteralsInContext
}

setElements = [[], [1, 2, 3], hashedLiterals, [HashedSet()]]
hashedSets = list(map(lambda x: HashedSet(x), setElements))
wrappedHashedSets = list(map(lambda x: Wrapper(x), hashedSets))

def checkHashedSetsInContext(ctx):
    for wrap in wrappedHashedSets:

        hashedSet = wrap.something
        
        wrapToCheck = ctx.objects.get(wrap.hash())

        if not isinstance(wrapToCheck, Wrapper):
            print('-> the wrapper with hash ' + wrap.hash() + ' is missing (it wraps ' + wrap.something.hash() + ').')
            return False

        toCheck = wrapToCheck.something

        if toCheck == None:
            print('-> the wrapper with hash ' + wrap.hash() + ' is empty.')
            return False

        if not isinstance(toCheck, HashedSet):
            print('-> the wrapper with hash ' + wrap.hash() + ' contains something else than a HashedSet.')
            return False

        if toCheck.size() != hashedSet.size():
            print('-> the set with hash ' + hashedSet.hash() + ' is expected to have ' + str(hashedSet.size()) + ' elements, but has ' + str(toCheck.size()))
            return False

        for elmt in toCheck.values():
            if not hashedSet.has(elmt):
                print('-> value ' + elmt + ' is missing from set with hash ' + hashedSet.hash())
                return False
    return True


checkHashedSets = {
    'slug': 'hashing-02',
    'desc': 'HashedSet check',
    'gen': lambda: list(wrappedHashedSets),
    'check': checkHashedSetsInContext

}

maps = [{'a': HashedLiteral(6), 'b': HashedLiteral(-7)}, {}]
hashedMaps = list(map(lambda x: HashedMap(x.items()), maps))
wrappedHashedMaps = list(map(lambda x: Wrapper(x), hashedMaps))

def checkHashedMapsInContext(ctx):
    for wrap in wrappedHashedMaps:

        hashedMap = wrap.something

        wrapToCheck = ctx.objects.get(wrap.hash())

        if not isinstance(wrapToCheck, Wrapper):
            return False

        toCheck = wrapToCheck.something

        if toCheck == None:
            return False

        if not isinstance(toCheck, HashedMap):
            return False

        if not toCheck.size() == hashedMap.size():
            return False

        for key in toCheck.keys():
            if not hashedMap.get(key).equals((toCheck.get(key))):
                return False

    return True

checkHashedMaps = {
    'slug': 'hashing-03',
    'desc': 'HashedMap check',
    'gen': lambda: list(wrappedHashedMaps),
    'check': checkHashedMapsInContext
}

checks = [checkLiterals, checkHashedSets, checkHashedMaps]