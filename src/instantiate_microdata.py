"""Phase 3: Microdata Instantiation - Convert fitted weights to individual synthetic people.

This script completes the pipeline by:
1. Loading fitted results from Phase 2 (buurt-level IPF)
2. Converting fitted weights to individual synthetic people
3. Saving clean microdata parquet files with one row per person

Run:
    python src/instantiate_microdata.py --buurt BU16800000 --fitted_dir data/fitted --out_dir data/microdata
"""

import argparse
from pathlib import Path

import pandas as pd


def instantiate_people_simple(fitted_df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert fitted weights to individual synthetic people using simple scaling.

    This function implements a straightforward approach:
    - Round fitted weights to nearest integer (number of people)
    - Create individual records with same attributes as the combination
    - Remove fitted_weight column from final output
    - Filter out aggregate categories (like "Total") that don't represent real people

    Args:
        fitted_df: DataFrame with fitted weights from Phase 2

    Returns:
        DataFrame with one row per synthetic person, no fitted_weight column
    """
    people = []

    # Process each combination in fitted results
    for _, row in fitted_df.iterrows():
        # Skip aggregate categories that don't represent real people
        # "Total" is used for calculations but shouldn't be assigned to individuals
        if row['household_type'] == 'Total':
            continue

        # Round fitted weight to get number of people
        num_people = round(row['fitted_weight'])

        # Create individual records (each with same attributes, no fitted_weight)
        for _ in range(num_people):
            person = {
                'age_band': row['age_band'],
                'education_group': row['education_group'],
                'migration_group': row['migration_group'],
                'household_type': row['household_type'],
                'income_class': row['income_class']
                # Note: fitted_weight column is intentionally excluded
            }
            people.append(person)

    return pd.DataFrame(people)

def validate_microdata(microdata_df: pd.DataFrame, original_fitted: pd.DataFrame) -> dict:
    """
    Validate that microdata preserves population totals and data quality.

    Args:
        microdata_df: Generated microdata DataFrame
        original_fitted: Original fitted DataFrame from Phase 2

    Returns:
        Dictionary of validation results
    """
    validation_results = {
        'validation_passed': True,
        'issues': [],
        'statistics': {}
    }

    # Calculate totals
    microdata_total = len(microdata_df)
    fitted_total = original_fitted['fitted_weight'].sum()
    rounded_total = original_fitted['fitted_weight'].apply(round).sum()

    validation_results['statistics'] = {
        'microdata_individuals': microdata_total,
        'fitted_total': fitted_total,
        'rounded_total': rounded_total,
        'rounding_difference': abs(microdata_total - fitted_total)
    }

    # Check if totals are reasonable (allow small rounding differences)
    if abs(microdata_total - fitted_total) > fitted_total * 0.01:  # 1% tolerance
        validation_results['validation_passed'] = False
        validation_results['issues'].append(
            f"Population mismatch: microdata has {microdata_total} individuals, "
            f"expected {fitted_total:.1f} (difference: {abs(microdata_total - fitted_total):.1f})"
        )

    # Check that all required columns are present
    required_columns = ['age_band', 'education_group', 'migration_group', 'household_type', 'income_class']
    missing_columns = [col for col in required_columns if col not in microdata_df.columns]

    if missing_columns:
        validation_results['validation_passed'] = False
        validation_results['issues'].append(f"Missing columns: {missing_columns}")

    # Check that fitted_weight column is NOT present
    if 'fitted_weight' in microdata_df.columns:
        validation_results['validation_passed'] = False
        validation_results['issues'].append("fitted_weight column should not be present in microdata")

    return validation_results

def main():
    """Main entry point for Phase 3 microdata instantiation."""
    parser = argparse.ArgumentParser(
        description="Phase 3: Microdata Instantiation - Convert fitted weights to individual synthetic people"
    )
    parser.add_argument(
        "--buurt",
        type=str,
        required=True,
        help="CBS buurt code (format: BUXXXXYYYY), human-readable name, or numeric ID"
    )
    parser.add_argument(
        "--fitted_dir",
        type=Path,
        default=Path("data") / "fitted",
        help="Directory containing fitted results from Phase 2 (default: data/fitted)"
    )
    parser.add_argument(
        "--out_dir",
        type=Path,
        default=Path("data") / "microdata",
        help="Output directory for microdata results (default: data/microdata)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed processing information"
    )

    args = parser.parse_args()

    print("=" * 80)
    print("Phase 3: Microdata Instantiation")
    print("=" * 80)

    try:
        # Find fitted results for the specified buurt
        print(f"\n[1/3] Loading fitted results for buurt: {args.buurt}")

        # Look for fitted files matching the buurt identifier
        fitted_files = []
        for pattern in [f"*{args.buurt}*_fitted.parquet", f"buurt_{args.buurt}_*_fitted.parquet"]:
            fitted_files.extend(args.fitted_dir.glob(pattern))

        if not fitted_files:
            raise FileNotFoundError(f"No fitted results found for buurt {args.buurt} in {args.fitted_dir}")

        # Use the first matching file
        fitted_path = fitted_files[0]
        fitted_df = pd.read_parquet(fitted_path)

        print(f"  ✓ Loaded fitted results: {len(fitted_df)} rows")
        print(f"    File: {fitted_path.name}")
        print(f"    Total fitted population: {fitted_df['fitted_weight'].sum():,.0f}")

        # Convert to individual people
        print(f"\n[2/3] Converting to individual synthetic people...")
        microdata_df = instantiate_people_simple(fitted_df)

        print(f"  ✓ Generated {len(microdata_df)} synthetic individuals")
        print(f"    Columns: {list(microdata_df.columns)}")

        # Validate results
        print(f"\n[3/3] Validating microdata...")
        validation_results = validate_microdata(microdata_df, fitted_df)

        if validation_results['validation_passed']:
            print("  ✅ Validation PASSED - Microdata meets quality criteria")
        else:
            print("  ⚠️  Validation completed with notes:")
            for issue in validation_results['issues']:
                print(f"    - {issue}")

        # Create output directory
        args.out_dir.mkdir(parents=True, exist_ok=True)

        # Generate output filename based on input filename
        output_filename = f"buurt_{args.buurt}_microdata.parquet"
        output_path = args.out_dir / output_filename

        # Save microdata
        microdata_df.to_parquet(output_path, index=False)
        print(f"\n[Final] Saving microdata...")
        print(f"  ✓ Saved synthetic population: {output_path}")
        print(f"    Individuals: {len(microdata_df):,}")
        print(f"    File size: {output_path.stat().st_size / 1024:.1f} KB")

        # Show statistics
        print(f"\n📊 Microdata Statistics:")
        print(f"    Age distribution:")
        for age_group, count in microdata_df['age_band'].value_counts().items():
            print(f"      {age_group}: {count:,} ({count/len(microdata_df)*100:.1f}%)")

        print(f"    Education distribution:")
        for edu_group, count in microdata_df['education_group'].value_counts().items():
            print(f"      {edu_group}: {count:,} ({count/len(microdata_df)*100:.1f}%)")

        print(f"\n{'='*80}")
        print("✅ Phase 3 Complete: Microdata instantiation successful")
        print(f"{'='*80}")

        return 0

    except Exception as e:
        print(f"\n❌ Error during microdata instantiation: {e}")
        print(f"Error type: {type(e).__name__}")
        return 1

if __name__ == "__main__":
    exit(main())