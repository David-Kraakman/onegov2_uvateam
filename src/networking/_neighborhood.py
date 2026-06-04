from dataclasses import dataclass
import networkx as nx

household_size = 2

households_target = 190000
households_single_target = 100000
households_together_target = 40000
households_kids_target = 50000


@dataclass
class HouseholdData:
    households: int
    single: int
    together: int
    kids: int
    problem_nodes: list[int]


def _parenting(g: nx.Graph):
    """Link all children"""


def iterate_islands(g: nx.Graph):
    """
    Loop over all islands (connected components) in the network.

    An island is a maximal set of nodes where every node is connected
    to at least one other node via a path. Isolated nodes are single-node islands.

    Yields:
        nx.Graph: A subgraph representing each island/connected component
    """
    connected_components = nx.connected_components(g)
    for component_nodes in connected_components:
        island = g.subgraph(component_nodes)
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
    data = HouseholdData(households=0, single=0, together=0, kids=0, problem_nodes=[])

    for island in iterate_islands(g):
        # Get all nodes in this household island

        # Increment total household count
        data.households += 1

        # Extract ages of all members in this island
        ages = []
        for age in island.nodes.data("age"):
            if age is not None:
                ages.append(age)

        # Count adults and children
        adults_25_plus = sum(1 for age in ages if age >= 25)
        adults_15_plus = sum(1 for age in ages if age >= 15)
        children = sum(1 for age in ages if age < 18)

        # Categorize household
        if adults_25_plus > 0 and children > 0:
            # Adults (25+) with children
            data.kids += 1
        elif adults_15_plus > 1:
            # Multiple adults (25+) without children
            data.together += 1
        elif adults_15_plus == 1:
            # Single adult (15+)
            data.single += 1
        else:
            # Problem nodes: doesn't fit any category
            data.problem_nodes.extend(island.nodes)

    return data


def link_neighborhood(g: nx.Graph):
    """Link households in the neighborhood based on marital status and age."""
