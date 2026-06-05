#!/usr/bin/env python3
"""
IPF Fit Analysis Script

This script analyzes how well the IPF results fit the original buurt constraints.
It provides detailed statistics on the quality of the IPF fitting process.

Usage:
    python src/analyze_ipf_fit.py --buurt BU16800000 [--fitted_dir data/fitted] [--reference_dir data/reference]
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class IPFAnalysisError(Exception):
    """Custom exception for IPF analysis errors"""
    pass

class IPFFitAnalyzer:
    """Class to analyze IPF fit quality"""

    def __init__(self, fitted_dir: str = "data/fitted", reference_dir: str = "data/reference"):
        self.fitted_dir = Path(fitted_dir)
        self.reference_dir = Path(reference_dir)

    def load_fitted_data(self, buurt_id: str) -> Dict[str, Any]:
        """Load fitted data and metadata for a buurt"""
        logger.info(f"📊 Loading fitted data for buurt {buurt_id}...")

        # Find the fitted file (handle different naming conventions)
        fitted_files = list(self.fitted_dir.glob(f"buurt_{buurt_id}_*_fitted.parquet"))
        if not fitted_files:
            fitted_files = list(self.fitted_dir.glob(f"buurt_{buurt_id}_fitted.parquet"))

        if not fitted_files:
            raise IPFAnalysisError(f"No fitted data found for buurt {buurt_id}")

        fitted_file = fitted_files[0]
        metadata_file = fitted_file.with_suffix('.metadata.json')

        # Load fitted data
        fitted_df = pd.read_parquet(fitted_file)
        logger.info(f"✅ Loaded fitted data: {len(fitted_df)} rows")

        # Load metadata
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            logger.info(f"✅ Loaded metadata: {len(metadata)} keys")
        else:
            metadata = {}
            logger.warning(f"⚠️  No metadata file found: {metadata_file}")

        return {
            'fitted_data': fitted_df,
            'metadata': metadata,
            'fitted_file': fitted_file,
            'metadata_file': metadata_file
        }

    def load_reference_data(self) -> pd.DataFrame:
        """Load reference data from 86165NED"""
        reference_file = self.reference_dir / "86165NED.parquet"
        if not reference_file.exists():
            raise IPFAnalysisError(f"Reference data not found: {reference_file}")

        logger.info("📊 Loading reference data...")
        df = pd.read_parquet(reference_file)
        logger.info(f"✅ Loaded reference data: {len(df)} rows, {len(df.columns)} columns")
        return df

    def find_buurt_in_reference(self, df: pd.DataFrame, buurt_id: str) -> pd.Series:
        """Find the specific buurt in the reference data"""
        # Try different identification methods
        buurt_row = None

        # Method 1: Try CBS buurt code (BUXXXXYYYY format)
        if buurt_id.startswith("BU") and len(buurt_id) == 10:
            buurt_row = df[df['Codering_3'].str.strip() == buurt_id]
            if len(buurt_row) == 1:
                return buurt_row.iloc[0]

        # Method 2: Try to find by partial matching
        buurt_row = df[df['Codering_3'].str.contains(buurt_id, case=False, na=False)]
        if len(buurt_row) == 1:
            return buurt_row.iloc[0]

        # Method 3: Try human-readable name
        buurt_row = df[df['WijkenEnBuurten'].str.contains(buurt_id, case=False, na=False)]
        if len(buurt_row) == 1:
            return buurt_row.iloc[0]

        if buurt_row is None or len(buurt_row) == 0:
            raise IPFAnalysisError(f"Could not find buurt {buurt_id} in reference data")

        return buurt_row.iloc[0]

    def calculate_fit_statistics(self, fitted_df: pd.DataFrame, buurt_row: pd.Series) -> Dict[str, Any]:
        """Calculate detailed fit statistics"""
        logger.info("📊 Calculating IPF fit statistics...")

        # Extract constraints from reference data
        constraints = {
            'population': buurt_row["AantalInwoners_5"],
            'households': buurt_row["HuishoudensTotaal_29"],
            'age_0_14': buurt_row["k_0Tot15Jaar_8"],
            'age_15_24': buurt_row["k_15Tot25Jaar_9"],
            'age_25_44': buurt_row["k_25Tot45Jaar_10"],
            'age_45_64': buurt_row["k_45Tot65Jaar_11"],
            'age_65_plus': buurt_row["k_65JaarOfOuder_12"],
            'migration_netherlands': buurt_row["Nederland_17"],
            'migration_eu_non_nl': buurt_row["EuropaExclusiefNederland_18"],
            'migration_non_eu': buurt_row["BuitenEuropa_19"],
            'household_single': buurt_row["Eenpersoonshuishoudens_30"],
            'household_no_kids': buurt_row["HuishoudensZonderKinderen_31"],
            'household_with_kids': buurt_row["HuishoudensMetKinderen_32"]
        }

        # Calculate fitted totals from the fitted data
        fitted_totals = {
            'population': fitted_df['fitted_weight'].sum(),
            'households': fitted_df['fitted_weight'].sum()  # Approximation
        }

        # Calculate age distribution from fitted data
        age_mapping = {
            '0-14': 'age_0_14',
            '15-24': 'age_15_24',
            '25-44': 'age_25_44',
            '45-64': 'age_45_64',
            '65+': 'age_65_plus'
        }

        for age_band, constraint_key in age_mapping.items():
            age_df = fitted_df[fitted_df['age_band'] == age_band]
            fitted_totals[constraint_key] = age_df['fitted_weight'].sum()

        # Calculate migration distribution from fitted data
        migration_mapping = {
            'Netherlands': 'migration_netherlands',
            'EU_non_NL': 'migration_eu_non_nl',
            'Non_EU': 'migration_non_eu'
        }

        for migration_group, constraint_key in migration_mapping.items():
            mig_df = fitted_df[fitted_df['migration_group'] == migration_group]
            fitted_totals[constraint_key] = mig_df['fitted_weight'].sum()

        # Calculate household distribution from fitted data
        household_mapping = {
            'Single': 'household_single',
            'Cohabiting': 'household_no_kids',
            'Married_no_kids': 'household_no_kids',
            'Cohabiting_no_kids': 'household_no_kids',
            'Married_with_kids': 'household_with_kids',
            'Cohabiting_with_kids': 'household_with_kids',
            'Single_parent': 'household_with_kids',
            'Living_with_parents': 'household_with_kids'
        }

        # Initialize household totals
        fitted_totals['household_single'] = 0
        fitted_totals['household_no_kids'] = 0
        fitted_totals['household_with_kids'] = 0

        # Sum up household types
        for household_type, constraint_key in household_mapping.items():
            hh_df = fitted_df[fitted_df['household_type'] == household_type]
            fitted_totals[constraint_key] += hh_df['fitted_weight'].sum()

        # Calculate statistics
        statistics = {
            'constraints': constraints,
            'fitted': fitted_totals,
            'errors': {},
            'percent_errors': {},
            'absolute_errors': {}
        }

        # Calculate errors for each constraint
        for key in constraints:
            if key in fitted_totals and constraints[key] > 0:
                error = fitted_totals[key] - constraints[key]
                percent_error = (error / constraints[key]) * 100

                statistics['errors'][key] = error
                statistics['percent_errors'][key] = percent_error
                statistics['absolute_errors'][key] = abs(error)

        return statistics

    def analyze_ipf_fit(self, buurt_id: str) -> Dict[str, Any]:
        """Main analysis method"""
        try:
            # Load fitted data
            fitted_data = self.load_fitted_data(buurt_id)
            fitted_df = fitted_data['fitted_data']
            metadata = fitted_data['metadata']

            # Load reference data
            reference_df = self.load_reference_data()

            # Find buurt in reference data
            buurt_row = self.find_buurt_in_reference(reference_df, buurt_id)

            # Calculate fit statistics
            statistics = self.calculate_fit_statistics(fitted_df, buurt_row)

            # Add metadata to statistics
            statistics['metadata'] = metadata
            statistics['buurt_info'] = {
                'buurt_id': buurt_id,
                'name': buurt_row.get('WijkenEnBuurten', 'Unknown'),
                'population': buurt_row.get('AantalInwoners_5', 0),
                'households': buurt_row.get('HuishoudensTotaal_29', 0)
            }

            return statistics

        except Exception as e:
            logger.error(f"❌ IPF analysis failed: {e}")
            raise IPFAnalysisError(f"IPF analysis failed: {e}") from e

    def print_analysis_results(self, statistics: Dict[str, Any]) -> None:
        """Print analysis results in a readable format"""
        buurt_info = statistics['buurt_info']
        constraints = statistics['constraints']
        fitted = statistics['fitted']
        percent_errors = statistics['percent_errors']

        logger.info("=" * 80)
        logger.info("📊 IPF FIT ANALYSIS RESULTS")
        logger.info("=" * 80)
        logger.info(f"Buurt: {buurt_info['buurt_id']} - {buurt_info['name']}")
        logger.info(f"Population: {buurt_info['population']:,}")
        logger.info(f"Households: {buurt_info['households']:,}")
        logger.info("-" * 80)

        # Overall fit quality
        overall_error = np.mean([abs(err) for err in percent_errors.values()])
        logger.info(f"🎯 Overall Fit Quality: {overall_error:.2f}% average error")
        logger.info("-" * 80)

        # Age distribution analysis
        logger.info("📊 AGE DISTRIBUTION FIT:")
        age_constraints = ['age_0_14', 'age_15_24', 'age_25_44', 'age_45_64', 'age_65_plus']
        for constraint in age_constraints:
            if constraint in constraints:
                error = percent_errors.get(constraint, 0)
                status = "✅" if abs(error) < 5 else "⚠️ "
                logger.info(f"  {status} {constraint}: {fitted[constraint]:.0f} (target: {constraints[constraint]:.0f}, error: {error:.2f}%)")

        logger.info("-" * 80)

        # Migration distribution analysis
        logger.info("📊 MIGRATION DISTRIBUTION FIT:")
        migration_constraints = ['migration_netherlands', 'migration_eu_non_nl', 'migration_non_eu']
        for constraint in migration_constraints:
            if constraint in constraints:
                error = percent_errors.get(constraint, 0)
                status = "✅" if abs(error) < 5 else "⚠️ "
                logger.info(f"  {status} {constraint}: {fitted[constraint]:.0f} (target: {constraints[constraint]:.0f}, error: {error:.2f}%)")

        logger.info("-" * 80)

        # Household distribution analysis
        logger.info("📊 HOUSEHOLD DISTRIBUTION FIT:")
        household_constraints = ['household_single', 'household_no_kids', 'household_with_kids']
        for constraint in household_constraints:
            if constraint in constraints:
                error = percent_errors.get(constraint, 0)
                status = "✅" if abs(error) < 5 else "⚠️ "
                logger.info(f"  {status} {constraint}: {fitted[constraint]:.0f} (target: {constraints[constraint]:.0f}, error: {error:.2f}%)")

        logger.info("-" * 80)

        # Quality assessment
        max_error = max(abs(err) for err in percent_errors.values())
        if max_error < 5:
            quality = "🎉 EXCELLENT"
        elif max_error < 10:
            quality = "✅ GOOD"
        elif max_error < 20:
            quality = "⚠️  FAIR"
        else:
            quality = "❌ POOR"

        logger.info(f"🏆 IPF Fit Quality Assessment: {quality}")
        logger.info(f"   Maximum error: {max_error:.2f}%")
        logger.info(f"   Average error: {overall_error:.2f}%")
        logger.info("=" * 80)

def main():
    """Main entry point for IPF fit analysis"""
    parser = argparse.ArgumentParser(
        description="IPF Fit Analysis - Analyze how well IPF results fit original constraints",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze IPF fit for a specific buurt
  python src/analyze_ipf_fit.py --buurt BU16800000

  # Analyze with custom directories
  python src/analyze_ipf_fit.py --buurt BU16800000 --fitted_dir data/fitted --reference_dir data/reference
        """
    )

    parser.add_argument(
        "--buurt",
        required=True,
        help="Buurt identifier (CBS code, name, or ID) to analyze"
    )

    parser.add_argument(
        "--fitted_dir",
        default="data/fitted",
        help="Directory for fitted results (default: data/fitted)"
    )

    parser.add_argument(
        "--reference_dir",
        default="data/reference",
        help="Directory for reference datasets (default: data/reference)"
    )

    args = parser.parse_args()

    try:
        # Create analyzer
        analyzer = IPFFitAnalyzer(
            fitted_dir=args.fitted_dir,
            reference_dir=args.reference_dir
        )

        # Run analysis
        statistics = analyzer.analyze_ipf_fit(args.buurt)

        # Print results
        analyzer.print_analysis_results(statistics)

        return 0

    except IPFAnalysisError as e:
        logger.error(f"💥 IPF analysis failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"💥 Unexpected analysis error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())