# Synthetic Population Pipeline

A three-phase pipeline for generating synthetic population data at the buurt (neighborhood) level using CBS datasets and Iterative Proportional Fitting (IPF).

## 🚀 Quick Start

### Pipeline Status
✅ **Phase 1 Complete**: National seed matrix generation
✅ **Phase 2 Partial**: IPF execution for 2 buurten
⏳ **Phase 3 Pending**: Microdata instantiation

### Basic Commands
```bash
# Phase 1: Generate seed matrix
python src/generate_seed.py --reference-dir data/reference --out-dir data/seed

# Phase 2: Run IPF for a specific buurt
python src/IPF.py --buurt BU16800000 --seed_dir data/seed --reference_dir data/reference
```


```bash
# commands for downloading relevant raw data files.
uv run tooling/fetchers/cbs_statline.py --table 37620 --out data/reference
uv run tooling/fetchers/cbs_statline.py --table 82275NED --out data/reference
uv run tooling/fetchers/cbs_statline.py --table 82309NED --out data/reference
uv run tooling/fetchers/cbs_statline.py --table 83931NED --out data/reference
uv run tooling/fetchers/cbs_statline.py --table 86165NED --out data/reference
```

## 📚 Documentation

For complete documentation, see [DOCUMENTATION.md](DOCUMENTATION.md)

## 🔧 Development

### Data Fetching
```bash
cd tooling
python -m fetchers.cbs_statline --table 86165NED --out ../data/reference
```

## 🎯 Next Steps
1. Complete Phase 3 microdata instantiation
2. Implement batch processing for all buurten
3. Add post-processing for additional variables
