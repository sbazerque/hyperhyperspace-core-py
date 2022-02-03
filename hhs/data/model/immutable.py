from abc import ABC, abstractmethod
import logging
import base64
import codecs

from hhs.data.model import hashing
from hhs.data.model import classes

from hhs.data.model.context import Context

BITS_FOR_ID = 128

class HashedObject(ABC):

    validationLog = logging.getLogger(__name__ + '/validation')

    def __init__(self):

        self.id             = None
        self.author         = None

        self._signOnSave    = False
        self._lastHash      = None
        self._lastSignature = None

        self._resources     = None

    @abstractmethod
    def getClassName():
        pass

    @abstractmethod
    def init():
        pass

    @abstractmethod
    def validate(references):
        pass

    def getId(self):
        return self.id

    def setId(self, id):
        self.id = id

    def setRandomId(self):
        #TODO: use b64 here
        self.id = hashing.RNG().randomHexString(BITS_FOR_ID)

    def hasId(self):
        return self.id != None

    def setAuthor(self, author):
        if not author.hasKeyPair():
            raise Exception('Trying to set the author of an object, but the received identity does not have an attached key pair to sign it.')

        if not author.equals(self.author):
            self.author = author
            self._signOnSave = True

    def getAuthor(self):
        return self.author

    def hasLastSignature(self):
        return self._lastSignature != None

    def setLastSignature(self, signature):
        self._lastSignature = signature

    def getLastSignature(self):
        if (self._lastSignature == None):
            raise Exception('Attempted to retrieve last signature for unsigned object')

        return self._lastSignature

    def overrideChildrenId(self):
        for k,v in vars(self).items():
            if len(k) > 0 and k[0] != '_':
                if isinstance(v, HashedObject):
                    self.overrideIdForPath(k, v)


    def overrideIdForPath(self, path, target):
        parentId = self.getId()

        if (parentId == None):
            raise Exception("Can't override a child's Id because parent's Id is unset")

        target.setId(HashedObject.generateIdForPath(parentId, path))

    def hasStore(self):
        return self._resources != None and 'store' in self._resources

    def setStore(self, store):

        if self._resources == None:
            self._resources = { }

        self._resources.store = store

    def getStore(self):

        if not self.hasStore():
            raise Exception('Attempted to get store from object resources, but one is not present in instance of ' + self._lastHash)

        return self._resources.store

    def getMesh(self):

        if self._resources == None or not 'mesh' in self._resources:
            raise Exception('Attempted to get mesh from object resources, but one is not present.');
        else:
            return self._resources.mesh

    def hasLastHash(self):
        return self._lastHash != None

    def setLastHash(self, hash):
        self._lastHash = hash

    def getLastHash(self):
        
        if self._lastHash == None:
            self.hash()

        return self._lastHash


    def shouldSignOnSave(self):
        return self._signOnSave
  
    def hash(self, seed=None):

        h = self.customHash(seed)

        if h == None:
            context = self.toContext()
            if seed == None:
                h = context.rootHashes[0]
            else:
                literal = context.literals.get(context.rootHashes[0])
                h = hashing.forValue(literal.value, seed)

        if seed == None: 
            self._lastHash = h

        return h

    def customHash(self, seed=None):
        pass

    def createReference(self):
        return HashReference(self.hash(), self.getClassName())

    def equals(self, another):
        return another != None and self.hash() == another.hash()

    def clone(self):
        c = self.toContext()
        
        c.objects = {}

        clone = HashedObject.fromContext(c)

        clone.init()

        clone._signOnSave    = self._signOnSave
        clone._lastSignature = self._lastSignature
        
        return clone

    def addDerivedField(self, fieldName, obj):
        obj.setId(self.getDerivedFieldId(fieldName))
        self[fieldName] = obj

    def checkDerivedField(self, fieldName):
        field = self.get(fieldName)

        return field != None and isinstance(field, HashedObject) and \
               field.getId() == self.getDerivedFieldId(fieldName)

    def getDerivedFieldId(self, fieldName):
        return hashing.forValue('#' + self.getId() + '.' + fieldName)

    def setResources(self, resources):
        self._resources = resources

    def getResources(self):
        return self._resources

    def toLiteralContext(self, context=None):

        if context == None:
            context = Context()

        self.toContext(context)

        return context.toLiteralContext()

    def toLiteral(self):
        context = self.toContext()

        return context.literals.get(context.rootHashes[0])

    def toContext(self, context=None):

        if context == None:
            context = Context()
        
        h = self.literalizeInContext(context, '')

        if context.rootHashes.count(h) > 0:
            print('duplicate root hash ' + h)
            print(self)
            #import pdb; pdb.set_trace();

        context.rootHashes.append(h)

        return context

    def literalizeInContext(self, context, path, flags=[]):
        
        fields = {}
        dependencies = {}

        for fieldName, value in vars(self).items():
            if len(fieldName) > 0 and fieldName[0] != '_':
                if (HashedObject.shouldLiteralizeField(value)):
                    fieldPath = fieldName
                    if path != '':
                        fieldPath = path + '.' + fieldName
                    
                    fieldLiteral = HashedObject.literalizeField(fieldPath, value, context)
                    fields[fieldName] = fieldLiteral['value']
                    HashedObject.collectChildDeps(dependencies, fieldLiteral['dependencies'])

        value = {
            '_type'   : 'hashed_object', 
            '_class'  : self.getClassName(),
            '_fields' : fields,
            '_flags'  : flags
        }

        h = self.customHash()

        if h == None:
            h = hashing.forValue(value)

        

        literal = { 'hash': h, 'value': value, 'dependencies': list(dependencies.values()) }

        if (self.author != None):
            literal.author = value['_fields']['author']['_hash']

        # if we have a signature, we add it to the literal
        if (self.author != None and self.hasLastSignature()):
            literal.signature = self.getLastSignature()

        if (context.resources != None and
            'aliasing' in context.resources and
            context.resources['aliasing'].get(h) != None):
            context.objects[h] = context.resources['aliasing'][h]
        else:
            context.objects[h] = self
        
        context.literals[h] = literal

        self.setLastHash(h)

        return h

    @staticmethod
    def shouldLiteralizeField(something):

        if (something == None):
            return False
        else:
            if callable(something):
                return False
            else:
                return True


    @staticmethod
    def literalizeField(fieldPath, something, context=None): #{ value: any, dependencies : Set<Dependency> }  {

        typ = type(something)

        value = None
        dependencies = {}

        if typ == bool or typ == int or typ == float or typ == str:
            value = something
        elif typ == list:
            value = []
            for elmt in something:
                if HashedObject.shouldLiteralizeField(elmt):
                    child = HashedObject.literalizeField(fieldPath, elmt, context)
                    value.append(child['value'])
                    HashedObject.collectChildDeps(dependencies, child['dependencies'])
        elif typ == dict:
            value = {}

            for fieldName, fieldValue in something.items():
                if len(fieldName) > 0 and fieldName[0] != '_':
                    if HashedObject.shouldLiteralizeField(fieldValue):
                        field = HashedObject.literalizeField(fieldPath + '.' + fieldName, fieldValue, context)
                        value[fieldName] = field['value']
                        HashedObject.collectChildDeps(dependencies, field['dependencies'])

        else:
            if isinstance(something, HashReference):
                dependency = { 'path': fieldPath, 'hash': something.hash, 'className': something.className, 'type': 'reference'}
                dependencies[hashing.forValue(dependency)] = dependency
                value = reference.literalize()
            elif isinstance(something, HashedSet) or isinstance(something, HashedMap):
                literal = something.literalize(fieldPath, context)
                value   = literal['value']
                HashedObject.collectChildDeps(dependencies, literal['dependencies'])
            elif isinstance(something, HashedObject):
                if context == None:
                    raise Exception('Context needed to deliteralize HashedObject')
                
                h = something.literalizeInContext(context, fieldPath)
                dependency = {'path': fieldPath, 'hash': h, 'className': something.getClassName(), 'type': 'literal'}
                dependencies[hashing.forValue(dependency)] = dependency

                value = { '_type': 'hashed_object_dependency', '_hash': h }

                hashedDeps = list(map(lambda d: [hashing.forValue(d), d], context.literals.get(h)['dependencies']))

                HashedObject.collectChildDeps(dependencies, dict(hashedDeps))
            else:
                raise Exception('Unexpected type encountered while attempting to literalize: ' + str(typ))

        return { 'value': value, 'dependencies': dependencies }


    @staticmethod
    def fromLiteralContext(literalContext, h=None):

        context = Context()
        context.fromLiteralContext(literalContext)

        return HashedObject.fromContext(context, h)

    
    @staticmethod
    def fromLiteral(literal):

        context = Context()
        context.rootHashes.append(literal.hash)
        context.literals[literal.hash] = literal

        return HashedObject.fromContext(context)

    # IMPORTANT: this method is NOT reentrant / thread safe!

    @staticmethod
    async def fromContextWithValidation(context, h=None): #Promise<HashedObject>
        if h == None:
            if len(context.rootHashes) == 0:
                raise Exception('Cannot deliteralize object because the hash was not provided, and there are no hashes in its literal representation.');
            elif len(context.rootHashes) > 1:
                raise Exception('Cannot deliteralize object because the hash was not provided, and there are more than one hashes in its literal representation.');
            h = context.rootHashes[0];

        if h in context.objects:
            return context.objects.get(h)
        else:
            literal = context.literals.get(h)

            if literal == None:
                raise Exception('Literal for ' + h + ' missing from context')

            for dep in literal['dependencies']:
                if not dep['hash'] in context.objects:
                    await HashedObject.fromContextWithValidation(context, dep['hash'])

            obj = HashedObject.fromContext(context, h, True)

            if obj.hash() != h:
                context.objects.pop(h, None)
                raise Exception('Wrong hash for ' + h + ' of type ' + obj.getClassName() + ', hashed to ' + obj.getLastHash() + ' instead')

            if obj.author != None:
                if literal.signature == None:
                    context.objects.pop(h, None)
                    raise Exception('Missing signature for ' + h + ' of type ' + obj.getClassName())

                if not await obj.author.verifySignature(h, literal.signature):
                    context.objects.pop(h, None)
                    raise Exception('Invalid signature for ' + h + ' of type ' + obj.getClassName())

            if context.resources != None:
                obj.setResources(context.resources)
            
            if not await obj.validate(context.objects):
                context.objects.pop(h, None)
                raise Exception('Validation failed for ' + h + ' of type ' + obj.getClassName())

            return obj
    
    @staticmethod
    def fromContext(context, h=None, validate=False):

        if h == None:
            if len(context.rootHashes) == 0:
                raise Exception('Cannot deliteralize object because the hash was not provided, and there are no hashes in its literal representation.')
            elif len(context.rootHashes) > 1:
                raise Exception('Cannot deliteralize object because the hash was not provided, and there are more than one hashes in its literal representation.');

            h = context.rootHashes[0]

        HashedObject.deliteralizeInContext(h, context, validate)

        return context.objects.get(h)

    # deliteralizeInContext: take the literal with the given hash from the context,
    #                        recreate the object and insert it into the context
    #                        (be smart and only do it if it hasn't been done already)

    @staticmethod
    def deliteralizeInContext(h, context, validate=False):

        hashedObject = context.objects.get(hash)

        if hashedObject != None:
            return

        # check if we can extract the object from the shared context
        sharedObject = None
        if context != None and context.resources != None and context.resources.aliasing != None:
            sharedObject = context.resources.aliasing.get(h)

        if sharedObject != None:
            context.objects[h] = sharedObject
            return

        literal = context.literals.get(h)

        if literal == None:
            raise Exception("Can't deliteralize object with hash " + h + " because its literal is missing from the received context")

        value = literal['value']

        # all the dependencies have been delieralized in the context

        if value['_type'] != 'hashed_object':
            raise Exception("Missing 'hashed_object' type signature while attempting to deliteralize " + literal.hash)
        
        constr = classes.lookup(value['_class']);

        if constr == None:
            raise Exception("A local implementation of class '" + value['_class'] + "' is necessary to deliteralize " + literal.hash)
        else:
            hashedObject = constr()

        for fieldName, fieldValue in value['_fields'].items():
            if len(fieldName)>0 and fieldName[0] != '_':
                hashedObject.__setattr__(fieldName, HashedObject.deliteralizeField(fieldValue, context, validate))

        if context.resources != None:
            hashedObject.setResources(context.resources)
        
        hashedObject.setLastHash(h)

        hashedObject.init()

        if hashedObject.author != None:
            hashedObject.setLastSignature(literal.signature)

        context.objects[h] = hashedObject

    @staticmethod
    def deliteralizeField(value, context, validate=False):

        something = None

        typ = type(value)

        if typ == bool or typ == int or typ == float or typ == str:
            something = value
        elif typ == list:
            something = []
            for elmt in value:
                something.append(HashedObject.deliteralizeField(elmt, context, validate));
        elif typ == dict:
            _typ = value.get('_type')
            if _typ == None:
                something = {}

                for fieldName, fieldValue in value.items():
                    something[fieldName] = HashedObject.deliteralizeField(fieldValue, context, validate)
            
            elif _typ == 'hashed_set':
                something = HashedSet.deliteralize(value, context, validate)
            elif _typ == 'hashed_map':
                something = HashedMap.deliteralize(value, context)
            elif _typ == 'hashed_object_reference':
                something = HashReference.deliteralize(value)
            elif _typ == 'hashed_object_dependency':
                h = value['_hash']

                HashedObject.deliteralizeInContext(h, context, validate)
                something = context.objects.get(h)
            elif _typ == 'hashed_object':
                raise Exception("Attempted to deliteralize embedded hashed object in literal (a hash reference should be used instead)")
            else:
                raise Exception("Unknown _type value found while attempting to deliteralize: " + value['_type'])
        else:
            raise Exception("Unexpected type encountered while attempting to deliteralize: " + str(typ))

        return something

    @staticmethod
    def collectChildDeps(parentDeps, childDeps):
        for childDepHash, childDep in childDeps.items():
            parentDeps[childDepHash] = childDep

    @staticmethod
    def generateIdForPath(parentId, path):
        return hashing.forValue('#' + parentId + '.' + path)

    @staticmethod
    def hashElement(element):

        h = None

        if isinstance(element, HashedObject):
            h = element.hash()
        else:
            h = hashing.forValue(HashedObject.literalizeField('', element)['value'])

        return h



class HashReference:

    def __init__(self, refHash, className):
        self.hash = refHash
        self.className = className

    def literalize(self):
        return { '_type': 'hashed_object_reference', '_hash': self.hash, '_class': self.className }
    
    @staticmethod
    def deliteralize(literal):
        return HashReference(literal._hash, literal._class)

    @staticmethod
    def hashFromLiteral(literal):
        return literal._hash

    @staticmethod
    def classNameFromLiteral(literal):
        return literal._class


class HashedMap:

    def __init__(self, entries=None):

        self.content       = {}
        self.contentHashes = {}

        if entries != None:
            for k,v in entries:
                self.set(k, v)

    def set(self, key, value):
        h = HashedObject.hashElement(value)
        self.content[key] = value
        self.contentHashes[key] = h

    def remove(self, key):
        self.content.pop(key, None)
        self.contentHashes.pop(key, None)

    def has(self, key):
        return key in self.contentHashes

    def get(self, key):
        return self.content.get(key)

    def entries(self):
        return self.content.items()

    def size(self):
        return len(self.content)

    def keys(self):
        return self.content.keys()

    def values(self):
        return self.content.values()

    def valueHashes(self):
        return self.contentHashes.values()

    def toArrays(self): #{entries: [K,V][], hashes: Hash[]}
        
        keys = list(self.content.keys())

        keys.sort()

        entries = []
        hashes  = []

        for key in keys:
            entries.append([key, self.content.get(key)])
            hashes.append(self.contentHashes.get(key))

        return { 'entries': entries, 'hashes': hashes}

    def fromArrays(self, hashes, entries):

        for k,v in entries:
            self.set(k,v)

    def equals(self, another):
        selfArrays    = self.toArrays()
        anotherArrays = another.toArrays()

        if not len(selfArrays.entries) == len(anotherArrays.entries):
            return False

        i=0

        while i<len(selfArrays.entries):

            selfEntryKey    = selfArrays.entries[i][0]
            anotherEntryKey = anotherArrays.entries[i][0]

            if not selfEntryKey == anotherEntryKey:
                return False

            if not selfArrays.hashes[i] == anotherArrays.hashes[i]:
                return False

        return True

    def literalize(self, path='', context=None): # { value: any, dependencies : Map<Hash, Dependency> } 

        dependencies = {}

        if context == None:
            context = Context()

        arrays = self.toArrays()
        hashes = arrays['hashes']
        child = HashedObject.literalizeField(path, arrays['entries'], context)
        entries = child['value']
        HashedObject.collectChildDeps(dependencies, child['dependencies'])

        value = {'_type': 'hashed_map', '_hashes': hashes, '_entries': entries }

        return { 'value': value, 'dependencies': dependencies }

    def hash(self):
        return hashing.forValue(self.literalize()['value'])

    @staticmethod
    def deliteralize(value, context, validate=False): #HashedMap<any, any>

        if value.get('_type') != 'hashed_map':
            raise Exception("Trying to deliteralize value, but _type is '" + value.get('_type') + "' (shoud be 'hashed_map')");

        hashes = value['_hashes']
        entries = HashedObject.deliteralizeField(value['_entries'], context, validate)

        if validate and len(hashes) != len(entries):
            raise Exception('Trying to deliteralize HashedMap but hashes and entries arrays have different lengths.')

        hmap = HashedMap()
        hmap.fromArrays(hashes, entries)

        if validate:
            another = HashedMap()
            for k,v in hmap.entries():
                another.set(k,v)
            if not hmap.equals(another):
                raise Exception('HashedMap failed validation: reconstruction resulted in a different map.')

        return hmap



class HashedSet:

    def __init__(self, values=None):
        self.hashedElements = {}
        if (values != None):
            for v in values:
                self.add(v)

    def add(self, element):
        elementHash = HashedObject.hashElement(element)
        self.hashedElements[elementHash] = element

    def remove(self, element):
        elementHash = HashedObject.hashElement(element)
        return self.removeByHash(elementHash)

    def removeByHash(self, h):
        return self.hashedElements.pop(h, None)

    def has(self, element):
        h = HashedObject.hashElement(element)
        return self.hasByHash(h)

    def hasByHash(self, h):
        return h in self.hashedElements

    def get(self, h):
        return self.hashedElements.get(h)

    def values(self):
        return self.hashedElements.values()

    def toArrays(self): #{hashes: string[], elements: T[]}
        hashes = list(self.hashedElements.keys())
        hashes.sort()

        elements = []

        for h in hashes:
            elements.append(self.hashedElements.get(h))

        return {'hashes': hashes, 'elements': elements}

    def fromArrays(self, hashes, elements):
        for element in elements:
            self.add(element)

    def equals(self, another):
        hashes = list(self.hashedElements.keys())
        hashes.sort()
        anotherHashes = list(another.hashedElements.keys())
        anotherHashes.sort()

        if len(hashes) != len(anotherHashes):
            return False

        i=0
        while i<len(hashes):
            if hashes[i] != anotherHashes[i]:
                return False
            i = i + 1

        return True

    def literalize(self, path='', context=None): #{ value: any, dependencies : Map<Hash, Dependency> }
           
        dependencies = {}

        if context == None:
            context = Context()

        arrays = self.toArrays()
        hashes = arrays['hashes']
        child = HashedObject.literalizeField(path, arrays['elements'], context)
        elements = child['value']
        HashedObject.collectChildDeps(dependencies, child['dependencies'])

        value = {'_type': 'hashed_set', '_hashes': hashes, '_elements': elements}

        return { 'value': value, 'dependencies': dependencies}

    def hash(self):
        return hashing.forValue(self.literalize()['value'])

    def size(self):
        return len(self.hashedElements)

    @staticmethod
    def deliteralize(value, context, validate=False): #HashedSet<any>
        
        if value['_type'] != 'hashed_set':
            raise Exception("Trying to deliteralize value, but _type is '" + value['_type'] + "' (shoud be 'hashed_set')")

        if validate and len(value) != 3:
            raise Exception("HashedSet literal values should have exactly 3 keys, found " + str(list(value.keys())))
 

        hashes   = value['_hashes']
        elements = HashedObject.deliteralizeField(value['_elements'], context, validate)

        if validate and len(hashes) != len(elements):
            raise Exception('HashedSet literal has a different number of elements and hashes.')

        hset = HashedSet()
        hset.fromArrays(hashes, elements)

        if validate:

            another = HashedSet()

            for element in elements:
                another.add(element)

            if not hset.equals(another):
                raise Exception('HashedSet failed validation: reconstruction resulted in a different set.')

        return hset

    @staticmethod
    def elementsFromLiteral(literal):
        return literal['_elements']


class HashedLiteral(HashedObject):

    className = 'hhs/v0/HashedLiteral'

    def __init__(self, value=None):
        super(HashedLiteral, self).__init__()
        self.value = value

    def getClassName(self):
        return HashedLiteral.className

    def init(self):
        pass

    async def validate(self, references):
        return HashedLiteral.valid(self.value)

    @staticmethod
    def valid(value, seen=set()):

        typ = type(value)

        if typ == bool or typ == int or typ == float or typ == str:
            return True
        elif typ == dict or typ == list:
            if id(value) in seen:
                return False
            
            seen.add(id(value))

            if typ == list:
                for elmt in value:
                    if not HashedLiteral.valid(elmt, seen):
                        return False
            
            if typ == dict:
                for k,v in value.items():
                    if type(k) != str:
                        return False
                    if not HashedLiteral.valid(v, seen):
                        return False

            return True
        else:
            return False

classes.register(HashedLiteral.className, HashedLiteral)