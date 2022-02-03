A Python port of [Hyper Hyper Space's core library](https://github.com/hyperhyperspace/hyperhyperspace-core).

Uses Python 3.10 and no dependencies outside of the standard library.

Done mostly for fun, but also to check the interop test suite provided by the reference TypeScript version linked above. Each .ctx file in the test suite contains a set of literalized objects, that are deliteralized and checked.

The file PORTING.md contains some notes about the order in which modules were ported and what's in each file.

The immutable part of the data model has been (apparently) successfully ported, and the interop check files can be generated and checked by running:

```
compat.model.run.generate
compat.model.run.check
```
The .ctx files from the TypeScript version where copied and are in the repo as well.