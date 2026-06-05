# Synthetic Population Pipeline

A three-phase pipeline for generating synthetic population data at the buurt (neighborhood) level using CBS datasets and Iterative Proportional Fitting (IPF).

## 🚀 Quick Start

### Pipeline Status
✅ **Phase 1 Complete**: National seed matrix generation
✅ **Phase 2 Complete**: IPF execution with fixed household constraints
✅ **Phase 3 Complete**: Microdata instantiation implemented
✅ **Main Pipeline Complete**: End-to-end workflow with data checking
✅ **Validation Fixed**: All IPF validation issues resolved

### Basic Commands
```bash
# Complete pipeline for a specific buurt (recommended)
python src/main_pipeline.py --buurt BU16800000

# Complete pipeline with automatic data download
python src/main_pipeline.py --buurt BU16800000 --download

# Complete pipeline with IPF fit analysis
python src/main_pipeline.py --buurt BU16800000 --analyze

# Complete pipeline with all options
python src/main_pipeline.py --buurt BU16800000 --download --verbose --analyze

# Individual phase commands
python src/generate_seed.py --reference-dir data/reference --out-dir data/seed
python src/IPF.py --buurt BU16800000 --seed_dir data/seed --reference_dir data/reference
python src/instantiate_microdata.py --buurt BU16800000 --fitted_dir data/fitted --out_dir data/microdata
python src/analyze_ipf_fit.py --buurt BU16800000 --fitted_dir data/fitted --reference_dir data/reference
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
