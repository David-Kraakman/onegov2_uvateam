import random
import sys
import os

# Add the parent directory to the path to import src modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import networkx as nx
from src.networking._household import (
    link_household,
    HouseholdData,
    infer_households,
)


def generate_test_network(num_nodes: int = 100, seed: int | None = None) -> nx.Graph:
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

    living_situations = [
        "ThuiswonendKind",
        "PartnerInNietGehuwdPaarZonderKinderen",
        "PartnerInNietGehuwdPaarMetKinderen",
        "PartnerInGehuwdPaarZonderKinderen",
        "PartnerInGehuwdPaarMetKinderen",
        "OuderInEenouderhuishouden",
        "Alleenstaand",
        "OverigLidHuishouden",
    ]
    children = 0
    # Add nodes with random ages (0-100)
    for i in range(num_nodes):
        age = random.randint(0, 100)
        living_situation = random.choice(living_situations)
        if living_situation == "ThuiswonendKind":
            children += 1
        g.add_node(i, age=age, living_situation=living_situation)

    print(f"Kids: {children}")

    return g


def test_single_node_island():
    """Test classification of single isolated nodes."""
    print("\n=== Test: Single Node Islands ===")
    g = generate_test_network(num_nodes=50000, seed=42)

    try:
        link_household(g)
        print("✓ link_neighborhood() succeeded")
    except Exception as e:
        print(f"✗ link_neighborhood() failed: {e}")
        return False
    return True


if __name__ == "__main__":
    print("Running comprehensive neighborhood generator tests...\n")
    results = []

    results.append(("link_neighborhood()", test_single_node_island()))

    print("\n=== Test Summary ===")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    for name, result in results:
        status = "✓" if result else "✗"
        print(f"  {status} {name}")
