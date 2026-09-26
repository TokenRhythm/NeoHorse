# Third-party attribution

Copyright 2026 Jared Palmer. Licensed under Apache License 2.0; see LICENSE.

Origin recorded by the model bundle: https://github.com/jaredpalmer/kev
Immediate source: NeoHorse-Jev-4B 0.2.0 deployment package,
`neohorse_decision/_vendor/model.py` and `schema.py`.
This copy is based on the model bundle's vendored revision, not upstream HEAD.

Changes on 2026-09-23: model.py retains encoding constants, user_tokens,
encode, rows_of and PointerHead; training/backbone loading, attention masks
and unused imports/helpers were removed. schema.py keeps the original
implementation, with attribution headers added. No input formatting or
pointer formula changes are intended. This directory is imported locally;
the neohorse_decision distribution is not needed.

This attribution covers these vendored utilities, not the model weights or
the vLLM / SGLang engines, which have their own licenses.

## Original bundle notice (preserved)

`model.py` and `schema.py` derive from Jared Palmer's Kev (https://github.com/jaredpalmer/kev), Copyright 2026 Jared Palmer, Apache-2.0; see LICENSE.

They were copied from the exact local runtime used for this checkpoint. `schema.py` renames the default API model identifier to `neohorse-jev`; decision encoding and probability readout are unchanged. The package does not fetch or import an external Kev distribution. Vendored code is versioned with this package, not automatically updated from upstream.

This notice does not assign a new license to the model weights or training data.
