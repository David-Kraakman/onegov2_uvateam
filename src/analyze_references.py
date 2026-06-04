"""Inspect cached CBS reference tables for phase-1 seed preparation.

The script reads parquet files from ``data/reference`` and reports:
- row and column counts,
- raw column names,
- likely geography / category / measure columns,
- and a short note about the table shape.

It is intentionally heuristic: the goal is to help the phase-1 seed builder
identify which raw columns can be used without hard-coding a full catalogue.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


TABLE_HINTS: dict[str, dict[str, list[str] | str]] = {
	"86165NED": {
		"note": "Buurt-level anchor table. Use the national rows for age, household, migration, income and housing margins.",
		"usable_columns": [
			"WijkenEnBuurten",
			"SoortRegio_2",
			"IndelingswijzigingGemeenteWijkBuurt_4",
			"AantalInwoners_5",
			"k_0Tot15Jaar_8",
			"k_15Tot25Jaar_9",
			"k_25Tot45Jaar_10",
			"k_45Tot65Jaar_11",
			"k_65JaarOfOuder_12",
			"HuishoudensTotaal_29",
			"Eenpersoonshuishoudens_30",
			"HuishoudensZonderKinderen_31",
			"HuishoudensMetKinderen_32",
			"GemiddeldeHuishoudensgrootte_33",
			"Nederland_17",
			"EuropaExclusiefNederland_18",
			"BuitenEuropa_19",
			"GemiddeldInkomenPerInwoner_78",
			"GemiddeldInkomenPerInkomensontvanger_77",
			"GemGestandaardiseerdInkomen_83",
			"k_40HuishoudensMetLaagsteInkomen_84",
			"k_20HuishoudensMetHoogsteInkomen_85",
			"HuurwoningenTotaal_48",
			"Koopwoningen_47",
			"PercentageEengezinswoning_40",
			"PercentageMeergezinswoning_45",
			"WerkzameBeroepsbevolking_70",
			"Nettoarbeidsparticipatie_71",
			"WerknemersMetVasteArbeidsr_73",
			"WerknemersMetFlexibeleArbe_74",
			"AantalPubliekeLaadpalen_61",
			"PersonenautoSTotaal_104",
		],
	},
	"83931NED": {
		"note": "Income microdistribution table. Use the national rows and keep the income class labels.",
		"usable_columns": [
			"RegioS",
			"Inkomensbegrippen",
			"Inkomensklassen",
			"Geslacht",
			"KenmerkenVanPersonen",
			"Perioden",
			"PersonenMetInkomen_1",
			"GemiddeldInkomen_2",
			"MediaanInkomen_3",
		],
	},
	"37620": {
		"note": "Household composition joint table. Keep the age and household-type fields.",
		"usable_columns": [
			"Geslacht",
			"Leeftijd",
			"Perioden",
			"TotaalPersonenInHuishoudens_1",
			"TotaalPersonenInParticuliereHuish_2",
			"ThuiswonendKind_3",
			"Alleenstaand_4",
			"TotaalSamenwonendePersonen_5",
			"PartnerInNietGehuwdPaarZonderKi_6",
			"PartnerInGehuwdPaarZonderKinderen_7",
			"PartnerInNietGehuwdPaarMetKinderen_8",
			"PartnerInGehuwdPaarMetKinderen_9",
			"OuderInEenouderhuishouden_10",
			"OverigLidHuishouden_11",
			"PersonenInInstitutioneleHuishoudens_12",
		],
	},
	"82275NED": {
		"note": "Correct education/migration table for phase 1. The inspected parquet matches the catalogue-backed education source.",
		"usable_columns": [
			"Geslacht",
			"Leeftijd",
			"Migratieachtergrond",
			"HoogstBehaaldOnderwijsniveau",
			"Perioden",
			"Bevolking_1",
		],
	},
	"82309NED": {
		"note": "Correct labor-participation table for phase 1. Use age + education + labor status margins from this file.",
		"usable_columns": [
			"Geslacht",
			"Leeftijd",
			"HoogstBehaaldOnderwijsniveau",
			"Perioden",
			"BeroepsEnNietBeroepsbevolking_1",
			"Beroepsbevolking_2",
			"WerkzameBeroepsbevolking_3",
			"Werknemer_4",
			"WerknemerMetVasteArbeidsrelatie_5",
			"WerknemerMetFlexibeleArbeidsrelatie_6",
			"Zelfstandige_7",
			"WerklozeBeroepsbevolking_20",
			"Werkloosheidspercentage_21",
			"BrutoArbeidsparticipatie_23",
			"NettoArbeidsparticipatie_24",
		],
	},
	"85321NED": {
		"note": "Does not match the phase-1 education/employment source described in the pipeline. Treat as out-of-scope for seed preparation unless a later phase explicitly needs victimization data.",
		"usable_columns": [
			"Marges",
			"Persoonskenmerken",
			"Perioden",
			"Totaal_2",
			"OpWerk_30",
			"AangifteBijPolitieTotaal_843",
		],
	},
}

DEFAULT_KEYWORDS = {
	"geography": ("regio", "wijk", "buurt", "gebied", "gemeente", "provincie", "period"),
	"age": ("leeftijd", "age"),
	"education": ("onderwijs", "opleiding", "educ"),
	"employment": ("arbeid", "baan", "werk", "particip", "employment"),
	"migration": ("migratie", "herkomst", "background"),
	"income": ("inkomen", "income"),
	"household": ("huishoud", "household"),
	"measure": ("totaal", "aantal", "persons", "personen", "waarde", "count"),
}


def _find_matches(columns: list[str], keywords: tuple[str, ...]) -> list[str]:
	lowered = [column.lower() for column in columns]
	matches = [column for column, lower in zip(columns, lowered) if any(keyword in lower for keyword in keywords)]
	return matches


def _inspect_table(path: Path) -> dict[str, object]:
	frame = pd.read_parquet(path)
	table_id = path.stem.split("_")[0]
	hints = TABLE_HINTS.get(table_id, {})
	columns = [str(column) for column in frame.columns]

	if "usable_columns" in hints:
		useful = [column for column in hints["usable_columns"] if column in columns]
		geography = _find_matches(useful, DEFAULT_KEYWORDS["geography"])
		age = _find_matches(useful, DEFAULT_KEYWORDS["age"])
		education = _find_matches(useful, DEFAULT_KEYWORDS["education"])
		employment = _find_matches(useful, DEFAULT_KEYWORDS["employment"])
		migration = _find_matches(useful, DEFAULT_KEYWORDS["migration"])
		income = _find_matches(useful, DEFAULT_KEYWORDS["income"])
		household = _find_matches(useful, DEFAULT_KEYWORDS["household"])
		measure = [column for column in useful if column not in geography + age + education + employment + migration + income + household]
	else:
		geography = hints.get("geography", []) + _find_matches(columns, DEFAULT_KEYWORDS["geography"])
		measure = hints.get("measure", []) + _find_matches(columns, DEFAULT_KEYWORDS["measure"])
		age = _find_matches(columns, DEFAULT_KEYWORDS["age"])
		education = _find_matches(columns, DEFAULT_KEYWORDS["education"])
		employment = _find_matches(columns, DEFAULT_KEYWORDS["employment"])
		migration = _find_matches(columns, DEFAULT_KEYWORDS["migration"])
		income = _find_matches(columns, DEFAULT_KEYWORDS["income"])
		household = _find_matches(columns, DEFAULT_KEYWORDS["household"])

		useful = []
		for group in (geography, age, education, employment, migration, income, household, measure):
			for column in group:
				if column not in useful and column in columns:
					useful.append(column)

	return {
		"table_id": table_id,
		"rows": int(len(frame)),
		"columns": int(len(columns)),
		"note": hints.get("note", ""),
		"raw_columns": columns,
		"likely_useful_columns": useful,
		"column_groups": {
			"geography": geography,
			"age": age,
			"education": education,
			"employment": employment,
			"migration": migration,
			"income": income,
			"household": household,
			"measure": measure,
		},
	}


def main() -> None:
	parser = argparse.ArgumentParser()
	parser.add_argument(
		"--reference-dir",
		default=Path("data") / "reference",
		type=Path,
		help="Directory containing CBS parquet reference tables.",
	)
	args = parser.parse_args()

	reference_dir: Path = args.reference_dir
	if not reference_dir.exists():
		raise SystemExit(f"Reference directory not found: {reference_dir}")

	parquet_files = sorted(reference_dir.glob("*.parquet"))
	if not parquet_files:
		raise SystemExit(f"No parquet files found in {reference_dir}")

	for path in parquet_files:
		info = _inspect_table(path)
		print(f"[{info['table_id']}] {path.name}")
		print(f"  rows: {info['rows']}  columns: {info['columns']}")
		print(f"  likely useful columns: {', '.join(info['likely_useful_columns']) if info['likely_useful_columns'] else 'none detected'}")
		for group_name, values in info["column_groups"].items():
			if values:
				print(f"  {group_name}: {', '.join(values)}")
		print()


if __name__ == "__main__":
	main()
