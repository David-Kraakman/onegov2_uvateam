import argparse
import os

from ipfn import ipfn
import numpy as np
import pandas as pd


def parseargs() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data_dir",
        type=str,
        required=True,
        help="Directory containing the input dataframes for IPF"
    ),
    parser.add_argument(
        "--buurt", 
        type=str,
        required=True,
        help="CBS ID of buurt"
    )
    return parser.parse_args()

def main(args: argparse.Namespace) -> None:
    pass

if __name__ == "__main__":
    args = parseargs()
    main(args)