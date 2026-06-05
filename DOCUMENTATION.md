# Synthetic Population Pipeline - Complete Documentation

## 🎯 Project Overview

This project implements a three-phase pipeline for generating synthetic population data at the buurt (neighborhood) level using CBS datasets and Iterative Proportional Fitting (IPF).

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Virtual environment (recommended)
- Required packages: `pip install -e .`

### Pipeline Status
✅ **Phase 1 Complete**: National seed matrix generation
✅ **Phase 2 Partial**: IPF execution for 2 buurten (Annen, Verspreide huizen Annen)
⏳ **Phase 3 Pending**: Microdata instantiation and post-processing

## 📊 Pipeline Overview

### Phase 1: Seed Preparation
```bash
python src/generate_seed.py --reference-dir data/reference --out-dir data/seed
```
- Loads raw CBS data
- Preprocesses and normalizes schemas
- Builds national age spine
- Generates seed matrix using Naive Bayes structure
- Applies structural zeros

### Phase 2: IPF Execution
```bash
python src/IPF.py --buurt BU16800000 --seed_dir data/seed --reference_dir data/reference
```
- Loads national seed matrix
- Extracts buurt-level constraints
- Executes IPF with age, migration, education, and household constraints
- Validates results and saves fitted data

### Phase 3: Microdata Instantiation (Future)
- Stochastic rounding of fitted weights
- Integer age imputation
- Behavioral assignment (mobility, etc.)
- Spatial metadata joins

## 🗂️ Data Artifacts

### Data Directory Structure
```
data/
├── reference/              # Raw CBS data (Phase 0 - Data Acquisition)
├── seed/                  # Preprocessed data and seed matrix (Phase 1)
└── fitted/                # IPF results (Phase 2)
```

### Phase 0: Raw Data Acquisition
**Location**: `data/reference/`

Original CBS datasets downloaded using the fetcher tools:
- `37620.parquet` - Household composition data (national level)
- `82275NED.parquet` - Education × migration data (national level)
- `83931NED.parquet` - Age × income × migration data (national level)
- `86165NED.parquet` - Buurt-level demographic data (local constraints)

### Phase 1: Seed Preparation Artifacts
**Location**: `data/seed/`

#### Preprocessed Tables
- `37620_preprocessed.parquet` - Cleaned household composition data
- `82275NED_preprocessed.parquet` - Cleaned education × migration data
- `83931NED_preprocessed.parquet` - Cleaned age × income data
- `86165NED_preprocessed.parquet` - Cleaned national anchor data

#### Core Artifacts
- `age_spine.parquet` - National age distribution (5 bins: 0-14, 15-24, 25-44, 45-64, 65+)
- `seed_matrix.parquet` - National seed matrix (age × education × migration × household with weights)
- `preprocessing_metadata.json` - Complete metadata about preprocessing steps

### Phase 2: IPF Execution Artifacts
**Location**: `data/fitted/`

#### Current Results
- `buurt_BU16800000_Annen_fitted.parquet` - IPF results for Annen neighborhood
- `buurt_BU16800000_Annen_metadata.json` - Metadata for Annen IPF run
- `buurt_BU16800009_Verspreide_huizen_Annen_fitted.parquet` - IPF results for Verspreide huizen Annen
- `buurt_BU16800009_Verspreide_huizen_Annen_metadata.json` - Metadata for Verspreide huizen Annen IPF run

## 📈 Quality Metrics

### Phase 1 Validation
- ✅ Age spine validation: 0.0000% error on all age margins
- ✅ Schema consistency: All tables use canonical naming
- ✅ Structural zeros: 0-14 age group with tertiary education removed
- ✅ Data completeness: All required categories present

### Phase 2 Validation
- ✅ Annen: 100% population match, all marginals within 1% tolerance
- ✅ Verspreide huizen Annen: 103.45% population match, all marginals within 1% tolerance
- ✅ Constraint matching: Age, migration, education, and household constraints satisfied
- ✅ Non-negative weights: All fitted weights valid

## 🔧 Technical Implementation

### Phase 1: Seed Generation
```python
# Key steps in src/generate_seed.py
1. Load and preprocess 5 CBS tables
2. Normalize schemas to canonical format
3. Harmonize age bins to 5 categories
4. Build national age spine
5. Force-scale joint tables to age spine
6. Assemble Cartesian product seed matrix (age × education × migration × household)
7. Apply structural zeros (age-inappropriate combinations)
8. Validate and save artifacts
```

### Phase 2: IPF Execution
```python
# Key steps in src/IPF.py
1. Load national seed matrix
2. Identify target buurt (CBS code, name, or ID)
3. Extract buurt-level constraints (age, migration, education)
4. Prepare IPF input data
5. Execute IPF with ipfn library
6. Validate fitted results
7. Save fitted data and metadata
```

## 🚀 Next Development Steps

### Phase 2 Completion
- [ ] Implement batch processing for all buurten
- [ ] Add progress tracking and parallel execution
- [ ] Optimize memory usage for large-scale processing

### Phase 3 Implementation
- [ ] Stochastic rounding of fitted weights
- [ ] Integer age imputation (4-17 for school flag)
- [ ] Behavioral assignment (mobility, commute distance)
- [ ] Household aggregation and income calculation
- [ ] Spatial metadata joins (land use, infrastructure)

### Pipeline Enhancements
- [ ] Add comprehensive error handling
- [ ] Implement automated testing suite
- [ ] Add data versioning and provenance tracking
- [ ] Create visualization tools for results
- [ ] Document API for downstream integration

## 📚 Detailed Methodology

### Pipeline Methodology
The pipeline uses a Star Schema approach around the Age variable to avoid infinite oscillation in the IPF algorithm. Age serves as the central spine with other variables conditioned on it.

### Key Innovations
- **Star Schema Approach**: Age as central spine to avoid IPF oscillation
- **National Seed Matrix**: Reusable prior for all neighborhoods
- **Conditional Probability Scaling**: Force-scaling to maintain consistency
- **Structural Zeros**: Explicit handling of impossible combinations
- **Multi-level Constraints**: Age, migration, education, and household constraints working together
- **Household Composition Modeling**: Realistic household type distributions using national proportions

## 🔗 Key Relationships
- **Seed Matrix** → **IPF Input**: The national seed matrix provides the starting point for all buurt-level IPF runs
- **Constraints** → **IPF Targets**: Buurt-level marginals from 86165NED define the target distributions
- **Metadata** → **Reproducibility**: All processing steps are documented with timestamps and parameters

## 🎯 Project Goals
1. **Reproducibility**: All steps documented with metadata and versioning
2. **Quality**: Rigorous validation at each pipeline stage
3. **Scalability**: Design supports processing all Dutch buurten
4. **Extensibility**: Modular architecture for adding new variables
5. **Transparency**: Clear documentation of methodology and assumptions

## 📁 Project Structure
```
.
├── data/                  # All pipeline data artifacts
│   ├── reference/         # Raw CBS datasets (Phase 0)
│   ├── seed/             # Preprocessed data & seed matrix (Phase 1)
│   └── fitted/           # IPF results (Phase 2)
├── docs/                 # Additional documentation
├── src/                  # Core pipeline implementation
│   ├── generate_seed.py    # Phase 1 implementation
│   ├── IPF.py             # Phase 2 implementation
│   ├── analyze_references.py
│   ├── analyze_preprocessed.py
│   └── utils.py
└── tooling/              # Data fetching tools
```

## 🔧 Development Tools

### Data Fetching
```bash
cd tooling
python -m fetchers.cbs_statline --table 86165NED --out ../data/reference
```

### Schema Analysis
```bash
python src/analyze_references.py --reference-dir data/reference
python src/analyze_preprocessed.py --seed-dir data/seed
```

## 📊 Data Lineage
```
Raw CBS Data → Preprocessing → Seed Matrix → IPF Fitting → Microdata (future)
```

## 📈 File Formats
- `.parquet` files: Apache Parquet format for efficient storage of tabular data
- `.json` files: Metadata and configuration information

## 🎯 Additional Resources
- `log.md` - Development progress and milestones
- `pipeline2.md` - Detailed pipeline methodology
- `execution2.md` - Implementation execution plan