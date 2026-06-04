# Phase 1 Execution Plan: Seed Preparation

This document turns the first phase of [`pipeline2.md`](pipeline2.md) into an actionable implementation plan. The goal is to produce one national seed matrix that can be reused by the buurt-level IPF step.

## Scope and handoff

- Build the national seed only; no local buurt fitting, rounding, or post-processing yet.
- The seed must be usable by the current IPF entry point in [`src/IPF.py`](src/IPF.py), which expects a directory of aggregate tables and passes them to `ipfn.ipfn(...).iteration()`.
- [`src/generate_seed.py`](src/generate_seed.py) is currently empty, so it will become the phase-1 build entry point.

## Decisions that must be settled before implementation

1. **Data acquisition method.** Use the existing CBS fetcher in [`tooling/fetchers/cbs_statline.py`](tooling/fetchers/cbs_statline.py) to download the required tables and cache them as parquet files under a reference directory such as `data/reference/`.
2. **Input tables for phase 1.** Use the catalogue-backed CBS tables for the three seed axes described in `pipeline2.md`: `83931NED` for age × migration × income, `37620` for age × household composition, and `82275NED` + `82309NED` for age × education × employment.
3. **Age spine source.** Use one national age marginal as the single controlling age distribution. The age spine must be the reference distribution that all age-bearing joint tables are scaled to.
4. **Category normalization.** Convert all table-specific labels to a canonical schema before combining any tables.
5. **Output format.** Write the seed as a tabular file with one row per full category combination and one weight column, so the next stage can reload it directly.

## Working out the phase-1 data flow

### 1. Fetch and cache the source tables

Fetch the required CBS tables with `tooling/fetchers/cbs_statline.py` and store each result as a parquet file in the reference data directory.

Criteria:
- Each source table is fetched once and saved under a deterministic filename.
- The fetch output includes the full table, not a pre-trimmed subset, because the row and column selection happens in the next step.
- If a region filter is ever used, it must remain client-side and be recorded in the cache metadata.

### 2. Inspect the raw schemas and identify the usable columns

For each downloaded table, determine:
- the geography column that identifies the national or buurt row,
- the category columns that define the joint distribution,
- the measure column that contains the counts or percentages,
- any metadata columns that should be dropped.

Criteria:
- The selected measure column is numeric and represents the table’s marginal or joint counts.
- Metadata columns such as ids, period labels, and other descriptive fields are excluded from the seed calculation.
- The schema decision is documented per table so the build is reproducible.
- The current cache shows that `85321NED` is not the expected education/employment source for this phase; the usable phase-1 source set is `86165NED`, `83931NED`, `37620`, `82275NED`, and `82309NED`.

### 3. Select the rows that belong in the national seed

Keep the national-level rows from the joint tables and exclude local buurt rows from the seed build.

Criteria:
- Only the national distributions are used to build the global prior.
- If a table contains multiple years or periods, the latest consistent period is chosen and the choice is recorded.
- Any table that cannot be aligned to the target national reference period is rejected rather than silently mixed in.

### 4. Normalize row and column names

Rename all retained columns to a canonical schema before any joins or pivots.

Proposed canonical names:
- `age_band`
- `migration_group`
- `income_group`
- `household_group`
- `education_group`
- `employment_group`
- `total`

Criteria:
- Equivalent labels from different CBS tables map to the same canonical category names.
- Age labels are normalized to the shared coarse bins used by the pipeline: `0-14`, `15-24`, `25-44`, `45-64`, and `65+`.
- Any category that is not needed for the seed is removed before the seed matrix is built.

### 5. Harmonize the age taxonomy

Aggregate each age-bearing joint table to the shared coarse age bins.

Criteria:
- Every joint table uses the same five age bins after harmonization.
- The age groups in the source tables are aggregated deterministically, not heuristically.
- If a source age bin straddles two target bins, the split rule must be explicit and documented.

### 6. Build the single age spine

Extract the national age marginal and use it as the only age reference for all seed components.

Criteria:
- The age spine sums to the national population covered by the seed.
- The age distribution is the same for the age axis in every joint table after scaling.
- The spine is stored as its own artifact so it can be reused and checked independently.

### 7. Force-scale the joint tables to the age spine

For each age-bearing joint table, convert the raw counts into conditional distributions given age and scale them back to the single national age spine.

Criteria:
- For every age bin, the conditional probabilities in the joint table sum to 1 before re-scaling.
- After re-scaling, the age margin of each table exactly matches the spine within floating-point tolerance.
- Any row with a zero age total is handled explicitly to avoid division errors.

### 8. Assemble the Cartesian product seed

Create one full Cartesian product over all retained categories and assign a base weight to each row using the Naive Bayes structure described in `pipeline2.md`:

$$
P(\text{row}) = P(\text{age}) \times P(\text{mig},\text{inc} \mid \text{age}) \times P(\text{hh} \mid \text{age}) \times P(\text{edu},\text{emp} \mid \text{age})
$$

Criteria:
- Every valid category combination appears exactly once.
- The weight column is numeric and non-negative.
- The seed total is normalized to the intended national scale and matches the age spine total.

### 9. Apply structural zeros

Set impossible combinations to zero before the seed is handed to IPF.

Criteria:
- Contradictory combinations are explicitly listed and do not rely on downstream convergence to eliminate them.
- At minimum, age-inappropriate combinations such as `0-14` with advanced educational attainment are zeroed.
- Structural-zero rules are stored in code or configuration so they can be audited later.

### 10. Validate the seed before handing it to IPF

Check that the seed is internally consistent and ready for the buurt-level fitting stage.

Criteria:
- The seed has the expected dimensionality and row count.
- The marginal totals implied by the seed reproduce the national age spine and the conditional tables within tolerance.
- No required category is missing, duplicated, or renamed inconsistently.
- The output file can be loaded directly into a pandas DataFrame and reused by the next phase without extra cleaning.

## Implementation sequence

1. Add the phase-1 build logic to [`src/generate_seed.py`](src/generate_seed.py).
2. Reuse the CBS fetcher in [`tooling/fetchers/cbs_statline.py`](tooling/fetchers/cbs_statline.py) to populate the reference input directory.
3. Implement table-specific column normalization and age-bin harmonization.
4. Build the age spine and scale each joint table to it.
5. Generate the full seed matrix, apply structural zeros, and save the result.
6. Add a short verification routine that checks margins, totals, and schema before the seed is consumed by [`src/IPF.py`](src/IPF.py).

## Expected outputs

- One saved seed file containing the full national prior matrix.
- One saved age-spine file used to scale all age-bearing tables.
- Optional lightweight metadata file describing the source tables, selected period, column mappings, and zero rules.
- A schema-inspection report that documents which raw columns are kept from each downloaded table and which source tables are rejected for phase 1.

## Completion criteria

Phase 1 is complete when the repository can:

- fetch the required CBS tables into a local cache,
- normalize them to one canonical category schema,
- build a single national seed matrix with a shared age spine,
- apply structural zeros,
- and load the resulting seed as the input for the buurt-level IPF stage without manual cleanup.
