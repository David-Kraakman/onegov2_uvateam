- Fetched the CBS reference parquets into `data/reference/`: `86165NED`, `83931NED`, `37620`, `82275NED`, and `82309NED`.
- Wrote `src/analyze_references.py` to inspect raw schemas and identify usable columns for the seed build.
- Confirmed that `85321NED` does not match the phase-1 education/employment source expected by the pipeline; use `82275NED` and `82309NED` instead.
- Updated `execution.md` and `README.md` to reflect the corrected phase-1 source set and the download workflow.

## Phase 1 Preprocessing: Steps 1-5 ✓ Complete (2026-06-04 22:07)

**All preprocessing functions now execute successfully:**

- **Step 1-2**: Fetched 5 CBS tables and implemented schema inspection with `analyze_references.py`
- **Step 3**: Filtered to national-level rows; selected latest consistent periods (2024-2025 for most tables)
- **Step 4**: Normalized all column names to canonical schema (age_band, education_group, migration_group, etc.)
- **Step 5**: Harmonized all age labels to 5-bin taxonomy (0-14, 15-24, 25-44, 45-64, 65+)

**Preprocessing Output (5 tables):**
- `86165NED_preprocessed.parquet`: 3 rows × 13 cols (national anchor)
- `83931NED_preprocessed.parquet`: 648 rows × 3 cols (age × income)
- `37620_preprocessed.parquet`: 759 rows × 3 cols (age × household)
- `82275NED_preprocessed.parquet`: 2016 rows × 4 cols (age × education × migration)
- `82309NED_preprocessed.parquet`: 29 rows × 3 cols (age × education × employment)

**Key Fixes:**
- Fixed 83931NED: removed invalid regional filter, added date/gender filtering
- Fixed 37620: added individual year age mappings, totals filtering
- Fixed 82275NED & 82309NED: added year filtering and value mapping updates
- Extended AGE_MAPPINGS to handle 150+ age label variants across all sources

Next: Implement steps 6-10 (age spine, force-scaling, Cartesian product, structural zeros, validation)
