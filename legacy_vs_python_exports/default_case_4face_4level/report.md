# Legacy vs Python Export Comparison

Case: `default_case_4face_4level`

## Text and engineering exports

| Format | File | Match | Python lines | Legacy lines | Diff |
| --- | --- | --- | ---: | ---: | --- |
| `HRP PAT` | `hrp.pat` | YES | 365 | 365 | `-` |
| `VRP PAT` | `vrp.pat` | YES | 1806 | 1806 | `-` |
| `HRP Text` | `hrp.txt` | YES | 363 | 363 | `-` |
| `VRP Text` | `vrp.txt` | YES | 1803 | 1803 | `-` |
| `HRP CSV` | `hrp.csv` | YES | 368 | 368 | `-` |
| `VRP CSV` | `vrp.csv` | YES | 1808 | 1808 | `-` |
| `HRP V-Soft` | `hrp.vep` | YES | 361 | 361 | `-` |
| `VRP V-Soft` | `vrp.vep` | YES | 1803 | 1803 | `-` |
| `HRP ATDI` | `hrp.H_DIA.DIA` | YES | 373 | 373 | `-` |
| `VRP ATDI` | `vrp.V_DIA.DIA` | YES | 373 | 373 | `-` |
| `3D ATDI` | `pattern3d.csv` | YES | 362 | 362 | `-` |
| `3D Text` | `pattern.3dp` | YES | 1805 | 1805 | `-` |
| `NGW3D` | `pattern.ng3dant` | YES | 258 | 258 | `-` |
| `PRN` | `pattern.prn` | YES | 730 | 730 | `-` |
| `EDX` | `pattern.ProgiraEDX.pat` | YES | 545 | 545 | `-` |
| `Complex EDX` | `pattern_complex.ProgiraEDX.pat` | YES | 525 | 525 | `-` |
| `Directivity` | `pattern.dir` | YES | 6 | 6 | `-` |

## Visual and binary exports

The Python outputs were generated into `adt_py/` for these formats too:

- `HRP JPEG` -> `adt_py/hrp.jpg`
- `VRP JPEG` -> `adt_py/vrp.jpg`
- `Layout JPEG` -> `adt_py/layout.jpg`
- `Summary PDF` -> `adt_py/summary.pdf`
- `Panel PDF` -> `adt_py/panels.pdf`
- `All PDF` -> `adt_py/all.pdf`
- `Video` -> `adt_py/vrp_animation.avi`

The legacy renderer/source mapping for those visual exports is documented in `legacy_reference/VISUAL_EXPORT_NOTES.md`.

