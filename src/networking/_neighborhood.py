from dataclasses import dataclass
from enum import Enum
from itertools import combinations
import networkx as nx
import random
import math

household_size = 2

households_target = 40000
households_single_target = 20000
households_together_target = 10000
households_kids_target = 10000
target_size = 2.5


class HouseholdType(Enum):
    SINGLE = 0
    TOGETHER = 1
    KIDS = 2
    PROBLEM = 3


@dataclass
class HouseholdData:
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
        )

    def set(self, other):
        self.households = other.households
        self.single = other.single
        self.together = other.together
        self.kids = other.kids
        self.problem_nodes = other.problem_nodes


@dataclass
class Person:
    household_type: HouseholdType
    age: int


def classify_household(household: dict[int, Person]) -> HouseholdType:
    # Extract ages of all members in this island
    ages = []
    for person in household.values():
        ages.append(person.age)

    # Count adults and children
    adults_25_plus = sum(1 for age in ages if age >= 25)
    adults_15_plus = sum(1 for age in ages if age >= 15)
    children = len(ages) - adults_15_plus

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


def remove_household(household: dict[int, Person], data: HouseholdData):
    household_type = classify_household(household)
    household_size = len(household)
    data.size_diff -= abs(target_size - household_size)
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
            data.problem_nodes -= household_size
            data.households += 1


def add_household(household: dict[int, Person], data: HouseholdData):
    household_type = classify_household(household)
    household_size = len(household)
    data.size_diff += abs(target_size - household_size)
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
            data.problem_nodes += household_size


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


def count_households(households: list[dict[int, Person]]) -> HouseholdData:
    data = HouseholdData(0, 0, 0, 0, 0)
    for household in households:
        print(household)
        add_household(household, data)
    return data


def calculate_energy(household_data: HouseholdData) -> float:
    """
    Calculate energy as the sum of squared differences from target values.

    Args:
        household_data: Current household distribution

    Returns:
        float: Energy value (lower is better)
    """
    single_diff = abs(household_data.single - households_single_target) ** 2
    together_diff = abs(household_data.together - households_together_target) ** 2
    kids_diff = abs(household_data.kids - households_kids_target) ** 2
    problem_diff = household_data.problem_nodes**2

    energy = (
        single_diff
        + together_diff
        + kids_diff
        + problem_diff
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


def sample_nodes(
    households: list[dict[int, Person]],
    household_index: dict[int, int],
    node_ids: list[int],
    single: list[int],
    together: list[int],
    kids: list[int],
) -> tuple[int, int]:
    node1_index = random.randint(0, len(node_ids) - 1)
    node1 = node_ids[node1_index]
    person1 = households[household_index[node1]][node1]
    node2_samples = None
    match person1.household_type:
        case HouseholdType.SINGLE:
            node2_samples = single
        case HouseholdType.TOGETHER:
            node2_samples = together
        case HouseholdType.KIDS:
            node2_samples = kids
        case _:
            e = f"Invalid householdtype for person {node1}"
            raise Exception(e)
    node2_index = random.randint(0, len(node2_samples) - 1)
    node2 = node_ids[node2_index]
    return node1, node2


def node_disconnect(
    households: list[dict[int, Person]],
    household: dict[int, Person],
    household_index: dict[int, int],
    node: int,
) -> dict[int, Person]:
    person = household.pop(node)
    household_index[node] = len(households)
    new_household = {node: person}
    households.append(new_household)
    return new_household


def household_connect(
    households: list[dict[int, Person]],
    household_index: dict[int, int],
    household1: dict[int, Person],
    household2: dict[int, Person],
):
    for id in household1.keys():
        household1_num = household_index[id]
        break
    first = True
    for id, person in household2.items():
        if first:
            household2_num = household_index[id]
        household_index[id] = household1_num
        household1[id] = person

    replcmnt = households.pop()
    if household2_num != len(households):
        # Household2 wasnt the replacement
        households[household2_num] = replcmnt


def household_reset(
    households: list[dict[int, Person]],
    household_index: dict[int, int],
    new_household: dict[int, Person],
    prev_household: dict[int, Person],
):
    households.append(prev_household)
    household_count = len(households)
    for id in prev_household.keys():
        new_household.pop(id)
        household_index[id] = household_count - 1


def change_household(
    node_ids,
    households: list[dict[int, Person]],
    household_index: dict[int, int],
    single,
    together,
    kids,
    data: HouseholdData,
    temperature: float,
):
    node1, node2 = sample_nodes(
        households, household_index, node_ids, single, together, kids
    )

    new_data = data.copy()
    node1_household = households[household_index[node1]]
    if node2 in node1_household:
        remove_household(node1_household, new_data)
        node2_household = node1_household
        node1_household = node_disconnect(
            households, node1_household, household_index, node1
        )
        add_household(node1_household, new_data)
        add_household(node2_household, new_data)
        if metropolis_criterion(new_data, data, temperature):
            data.set(new_data)
        else:
            household_connect(
                households, household_index, node2_household, node1_household
            )
    else:
        node2_household = households[household_index[node2]]
        remove_household(node1_household, new_data)
        remove_household(node2_household, new_data)
        household_connect(households, household_index, node1_household, node2_household)
        add_household(node1_household, data)
        if metropolis_criterion(new_data, data, temperature):
            data.set(new_data)
        else:
            household_reset(
                households, household_index, node1_household, node2_household
            )


def infer_households(g: nx.Graph) -> tuple[list[dict[int, Person]], dict[int, int]]:
    households = []
    household_index = {}

    for i, island in enumerate(iterate_islands(g)):
        # Get all nodes in this household island
        # TODO: Householdtype may mismatch with generated data
        households.append(
            {
                node_id: Person(node["household_type"], node["age"])
                for node_id, node in zip(island, nx.subgraph(g, island))
            }
        )
        for node_id in island:
            household_index[node_id] = i

    return households, household_index


def distinguish_households(households: list[dict[int, Person]]):
    single = list()
    together = list()
    kids = list()
    for household in households:
        for id, person in household.items():
            match person.household_type:
                case HouseholdType.KIDS:
                    kids.append(id)
                case HouseholdType.TOGETHER:
                    together.append(id)
                case HouseholdType.SINGLE:
                    single.append(id)

    return single, together, kids


def apply_edge(g: nx.Graph, households: list[dict[int, Person]]):
    """
    Creates fully connected islands for each household.

    Args:
        g: NetworkX graph
        households: A list of sets, each set representing one fully connected household.
    """
    for household in households:
        for node1, node2 in combinations(household.keys(), 2):
            g.add_edge(node1, node2)


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

    temperature = initial_temperature

    iteration = 0

    node_ids = list(g.nodes)
    households, household_index = infer_households(g)
    data = count_households(households)
    single, together, kids = distinguish_households(households)

    # Simulated annealing loop
    while temperature > min_temperature:
        for _ in range(iterations_per_temp):
            # Generate neighbor solution
            change_household(
                node_ids,
                households,
                household_index,
                single,
                together,
                kids,
                data,
                temperature,
            )

            iteration += 1

        # Cool down
        temperature *= cooling_rate

        print(
            f"Iteration {iteration}, T={temperature:.4f}, Energy={calculate_energy(data):.2f}"
        )
        print(
            f"  Total: {data.households}, Single: {data.single}, Together: {data.together}, Kids: {data.kids}, Problem:{data.problem_nodes}"
        )
