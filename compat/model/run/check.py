from hhs.data.model.immutable import Context, HashedObject
from compat.model import immutable

import json
import asyncio
BOLD = '\x1b[1;37m'
PASS = '\x1b[1;32m'
FAIL = '\x1b[1;31m'
ENDC = '\x1b[0m'

async def loadFromFile(filename, validate=True):
    ctx = Context()

    f = open(filename, 'rb')


    contents = f.read().decode('utf-8')
    ctx.fromLiteralContext(json.loads(contents))
    
    for h in ctx.rootHashes:
        obj = await (HashedObject.fromContextWithValidation(ctx, h) if validate else HashedObject.fromContext(ctx, h))
        ctx.objects[h] = obj

    return ctx

srcs = ['./compat/model/data-ts', './compat/model/data-py']

async def run():

    print('Starting compat testing run')

    for src in srcs:

        print()
        print(BOLD + 'Checking folder ' + src + '...' + ENDC)

        for t in immutable.checks:

            print(t['slug'] + ': ' + t['desc'])
        
            ctx = await loadFromFile(src + '/' + t['slug'] + '.ctx')

            if t['check'](ctx):
                print(PASS + 'pass' + ENDC)
            else:
                print(FAIL + 'fail' + ENDC)

asyncio.run(run())