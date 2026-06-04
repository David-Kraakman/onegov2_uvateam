from dataclasses import dataclass
from enum import Enum
import networkx as nx
import random
import math

household_size = 2

households_target = 40000
households_single_target = 20000
households_together_target = 10000
households_kids_target = 10000
target_size = 2.5


@dataclass
class HouseholdData:
    households: int
    single: int
    together: int
    kids: int
    problem_nodes: int
    size_diff: float

    def copy(self):
        return HouseholdData(
            self.households,
            self.single,
            self.together,
            self.kids,
            self.problem_nodes,
            self.size_diff,
        )

    def set(self, other):
        self.households = other.households
        self.single = other.single
        self.together = other.together
        self.kids = other.kids
        self.problem_nodes = other.problem_nodes
        self.size_diff = other.size_diff


class HouseholdType(Enum):
    SINGLE = 0
    TOGETHER = 1
    KIDS = 2
    PROBLEM = 3


def classify_household(g: nx.Graph, island) -> HouseholdType:
    # Extract ages of all members in this island
    ages = []
    for node_id in island:
        ages.append(g.nodes[node_id]["age"])

    # Count adults and children
    adults_25_plus = sum(1 for age in ages if age >= 25)
    adults_15_plus = sum(1 for age in ages if age >= 15)
    children = sum(1 for age in ages if age < 15)

    # Categorize household
    if adults_25_plus > 0 and children > 0:
        # Adults (25+) with children
        return HouseholdType.KIDS
    elif adults_15_plus > 1 and children == 0:
        # Multiple adults (25+) without children
        return HouseholdType.TOGETHER
    elif adults_15_plus == 1 and children == 0:
        # Single adult (15+)
        return HouseholdType.SINGLE
    else:
        # Problem nodes: doesn't fit any category
        return HouseholdType.PROBLEM


def remove_household(g: nx.Graph, island, data: HouseholdData):
    data.households -= 1
    household_type = classify_household(g, island)
    data.size_diff -= abs(target_size - len(island)) ** 2
    # Categorize household
    match household_type:
        case HouseholdType.SINGLE:
            data.single -= 1
        case HouseholdType.TOGETHER:
            data.together -= 1
        case HouseholdType.KIDS:
            data.kids -= 1
        case HouseholdType.PROBLEM:
            # Problem nodes: doesn't fit any category
            data.problem_nodes -= len(island)
            data.households += 1


def add_household(g: nx.Graph, island, data: HouseholdData):
    data.households += 1
    household_type = classify_household(g, island)
    data.size_diff += abs(target_size - len(island)) ** 2
    # Categorize household
    match household_type:
        case HouseholdType.SINGLE:
            data.single += 1
        case HouseholdType.TOGETHER:
            data.together += 1
        case HouseholdType.KIDS:
            data.kids += 1
        case HouseholdType.PROBLEM:
            data.households -= 1
            # Problem nodes: doesn't fit any category
            data.problem_nodes += len(island)


def iterate_islands(g: nx.Graph):
    """
    Loop over all islands (connected components) in the network.

    An island is a maximal set of nodes where every node is connected
    to at least one other node via a path. Isolated nodes are single-node islands.

    Yields:
        nx.Graph: A subgraph representing each island/connected component
    """
    connected_components = nx.connected_components(g)
    for island in connected_components:
        yield island


def count_households(g: nx.Graph) -> HouseholdData:
    """
    Count and categorize households based on their composition.

    Categories:
    - single: One adult (age 15+) living alone
    - together: Multiple adults (age 25+) without children
    - kids: Adults (age 25+) with at least one child (age 0-17)
    - problem_nodes: Households that don't fit the above categories

    Args:
        g: NetworkX graph where nodes represent household members

    Returns:
        HouseholdData: Aggregated household statistics and problem nodes
    """
    data = HouseholdData(
        households=0, single=0, together=0, kids=0, problem_nodes=0, size_diff=0
    )

    for island in iterate_islands(g):
        # Get all nodes in this household island
        add_household(g, island, data)

    return data


def calculate_energy(household_data: HouseholdData) -> float:
    """
    Calculate energy as the sum of squared differences from target values.

    Energy = (single_diff)^2 + (together_diff)^2 + (kids_diff)^2 + (problem_nodes)^2

    Args:
        household_data: Current household distribution

    Returns:
        float: Energy value (lower is better)
    """
    single_diff = abs(household_data.single - households_single_target) ** 2
    together_diff = abs(household_data.together - households_together_target) ** 2
    kids_diff = abs(household_data.kids - households_kids_target) ** 2
    problem_diff = household_data.problem_nodes**2
    households_diff = abs(household_data.households - households_target) ** 2

    energy = (
        single_diff
        + together_diff
        + kids_diff
        + problem_diff
        + households_diff
        + household_data.size_diff * 2
    )
    return energy


def metropolis_criterion(
    new_data: HouseholdData, old_data: HouseholdData, temperature: float
) -> bool:
    """
    Metropolis criterion for accepting a neighbor solution.

    Args:
        new_data: Energy of new solution
        old_data: Energy of old solution
        temperature: Current temperature

    Returns:
        bool: Whether to accept the neighbor solution
    """
    old_energy = calculate_energy(old_data)
    new_energy = calculate_energy(new_data)
    if new_energy < old_energy:
        return True

    if temperature == 0:
        return False

    # Probability of accepting worse solution
    probability = math.exp((old_energy - new_energy) / temperature)
    return random.random() < probability


def change_edge(g: nx.Graph, data: HouseholdData, temperature: float):
    nodes = list(g.nodes())
    node1, node2 = random.sample(nodes, 2)
    while node1 == node2:
        node1, node2 = random.sample(nodes, 2)

    old_data = data.copy()
    node1_connected = nx.node_connected_component(g, node1)
    if node2 in node1_connected:
        remove_household(g, node1_connected, data)
        for node in node1_connected:
            if node == node1:
                continue
            g.remove_edge(node1, node)
        add_household(g, {node1}, data)
        add_household(g, node1_connected - {node1}, data)
        if not metropolis_criterion(data, old_data, temperature):
            for node in node1_connected:
                if node == node1:
                    continue
                g.add_edge(node1, node)
            data.set(old_data)
    else:
        node2_connected = nx.node_connected_component(g, node2)
        remove_household(g, node1_connected, data)
        remove_household(g, node2_connected, data)
        for node_first in node1_connected:
            for node_second in node2_connected:
                g.add_edge(node_first, node_second)
        add_household(g, node1_connected | node2_connected, data)
        if not metropolis_criterion(data, old_data, temperature):
            for node_first in node1_connected:
                for node_second in node2_connected:
                    g.remove_edge(node_first, node_second)
            data.set(old_data)


def link_neighborhood(g: nx.Graph):
    """
    Link households in the neighborhood using simulated annealing.

    Uses simulated annealing to optimize network structure to match target
    household distributions (single, together, kids). The energy function
    measures the squared difference from target values.

    Args:
        g: NetworkX graph to optimize
    """
    # Simulated annealing parameters
    initial_temperature = 1000.0
    cooling_rate = 0.99
    min_temperature = 1e-8
    iterations_per_temp = 100

    # Get initial state
    data = count_households(g)
    global current_energy
    current_energy = calculate_energy(data)

    temperature = initial_temperature

    iteration = 0

    # Simulated annealing loop
    while temperature > min_temperature:
        for _ in range(iterations_per_temp):
            # Generate neighbor solution
            change_edge(g, data, temperature)

            iteration += 1

        # Cool down
        temperature *= cooling_rate

        print(
            f"Iteration {iteration}, T={temperature:.4f}, Energy={current_energy:.2f}"
        )
        print(
            f"  Total: {data.households}, Single: {data.single}, Together: {data.together}, Kids: {data.kids}, Problem:{data.problem_nodes}"
        )
        current_energy = calculate_energy(data)
