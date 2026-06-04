"""Analyze preprocessed parquet files from Phase 1 seed preparation.

This script validates that the preprocessing steps have been completed correctly
and checks the quality of the preprocessed data. It verifies:

1. File existence and expected dimensions
2. Canonical schema normalization (age_band, education_group, etc.)
3. Age taxonomy harmonization to 5-bin system
4. Data quality (missing values, negative values, etc.)
5. Schema consistency across all tables

Run:
    python src/analyze_preprocessed.py --seed-dir data/seed --reference-dir data/reference
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Expected canonical column names after preprocessing
CANONICAL_SCHEMA = {
    "86165NED_preprocessed": [
        "population", "age_0_14", "age_15_24", "age_25_44", "age_45_64", "age_65_plus",
        "migration_netherlands", "migration_eu_non_nl", "migration_non_eu",
        "household_total", "household_single", "household_no_kids", "household_with_kids"
    ],
    "83931NED_preprocessed": ["age_band", "income_class", "total"],
    "37620_preprocessed": ["age_band", "household_type", "total"],
    "82275NED_preprocessed": ["age_band", "migration_group", "education_group", "total"],
    "82309NED_preprocessed": ["age_band", "education_group", "total"]
}

# Expected age bins after harmonization
EXPECTED_AGE_BINS = ["0-14", "15-24", "25-44", "45-64", "65+"]

# Expected file dimensions from log.md
EXPECTED_DIMENSIONS = {
    "86165NED_preprocessed.parquet": (3, 13),
    "83931NED_preprocessed.parquet": (648, 3),
    "37620_preprocessed.parquet": (759, 3),
    "82275NED_preprocessed.parquet": (2016, 4),
    "82309NED_preprocessed.parquet": (29, 3)
}

def find_preprocessed_files(search_dirs: List[Path]) -> Dict[str, Path]:
    """Find preprocessed parquet files in multiple search directories."""
    preprocessed_files = {}

    # Expected file names with _preprocessed suffix
    expected_files_preprocessed = [
        "86165NED_preprocessed.parquet",
        "83931NED_preprocessed.parquet",
        "37620_preprocessed.parquet",
        "82275NED_preprocessed.parquet",
        "82309NED_preprocessed.parquet"
    ]

    # Base file names without _preprocessed suffix
    expected_files_base = [
        "86165NED.parquet",
        "83931NED.parquet",
        "37620.parquet",
        "82275NED.parquet",
        "82309NED.parquet"
    ]

    for search_dir in search_dirs:
        if search_dir.exists():
            # First try to find files with _preprocessed suffix
            for expected_file in expected_files_preprocessed:
                file_path = search_dir / expected_file
                if file_path.exists() and file_path not in preprocessed_files.values():
                    table_name = expected_file.replace("_preprocessed.parquet", "")
                    preprocessed_files[table_name] = file_path

            # If not found, try base filenames
            for expected_file in expected_files_base:
                if expected_file.replace(".parquet", "") not in preprocessed_files:
                    file_path = search_dir / expected_file
                    if file_path.exists() and file_path not in preprocessed_files.values():
                        table_name = expected_file.replace(".parquet", "")
                        preprocessed_files[table_name] = file_path

    return preprocessed_files

def validate_schema(df: pd.DataFrame, table_name: str, file_path: Path) -> Dict[str, object]:
    """Validate that the DataFrame follows the expected canonical schema."""
    validation_results = {
        "table": table_name,
        "file": str(file_path),
        "schema_valid": False,
        "missing_columns": [],
        "extra_columns": [],
        "column_types": {},
        "issues": []
    }

    expected_columns = CANONICAL_SCHEMA.get(table_name + "_preprocessed", [])

    # Check for missing columns
    missing_columns = [col for col in expected_columns if col not in df.columns]
    validation_results["missing_columns"] = missing_columns

    # Check for extra columns
    extra_columns = [col for col in df.columns if col not in expected_columns]
    validation_results["extra_columns"] = extra_columns

    # Check column data types
    for col in df.columns:
        validation_results["column_types"][col] = str(df[col].dtype)

        # Check for numeric columns that should be numeric
        if col in ["total", "population"] + [c for c in df.columns if c.startswith("age_") or c.startswith("migration_") or c.startswith("household_")]:
            if not pd.api.types.is_numeric_dtype(df[col]):
                validation_results["issues"].append(f"Column '{col}' should be numeric but is {df[col].dtype}")

    # Overall schema validation
    validation_results["schema_valid"] = len(missing_columns) == 0 and len(extra_columns) == 0

    return validation_results

def validate_age_harmonization(df: pd.DataFrame, table_name: str) -> Dict[str, object]:
    """Validate that age bins are properly harmonized to the 5-bin taxonomy."""
    age_validation = {
        "age_harmonization_valid": False,
        "age_column": None,
        "unique_age_values": [],
        "invalid_age_values": [],
        "age_distribution": {}
    }

    # Find age-related columns
    age_columns = [col for col in df.columns if "age" in col.lower()]

    if not age_columns:
        age_validation["issues"] = ["No age-related columns found"]
        return age_validation

    # For most tables, we expect "age_band" column
    if "age_band" in df.columns:
        age_validation["age_column"] = "age_band"
        age_values = df["age_band"].unique()
        age_validation["unique_age_values"] = sorted([str(v) for v in age_values])

        # Check if all age values are in expected bins
        valid_age_values = [str(v) for v in age_values if str(v) in EXPECTED_AGE_BINS]
        invalid_age_values = [str(v) for v in age_values if str(v) not in EXPECTED_AGE_BINS]

        age_validation["invalid_age_values"] = invalid_age_values
        age_validation["age_harmonization_valid"] = len(invalid_age_values) == 0

        # Calculate age distribution
        if age_validation["age_harmonization_valid"]:
            age_counts = df["age_band"].value_counts().to_dict()
            age_validation["age_distribution"] = {str(k): int(v) for k, v in age_counts.items()}

    elif any(col.startswith("age_") for col in df.columns):
        # For 86165NED, we have separate age columns
        age_validation["age_column"] = "age_* columns"
        age_columns = [col for col in df.columns if col.startswith("age_")]
        age_validation["unique_age_values"] = age_columns

        # Check if we have all expected age bins
        expected_age_cols = ["age_0_14", "age_15_24", "age_25_44", "age_45_64", "age_65_plus"]
        missing_age_cols = [col for col in expected_age_cols if col not in age_columns]
        age_validation["age_harmonization_valid"] = len(missing_age_cols) == 0
        age_validation["invalid_age_values"] = missing_age_cols

    else:
        age_validation["issues"] = ["No recognizable age column pattern found"]

    return age_validation

def check_data_quality(df: pd.DataFrame, table_name: str) -> Dict[str, object]:
    """Perform comprehensive data quality checks."""
    quality_checks = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "missing_values": {},
        "negative_values": {},
        "zero_values": {},
        "data_quality_issues": []
    }

    # Check each column for data quality issues
    for col in df.columns:
        # Missing values
        missing_count = df[col].isna().sum()
        if missing_count > 0:
            quality_checks["missing_values"][col] = int(missing_count)

        # Negative values (for numeric columns)
        if pd.api.types.is_numeric_dtype(df[col]):
            negative_count = (df[col] < 0).sum()
            if negative_count > 0:
                quality_checks["negative_values"][col] = int(negative_count)

            # Zero values
            zero_count = (df[col] == 0).sum()
            if zero_count > 0:
                quality_checks["zero_values"][col] = int(zero_count)

    # Summarize issues
    if quality_checks["missing_values"]:
        quality_checks["data_quality_issues"].append(
            f"Missing values found in columns: {list(quality_checks['missing_values'].keys())}"
        )

    if quality_checks["negative_values"]:
        quality_checks["data_quality_issues"].append(
            f"Negative values found in columns: {list(quality_checks['negative_values'].keys())}"
        )

    return quality_checks

def analyze_preprocessed_file(file_path: Path) -> Dict[str, object]:
    """Analyze a single preprocessed parquet file."""
    try:
        # Read the parquet file
        df = pd.read_parquet(file_path)

        table_name = file_path.stem.replace("_preprocessed", "")

        # Perform all validations
        analysis_results = {
            "file": str(file_path),
            "table": table_name,
            "exists": True,
            "read_success": True,
            "shape": df.shape,
            "schema_validation": validate_schema(df, table_name, file_path),
            "age_validation": validate_age_harmonization(df, table_name),
            "quality_checks": check_data_quality(df, table_name),
            "sample_data": df.head(5).to_dict(orient="records")
        }

        # Check against expected dimensions
        expected_file_name = f"{table_name}_preprocessed.parquet"
        if expected_file_name in EXPECTED_DIMENSIONS:
            expected_rows, expected_cols = EXPECTED_DIMENSIONS[expected_file_name]
            analysis_results["expected_shape"] = (expected_rows, expected_cols)
            analysis_results["shape_matches_expected"] = (
                df.shape[0] == expected_rows and df.shape[1] == expected_cols
            )
        else:
            analysis_results["shape_matches_expected"] = None

        return analysis_results

    except Exception as e:
        return {
            "file": str(file_path),
            "table": file_path.stem.replace("_preprocessed", ""),
            "exists": file_path.exists(),
            "read_success": False,
            "error": str(e),
            "schema_validation": {},
            "age_validation": {},
            "quality_checks": {}
        }

def generate_analysis_report(all_results: Dict[str, Dict]) -> Dict[str, object]:
    """Generate a comprehensive analysis report."""
    report = {
        "summary": {
            "total_files_expected": 5,
            "total_files_found": len(all_results),
            "total_files_analyzed": 0,
            "total_files_with_errors": 0,
            "files_missing": [],
            "overall_status": "INCOMPLETE"
        },
        "detailed_results": all_results,
        "validation_issues": [],
        "recommendations": []
    }

    # Check which files are missing
    expected_tables = ["86165NED", "83931NED", "37620", "82275NED", "82309NED"]
    found_tables = [result["table"] for result in all_results.values()]

    report["summary"]["files_missing"] = [table for table in expected_tables if table not in found_tables]

    # Analyze each result
    for table_name, result in all_results.items():
        if result.get("read_success", False):
            report["summary"]["total_files_analyzed"] += 1

            # Check for schema issues
            if not result["schema_validation"].get("schema_valid", True):
                report["validation_issues"].append(
                    f"Table {table_name}: Schema validation failed - "
                    f"missing: {result['schema_validation']['missing_columns']}, "
                    f"extra: {result['schema_validation']['extra_columns']}"
                )

            # Check for age harmonization issues
            if not result["age_validation"].get("age_harmonization_valid", True):
                report["validation_issues"].append(
                    f"Table {table_name}: Age harmonization validation failed - "
                    f"invalid age values: {result['age_validation']['invalid_age_values']}"
                )

            # Check for data quality issues
            if result["quality_checks"].get("data_quality_issues"):
                report["validation_issues"].extend([
                    f"Table {table_name}: {issue}"
                    for issue in result["quality_checks"]["data_quality_issues"]
                ])

        else:
            report["summary"]["total_files_with_errors"] += 1
            report["validation_issues"].append(
                f"Table {table_name}: Analysis failed - {result.get('error', 'Unknown error')}"
            )

    # Determine overall status
    if report["summary"]["total_files_with_errors"] > 0:
        report["summary"]["overall_status"] = "ERRORS_FOUND"
    elif report["summary"]["files_missing"]:
        report["summary"]["overall_status"] = "INCOMPLETE"
    elif report["validation_issues"]:
        report["summary"]["overall_status"] = "VALIDATION_ISSUES"
    else:
        report["summary"]["overall_status"] = "SUCCESS"

    # Generate recommendations
    if report["summary"]["files_missing"]:
        report["recommendations"].append(
            f"Run preprocessing to generate missing files: {', '.join(report['summary']['files_missing'])}"
        )

    if report["validation_issues"]:
        report["recommendations"].append(
            "Review validation issues and check preprocessing logic"
        )

    if report["summary"]["overall_status"] == "SUCCESS":
        report["recommendations"].append(
            "Preprocessing completed successfully. Ready for seed matrix generation."
        )

    return report

def print_analysis_summary(report: Dict[str, object]) -> None:
    """Print a human-readable summary of the analysis results."""
    print("=" * 80)
    print("PREPROCESSED DATA ANALYSIS REPORT")
    print("=" * 80)
    print(f"Status: {report['summary']['overall_status']}")
    print(f"Files Expected: {report['summary']['total_files_expected']}")
    print(f"Files Found: {report['summary']['total_files_found']}")
    print(f"Files Analyzed: {report['summary']['total_files_analyzed']}")
    print(f"Files with Errors: {report['summary']['total_files_with_errors']}")

    if report['summary']['files_missing']:
        print(f"\n⚠ Missing Files: {', '.join(report['summary']['files_missing'])}")

    print("\n" + "-" * 60)
    print("VALIDATION SUMMARY")
    print("-" * 60)

    if report['validation_issues']:
        print("❌ Validation Issues Found:")
        for i, issue in enumerate(report['validation_issues'], 1):
            print(f"  {i}. {issue}")
    else:
        print("✅ No validation issues found")

    if report['recommendations']:
        print("\n" + "-" * 60)
        print("RECOMMENDATIONS")
        print("-" * 60)
        for i, recommendation in enumerate(report['recommendations'], 1):
            print(f"  {i}. {recommendation}")

    print("\n" + "=" * 80)

def main() -> None:
    """Main entry point for the preprocessed data analysis."""
    parser = argparse.ArgumentParser(
        description="Analyze preprocessed parquet files from Phase 1 seed preparation"
    )
    parser.add_argument(
        "--seed-dir",
        type=Path,
        default=Path("data/seed"),
        help="Directory containing preprocessed seed files (default: data/seed)"
    )
    parser.add_argument(
        "--reference-dir",
        type=Path,
        default=Path("data/reference"),
        help="Directory containing reference data files (default: data/reference)"
    )
    parser.add_argument(
        "--output-report",
        type=Path,
        help="Path to save detailed analysis report as JSON"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed analysis for each table"
    )

    args = parser.parse_args()

    # Search for preprocessed files in multiple locations
    search_dirs = [args.seed_dir, args.reference_dir, Path("data")]
    preprocessed_files = find_preprocessed_files(search_dirs)

    print(f"Searching for preprocessed files in: {[str(d) for d in search_dirs]}")
    print(f"Found {len(preprocessed_files)} preprocessed files:")

    if preprocessed_files:
        for table_name, file_path in preprocessed_files.items():
            print(f"  ✓ {table_name}: {file_path}")
    else:
        print("  None found")

    # Analyze each preprocessed file
    analysis_results = {}
    for table_name, file_path in preprocessed_files.items():
        print(f"\nAnalyzing {table_name}...")
        result = analyze_preprocessed_file(file_path)
        analysis_results[table_name] = result

        if args.verbose and result.get("read_success", False):
            print(f"  Shape: {result['shape']}")
            print(f"  Schema Valid: {result['schema_validation']['schema_valid']}")
            print(f"  Age Harmonization Valid: {result['age_validation']['age_harmonization_valid']}")
            print(f"  Data Quality Issues: {len(result['quality_checks']['data_quality_issues'])}")

    # Generate comprehensive report
    report = generate_analysis_report(analysis_results)

    # Print summary
    print_analysis_summary(report)

    # Save detailed report if requested
    if args.output_report:
        args.output_report.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output_report, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\n✓ Detailed analysis report saved to: {args.output_report}")

    # Return appropriate exit code
    if report["summary"]["overall_status"] == "SUCCESS":
        print("\n🎉 Preprocessing analysis completed successfully!")
        return 0
    else:
        print(f"\n⚠ Preprocessing analysis completed with status: {report['summary']['overall_status']}")
        return 1

if __name__ == "__main__":
    main()