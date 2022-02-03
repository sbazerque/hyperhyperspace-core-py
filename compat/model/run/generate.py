from hhs.data.model.immutable import Context
from compat.model import immutable

import json

def saveToFile(ctx, filename):
    contents = json.dumps(ctx.toLiteralContext())

    f = open(filename, 'wb')
    f.write(contents.encode('utf-8'))

dest = './compat/model/data-py'

for t in immutable.checks:
    
    ctx = Context()
    for obj in t['gen']():
        obj.toContext(ctx)

    saveToFile(ctx, dest + '/' + t['slug'] + '.ctx')
    print('generated ' + t['slug'] + '.ctx')