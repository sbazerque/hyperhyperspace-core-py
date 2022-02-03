from hhs.data.model import literals

class Context:

    def __init__(self):
        self.rootHashes = []
        self.objects    = {}
        self.literals   = {}
        self.resources  = None

    def has(self, h):
        return h in self.literals or \
               h in self.objects.has(hash) or \
               (self.resources != None and self.resources.aliasing != None and h in self.resources.aliasing)

    def toLiteralContext(self):
        return { 'rootHashes': list(self.rootHashes), 'literals': dict(self.literals.items()) }

    def fromLiteralContext(self, literalContext):
        self.rootHashes = list(literalContext['rootHashes'])
        self.literals   = dict(literalContext['literals'].items())
        self.objects    = {}

    def merge(self, other):
        roots = set(self.rootHashes + other.rootHashes)
        self.rootHashes = list(roots)

        for h, literal in other.literals.entries():
            if not h in self.literals:
                self.literals[h] = literal

        for h, obj in other.objects.entries():
            if not h in self.objects:
                self.objects[h] = obj

        if self.resources == None:
            self.resources = other.resources
        else:
            if other.resources != None and 'aliasing' in other.resources:

                if not 'aliasing' in self.resources:
                    self.resources['aliasing'] = {}

                for h, aliased in other.resources['aliasing'].entries():
                    if not h in self.resources['aliasing']:
                        self.resources.aliasing[h] = aliased

    # if a dependency is in more than one subobject, it will pick one of the shortest dep chains.
    def findMissingDeps(self, h, chain=[], missing={}):

        literal = self.literals.get(h)

        if literal == None:
            prevChain = missing.get(h)

            if prevChain == None or len(chain) < len(prevChain):
                missing[h] = chain

        else:
            for dep in literal['dependencies']:
                newChain = chain.slice()
                newChain.unshift(h)
                self.findMissingDeps(dep.hash, newChain, missing)

        return missing

    def checkLiteralHashes(self):

        result = True

        for h, literal in self.literals.entries():
            
            if h != literal.hash or not literals.validateHash(literal):
                result = False        # but what about custom hashes??
                break

        return result

    def checkRootHashes(self):

        result = True

        for h in self.rootHashes:
            if not h in self.literals:
                result = False
                break

        return result

