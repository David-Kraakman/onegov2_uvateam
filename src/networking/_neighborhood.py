import networkx as nx
import numpy as np
import random
from typing import Dict, List, Tuple, Any
from collections import defaultdict
import math

def calculate_dissimilarity(node_i: int, node_j: int, graph: nx.Graph, weights: Dict[str, float]) -> float:
    """
    Calculate dissimilarity between two nodes based on their attributes.

    Args:
        node_i: First node ID
        node_j: Second node ID
        graph: NetworkX graph containing node attributes
        weights: Dictionary of feature weights

    Returns:
        float: Dissimilarity score between 0 and 1
    """
    # Get node attributes
    attrs_i = graph.nodes[node_i]
    attrs_j = graph.nodes[node_j]

    dissimilarity = 0.0

    # Categorical variables - use indicator function
    for feature, weight in weights.items():
        if feature in ['migration_group', 'household_type']:
            if attrs_i.get(feature) != attrs_j.get(feature):
                dissimilarity += weight

    # Ordinal variables - use normalized difference
    ordinal_mappings = {
        'age_band': {'0-14': 0, '15-24': 1, '25-44': 2, '45-64': 3, '65+': 4},
        'education_group': {
            'Primary_or_None': 0,
            'Secondary_VMBO': 1,
            'Secondary_MBO': 2,
            'Secondary_HAVO_VWO': 3,
            'Tertiary_Higher': 4,
            'Tertiary_University': 5
        },
        'income_class': {
            'Inkomen: minder dan 10 000 euro': 0,
            'Inkomen: 10 000 tot 20 000 euro': 1,
            'Inkomen: 20 000 tot 30 000 euro': 2,
            'Inkomen: 30 000 tot 40 000 euro': 3,
            'Inkomen: 40 000 tot 50 000 euro': 4,
            'Inkomen: 50 000 tot 100 000 euro': 5,
            'Inkomen: 100 000 tot 200 000 euro': 6
        }
    }

    for feature, weight in weights.items():
        if feature in ordinal_mappings:
            mapping = ordinal_mappings[feature]
            val_i = mapping.get(attrs_i.get(feature), -1)
            val_j = mapping.get(attrs_j.get(feature), -1)

            if val_i >= 0 and val_j >= 0:  # Both values are valid
                max_diff = max(mapping.values()) - min(mapping.values())
                if max_diff > 0:
                    dissimilarity += weight * (abs(val_i - val_j) / max_diff)

    return dissimilarity

def generate_block_sizes(total_population: int) -> List[int]:
    """
    Generate block sizes using one-inflated log-normal distribution.

    Args:
        total_population: Total number of individuals

    Returns:
        List of block sizes
    """
    # Parameters from SBM.md
    mu = 3.5  # log scale mean
    sigma = 0.8  # log scale standard deviation
    p_1 = 0.1  # probability of size 1 blocks
    p_solitary = 0.1  # proportion of isolated individuals
    min_block_size = 2
    max_block_size = 20

    block_sizes = []
    remaining = total_population

    # Add solitary individuals (10% of population)
    num_solitary = int(total_population * p_solitary)
    block_sizes.extend([1] * num_solitary)
    remaining -= num_solitary

    # Generate blocks using one-inflated log-normal distribution
    while remaining > 0:
        # One-inflated log-normal: with probability p_1, size = 1
        if random.random() < p_1:
            size = 1
        else:
            # Sample from log-normal distribution
            log_normal_sample = np.random.lognormal(mu, sigma)
            size = int(round(log_normal_sample))

            # Constrain block size
            if size < min_block_size:
                size = min_block_size
            elif size > max_block_size:
                size = max_block_size

        # Don't add blocks larger than remaining population
        if size > remaining:
            size = remaining

        block_sizes.append(size)
        remaining -= size

    return block_sizes

def initialize_blocks(node_ids: List[int], block_sizes: List[int]) -> Dict[int, int]:
    """
    Create initial random block assignment.

    Args:
        node_ids: List of node IDs
        block_sizes: List of block sizes

    Returns:
        Dictionary mapping node_id to block_id
    """
    # Shuffle node IDs for random assignment
    shuffled_nodes = node_ids.copy()
    random.shuffle(shuffled_nodes)

    blocks = {}
    block_id = 0
    current_pos = 0

    for size in block_sizes:
        if size == 0:
            continue

        # Assign 'size' nodes to this block
        for i in range(size):
            if current_pos + i < len(shuffled_nodes):
                node = shuffled_nodes[current_pos + i]
                blocks[node] = block_id

        current_pos += size
        block_id += 1

    return blocks

def calculate_local_energy_change(node_i: int, node_j: int,
                                block_i: int, block_j: int,
                                blocks: Dict[int, int],
                                graph: nx.Graph,
                                weights: Dict[str, float]) -> float:
    """
    Calculate the change in energy if we swap nodes i and j between their blocks.

    Args:
        node_i: First node ID
        node_j: Second node ID
        block_i: Current block of node_i
        block_j: Current block of node_j
        blocks: Current block assignment
        graph: NetworkX graph
        weights: Feature weights

    Returns:
        float: Change in energy (ΔE)
    """
    # Get all nodes in each block (excluding the nodes being swapped)
    block_i_nodes = [n for n, b in blocks.items() if b == block_i and n != node_i]
    block_j_nodes = [n for n, b in blocks.items() if b == block_j and n != node_j]

    # Calculate current energy (node_i in block_i, node_j in block_j)
    current_energy = 0.0
    for node in block_i_nodes:
        current_energy += calculate_dissimilarity(node_i, node, graph, weights)
    for node in block_j_nodes:
        current_energy += calculate_dissimilarity(node_j, node, graph, weights)

    # Calculate new energy if swapped (node_j in block_i, node_i in block_j)
    new_energy = 0.0
    for node in block_i_nodes:
        new_energy += calculate_dissimilarity(node_j, node, graph, weights)
    for node in block_j_nodes:
        new_energy += calculate_dissimilarity(node_i, node, graph, weights)

    return new_energy - current_energy

def hill_climbing_optimization(graph: nx.Graph,
                             blocks: Dict[int, int],
                             max_iterations: int) -> Dict[int, int]:
    """
    Optimize block assignment using stochastic hill climbing.

    Args:
        graph: NetworkX graph
        blocks: Initial block assignment
        max_iterations: Maximum number of iterations

    Returns:
        Optimized block assignment
    """
    # Define weights for dissimilarity calculation
    weights = {
        'age_band': 0.4,
        'education_group': 0.25,
        'income_class': 0.15,
        'migration_group': 0.1,
        'household_type': 0.1
    }

    node_ids = list(graph.nodes())
    num_nodes = len(node_ids)

    # Convert blocks to list format for easier manipulation
    block_list = list(set(blocks.values()))
    num_blocks = len(block_list)

    # Create reverse mapping: block_id -> list of node_ids
    block_to_nodes = defaultdict(list)
    for node, block in blocks.items():
        block_to_nodes[block].append(node)

    optimized_blocks = blocks.copy()
    consecutive_rejections = 0
    iterations = 0

    while consecutive_rejections < max_iterations and iterations < 10 * num_nodes:
        # Pick two random nodes from different blocks
        node_i = random.choice(node_ids)
        block_i = optimized_blocks[node_i]

        # Find a node from a different block
        other_blocks = [b for b in block_list if b != block_i and len(block_to_nodes[b]) > 0]
        if not other_blocks:
            break

        block_j = random.choice(other_blocks)
        node_j = random.choice(block_to_nodes[block_j])

        # Calculate energy change
        delta_e = calculate_local_energy_change(
            node_i, node_j, block_i, block_j,
            optimized_blocks, graph, weights
        )

        # Acceptance criteria: only accept if energy decreases
        if delta_e < 0:
            # Swap the nodes between blocks
            optimized_blocks[node_i] = block_j
            optimized_blocks[node_j] = block_i

            # Update block_to_nodes mapping
            # Remove nodes from their current blocks
            if node_i in block_to_nodes[block_j]:
                block_to_nodes[block_j].remove(node_i)
            if node_j in block_to_nodes[block_i]:
                block_to_nodes[block_i].remove(node_j)

            # Add nodes to their new blocks
            block_to_nodes[block_i].append(node_j)
            block_to_nodes[block_j].append(node_i)

            consecutive_rejections = 0
        else:
            consecutive_rejections += 1

        iterations += 1

        # Print progress every 1000 iterations
        if iterations % 1000 == 0:
            print(f"Iteration {iterations}, Consecutive rejections: {consecutive_rejections}")

    return optimized_blocks

def add_sbm_edges(graph: nx.Graph, blocks: Dict[int, int],
                 p_in: float = 0.15, p_out: float = 0.02) -> None:
    """
    Add SBM edges to the existing household network.

    Args:
        graph: NetworkX graph with household edges already present
        blocks: Block assignment dictionary (node_id -> block_id)
        p_in: Intra-block connection probability
        p_out: Inter-block connection probability
    """
    # First, ensure all existing edges have 'layer' attribute
    for u, v in graph.edges():
        if 'layer' not in graph.edges[u, v]:
            graph.edges[u, v]['layer'] = 'household'

    # Create reverse mapping: block_id -> list of node_ids
    block_to_nodes = defaultdict(list)
    for node, block in blocks.items():
        block_to_nodes[block].append(node)

    # Generate intra-block edges (institution layer)
    intra_block_edges = []
    for block_id, nodes in block_to_nodes.items():
        if len(nodes) <= 1:
            continue

        # Create all possible pairs within the block
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                node_u = nodes[i]
                node_v = nodes[j]

                # Skip if edge already exists (household connection)
                if graph.has_edge(node_u, node_v):
                    continue

                # Add with probability p_in
                if random.random() < p_in:
                    intra_block_edges.append((node_u, node_v, {
                        'layer': 'institution',
                        'block_id': block_id
                    }))

    # Generate inter-block edges (community layer)
    inter_block_edges = []
    block_ids = list(block_to_nodes.keys())

    # Create edges between different blocks
    for i in range(len(block_ids)):
        for j in range(i + 1, len(block_ids)):
            block_u = block_ids[i]
            block_v = block_ids[j]

            nodes_u = block_to_nodes[block_u]
            nodes_v = block_to_nodes[block_v]

            # Create some connections between these blocks
            num_possible = len(nodes_u) * len(nodes_v)
            num_connections = min(int(num_possible * p_out), 10)  # Limit to reasonable number

            for _ in range(num_connections):
                node_u = random.choice(nodes_u)
                node_v = random.choice(nodes_v)

                # Skip if edge already exists
                if graph.has_edge(node_u, node_v):
                    continue

                inter_block_edges.append((node_u, node_v, {
                    'layer': 'community'
                }))

    # Add all new edges to the graph
    if intra_block_edges:
        graph.add_edges_from(intra_block_edges)
    if inter_block_edges:
        graph.add_edges_from(inter_block_edges)

def link_neighborhood(g: nx.Graph):
    """
    Main function to add neighborhood (SBM) connections to the household network.

    Args:
        g: NetworkX graph with household connections already established
    """
    print("Starting SBM neighborhood link generation...")

    # Step 1: Get all node IDs
    node_ids = list(g.nodes())
    total_population = len(node_ids)

    if total_population == 0:
        print("No nodes in graph, skipping SBM generation")
        return

    print(f"Total population: {total_population}")

    # Step 2: Generate block sizes
    print("Generating block sizes...")
    block_sizes = generate_block_sizes(total_population)
    print(f"Generated {len(block_sizes)} blocks with sizes: {sorted(block_sizes)[:10]}...")

    # Step 3: Initialize blocks
    print("Initializing block assignments...")
    blocks = initialize_blocks(node_ids, block_sizes)

    # Verify all nodes are assigned
    unassigned = [n for n in node_ids if n not in blocks]
    if unassigned:
        print(f"Warning: {len(unassigned)} nodes not assigned to blocks")

    # Step 4: Optimize block assignment
    print("Optimizing block assignments using hill climbing...")
    max_iterations = 5 * total_population
    optimized_blocks = hill_climbing_optimization(g, blocks, max_iterations)

    # Step 5: Add SBM edges
    print("Adding SBM edges...")
    add_sbm_edges(g, optimized_blocks)

    # Print summary statistics
    block_to_nodes = defaultdict(list)
    for node, block in optimized_blocks.items():
        block_to_nodes[block].append(node)

    print(f"SBM generation complete:")
    print(f"  - Total blocks: {len(block_to_nodes)}")
    print(f"  - Block size distribution: {sorted([len(nodes) for nodes in block_to_nodes.values()])}")
    print(f"  - Total edges added: {len(g.edges()) - len([e for e in g.edges() if g.edges[e].get('layer') == 'household'])}")