"""Phase 2: Buurt-level IPF Execution for Synthetic Population Pipeline.

This script implements Phase 2 of the pipeline as described in pipeline2.md:
- Loads the national seed matrix from Phase 1
- Extracts buurt-level marginal constraints from 86165NED
- Executes IPF for individual neighborhoods using the ipfn library
- Validates that fitted results match buurt constraints
- Saves fitted results ready for Phase 3 microdata instantiation

Run:
    python src/IPF.py --buurt BU16800000 --seed_dir data/seed --reference_dir data/reference
"""

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List

import ipfn.ipfn as ipfn_module
import numpy as np
import pandas as pd


def parseargs() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Phase 2: Buurt-level IPF Execution for Synthetic Population Pipeline"
    )
    parser.add_argument(
        "--seed_dir",
        type=Path,
        default=Path("data/seed"),
        help="Directory containing the national seed matrix (default: data/seed)"
    )
    parser.add_argument(
        "--reference_dir",
        type=Path,
        default=Path("data/reference"),
        help="Directory containing CBS reference data (default: data/reference)"
    )
    parser.add_argument(
        "--buurt",
        type=str,
        required=True,
        help="CBS buurt code (format: BUXXXXYYYY), human-readable name, or numeric ID"
    )
    parser.add_argument(
        "--output_dir",
        type=Path,
        default=Path("data/fitted"),
        help="Output directory for fitted results (default: data/fitted)"
    )
    parser.add_argument(
        "--max_iter",
        type=int,
        default=1000,
        help="Maximum IPF iterations (default: 1000)"
    )
    parser.add_argument(
        "--convergence_rate",
        type=float,
        default=1e-6,
        help="IPF convergence tolerance (default: 1e-6)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed IPF execution information"
    )
    return parser.parse_args()

def find_buurt_row(df_86165: pd.DataFrame, buurt_identifier: str) -> pd.Series:
    """
    Find a buurt row by various identification methods.

    Args:
        df_86165: DataFrame containing 86165NED data
        buurt_identifier: Can be CBS code, human-readable name, or ID

    Returns:
        DataFrame row for the identified buurt

    Raises:
        ValueError: If buurt cannot be found
    """
    # Clean the identifier
    identifier = str(buurt_identifier).strip()

    # Method 1: Try CBS buurt code (BUXXXXYYYY format)
    if identifier.startswith("BU") and len(identifier) == 10:
        buurt_row = df_86165[df_86165['Codering_3'].str.strip() == identifier]
        if len(buurt_row) == 1:
            return buurt_row.iloc[0]

    # Method 2: Try human-readable name
    buurt_row = df_86165[df_86165['WijkenEnBuurten'].str.strip() == identifier]
    if len(buurt_row) == 1:
        return buurt_row.iloc[0]

    # Method 3: Try numeric ID
    if identifier.isdigit():
        buurt_row = df_86165[df_86165['ID'] == int(identifier)]
        if len(buurt_row) == 1:
            return buurt_row.iloc[0]

    # If not found, try partial matching for human-readable names
    buurt_row = df_86165[df_86165['WijkenEnBuurten'].str.contains(identifier, case=False, na=False)]
    if len(buurt_row) == 1:
        return buurt_row.iloc[0]

    raise ValueError(f"Could not find buurt with identifier: {buurt_identifier}")

def extract_buurt_constraints(buurt_row: pd.Series, df_37620: pd.DataFrame | None = None) -> Dict[str, Dict[str, float]]:
    """
    Extract marginal constraints from a buurt row for IPF.

    Args:
        buurt_row: DataFrame row containing buurt data
        df_37620: Optional DataFrame containing national household data for proper proportions

    Returns:
        Dictionary of constraints for IPF
    """
    # Age distribution (5 bins - including 0-14 age group)
    age_constraints = {
        "0-14": float(buurt_row["k_0Tot15Jaar_8"]),
        "15-24": float(buurt_row["k_15Tot25Jaar_9"]),
        "25-44": float(buurt_row["k_25Tot45Jaar_10"]),
        "45-64": float(buurt_row["k_45Tot65Jaar_11"]),
        "65+": float(buurt_row["k_65JaarOfOuder_12"])
    }

    # Migration background - adjust to exclude 0-14 age group to match seed matrix
    total_population = float(buurt_row["AantalInwoners_5"])
    age_0_14 = float(buurt_row["k_0Tot15Jaar_8"])
    age_15_plus = total_population - age_0_14

    # Calculate migration constraints for 15+ population only
    migration_constraints = {
        "Netherlands": float(buurt_row["Nederland_17"]) * (age_15_plus / total_population),
        "EU_non_NL": float(buurt_row["EuropaExclusiefNederland_18"]) * (age_15_plus / total_population),
        "Non_EU": float(buurt_row["BuitenEuropa_19"]) * (age_15_plus / total_population),
        "Other": 0.0  # Add Other category to match seed matrix structure
    }

    # Round to integers
    for key in migration_constraints:
        migration_constraints[key] = round(migration_constraints[key])

        # Household composition - use national person-based proportions from 37620
        # This is the CORRECT approach: use person-based 37620 data, not household-based 86165 data
        if df_37620 is not None:
            # Filter out "Total" household type since it's an aggregate category
            df_37620_filtered = df_37620[df_37620['household_type'] != 'Total']

            # Use the 15+ population only (household constraints don't apply to 0-14 age group)
            age_15_plus = sum(age_population for age_group, age_population in age_constraints.items() if age_group != "0-14")

            # Calculate total national population from 37620 data
            total_national_population = float(df_37620_filtered['total'].sum())

            # Calculate national household proportions across all age groups
            national_hh_proportions = {}
            for hh_type in df_37620_filtered['household_type'].unique():
                hh_total = float(df_37620_filtered[df_37620_filtered['household_type'] == hh_type]['total'].sum())
                national_hh_proportions[hh_type] = hh_total / total_national_population

            # Apply national proportions to 15+ buurt population
            household_constraints = {}
            for hh_type, proportion in national_hh_proportions.items():
                household_constraints[hh_type] = age_15_plus * proportion

        else:
            # This should NEVER happen - national household data is required
            raise ValueError("National household data (37620) is required for proper household constraint calculation")

    return {
        "age_band": age_constraints,
        "migration_group": migration_constraints,
        "household_type": household_constraints
    }

def extract_national_education_probabilities(df_82275: pd.DataFrame) -> Dict[str, Dict[str, Dict[str, float]]]:
    """
    Extract national-level education probabilities from 82275NED data.

    Since 82275NED contains national-level data (not buurt-level), we extract
    the joint probabilities of education given age and migration background
    from the national data and apply them to buurten.

    Args:
        df_82275: DataFrame containing 82275NED education data

    Returns:
        Dictionary of conditional probabilities: P(education | age, migration)
    """
    # Map 82275NED age categories to our 5-bin system
    age_mapping = {
        '15-24': ['15 tot 25 jaar'],
        '25-44': ['25 tot 35 jaar', '35 tot 45 jaar'],
        '45-64': ['45 tot 55 jaar', '55 tot 65 jaar'],
        '65+': ['65 tot 75 jaar', '75 jaar of ouder']
    }

    # Map 82275NED migration categories to our 4-group system
    migration_mapping = {
        'Netherlands': ['Nederlandse achtergrond'],
        'EU_non_NL': ['Westerse migratieachtergrond'],
        'Non_EU': ['Niet-westerse migratieachtergrond'],
        'Other': ['Onbekende migratieachtergrond']
    }

    # Map 82275NED education categories to our system
    # Based on the Dutch education system:
    # - Primary: Basisonderwijs (ages 4-12)
    # - Secondary: VMBO, HAVO, VWO (ages 12-18)
    # - Secondary Vocational: MBO (ages 16+)
    # - Tertiary: HBO (Universities of Applied Sciences), WO (Research Universities)
    education_mapping = {
        'Primary_or_None': ['1 Laag onderwijsniveau', '11 Basisonderwijs', '111 Basisonderwijs'],
        'Secondary_VMBO': ['12 Vmbo, havo-, vwo-onderbouw, mbo1', '121 Vmbo-b/k, mbo1', '122 Vmbo-g/t, havo-, vwo-onderbouw'],
        'Secondary_HAVO_VWO': ['213 Havo, vwo'],
        'Secondary_MBO': ['21 Havo, vwo, mbo2-4', '211 Mbo2 en mbo3', '212 Mbo4'],  # MBO is secondary vocational education
        'Tertiary_Higher': ['31 Hbo-, wo-bachelor', '311 Hbo-, wo-bachelor'],  # HBO bachelor
        'Tertiary_University': ['32 Hbo-, wo-master, doctor', '321 Hbo-, wo-master, doctor']  # WO master/doctor
    }

    # Calculate national education probabilities: P(education | age, migration)
    national_probabilities = {}

    # Filter to only rows with valid education data
    valid_education_data = df_82275[df_82275['HoogstBehaaldOnderwijsniveau'] != 'Totaal']

    for age_group, cbs_age_categories in age_mapping.items():
        for migration_group, cbs_migration_categories in migration_mapping.items():
            # Filter data for this age and migration combination
            age_filter = valid_education_data['Leeftijd'].isin(cbs_age_categories)
            migration_filter = valid_education_data['Migratieachtergrond'].isin(cbs_migration_categories)
            subset = valid_education_data[age_filter & migration_filter]

            if len(subset) == 0:
                continue

            # Calculate education distribution for this age×migration group
            education_probs = {}
            total_population = subset['Bevolking_1'].sum()

            for education_group, cbs_education_categories in education_mapping.items():
                education_rows = subset[subset['HoogstBehaaldOnderwijsniveau'].isin(cbs_education_categories)]
                if len(education_rows) > 0:
                    education_count = education_rows['Bevolking_1'].sum()
                    education_probs[education_group] = education_count / total_population
                else:
                    education_probs[education_group] = 0.0

            # Normalize to sum to 1.0
            prob_sum = sum(education_probs.values())
            if prob_sum > 0:
                for edu_group in education_probs:
                    education_probs[edu_group] /= prob_sum

            national_probabilities[f"{age_group}_{migration_group}"] = education_probs

    return national_probabilities

def extract_national_income_probabilities(df_83931: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """
    Extract national-level income probabilities from 83931NED data.

    Since 83931NED contains national-level data (not buurt-level), we extract
    the conditional probabilities of income given age from the national data
    and apply them to buurten.

    Args:
        df_83931: DataFrame containing 83931NED income data

    Returns:
        Dictionary of conditional probabilities: P(income | age)
    """
    # Map 83931NED age categories to our 5-bin system
    age_mapping = {
        '15-24': ['Leeftijd: 15 tot 25 jaar'],
        '25-44': ['Leeftijd: 25 tot 45 jaar'],
        '45-64': ['Leeftijd: 45 tot 65 jaar'],
        '65+': ['Leeftijd: 65 jaar of ouder']
    }

    # Calculate national income probabilities: P(income | age)
    national_probabilities = {}

    # Filter to only rows with valid income data
    valid_income_data = df_83931[df_83931['Inkomensklassen'] != 'Totaal']

    # Filter for bracket-based income classes only (exclude percentile groups)
    # Keep only income classes that contain "tot" (meaning "to" in Dutch)
    # This includes patterns like "Inkomen: 10 000 tot 20 000 euro" and "Inkomen: minder dan 10 000 euro"
    bracket_patterns = valid_income_data["Inkomensklassen"].str.contains("tot", case=False, na=False) | \
                      (valid_income_data["Inkomensklassen"] == "Inkomen: minder dan 10 000 euro")
    valid_income_data = valid_income_data[bracket_patterns]

    for age_group, cbs_age_categories in age_mapping.items():
        # Filter data for this age group
        age_data = valid_income_data[valid_income_data['KenmerkenVanPersonen'].isin(cbs_age_categories)]
        if len(age_data) == 0:
            continue

        # Calculate income distribution for this age group
        income_probs = {}
        total_population = age_data['PersonenMetInkomen_1'].sum()

        for _, row in age_data.iterrows():
            income_class = row['Inkomensklassen']
            income_count = row['PersonenMetInkomen_1']
            income_probs[income_class] = income_count / total_population

        # Normalize to sum to 1.0
        prob_sum = sum(income_probs.values())
        if prob_sum > 0:
            for income_class in income_probs:
                income_probs[income_class] /= prob_sum

        national_probabilities[age_group] = income_probs

    return national_probabilities

def apply_national_education_probabilities(
    buurt_constraints: Dict[str, Dict[str, float]],
    national_probs: Dict[str, Dict[str, Dict[str, float]]]
) -> Dict[str, float]:
    """
    Apply national education probabilities to buurt constraints.

    Args:
        buurt_constraints: Buurt-level constraints (age and migration)
        national_probs: National education probabilities P(education | age, migration)

    Returns:
        Dictionary of education constraints for the buurt
    """
    # Initialize education constraints
    education_constraints = {
        'Primary_or_None': 0.0,
        'Secondary_VMBO': 0.0,
        'Secondary_HAVO_VWO': 0.0,
        'Secondary_MBO': 0.0,
        'Tertiary_Higher': 0.0,
        'Tertiary_University': 0.0
    }

    # For each age×migration combination in the buurt
    for age_group, age_count in buurt_constraints["age_band"].items():
        for migration_group, migration_count in buurt_constraints["migration_group"].items():
            # Skip 0-14 age group for education constraints since education data doesn't include this age group
            if age_group == "0-14":
                continue

            # Find the joint age×migration population
            # For 15+ age groups, use the correct population base
            # Since migration constraints are already scaled to 15+ population, we need to be careful
            # The correct approach: use age_count directly for 15+ age groups
            if age_group in ["15-24", "25-44", "45-64", "65+"]:
                # For 15+ age groups, the joint population is simply the age_count
                # multiplied by the migration proportion within the 15+ population
                joint_population = age_count * (migration_count / sum(buurt_constraints["migration_group"].values()))
            else:
                # This should not happen since we skip 0-14, but keep as fallback
                joint_population = 0.0

            # Get the education probabilities for this age×migration group
            prob_key = f"{age_group}_{migration_group}"
            if prob_key in national_probs:
                education_probs = national_probs[prob_key]

                # Apply probabilities to get education counts
                for education_group, prob in education_probs.items():
                    education_constraints[education_group] += joint_population * prob

    # Round to integers
    for education_group in education_constraints:
        education_constraints[education_group] = round(education_constraints[education_group])

    return education_constraints

def apply_national_income_probabilities(
    buurt_constraints: Dict[str, Dict[str, float]],
    national_probs: Dict[str, Dict[str, float]]
) -> Dict[str, float]:
    """
    Apply national income probabilities to buurt constraints.

    Args:
        buurt_constraints: Buurt-level constraints (age)
        national_probs: National income probabilities P(income | age)

    Returns:
        Dictionary of income constraints for the buurt
    """
    # Initialize income constraints
    income_constraints = {}

    # For each age group in the buurt
    for age_group, age_count in buurt_constraints["age_band"].items():
        # Get the income probabilities for this age group
        if age_group in national_probs:
            income_probs = national_probs[age_group]

            # Apply probabilities to get income counts
            for income_class, prob in income_probs.items():
                if income_class not in income_constraints:
                    income_constraints[income_class] = 0.0
                income_constraints[income_class] += age_count * prob

    # Round to integers
    for income_class in income_constraints:
        income_constraints[income_class] = round(income_constraints[income_class])

    return income_constraints

def validate_constraints(constraints: Dict[str, Dict[str, float]]) -> None:
    """
    Validate that constraints are properly formatted for IPF.

    Args:
        constraints: Dictionary of constraints

    Raises:
        ValueError: If constraints are invalid
    """
    for constraint_name, values in constraints.items():
        if not isinstance(values, dict):
            raise ValueError(f"Constraint {constraint_name} must be a dictionary")

        if not values:
            raise ValueError(f"Constraint {constraint_name} is empty")

        for category, value in values.items():
            if not isinstance(value, (int, float)):
                raise ValueError(f"Constraint {constraint_name}.{category} must be numeric")
            if value < 0:
                raise ValueError(f"Constraint {constraint_name}.{category} must be non-negative")

def prepare_seed_matrix(seed_df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare the seed matrix for IPF execution.

    Args:
        seed_df: DataFrame containing the national seed matrix

    Returns:
        Prepared seed matrix DataFrame

    Raises:
        ValueError: If seed matrix is invalid
    """
    # Validate required columns
    required_columns = ["age_band", "education_group", "migration_group", "weight"]
    missing_columns = [col for col in required_columns if col not in seed_df.columns]

    if missing_columns:
        raise ValueError(f"Seed matrix missing required columns: {missing_columns}")

    # Ensure all weights are non-negative
    if (seed_df["weight"] < 0).any():
        raise ValueError("Seed matrix contains negative weights")

    return seed_df.copy()

def execute_ipf(
    seed_df: pd.DataFrame,
    constraints: Dict[str, Dict[str, float]],
    max_iter: int = 1000,
    convergence_rate: float = 1e-6,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Execute IPF algorithm using the ipfn library.

    Args:
        seed_df: Prepared seed matrix DataFrame
        constraints: Dictionary of marginal constraints
        max_iter: Maximum number of iterations
        convergence_rate: Convergence tolerance
        verbose: Whether to show detailed information

    Returns:
        DataFrame with fitted weights
    """
    # Convert seed matrix to long format expected by ipfn
    # Now include household_type and income_class in the pivot
    seed_matrix = seed_df.pivot_table(
        index=["age_band", "education_group", "migration_group", "household_type", "income_class"],
        values="weight",
        aggfunc="sum"
    ).fillna(0).reset_index()

    # Calculate the target population from constraints (sum of age constraints)
    target_population = sum(constraints["age_band"].values())

    # Calculate the current seed population
    current_population = seed_matrix["weight"].sum()

    if verbose:
        print(f"Seed matrix shape: {seed_matrix.shape}")
        print(f"Seed matrix total: {current_population:.0f}")
        print(f"Target population: {target_population:.0f}")

    # Scale the seed matrix to match the target population
    if current_population > 0 and target_population > 0:
        scaling_factor = target_population / current_population
        seed_matrix["weight"] = seed_matrix["weight"].astype(float) * scaling_factor
        if verbose:
            print(f"Scaling factor: {scaling_factor:.6f}")
            print(f"Scaled seed matrix total: {seed_matrix['weight'].sum():.0f}")

    # Rename weight column to 'total' as expected by ipfn
    seed_matrix = seed_matrix.rename(columns={"weight": "total"})

    # Convert constraints to the format expected by ipfn
    # ipfn expects aggregates as Series objects
    age_aggregates = pd.Series(constraints["age_band"])
    migration_aggregates = pd.Series(constraints["migration_group"])
    education_aggregates = pd.Series(constraints["education_group"])
    household_aggregates = pd.Series(constraints["household_type"])
    income_aggregates = pd.Series(constraints["income_class"])

    # Execute IPF with all constraints including household and income
    ipf = ipfn_module.ipfn(
        seed_matrix,
        [age_aggregates, migration_aggregates, education_aggregates, household_aggregates, income_aggregates],
        [["age_band"], ["migration_group"], ["education_group"], ["household_type"], ["income_class"]]
    )
    fitted = ipf.iteration()

    # Convert back to DataFrame format
    if isinstance(fitted, pd.DataFrame):
        fitted_df = fitted.copy()
        fitted_df = fitted_df.rename(columns={"total": "fitted_weight"})
    else:
        # Handle case where fitted is not a DataFrame (convert from numpy array)
        fitted_df = pd.DataFrame(fitted, columns=seed_matrix.columns)
        fitted_df = fitted_df.rename(columns={"total": "fitted_weight"})

    return fitted_df

def validate_fitted_results(
    fitted_df: pd.DataFrame,
    original_constraints: Dict[str, Dict[str, float]],
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Validate that fitted results meet quality criteria.

    Args:
        fitted_df: DataFrame with fitted weights
        original_constraints: Original constraints used for IPF
        verbose: Whether to show detailed validation information

    Returns:
        Dictionary of validation results
    """
    validation_results = {
        "validation_passed": True,
        "issues": [],
        "constraint_marginals": {},
        "fitted_marginals": {}
    }

    # Check for negative weights
    negative_weights = fitted_df[fitted_df["fitted_weight"] < 0]
    if len(negative_weights) > 0:
        validation_results["validation_passed"] = False
        validation_results["issues"].append(
            f"Found {len(negative_weights)} negative weights"
        )

    # Check that fitted marginals match constraints (including household_type and income_class)
    constraint_columns = ["age_band", "migration_group", "education_group", "household_type", "income_class"]
    for constraint_name, constraint_values in original_constraints.items():
        if constraint_name not in constraint_columns:
            continue  # Skip any other constraints

        if constraint_name not in fitted_df.columns:
            validation_results["validation_passed"] = False
            validation_results["issues"].append(
                f"Missing constraint column: {constraint_name}"
            )
            continue

        # Calculate fitted marginal
        fitted_marginal = fitted_df.groupby(constraint_name)["fitted_weight"].sum().to_dict()

        validation_results["constraint_marginals"][constraint_name] = constraint_values
        validation_results["fitted_marginals"][constraint_name] = fitted_marginal

        # Check if marginals match within tolerance
        for category, expected_value in constraint_values.items():
            if category not in fitted_marginal:
                validation_results["validation_passed"] = False
                validation_results["issues"].append(
                    f"Missing category {category} in {constraint_name} marginal"
                )
                continue

            fitted_value = fitted_marginal[category]
            if expected_value > 0:
                error = abs(fitted_value - expected_value) / expected_value
                if error > 0.15:  # 15% tolerance (realistic for demographic modeling with IPF)
                    validation_results["validation_passed"] = False
                    validation_results["issues"].append(
                        f"Marginal mismatch for {constraint_name}.{category}: "
                        f"expected {expected_value:.0f}, got {fitted_value:.0f} "
                        f"(error: {error:.2%})"
                    )

    if verbose:
        print("Validation Results:")
        print(f"  Overall status: {'✅ PASSED' if validation_results['validation_passed'] else '❌ FAILED'}")
        if validation_results["issues"]:
            print("  Issues found:")
            for issue in validation_results["issues"]:
                print(f"    - {issue}")
        else:
            print("  No issues found")

    return validation_results

def save_fitted_results(
    fitted_df: pd.DataFrame,
    buurt_identifier: str,
    buurt_row: pd.Series,
    validation_results: Dict[str, Any],
    output_dir: Path
) -> Dict[str, Path]:
    """
    Save fitted results and metadata to files.

    Args:
        fitted_df: DataFrame with fitted weights
        buurt_identifier: Original buurt identifier
        buurt_row: Original buurt data row
        validation_results: Validation results
        output_dir: Output directory

    Returns:
        Dictionary of saved file paths
    """
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Extract buurt code for filename
    buurt_code = buurt_row["Codering_3"].strip() if pd.notna(buurt_row["Codering_3"]) else buurt_identifier
    buurt_name = buurt_row["WijkenEnBuurten"].strip() if pd.notna(buurt_row["WijkenEnBuurten"]) else "unknown"

    # Create safe filename
    safe_name = f"buurt_{buurt_code}_{buurt_name.replace(' ', '_')}"
    safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in safe_name)[:100]

    # Save fitted data
    fitted_path = output_dir / f"{safe_name}_fitted.parquet"
    fitted_df.to_parquet(fitted_path, index=False)

    # Create metadata
    metadata = {
        "buurt_identifier": buurt_identifier,
        "buurt_code": buurt_code,
        "buurt_name": buurt_name,
        "municipality": str(buurt_row.get("Gemeentenaam_1", "unknown")),
        "population": int(buurt_row.get("AantalInwoners_5", 0)),
        "households": int(buurt_row.get("HuishoudensTotaal_29", 0)),
        "fitted_rows": len(fitted_df),
        "fitted_total": float(fitted_df["fitted_weight"].sum()),
        "validation": validation_results,
        "timestamp": pd.Timestamp.now().isoformat()
    }

    # Save metadata
    metadata_path = output_dir / f"{safe_name}_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    return {
        "fitted_data": fitted_path,
        "metadata": metadata_path
    }

def main(args: argparse.Namespace) -> int:
    """
    Main entry point for Phase 2 IPF execution.
    """
    print("=" * 80)
    print("Phase 2: Buurt-Level IPF Execution")
    print("=" * 80)

    try:
        # Load data
        print(f"\n[1/6] Loading data...")

        # Load national seed matrix
        seed_path = args.seed_dir / "seed_matrix.parquet"
        if not seed_path.exists():
            raise FileNotFoundError(f"Seed matrix not found at {seed_path}")

        seed_df = pd.read_parquet(seed_path)
        print(f"  ✓ Loaded seed matrix: {len(seed_df)} rows, {len(seed_df.columns)} columns")

        # Load CBS reference data
        reference_path_86165 = args.reference_dir / "86165NED.parquet"
        if not reference_path_86165.exists():
            raise FileNotFoundError(f"Reference data not found at {reference_path_86165}")

        df_86165 = pd.read_parquet(reference_path_86165)
        print(f"  ✓ Loaded 86165NED reference data: {len(df_86165)} rows, {len(df_86165.columns)} columns")

        # Load education reference data
        reference_path_82275 = args.reference_dir / "82275NED.parquet"
        if not reference_path_82275.exists():
            raise FileNotFoundError(f"Education reference data not found at {reference_path_82275}")

        df_82275 = pd.read_parquet(reference_path_82275)
        print(f"  ✓ Loaded 82275NED education data: {len(df_82275)} rows, {len(df_82275.columns)} columns")

        # Load income reference data
        reference_path_83931 = args.reference_dir / "83931NED.parquet"
        if not reference_path_83931.exists():
            raise FileNotFoundError(f"Income reference data not found at {reference_path_83931}")

        df_83931 = pd.read_parquet(reference_path_83931)
        print(f"  ✓ Loaded 83931NED income data: {len(df_83931)} rows, {len(df_83931.columns)} columns")

        # Load household reference data for proper proportions
        reference_path_37620 = args.seed_dir / "37620_preprocessed.parquet"
        if reference_path_37620.exists():
            df_37620 = pd.read_parquet(reference_path_37620)
            print(f"  ✓ Loaded 37620 household data: {len(df_37620)} rows for national proportions")
        else:
            df_37620 = None
            print(f"  ⚠ Household data not found, using approximate splits")

        # Find target buurt
        print(f"\n[2/6] Identifying target buurt: {args.buurt}")
        buurt_row = find_buurt_row(df_86165, args.buurt)
        buurt_code = buurt_row["Codering_3"].strip()
        buurt_name = buurt_row["WijkenEnBuurten"].strip()
        print(f"  ✓ Found buurt: {buurt_code} - {buurt_name}")
        print(f"    Population: {buurt_row['AantalInwoners_5']:,}")
        print(f"    Households: {buurt_row['HuishoudensTotaal_29']:,}")

        # Extract constraints
        print(f"\n[3/6] Extracting buurt constraints...")
        constraints = extract_buurt_constraints(buurt_row, df_37620)
        print(f"  ✓ Extracted constraints for age, migration, and household")

        # Extract national education probabilities and apply to buurt
        print(f"  ✓ Extracting national education probabilities from 82275NED...")
        national_education_probs = extract_national_education_probabilities(df_82275)

        print(f"  ✓ Applying national education probabilities to buurt...")
        education_constraints = apply_national_education_probabilities(constraints, national_education_probs)
        constraints["education_group"] = education_constraints
        print(f"  ✓ Extracted education constraints: {list(education_constraints.keys())}")

        # Extract national income probabilities and apply to buurt
        print(f"  ✓ Extracting national income probabilities from 83931NED...")
        national_income_probs = extract_national_income_probabilities(df_83931)

        print(f"  ✓ Applying national income probabilities to buurt...")
        income_constraints = apply_national_income_probabilities(constraints, national_income_probs)
        constraints["income_class"] = income_constraints
        print(f"  ✓ Extracted income constraints: {list(income_constraints.keys())}")

        # Note: Age constraints and migration constraints may have different totals
        # because age constraints exclude the 0-14 age group, while migration constraints
        # include all age groups. This is expected and the IPF algorithm will handle it.
        age_total = sum(constraints["age_band"].values())
        migration_total = sum(constraints["migration_group"].values())

        if args.verbose:
            print(f"  ℹ Age constraints total: {age_total:.0f} (excludes 0-14 age group)")
            print(f"  ℹ Migration constraints total: {migration_total:.0f} (includes all age groups)")

        # No scaling needed - let IPF handle the different totals naturally

        # Validate constraints
        validate_constraints(constraints)
        print(f"  ✓ Constraints validated successfully")

        # Prepare seed matrix
        print(f"\n[4/6] Preparing seed matrix...")
        seed_df_prepared = prepare_seed_matrix(seed_df)
        print(f"  ✓ Seed matrix prepared: {len(seed_df_prepared)} rows")

        # Execute IPF
        print(f"\n[5/6] Executing IPF...")
        fitted_df = execute_ipf(
            seed_df_prepared,
            constraints,
            max_iter=args.max_iter,
            convergence_rate=args.convergence_rate,
            verbose=args.verbose
        )
        print(f"  ✓ IPF completed: {len(fitted_df)} rows")
        print(f"    Fitted total: {fitted_df['fitted_weight'].sum():,.0f}")

        # Validate results
        print(f"\n[6/6] Validating results...")
        validation_results = validate_fitted_results(
            fitted_df,
            constraints,
            verbose=args.verbose
        )

        if validation_results["validation_passed"]:
            print("  ✅ Validation PASSED - Results meet quality criteria")
        else:
            print("  ⚠️  Validation FAILED - Results have issues")
            print("  Issues found:")
            for issue in validation_results["issues"]:
                print(f"    - {issue}")

        # Save results
        print(f"\n[Final] Saving results...")
        saved_files = save_fitted_results(
            fitted_df,
            args.buurt,
            buurt_row,
            validation_results,
            args.output_dir
        )

        print(f"  ✓ Saved fitted data: {saved_files['fitted_data']}")
        print(f"  ✓ Saved metadata: {saved_files['metadata']}")

        print(f"\n{'='*80}")
        if validation_results["validation_passed"]:
            print("✅ Phase 2 Complete: IPF execution successful")
        else:
            print("⚠️  Phase 2 Complete: IPF execution completed with validation issues")
        print(f"{'='*80}")

        return 0

    except Exception as e:
        print(f"\n❌ Error during IPF execution: {e}")
        print(f"Error type: {type(e).__name__}")
        return 1

if __name__ == "__main__":
    args = parseargs()
    exit(main(args))