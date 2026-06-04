import networkx as nx
import pandas as pd
from pathlib import Path
import argparse

from _household import link_households
from _neighborhood import link_neighborhood


def read_dataframe(file_path: str):
    path = Path(file_path)

    # Validate file exists
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Validate it's a CSV file
    if path.suffix.lower() != ".csv":
        raise ValueError(f"File must be a CSV file, got: {path.suffix}")

    # Read the dataframe
    return pd.read_csv(file_path)


def create_nodes_from_csv(graph: nx.Graph, df: pd.DataFrame, name_column: str) -> None:
    """
    Read a CSV file and create nodes for each row, with columns as attributes.

    Args:
        graph: NetworkX graph object to add nodes to
        file_path: Path to the CSV file
        name_column: Column name to use as node identifiers

    Raises:
        ValueError: If file_path is not a CSV file
        FileNotFoundError: If file does not exist
    """

    # Create nodes from dataframe
    for _, row in df.iterrows():
        node_name = row[name_column]
        # Create attributes dict from all columns except the name column
        attributes = {col: row[col] for col in df.columns if col != name_column}
        graph.add_node(node_name, **attributes)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Read a CSV file and create network nodes from rows"
    )
    parser.add_argument("file_path", type=str, help="Path to the CSV file")

    return parser.parse_args()


def generate_network(df: pd.DataFrame) -> nx.Graph:
    g = nx.Graph()

    # Generate edges for households
    link_households(g)

    # Generate edges for neighborhood
    link_neighborhood(g)

    return g


def main() -> None:
    args = parse_args()

    df = read_dataframe(args.file_path)
    generate_network(df)


if __name__ == "__main__":
    main()
