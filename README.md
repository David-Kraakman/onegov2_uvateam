# Reference data setup

This repository keeps the raw CBS inputs in `data/reference/` as parquet files. They are downloaded from the public CBS Open Data API through the small fetcher in `tooling/fetchers/cbs_statline.py`.

## Download the reference tables

Run the fetcher from the `tooling/` folder so the module imports resolve correctly:

```powershell
cd tooling
..\.venv\Scripts\python.exe -m fetchers.cbs_statline --table 86165NED --out ..\data\reference
..\.venv\Scripts\python.exe -m fetchers.cbs_statline --table 83931NED --out ..\data\reference
..\.venv\Scripts\python.exe -m fetchers.cbs_statline --table 37620 --out ..\data\reference
..\.venv\Scripts\python.exe -m fetchers.cbs_statline --table 82275NED --out ..\data\reference
..\.venv\Scripts\python.exe -m fetchers.cbs_statline --table 82309NED --out ..\data\reference
```

The cached files are written as:

- `data/reference/86165NED.parquet`
- `data/reference/83931NED.parquet`
- `data/reference/37620.parquet`
- `data/reference/82275NED.parquet`
- `data/reference/82309NED.parquet`

## Inspect the raw schemas

After downloading, run the analysis helper to see the raw column layout and the likely usable columns for phase 1:

```powershell
..\.venv\Scripts\python.exe .\src\analyze_references.py --reference-dir .\data\reference
```

The script reports the relevant columns per table and flags `85321NED` as out of scope for the phase-1 seed build.
