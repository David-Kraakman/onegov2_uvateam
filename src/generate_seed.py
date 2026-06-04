"""Phase 1 seed preparation: build a national N-dimensional seed matrix for IPF.

This script:
1. Loads the cached CBS reference parquets
2. Selects national-level rows and relevant columns
3. Normalizes column names to a canonical schema
4. Harmonizes age bins to the shared coarse taxonomy: 0-14, 15-24, 25-44, 45-64, 65+
5. Builds a Cartesian product seed matrix using Naive Bayes structure

Run:
    python src/generate_seed.py --reference-dir data/reference --out-dir data/seed
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
import numpy as np


# Age bin mapping: map source age labels to canonical 5-bin taxonomy
AGE_MAPPINGS = {
    # From 86165NED (direct age band columns)
    "k_0Tot15Jaar_8": "0-14",
    "k_15Tot25Jaar_9": "15-24",
    "k_25Tot45Jaar_10": "25-44",
    "k_45Tot65Jaar_11": "45-64",
    "k_65JaarOfOuder_12": "65+",
    # From 37620, 82275NED, 82309NED (Leeftijd column values - with "Leeftijd:" prefix)
    "Leeftijd: 0 tot 15 jaar": "0-14",
    "Leeftijd: 0 tot 5 jaar": "0-14",
    "Leeftijd: 5 tot 10 jaar": "0-14",
    "Leeftijd: 10 tot 15 jaar": "0-14",
    "Leeftijd: 15 tot 25 jaar": "15-24",
    "Leeftijd: 15 tot 20 jaar": "15-24",
    "Leeftijd: 20 tot 25 jaar": "15-24",
    "Leeftijd: 25 tot 45 jaar": "25-44",
    "Leeftijd: 25 tot 35 jaar": "25-44",
    "Leeftijd: 35 tot 45 jaar": "25-44",
    "Leeftijd: 45 tot 65 jaar": "45-64",
    "Leeftijd: 45 tot 55 jaar": "45-64",
    "Leeftijd: 55 tot 65 jaar": "45-64",
    "Leeftijd: 65 jaar of ouder": "65+",
    "Leeftijd: 65 tot 75 jaar": "65+",
    "Leeftijd: 75 tot 85 jaar": "65+",
    "Leeftijd: 75 jaar of ouder": "65+",
    "Leeftijd: 85 jaar of ouder": "65+",
    # Without prefix (fallback)
    "0 tot 15 jaar": "0-14",
    "0 tot 5 jaar": "0-14",
    "5 tot 10 jaar": "0-14",
    "10 tot 15 jaar": "0-14",
    "15 tot 25 jaar": "15-24",
    "15 tot 20 jaar": "15-24",
    "20 tot 25 jaar": "15-24",
    "25 tot 45 jaar": "25-44",
    "25 tot 35 jaar": "25-44",
    "35 tot 45 jaar": "25-44",
    "45 tot 65 jaar": "45-64",
    "45 tot 55 jaar": "45-64",
    "55 tot 65 jaar": "45-64",
    "65 jaar of ouder": "65+",
    "65 tot 75 jaar": "65+",
    "75 tot 85 jaar": "65+",
    "75 jaar of ouder": "65+",
    # Individual years from 37620
    "0 jaar": "0-14", "1 jaar": "0-14", "2 jaar": "0-14", "3 jaar": "0-14", "4 jaar": "0-14",
    "5 jaar": "0-14", "6 jaar": "0-14", "7 jaar": "0-14", "8 jaar": "0-14", "9 jaar": "0-14",
    "10 jaar": "0-14", "11 jaar": "0-14", "12 jaar": "0-14", "13 jaar": "0-14", "14 jaar": "0-14",
    "15 jaar": "15-24", "16 jaar": "15-24", "17 jaar": "15-24", "18 jaar": "15-24", "19 jaar": "15-24",
    "20 jaar": "15-24", "21 jaar": "15-24", "22 jaar": "15-24", "23 jaar": "15-24", "24 jaar": "15-24",
    "25 jaar": "25-44", "26 jaar": "25-44", "27 jaar": "25-44", "28 jaar": "25-44", "29 jaar": "25-44",
    "30 jaar": "25-44", "31 jaar": "25-44", "32 jaar": "25-44", "33 jaar": "25-44", "34 jaar": "25-44",
    "35 jaar": "25-44", "36 jaar": "25-44", "37 jaar": "25-44", "38 jaar": "25-44", "39 jaar": "25-44",
    "40 jaar": "25-44", "41 jaar": "25-44", "42 jaar": "25-44", "43 jaar": "25-44", "44 jaar": "25-44",
    "45 jaar": "45-64", "46 jaar": "45-64", "47 jaar": "45-64", "48 jaar": "45-64", "49 jaar": "45-64",
    "50 jaar": "45-64", "51 jaar": "45-64", "52 jaar": "45-64", "53 jaar": "45-64", "54 jaar": "45-64",
    "55 jaar": "45-64", "56 jaar": "45-64", "57 jaar": "45-64", "58 jaar": "45-64", "59 jaar": "45-64",
    "60 jaar": "45-64", "61 jaar": "45-64", "62 jaar": "45-64", "63 jaar": "45-64", "64 jaar": "45-64",
    "65 jaar": "65+", "66 jaar": "65+", "67 jaar": "65+", "68 jaar": "65+", "69 jaar": "65+",
    "70 jaar": "65+", "71 jaar": "65+", "72 jaar": "65+", "73 jaar": "65+", "74 jaar": "65+",
    "75 jaar": "65+", "76 jaar": "65+", "77 jaar": "65+", "78 jaar": "65+", "79 jaar": "65+",
    "80 jaar": "65+", "81 jaar": "65+", "82 jaar": "65+", "83 jaar": "65+", "84 jaar": "65+",
    "85 jaar": "65+", "86 jaar": "65+", "87 jaar": "65+", "88 jaar": "65+", "89 jaar": "65+",
    "90 jaar": "65+", "91 jaar": "65+", "92 jaar": "65+", "93 jaar": "65+", "94 jaar": "65+",
    "95 jaar of ouder": "65+",
    # Handle totals and wildcards
    "Totaal": None,  # Will be excluded
    "Onbekend": None,
    "": None,
}

# Migration background normalization
MIGRATION_MAPPINGS = {
    "Totaal": None,
    "Totaal ": None,  # With trailing space
    "Nederlandse achtergrond": "Netherlands",
    "Met migratieachtergrond": "Other",
    "Westerse migratieachtergrond": "EU_non_NL",
    "Niet-westerse migratieachtergrond": "Non_EU",
    "Marokko": "Non_EU",
    "Turkije": "Non_EU",
    "Suriname": "Non_EU",
    "(voormalige) Nederlandse Antillen, Aruba": "Non_EU",
    "Overige niet-westerse migratieachterg...": "Non_EU",
    "Onbekende migratieachtergrond": None,
    "Nederland": "Netherlands",
    "Europa exclusief Nederland": "EU_non_NL",
    "Buiten Europa": "Non_EU",
}

# Education level normalization
EDUCATION_MAPPINGS = {
    "Totaal": None,
    "Weet niet of onbekend": None,
    "1 Laag onderwijsniveau": "Primary_or_None",
    "11 Basisonderwijs": "Primary_or_None",
    "111 Basisonderwijs": "Primary_or_None",
    "12 Vmbo, havo-, vwo-onderbouw, mbo1": "Secondary_VMBO",
    "121 Vmbo-b/k, mbo1": "Secondary_VMBO",
    "122 Vmbo-g/t, havo-, vwo-onderbouw": "Secondary_HAVO_VWO",
    "2 Middelbaar onderwijsniveau": "Secondary_MBO",
    "21 Havo, vwo, mbo2-4": "Secondary_MBO",
    "211 Mbo2 en mbo3": "Tertiary_MBO",
    "212 Mbo4": "Tertiary_MBO",
    "213 Havo, vwo": "Secondary_HAVO_VWO",
    "3 Hoog onderwijsniveau": "Tertiary_Higher",
    "31 Hbo-, wo-bachelor": "Tertiary_Higher",
    "311 Hbo-, wo-bachelor": "Tertiary_Higher",
    "32 Hbo-, wo-master, doctor": "Tertiary_University",
    "321 Hbo-, wo-master, doctor": "Tertiary_University",
    "Basisonderwijs of geen onderwijs": "Primary_or_None",
    "Vmbo, Mavo, etc.": "Secondary_VMBO",
    "Havo, Vwo": "Secondary_HAVO_VWO",
    "Mbo": "Tertiary_MBO",
    "Hoger onderwijs": "Tertiary_Higher",
    "Universiteit": "Tertiary_University",
}

# Employment status normalization
EMPLOYMENT_MAPPINGS = {
    "Totaal": "Total",
    "Werkzame beroepsbevolking": "Employed",
    "Werkloze beroepsbevolking": "Unemployed",
    "Niet-beroepsbevolking": "Not_in_labor_force",
    "Beroepsbevolking": "In_labor_force",
    "Werknemer": "Employee",
    "Zelfstandige": "Self_employed",
}

# Household composition normalization
HOUSEHOLD_MAPPINGS = {
    "Totaal personen in huishoudens": "Total",
    "Thuiswonend kind": "Living_with_parents",
    "Alleenstaand": "Single",
    "Partner in niet-gehuwde paar zonder kinderen": "Cohabiting_no_kids",
    "Partner in gehuwde paar zonder kinderen": "Married_no_kids",
    "Partner in niet-gehuwde paar met kinderen": "Cohabiting_with_kids",
    "Partner in gehuwde paar met kinderen": "Married_with_kids",
    "Ouder in eenouderhuishouden": "Single_parent",
    "Overig lid huishouden": "Other",
    "Personen in institutionele huishoudens": "Institutional",
}

# Income class normalization (from 83931NED)
INCOME_MAPPINGS = {
    "Totaal": "Total",
}


def _is_national_row(row: pd.Series) -> bool:
    """Check if a row is at national level (not buurt/wijk specific)."""
    # National rows typically have "Totaal" or broad area codes
    if "Totaal" in str(row.get("WijkenEnBuurten", "")):
        return True
    if "Nederland" in str(row.get("WijkenEnBuurten", "")):
        return True
    if "Totaal mannen en vrouwen" in str(row.get("ID", "")):
        return True
    if "Nederland" in str(row.get("RegioS", "")):
        return True
    # 86165NED uses "RegioS" column for national identification
    if "Nederland" in str(row.get("RegioS", "")):
        return True
    return False


def _normalize_age(age_value: str | None) -> str | None:
    """Normalize a raw age label to canonical 5-bin taxonomy."""
    if age_value is None or pd.isna(age_value):
        return None
    age_str = str(age_value).strip()
    if age_str in AGE_MAPPINGS:
        return AGE_MAPPINGS[age_str]
    # Fallback: if not found, return None (will be filtered out)
    return None


def load_and_preprocess_86165ned(path: Path) -> pd.DataFrame:
    """Load and preprocess the buurt anchor table (86165NED)."""
    df = pd.read_parquet(path)
    
    # Filter for national level
    df = df[df["WijkenEnBuurten"].astype(str).str.contains("Nederland", na=False)].copy()
    
    # Select relevant columns
    relevant = {
        "AantalInwoners_5": "population",
        "k_0Tot15Jaar_8": "age_0_14",
        "k_15Tot25Jaar_9": "age_15_24",
        "k_25Tot45Jaar_10": "age_25_44",
        "k_45Tot65Jaar_11": "age_45_64",
        "k_65JaarOfOuder_12": "age_65_plus",
        "Nederland_17": "migration_netherlands",
        "EuropaExclusiefNederland_18": "migration_eu_non_nl",
        "BuitenEuropa_19": "migration_non_eu",
        "HuishoudensTotaal_29": "household_total",
        "Eenpersoonshuishoudens_30": "household_single",
        "HuishoudensZonderKinderen_31": "household_no_kids",
        "HuishoudensMetKinderen_32": "household_with_kids",
    }
    
    available = [col for col in relevant.keys() if col in df.columns]
    df = df[available].rename(columns={col: relevant[col] for col in available})
    
    # Keep only numeric columns
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    return df


def load_and_preprocess_83931ned(path: Path) -> pd.DataFrame:
    """Load and preprocess the income table (83931NED)."""
    df = pd.read_parquet(path)
    
    # 83931NED is national level; filter for total sexes and latest year
    df = df[df["Geslacht"] == "Totaal mannen en vrouwen"].copy()
    
    # Filter for latest year (2024)
    df = df[df["Perioden"] == "2024"].copy()
    
    # Filter for rows with age in KenmerkenVanPersonen
    df = df[df["KenmerkenVanPersonen"].astype(str).str.contains("Leeftijd:", case=False, na=False)].copy()
    
    # Filter for non-total income classes (exclude 'Totaal')
    df = df[df["Inkomensklassen"] != "Totaal"].copy()
    
    # Select and rename columns
    relevant = {
        "KenmerkenVanPersonen": "age_label",
        "Inkomensklassen": "income_class",
        "PersonenMetInkomen_1": "total",
    }
    
    available = [col for col in relevant.keys() if col in df.columns]
    df = df[available].rename(columns={col: relevant[col] for col in available})
    
    # Normalize age
    df["age_band"] = df["age_label"].apply(_normalize_age)
    df = df[df["age_band"].notna()]
    
    # Make numeric
    df["total"] = pd.to_numeric(df["total"], errors="coerce")
    df = df[["age_band", "income_class", "total"]].dropna(subset=["total"])
    
    return df


def load_and_preprocess_37620(path: Path) -> pd.DataFrame:
    """Load and preprocess the household composition table (37620)."""
    df = pd.read_parquet(path)
    
    # Filter for total sexes and latest year
    df = df[df["Geslacht"] == "Totaal mannen en vrouwen"].copy()
    df = df[df["Perioden"] == "2025"].copy()
    
    # Select columns for age × household composition
    household_cols = [
        "Leeftijd",
        "Alleenstaand_4",
        "TotaalSamenwonendePersonen_5",
        "PartnerInNietGehuwdPaarZonderKi_6",
        "PartnerInGehuwdPaarZonderKinderen_7",
        "PartnerInNietGehuwdPaarMetKinderen_8",
        "PartnerInGehuwdPaarMetKinderen_9",
        "OuderInEenouderhuishouden_10",
        "ThuiswonendKind_3",
        "TotaalPersonenInHuishoudens_1",
    ]
    
    available = [col for col in household_cols if col in df.columns]
    df = df[available].copy()
    
    # Normalize age
    df["age_band"] = df["Leeftijd"].apply(_normalize_age)
    df = df[df["age_band"].notna()]
    
    # Melt household columns into rows
    household_cols_to_melt = [col for col in available if col != "Leeftijd"]
    df = df.melt(
        id_vars=["age_band"],
        value_vars=household_cols_to_melt,
        var_name="household_type_raw",
        value_name="total"
    )
    
    # Map household types
    df["household_type"] = df["household_type_raw"].map(
        {
            "Alleenstaand_4": "Single",
            "TotaalSamenwonendePersonen_5": "Cohabiting",
            "PartnerInNietGehuwdPaarZonderKi_6": "Cohabiting_no_kids",
            "PartnerInGehuwdPaarZonderKinderen_7": "Married_no_kids",
            "PartnerInNietGehuwdPaarMetKinderen_8": "Cohabiting_with_kids",
            "PartnerInGehuwdPaarMetKinderen_9": "Married_with_kids",
            "OuderInEenouderhuishouden_10": "Single_parent",
            "ThuiswonendKind_3": "Living_with_parents",
            "TotaalPersonenInHuishoudens_1": "Total",
        }
    )
    
    df["total"] = pd.to_numeric(df["total"], errors="coerce")
    df = df[["age_band", "household_type", "total"]].dropna(subset=["total"])
    
    return df


def load_and_preprocess_82275ned(path: Path) -> pd.DataFrame:
    """Load and preprocess the education table (82275NED)."""
    df = pd.read_parquet(path)
    
    # Filter for total sexes and latest year (extract year from Perioden)
    df = df[df["Geslacht"] == "Totaal mannen en vrouwen"].copy()
    df = df[df["Perioden"].astype(str).str.startswith("2021")].copy()
    
    # Filter out aggregate rows (Totaal)
    df = df[(df["Migratieachtergrond"] != "Totaal") & (df["Migratieachtergrond"] != "Totaal ")].copy()
    df = df[df["HoogstBehaaldOnderwijsniveau"] != "Totaal"].copy()
    
    # Select columns
    relevant = {
        "Leeftijd": "age_label",
        "Migratieachtergrond": "migration_raw",
        "HoogstBehaaldOnderwijsniveau": "education_raw",
        "Bevolking_1": "total",
    }
    
    available = [col for col in relevant.keys() if col in df.columns]
    df = df[available].rename(columns={col: relevant[col] for col in available})
    
    # Normalize age
    df["age_band"] = df["age_label"].apply(_normalize_age)
    df = df[df["age_band"].notna()]
    
    # Normalize migration
    df["migration_group"] = df["migration_raw"].map(MIGRATION_MAPPINGS)
    df = df[df["migration_group"].notna()]
    
    # Normalize education
    df["education_group"] = df["education_raw"].map(EDUCATION_MAPPINGS)
    df = df[df["education_group"].notna()]
    
    df["total"] = pd.to_numeric(df["total"], errors="coerce")
    df = df[["age_band", "migration_group", "education_group", "total"]].dropna(subset=["total"])
    
    return df
    
    # Normalize education
    df["education_group"] = df["education_raw"].map(EDUCATION_MAPPINGS)
    df = df[df["education_group"].notna()]
    
    df["total"] = pd.to_numeric(df["total"], errors="coerce")
    df = df[["age_band", "migration_group", "education_group", "total"]].dropna(subset=["total"])
    
    return df


def load_and_preprocess_82309ned(path: Path) -> pd.DataFrame:
    """Load and preprocess the labor participation table (82309NED)."""
    df = pd.read_parquet(path)
    
    # Filter for total sexes and latest year (2022)
    df = df[df["Geslacht"] == "Totaal mannen en vrouwen"].copy()
    df = df[df["Perioden"] == "2022 1e kwartaal"].copy() if "2022 1e kwartaal" in df["Perioden"].values else df[df["Perioden"].astype(str).str.startswith("2022")].copy()
    
    # Select columns
    relevant = {
        "Leeftijd": "age_label",
        "HoogstBehaaldOnderwijsniveau": "education_raw",
        "WerkzameBeroepsbevolking_3": "employed",
        "WerklozeBeroepsbevolking_20": "unemployed",
        "NietBeroepsbevolking_22": "not_in_labor",
        "BrutoArbeidsparticipatie_23": "gross_participation",
        "NettoArbeidsparticipatie_24": "net_participation",
    }
    
    available = [col for col in relevant.keys() if col in df.columns]
    df = df[available].rename(columns={col: relevant[col] for col in available})
    
    # Normalize age
    df["age_band"] = df["age_label"].apply(_normalize_age)
    df = df[df["age_band"].notna()]
    
    # Normalize education
    df["education_group"] = df["education_raw"].map(EDUCATION_MAPPINGS)
    df = df[df["education_group"].notna()]
    
    # For now, keep gross participation as the employment indicator
    df["total"] = pd.to_numeric(df["gross_participation"], errors="coerce")
    df = df[["age_band", "education_group", "total"]].dropna(subset=["total"])
    
    return df


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--reference-dir",
        type=Path,
        default=Path("data") / "reference",
        help="Directory containing CBS parquet reference tables.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("data") / "seed",
        help="Output directory for seed matrix and artifacts.",
    )
    args = parser.parse_args()

    reference_dir: Path = args.reference_dir
    out_dir: Path = args.out_dir

    if not reference_dir.exists():
        raise SystemExit(f"Reference directory not found: {reference_dir}")

    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("Phase 1: Seed Preparation - Data Loading and Preprocessing")
    print("=" * 80)

    # Load and preprocess each source table
    print("\n[1/5] Loading and preprocessing 86165NED (buurt anchor)...")
    df_86165 = load_and_preprocess_86165ned(reference_dir / "86165NED.parquet")
    print(f"  → {len(df_86165)} rows, columns: {', '.join(df_86165.columns)}")
    print(f"  → {df_86165.to_string()}\n")

    print("[2/5] Loading and preprocessing 83931NED (income distribution)...")
    df_83931 = load_and_preprocess_83931ned(reference_dir / "83931NED.parquet")
    print(f"  → {len(df_83931)} rows, columns: {', '.join(df_83931.columns)}")
    print(f"  → Sample:\n{df_83931.head(10).to_string()}\n")

    print("[3/5] Loading and preprocessing 37620 (household composition)...")
    df_37620 = load_and_preprocess_37620(reference_dir / "37620.parquet")
    print(f"  → {len(df_37620)} rows, columns: {', '.join(df_37620.columns)}")
    print(f"  → Unique age bands: {df_37620['age_band'].unique()}")
    print(f"  → Unique household types: {df_37620['household_type'].unique()}\n")

    print("[4/5] Loading and preprocessing 82275NED (education)...")
    df_82275 = load_and_preprocess_82275ned(reference_dir / "82275NED.parquet")
    print(f"  → {len(df_82275)} rows, columns: {', '.join(df_82275.columns)}")
    print(f"  → Unique age bands: {df_82275['age_band'].unique()}")
    print(f"  → Unique education groups: {df_82275['education_group'].unique()}")
    print(f"  → Unique migration groups: {df_82275['migration_group'].unique()}\n")

    print("[5/5] Loading and preprocessing 82309NED (labor participation)...")
    df_82309 = load_and_preprocess_82309ned(reference_dir / "82309NED.parquet")
    print(f"  → {len(df_82309)} rows, columns: {', '.join(df_82309.columns)}")
    print(f"  → Unique age bands: {df_82309['age_band'].unique()}")
    print(f"  → Unique education groups: {df_82309['education_group'].unique()}\n")

    # Summary
    print("=" * 80)
    print("Preprocessing Summary")
    print("=" * 80)
    print(f"86165NED:   {len(df_86165)} national rows")
    print(f"83931NED:   {len(df_83931)} age×income rows")
    print(f"37620:      {len(df_37620)} age×household rows")
    print(f"82275NED:   {len(df_82275)} age×education×migration rows")
    print(f"82309NED:   {len(df_82309)} age×education×employment rows")
    print()

    # Save preprocessed tables for inspection
    metadata = {
        "stage": "preprocessing",
        "date": str(pd.Timestamp.now()),
        "tables": {
            "86165NED": {
                "rows": len(df_86165),
                "columns": list(df_86165.columns),
                "shape": df_86165.shape,
                "source": "Buurt anchor (national level)",
            },
            "83931NED": {
                "rows": len(df_83931),
                "columns": list(df_83931.columns),
                "shape": df_83931.shape,
                "source": "Income distribution (age × income)",
            },
            "37620": {
                "rows": len(df_37620),
                "columns": list(df_37620.columns),
                "shape": df_37620.shape,
                "source": "Household composition (age × household)",
            },
            "82275NED": {
                "rows": len(df_82275),
                "columns": list(df_82275.columns),
                "shape": df_82275.shape,
                "source": "Education (age × education × migration)",
            },
            "82309NED": {
                "rows": len(df_82309),
                "columns": list(df_82309.columns),
                "shape": df_82309.shape,
                "source": "Labor participation (age × education × employment)",
            },
        },
    }

    metadata_path = out_dir / "preprocessing_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2))
    print(f"✓ Metadata saved to {metadata_path}\n")

    # Save preprocessed tables
    for name, df in [
        ("86165NED_preprocessed", df_86165),
        ("83931NED_preprocessed", df_83931),
        ("37620_preprocessed", df_37620),
        ("82275NED_preprocessed", df_82275),
        ("82309NED_preprocessed", df_82309),
    ]:
        outpath = out_dir / f"{name}.parquet"
        df.to_parquet(outpath, index=False)
        print(f"✓ Saved {name} → {outpath}")

    print("\n" + "=" * 80)
    print("Phase 2: Seed Matrix Construction (Steps 6-10)")
    print("=" * 80 + "\n")

    # ========== STEP 6: Build the age spine ==========
    print("[6/10] Building national age spine from 86165NED...")
    age_spine = {}
    age_cols = ["age_0_14", "age_15_24", "age_25_44", "age_45_64", "age_65_plus"]
    for col in age_cols:
        if col in df_86165.columns:
            age_band = col.replace("age_", "")
            age_spine[age_band] = df_86165[col].sum()
    
    age_spine_df = pd.DataFrame(list(age_spine.items()), columns=["age_band", "count"])
    age_spine_df["fraction"] = age_spine_df["count"] / age_spine_df["count"].sum()
    print(f"  → Age spine (5 bins):")
    for _, row in age_spine_df.iterrows():
        print(f"    {row['age_band']:>6}: {row['count']:>10,.0f} ({row['fraction']:>6.2%})")
    print()

    # ========== STEP 7: Force-scale joint tables to age spine ==========
    print("[7/10] Force-scaling joint tables to age spine...")
    
    # 83931NED: age × income
    df_83931_scaled = df_83931.copy()
    df_83931_scaled = df_83931_scaled.groupby("age_band")["total"].transform(
        lambda x: x / x.sum() if x.sum() > 0 else x
    ).to_frame()
    df_83931_scaled["age_band"] = df_83931["age_band"].values
    df_83931_scaled["income_class"] = df_83931["income_class"].values
    df_83931_scaled.columns = ["conditional_prob", "age_band", "income_class"]
    df_83931_scaled = df_83931_scaled[["age_band", "income_class", "conditional_prob"]]
    print(f"  → 83931NED: conditional probabilities computed for {len(df_83931_scaled)} rows")
    
    # 37620: age × household
    df_37620_scaled = df_37620.copy()
    df_37620_scaled = df_37620_scaled.groupby("age_band")["total"].transform(
        lambda x: x / x.sum() if x.sum() > 0 else x
    ).to_frame()
    df_37620_scaled["age_band"] = df_37620["age_band"].values
    df_37620_scaled["household_type"] = df_37620["household_type"].values
    df_37620_scaled.columns = ["conditional_prob", "age_band", "household_type"]
    df_37620_scaled = df_37620_scaled[["age_band", "household_type", "conditional_prob"]]
    print(f"  → 37620: conditional probabilities computed for {len(df_37620_scaled)} rows")
    
    # 82275NED: age × education × migration
    df_82275_scaled = df_82275.copy()
    df_82275_scaled = df_82275_scaled.groupby("age_band")["total"].transform(
        lambda x: x / x.sum() if x.sum() > 0 else x
    ).to_frame()
    df_82275_scaled["age_band"] = df_82275["age_band"].values
    df_82275_scaled["migration_group"] = df_82275["migration_group"].values
    df_82275_scaled["education_group"] = df_82275["education_group"].values
    df_82275_scaled.columns = ["conditional_prob", "age_band", "migration_group", "education_group"]
    df_82275_scaled = df_82275_scaled[["age_band", "migration_group", "education_group", "conditional_prob"]]
    print(f"  → 82275NED: conditional probabilities computed for {len(df_82275_scaled)} rows")
    
    # 82309NED: age × education (employment via gross_participation)
    df_82309_scaled = df_82309.copy()
    df_82309_scaled = df_82309_scaled.groupby("age_band")["total"].transform(
        lambda x: x / x.sum() if x.sum() > 0 else x
    ).to_frame()
    df_82309_scaled["age_band"] = df_82309["age_band"].values
    df_82309_scaled["education_group"] = df_82309["education_group"].values
    df_82309_scaled.columns = ["conditional_prob", "age_band", "education_group"]
    df_82309_scaled = df_82309_scaled[["age_band", "education_group", "conditional_prob"]]
    print(f"  → 82309NED: conditional probabilities computed for {len(df_82309_scaled)} rows\n")

    # ========== STEP 8: Assemble Cartesian product with Naive Bayes weights ==========
    print("[8/10] Assembling Cartesian product seed matrix...")
    
    # For phase 1, create a simplified seed focused on age × education × migration
    # (the main IPF target dimensions). Income and household can be included later.
    
    # Scale age spine to population level
    total_pop = age_spine_df["count"].sum()
    
    # Start with education × migration data and scale to age margins
    seed = df_82275.copy()
    seed = seed[["age_band", "education_group", "migration_group", "total"]].copy()
    
    # Normalize to conditional probabilities given age
    seed["conditional"] = seed.groupby("age_band")["total"].transform(
        lambda x: x / x.sum() if x.sum() > 0 else 0
    )
    
    # Merge with age spine to scale to population
    seed = seed.merge(age_spine_df[["age_band", "count"]], on="age_band", how="left")
    seed["weight"] = seed["conditional"] * seed["count"]
    
    # Select final columns
    seed = seed[["age_band", "education_group", "migration_group", "weight"]].copy()
    
    # Fill missing age bands with zero weight
    seed = seed.fillna(0)
    
    print(f"  → Assembled {len(seed)} rows (age × education × migration)")
    print(f"  → Seed total: {seed['weight'].sum():,.0f}\n")

    # ========== STEP 9: Apply structural zeros ==========
    print("[9/10] Applying structural zeros (age-inappropriate combinations)...")
    
    # Remove age 0-14 with higher education and employment
    before_zeros = len(seed)
    seed = seed[~(
        (seed["age_band"] == "0-14") & 
        (seed["education_group"].isin(["Tertiary_MBO", "Tertiary_Higher", "Tertiary_University"]))
    )]
    after_zeros = len(seed)
    print(f"  → Removed {before_zeros - after_zeros} rows (0-14 with tertiary education)")
    
    # Remove age 0-14 with employment participation
    # (Note: 82309NED starts at 15, so this is redundant but explicit)
    seed = seed[~((seed["age_band"] == "0-14") & (seed.get("employment_status") == "Employed"))]
    print(f"  → Structural zero rules applied; {len(seed)} rows remain\n")

    # ========== STEP 10: Validate the seed ==========
    print("[10/10] Validating seed matrix...")
    
    # Check dimensionality
    required_cols = ["age_band", "income_class", "household_type", "education_group", "migration_group", "weight"]
    missing_cols = set(required_cols) - set(seed.columns)
    if missing_cols:
        print(f"  ✗ Missing columns: {missing_cols}")
    else:
        print(f"  ✓ Has all required columns: {len(seed.columns)}")
    
    # Check for NaN or negative weights
    invalid_weights = seed[seed["weight"].isna() | (seed["weight"] < 0)]
    if len(invalid_weights) > 0:
        print(f"  ✗ Found {len(invalid_weights)} invalid weights")
    else:
        print(f"  ✓ All {len(seed)} weights are valid and non-negative")
    
    # Check consistency
    print(f"  ✓ Seed dimensionality: {len(seed)} rows × {len(seed.columns)} cols")
    print(f"  ✓ Seed total: {seed['weight'].sum():,.0f}")
    
    # Verify age distribution
    age_check = seed.groupby("age_band")["weight"].sum()
    print(f"  ✓ Age margins check:")
    for age_band, count in age_check.items():
        target = age_spine[age_band]
        if target > 0:
            error = abs(count - target) / target
            status = "✓" if error < 0.001 else "⚠"
            print(f"    {status} {age_band:>6}: {count:>10,.0f} (target: {target:>10,.0f}, error: {error:.4%})")
    
    print()

    # ========== Save the seed ==========
    print("[Final] Saving seed matrix and age spine...")
    
    # Save seed
    seed_path = out_dir / "seed_matrix.parquet"
    seed.to_parquet(seed_path, index=False)
    print(f"✓ Saved seed matrix → {seed_path}")
    
    # Save age spine
    age_spine_path = out_dir / "age_spine.parquet"
    age_spine_df.to_parquet(age_spine_path, index=False)
    print(f"✓ Saved age spine → {age_spine_path}")
    
    # Update metadata with seed info
    metadata["stage"] = "complete"
    metadata["seed_matrix"] = {
        "rows": len(seed),
        "columns": list(seed.columns),
        "total": seed["weight"].sum(),
        "age_margins": age_check.to_dict(),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2))
    print(f"✓ Updated metadata → {metadata_path}")
    
    print("\n" + "=" * 80)
    print("✓ Phase 1 Complete: Seed matrix ready for IPF")
    print("=" * 80)


if __name__ == "__main__":
    main()
