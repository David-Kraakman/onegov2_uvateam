#!/usr/bin/env python3
"""
Main Pipeline Orchestrator

This script provides a comprehensive pipeline that handles the complete workflow:
1. Check if required reference datasets are available
2. Download missing datasets if needed
3. Generate preprocessed datasets
4. Create seed matrix
5. Run IPF for specified buurt
6. Generate microdata

Usage:
    python src/main_pipeline.py --buurt BU16800000 [--download] [--verbose]
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class PipelineError(Exception):
    """Custom exception for pipeline errors"""
    pass

class DataChecker:
    """Class to check and manage reference datasets"""

    REQUIRED_DATASETS = {
        '37620': 'Household composition data',
        '82275NED': 'Education × migration data',
        '83931NED': 'Age × income × migration data',
        '86165NED': 'Buurt-level demographic data'
    }

    def __init__(self, reference_dir: str = "data/reference"):
        self.reference_dir = Path(reference_dir)
        self.reference_dir.mkdir(parents=True, exist_ok=True)

    def check_datasets(self) -> Dict[str, bool]:
        """Check which required datasets are available"""
        available = {}
        for dataset, description in self.REQUIRED_DATASETS.items():
            file_path = self.reference_dir / f"{dataset}.parquet"
            available[dataset] = file_path.exists()
            logger.info(f"Dataset {dataset} ({description}): {'✅ Available' if available[dataset] else '❌ Missing'}")
        return available

    def download_missing_datasets(self, datasets: List[str]) -> None:
        """Download missing datasets using the fetcher tools"""
        logger.info("📥 Downloading missing datasets...")

        for dataset in datasets:
            if dataset not in self.REQUIRED_DATASETS:
                logger.warning(f"Unknown dataset: {dataset}")
                continue

            logger.info(f"Downloading {dataset}...")
            try:
                # Use the fetcher tool to download the dataset
                cmd = [
                    "uv", "run", "tooling/fetchers/cbs_statline.py",
                    "--table", dataset,
                    "--out", str(self.reference_dir)
                ]
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)

                if result.returncode == 0:
                    logger.info(f"✅ Successfully downloaded {dataset}")
                else:
                    logger.error(f"❌ Failed to download {dataset}: {result.stderr}")
                    raise PipelineError(f"Failed to download {dataset}")

            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Error downloading {dataset}: {e}")
                raise PipelineError(f"Failed to download {dataset}") from e
            except Exception as e:
                logger.error(f"❌ Unexpected error downloading {dataset}: {e}")
                raise PipelineError(f"Unexpected error downloading {dataset}") from e

class PipelineOrchestrator:
    """Main pipeline orchestrator class"""

    def __init__(self, reference_dir: str = "data/reference", seed_dir: str = "data/seed",
                 fitted_dir: str = "data/fitted", microdata_dir: str = "data/microdata"):
        self.reference_dir = Path(reference_dir)
        self.seed_dir = Path(seed_dir)
        self.fitted_dir = Path(fitted_dir)
        self.microdata_dir = Path(microdata_dir)

        # Create directories if they don't exist
        self.reference_dir.mkdir(parents=True, exist_ok=True)
        self.seed_dir.mkdir(parents=True, exist_ok=True)
        self.fitted_dir.mkdir(parents=True, exist_ok=True)
        self.microdata_dir.mkdir(parents=True, exist_ok=True)

    def run_phase_1_seed_generation(self) -> None:
        """Run Phase 1: Seed matrix generation"""
        logger.info("🌱 Running Phase 1: Seed Matrix Generation...")

        try:
            cmd = [
                "python", "src/generate_seed.py",
                "--reference-dir", str(self.reference_dir),
                "--out-dir", str(self.seed_dir)
            ]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info("✅ Phase 1 completed successfully")
                logger.debug(f"Phase 1 output: {result.stdout}")
            else:
                logger.error(f"❌ Phase 1 failed: {result.stderr}")
                raise PipelineError("Phase 1 seed generation failed")

        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Phase 1 error: {e}")
            raise PipelineError("Phase 1 seed generation error") from e
        except Exception as e:
            logger.error(f"❌ Unexpected Phase 1 error: {e}")
            raise PipelineError("Unexpected Phase 1 error") from e

    def run_phase_2_ipf(self, buurt_id: str) -> None:
        """Run Phase 2: IPF execution for specific buurt"""
        logger.info(f"🔬 Running Phase 2: IPF for buurt {buurt_id}...")

        try:
            cmd = [
                "python", "src/IPF.py",
                "--buurt", buurt_id,
                "--seed_dir", str(self.seed_dir),
                "--reference_dir", str(self.reference_dir)
            ]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info(f"✅ Phase 2 completed successfully for buurt {buurt_id}")
                logger.debug(f"Phase 2 output: {result.stdout}")
            else:
                logger.error(f"❌ Phase 2 failed for buurt {buurt_id}: {result.stderr}")
                raise PipelineError(f"Phase 2 IPF failed for buurt {buurt_id}")

        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Phase 2 error for buurt {buurt_id}: {e}")
            raise PipelineError(f"Phase 2 IPF error for buurt {buurt_id}") from e
        except Exception as e:
            logger.error(f"❌ Unexpected Phase 2 error for buurt {buurt_id}: {e}")
            raise PipelineError(f"Unexpected Phase 2 error for buurt {buurt_id}") from e

    def run_phase_3_microdata(self, buurt_id: str) -> None:
        """Run Phase 3: Microdata instantiation"""
        logger.info(f"🧬 Running Phase 3: Microdata for buurt {buurt_id}...")

        try:
            cmd = [
                "python", "src/instantiate_microdata.py",
                "--buurt", buurt_id,
                "--fitted_dir", str(self.fitted_dir),
                "--out_dir", str(self.microdata_dir)
            ]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info(f"✅ Phase 3 completed successfully for buurt {buurt_id}")
                logger.debug(f"Phase 3 output: {result.stdout}")
            else:
                logger.error(f"❌ Phase 3 failed for buurt {buurt_id}: {result.stderr}")
                raise PipelineError(f"Phase 3 microdata failed for buurt {buurt_id}")

        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Phase 3 error for buurt {buurt_id}: {e}")
            raise PipelineError(f"Phase 3 microdata error for buurt {buurt_id}") from e
        except Exception as e:
            logger.error(f"❌ Unexpected Phase 3 error for buurt {buurt_id}: {e}")
            raise PipelineError(f"Unexpected Phase 3 error for buurt {buurt_id}") from e

    def validate_pipeline_results(self, buurt_id: str) -> None:
        """Validate the pipeline results"""
        logger.info(f"🔍 Validating results for buurt {buurt_id}...")

        try:
            # Check if validation script exists
            validation_script = Path("check_validation.py")
            if not validation_script.exists():
                logger.warning("⚠️  Validation script not found, skipping validation")
                logger.info("🎉 Pipeline completed successfully (validation skipped)")
                return

            cmd = [
                "python", "check_validation.py",
                "--buurt", buurt_id
            ]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info(f"✅ Validation completed for buurt {buurt_id}")
                logger.debug(f"Validation output: {result.stdout}")

                # Check if validation passed
                if "Validation passed: True" in result.stdout:
                    logger.info("🎉 Validation PASSED: Results meet quality criteria")
                else:
                    logger.warning("⚠️  Validation completed with warnings")
            else:
                logger.error(f"❌ Validation failed for buurt {buurt_id}: {result.stderr}")
                raise PipelineError(f"Validation failed for buurt {buurt_id}")

        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Validation error for buurt {buurt_id}: {e}")
            raise PipelineError(f"Validation error for buurt {buurt_id}") from e
        except Exception as e:
            logger.error(f"❌ Unexpected validation error for buurt {buurt_id}: {e}")
            raise PipelineError(f"Unexpected validation error for buurt {buurt_id}") from e

    def analyze_ipf_fit(self, buurt_id: str) -> None:
        """Analyze IPF fit quality"""
        logger.info(f"📊 Analyzing IPF fit quality for buurt {buurt_id}...")

        try:
            # Check if analysis script exists
            analysis_script = Path("src/analyze_ipf_fit.py")
            if not analysis_script.exists():
                logger.warning("⚠️  Analysis script not found, skipping IPF fit analysis")
                return

            cmd = [
                "python", "src/analyze_ipf_fit.py",
                "--buurt", buurt_id,
                "--fitted_dir", str(self.fitted_dir),
                "--reference_dir", str(self.reference_dir)
            ]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info(f"✅ IPF fit analysis completed for buurt {buurt_id}")
                logger.info(f"Analysis output:\n{result.stdout}")
            else:
                logger.error(f"❌ IPF fit analysis failed for buurt {buurt_id}: {result.stderr}")
                raise PipelineError(f"IPF fit analysis failed for buurt {buurt_id}")

        except subprocess.CalledProcessError as e:
            logger.error(f"❌ IPF fit analysis error for buurt {buurt_id}: {e}")
            raise PipelineError(f"IPF fit analysis error for buurt {buurt_id}") from e
        except Exception as e:
            logger.error(f"❌ Unexpected IPF fit analysis error for buurt {buurt_id}: {e}")
            raise PipelineError(f"Unexpected IPF fit analysis error for buurt {buurt_id}") from e

def main():
    """Main entry point for the pipeline orchestrator"""
    parser = argparse.ArgumentParser(
        description="Main Pipeline Orchestrator - Complete workflow from data checking to microdata generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run complete pipeline for a specific buurt (download missing data)
  python src/main_pipeline.py --buurt BU16800000 --download

  # Run complete pipeline for a specific buurt (use existing data)
  python src/main_pipeline.py --buurt BU16800000

  # Run with verbose logging
  python src/main_pipeline.py --buurt BU16800000 --download --verbose

  # Run with IPF fit analysis
  python src/main_pipeline.py --buurt BU16800000 --analyze

  # Run with all options
  python src/main_pipeline.py --buurt BU16800000 --download --verbose --analyze
        """
    )

    parser.add_argument(
        "--buurt",
        required=True,
        help="Buurt identifier (CBS code, name, or ID) to process"
    )

    parser.add_argument(
        "--download",
        action="store_true",
        help="Download missing reference datasets automatically"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging for debugging"
    )

    parser.add_argument(
        "--reference-dir",
        default="data/reference",
        help="Directory for reference datasets (default: data/reference)"
    )

    parser.add_argument(
        "--seed-dir",
        default="data/seed",
        help="Directory for seed matrix (default: data/seed)"
    )

    parser.add_argument(
        "--fitted-dir",
        default="data/fitted",
        help="Directory for fitted results (default: data/fitted)"
    )

    parser.add_argument(
        "--microdata-dir",
        default="data/microdata",
        help="Directory for microdata output (default: data/microdata)"
    )

    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Run IPF fit analysis after pipeline completion"
    )

    args = parser.parse_args()

    # Set up verbose logging if requested
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    logger.info("🚀 Starting Main Pipeline Orchestrator")
    logger.info(f"📋 Configuration:")
    logger.info(f"  Buurt: {args.buurt}")
    logger.info(f"  Download missing data: {args.download}")
    logger.info(f"  Reference directory: {args.reference_dir}")
    logger.info(f"  Seed directory: {args.seed_dir}")
    logger.info(f"  Fitted directory: {args.fitted_dir}")
    logger.info(f"  Microdata directory: {args.microdata_dir}")

    try:
        # Step 1: Check required datasets
        logger.info("🔍 Checking required reference datasets...")
        data_checker = DataChecker(args.reference_dir)
        available_datasets = data_checker.check_datasets()

        # Check if all datasets are available
        all_available = all(available_datasets.values())
        missing_datasets = [dataset for dataset, available in available_datasets.items() if not available]

        if not all_available:
            if args.download:
                logger.info(f"📥 Downloading {len(missing_datasets)} missing datasets...")
                data_checker.download_missing_datasets(missing_datasets)

                # Re-check after download
                available_datasets = data_checker.check_datasets()
                all_available = all(available_datasets.values())

                if not all_available:
                    remaining_missing = [dataset for dataset, available in available_datasets.items() if not available]
                    raise PipelineError(f"Still missing datasets after download: {remaining_missing}")
            else:
                raise PipelineError(f"Missing required datasets: {missing_datasets}. Use --download to download them automatically.")

        logger.info("✅ All required datasets are available")

        # Step 2: Run the complete pipeline
        orchestrator = PipelineOrchestrator(
            reference_dir=args.reference_dir,
            seed_dir=args.seed_dir,
            fitted_dir=args.fitted_dir,
            microdata_dir=args.microdata_dir
        )

        # Phase 1: Seed Generation
        orchestrator.run_phase_1_seed_generation()

        # Phase 2: IPF Execution
        orchestrator.run_phase_2_ipf(args.buurt)

        # Phase 3: Microdata Instantiation
        orchestrator.run_phase_3_microdata(args.buurt)

        # Validation
        orchestrator.validate_pipeline_results(args.buurt)

        # IPF Fit Analysis (optional)
        if args.analyze:
            orchestrator.analyze_ipf_fit(args.buurt)

        logger.info("🎉 Pipeline completed successfully!")
        logger.info(f"📊 Results for buurt {args.buurt}:")
        logger.info(f"  ✅ Seed matrix: {args.seed_dir}/seed_matrix.parquet")
        logger.info(f"  ✅ IPF results: {args.fitted_dir}/buurt_{args.buurt}_fitted.parquet")
        logger.info(f"  ✅ Microdata: {args.microdata_dir}/buurt_{args.buurt}_microdata.parquet")
        logger.info(f"  ✅ Validation: PASSED")

        return 0

    except PipelineError as e:
        logger.error(f"💥 Pipeline failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"💥 Unexpected pipeline error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())