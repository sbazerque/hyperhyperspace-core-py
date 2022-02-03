Porting Notes
=============

- Created hhs.crypto.hashing (RMD and SHA) using the standard python3 bridge to openssl.
- Created hhs.crypto.random using the built-in random source in Python
- Created package hhs.data.model, then
  - hhs.data.model.hashing: standardized object hashing
  - hhs.data.model.classes: class registry for typed object literalization / deliteralization
  - hhs.data.model.literals: handling of literalized objects
  - hhs.data.model.context: the context holds the state of an in progress object (de)literalization
  - hhs.data.model.immutable: base for all 'atomic' types (HashedObject) and support types: HashedSet HashedMap, HashReference, HashedLiteral (all immutable)

- Created compat.model.immutable, definitions and checks for immutable type compatibility testing

- Created compat.model.run, with:
  - check.py: check generated compat files from typescript and python
  - generate.py: generate compat files

  - hhs.data.model.mutable: TODO
  - hhs.data.model.causal: TODO