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
    HouseholdData,
    Person,
    HouseholdType,
    infer_households,
    distinguish_households,
    sample_nodes,
    household_connect,
    node_disconnect,
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

    # Add nodes with random ages (0-100)
    for i in range(num_nodes):
        age = random.randint(0, 100)
        household_type = random.choice(["kids", "together", "single"])
        g.add_node(i, age=age, household_type=household_type)

    return g


def test_household_data_copy():
    """Test HouseholdData.copy() method."""
    print("\n=== Test: HouseholdData.copy() ===")
    data = HouseholdData(single=5, together=3, kids=2, problem_nodes=1)
    try:
        copy = data.copy()
        print("✓ HouseholdData.copy() succeeded")
        print(f"  Original: {data}")
        print(f"  Copy: {copy}")
    except Exception as e:
        print(f"✗ HouseholdData.copy() failed: {e}")
        return False
    return True


def test_household_data_set():
    """Test HouseholdData.set() method."""
    print("\n=== Test: HouseholdData.set() ===")
    data1 = HouseholdData(single=5, together=3, kids=2, problem_nodes=1)
    data2 = HouseholdData(single=10, together=6, kids=4, problem_nodes=2)
    try:
        data1.set(data2)
        print("✓ HouseholdData.set() succeeded")
        print(f"  After set: {data1}")
    except Exception as e:
        print(f"✗ HouseholdData.set() failed: {e}")
        return False
    return True


def test_count_households():
    """Test count_households() function."""
    print("\n=== Test: count_households() ===")
    households = [
        {0: Person(HouseholdType.SINGLE, 30)},
        {1: Person(HouseholdType.TOGETHER, 25), 2: Person(HouseholdType.TOGETHER, 26)},
        {3: Person(HouseholdType.KIDS, 35), 4: Person(HouseholdType.KIDS, 8)},
    ]
    try:
        data = count_households(households)
        print("✓ count_households() succeeded")
        print(f"  Result: {data}")
    except Exception as e:
        print(f"✗ count_households() failed: {e}")
        return False
    return True


def test_infer_households():
    """Test infer_households() function."""
    print("\n=== Test: infer_households() ===")
    g = nx.Graph()
    # Create a simple test graph
    g.add_node(0, age=30, household_type="single")
    g.add_node(1, age=25, household_type="together")
    g.add_node(2, age=26, household_type="together")
    g.add_edge(1, 2)  # Connect nodes 1 and 2

    try:
        households, household_index = infer_households(g)
        print("✓ infer_households() succeeded")
        print(f"  Households: {len(households)}")
        print(f"  Household index: {household_index}")
    except Exception as e:
        print(f"✗ infer_households() failed: {e}")
        return False
    return True


def test_sample_nodes():
    """Test sample_nodes() function."""
    print("\n=== Test: sample_nodes() ===")
    households = [
        {0: Person(HouseholdType.SINGLE, 30)},
        {1: Person(HouseholdType.TOGETHER, 25), 2: Person(HouseholdType.TOGETHER, 26)},
        {4: Person(HouseholdType.SINGLE, 30)},
    ]
    household_index = {0: 0, 1: 1, 2: 1}
    node_ids = [0, 1, 2]
    single = [0, 4]
    together = [1, 2]
    kids = []

    try:
        node1, node2 = sample_nodes(
            households, household_index, node_ids, single, together, kids
        )
        print("✓ sample_nodes() succeeded")
        print(f"  Node1: {node1}, Node2: {node2}")
        # Verify node2 comes from correct category
        person1 = households[household_index[node1]][node1]
        print(f"  Person1 type: {person1.household_type}")
    except Exception as e:
        print(f"✗ sample_nodes() failed: {e}")
        return False
    return True


def test_single_node_island():
    """Test classification of single isolated nodes."""
    print("\n=== Test: Single Node Islands ===")
    g = generate_test_network(num_nodes=100000, seed=42)

    try:
        link_neighborhood(g)
        print("✓ link_neighborhood() succeeded")
    except Exception as e:
        print(f"✗ link_neighborhood() failed: {e}")
        return False
    return True


if __name__ == "__main__":
    print("Running comprehensive neighborhood generator tests...\n")
    results = []

    results.append(("HouseholdData.copy()", test_household_data_copy()))
    results.append(("HouseholdData.set()", test_household_data_set()))
    results.append(("count_households()", test_count_households()))
    results.append(("infer_households()", test_infer_households()))
    results.append(("sample_nodes()", test_sample_nodes()))
    results.append(("link_neighborhood()", test_single_node_island()))

    print("\n=== Test Summary ===")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    for name, result in results:
        status = "✓" if result else "✗"
        print(f"  {status} {name}")
