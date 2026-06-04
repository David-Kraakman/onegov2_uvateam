import argparse

import ipfn
import numpy as np
import pandas as pd


def argparse() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--buurt", 
        type=str,
        required=True,
        help="CBS ID of buurt"
    )
    parser.add_argument(
        "--contingency_table",
        type=str,
        required=True,
        help="Path to CSV file containing the contingency table seed."
    )
    parser.add_argument(
        "--aggregates",
        type=str,
        required=True,
        help="Path to CSV file containing the row marginals."
    )
    return parser.parse_args()

def main():
    pass

if __name__ == "__main__":

    main()