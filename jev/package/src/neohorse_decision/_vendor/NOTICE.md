# Third-party attribution

`model.py` and `schema.py` derive from Jared Palmer's Kev (https://github.com/jaredpalmer/kev), Copyright 2026 Jared Palmer, Apache-2.0; see LICENSE.

The starting files were copied from the local runtime used for this checkpoint. The default API model identifier in `schema.py` was changed to `neohorse-jev`.

NeoHorse modifications add `NEOHORSE_SHAPE_BUCKET` as the primary environment variable, retaining `KEV_SHAPE_BUCKET` as a lower-priority compatibility alias (default 64; 1 disables MPS sequence padding). Unused date-preprocessing helpers were removed, and stale comments and the package description were refreshed. Decision encoding, probability readout, and model weights are unchanged.

The package does not fetch or import an external Kev distribution. Vendored code is versioned with this package, not automatically updated from upstream.

This notice does not assign a new license to the model weights or training data.
