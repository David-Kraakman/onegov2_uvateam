import random
import sys
import os

# Add the parent directory to the path to import src modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import networkx as nx
from src.networking._neighborhood import (
    count_households,
    link_neighborhood,
    classify_household,
)


def generate_test_network(num_nodes: int = 100, seed: int = None) -> nx.Graph:
    """
    Generate a test network with isolated nodes and random ages.

    Args:
        num_nodes: Number of nodes to create
        seed: Random seed for reproducibility

    Returns:
        NetworkX graph with nodes having random age attributes
    """
    if seed is not None:
        random.seed(seed)

    g = nx.Graph()

    # Add nodes with random ages (0-100)
    for i in range(num_nodes):
        age = random.randint(0, 100)
        g.add_node(i, age=age)

    return g


def test_single_node_island():
    """Test classification of single isolated nodes."""
    print("\n=== Test: Single Node Islands ===")
    g = generate_test_network(num_nodes=100000, seed=42)

    data = count_households(g)

    print(f"Total households: {data.households}")
    print(f"Single adults: {data.single}")
    print(f"Together households: {data.together}")
    print(f"Households with kids: {data.kids}")
    print(f"Problem nodes: {data.problem_nodes}")

    link_neighborhood(g)


if __name__ == "__main__":
    test_single_node_island()
