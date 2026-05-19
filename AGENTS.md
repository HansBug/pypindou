# AGENTS.md

This repository is a pure Python library for converting images into fuse-bead pattern data.

## Scope

- Keep `pypindou` usable as a library. Do not add a CLI unless the project direction changes explicitly.
- Core input is an image; core output is a `Pattern` with grid, legend/counts, preview rendering, and metadata.
- Keep palette data generated from submodules with `make resource`; do not hand-edit `pypindou/resources/palettes.json`.

## Data Sources

- `data/pindou-color-data` is the domestic palette data source maintained at `HansBug/pindou-color-data`.
- `data/beadcolors` is the international palette data source maintained at `maxcleme/beadcolors`.
- After changing submodules or resource-building logic, run `make resource` and commit the generated `pypindou/resources/palettes.json`.
- Colors marked `unidentified: true` are excluded by default. Do not silently drop that flag when transforming data.

## Code Style

- Follow the local module layout: `color`, `image`, `pattern`, `benchmark`.
- Test paths mirror module paths under `test/`.
- Keep public APIs small and importable from `pypindou.__init__` only when they are stable enough for users.
- Prefer explicit dataclasses for public return objects.

## Verification

Before pushing meaningful changes:

```bash
make resource
make test
make docs
make package
```

If a change only touches docs or CI, run the relevant narrower command and mention what was skipped.

## Future Work

Planned directions include:

- better palette reduction metrics and benchmarks;
- board-aware pagination and placement constraints;
- PDF/XLSX export as downstream helpers;
- optional background removal / SAM integration through extras;
- human-friendly color replacement and operation-cost heuristics.
