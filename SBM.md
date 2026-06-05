SBM Block Assignment Implementation

This document specifies the algorithm for partitioning a neighborhood population into structurally fixed Stochastic Block Model (SBM) clusters. The assignment optimizes demographic homophily within blocks using a Stochastic Hill Climbing (Local Search) algorithm.

## Compatibility with Existing Household Network

The SBM implementation must work with the existing household network structure:

1. **Household Network Structure**: The household network is already created using the `_household.py` module, which:
   - Maps household types from microdata to PersonType enums
   - Creates fully connected household components
   - Uses household_type, age_band, education_group, migration_group, and income_class attributes

2. **Microdata Attributes**: The microdata contains the following attributes that can be used for the dissimilarity metric:
   - **Categorical variables**: migration_group (3 values), household_type (8 values)
   - **Ordinal variables**: age_band (5 values: 0-14, 15-24, 25-44, 45-64, 65+), education_group (6 values), income_class (7 values)

3. **Missing Layer Attributes**: The current household implementation does NOT add 'layer' attributes to edges. This needs to be added for SIR model compatibility.

## 1. Data Definitions and Dissimilarity Metric

The dataset contains exclusively categorical and ordinal variables. Continuous distance metrics are invalid. The algorithm requires a composite dissimilarity metric $D(i, j)$ between any two individuals $i$ and $j$.

### 1.1 Variable Classification

**Categorical ($C$)**:
- `migration_group`: Netherlands, EU_non_NL, Non_EU
- `household_type`: Cohabiting, Cohabiting_no_kids, Cohabiting_with_kids, Living_with_parents, Married_no_kids, Married_with_kids, Single, Single_parent

**Ordinal ($O$)**:
- `age_band`: 0-14 (0), 15-24 (1), 25-44 (2), 45-64 (3), 65+ (4)
- `education_group`: Primary_or_None (0), Secondary_VMBO (1), Secondary_MBO (2), Secondary_HAVO_VWO (3), Tertiary_Higher (4), Tertiary_University (5)
- `income_class`: Inkomen: minder dan 10 000 euro (0), Inkomen: 10 000 tot 20 000 euro (1), ..., Inkomen: 100 000 tot 200 000 euro (6)

### 1.2 Distance Calculation

The distance is a weighted sum of normalized feature differences:

$$D(i, j) = \sum_{f \in C} w_f \cdot \mathbb{I}(x_{i,f} \neq x_{j,f}) + \sum_{f \in O} w_f \cdot \frac{|x_{i,f} - x_{j,f}|}{\max(O_f) - \min(O_f)}$$

$\mathbb{I}$ is the indicator function (returns 1 if values differ, 0 if identical).

Ordinal variables are mapped to integer ranks. The absolute difference is normalized by the maximum possible rank difference for that feature, bounding the penalty to $[0, 1]$.

### 1.3 Weight Specification

$w_f$ represents the epidemiological weight of the feature. Recommended weights based on transmission relevance:

- `age_band`: 0.4 (highest weight - age mixing patterns are critical)
- `education_group`: 0.25 (education level affects social mixing)
- `income_class`: 0.15 (economic status affects social circles)
- `migration_group`: 0.1 (migration background affects community structure)
- `household_type`: 0.1 (household structure affects social patterns)

$\sum w_f = 1.0$

## 2. Block Size Distribution Parameters

The one-inflated log-normal distribution parameters for block sizes:

- **Mean (μ)**: 3.5 (log scale)
- **Standard deviation (σ)**: 0.8 (log scale)
- **Inflation probability (p_1)**: 0.1 (10% of blocks are size 1)
- **Minimum block size**: 2 (except for inflated size 1 blocks)
- **Maximum block size**: 30 (to prevent unrealistic large blocks)

## 3. SBM Connection Probabilities

- **Intra-block probability (p_in)**: 0.15 (15% connection probability within blocks)
- **Inter-block probability (p_out)**: 0.02 (2% connection probability between blocks)
- **Household probability**: 1.0 (all household members are connected)

## 4. Initialization Phase

Before optimization, the structural framework of the network must be generated and populated randomly.

### 4.1 Determine Block Capacities

1. Extract total population $N$ from the household network
2. Define proportion of isolated individuals $p_{solitary} = 0.1$. Append $(N \times p_{solitary})$ blocks of capacity 1.
3. Sample from the one-inflated log-normal distribution:
   - With probability $p_1 = 0.1$, sample size = 1
   - With probability $1-p_1 = 0.9$, sample from log-normal(μ=3.5, σ=0.8)
4. Round to integer, drop values < 2 (except size 1 blocks), and append to the capacity list until the sum of all block capacities equals $N$.

### 4.2 Random Assignment

1. Get all node IDs from the existing household network
2. Shuffle the list of node IDs
3. Partition the list sequentially into the defined block capacities
4. This establishes the initial state $S_0$

## 5. Optimization via Stochastic Hill Climbing

The objective is to minimize the total intra-block dissimilarity (the "Energy" of the system) by iteratively swapping individuals between blocks.

### 5.1 Energy Evaluation (The Swap)

To evaluate a state transition efficiently:

1. Select two random individuals $i$ and $j$ who currently reside in different blocks (let $i \in$ block $A$, $j \in$ block $B$)
2. Calculate current local energy:
   $E_{local\_old} = \sum_{x \in A \setminus \{i\}} D(i, x) + \sum_{y \in B \setminus \{j\}} D(j, y)$
3. Calculate hypothetical local energy if swapped:
   $E_{local\_new} = \sum_{x \in A \setminus \{i\}} D(j, x) + \sum_{y \in B \setminus \{j\}} D(i, y)$
4. $\Delta E = E_{local\_new} - E_{local\_old}$

### 5.2 Acceptance Criteria

Evaluate $\Delta E$ using a strict greedy criterion:

- If $\Delta E < 0$: The swap reduces dissimilarity. Accept the swap.
- If $\Delta E \ge 0$: The swap degrades or stalls homophily. Reject the swap.

### 5.3 Execution and Termination

The algorithm runs in a continuous loop evaluating random pairs.

- **Iteration**: In each step, pick pair $(i, j)$ at random from different blocks.
- **Evaluation**: Calculate $\Delta E$ and apply the acceptance criteria.
- **Termination**: Stop when $K = 5 \times N$ consecutive random swap attempts are rejected.

## 6. Finalization and NetworkX Integration

### 6.1 Add Layer Attributes to Household Edges

Before adding SBM edges, ensure all existing household edges have the 'layer' attribute:

```python
# Add 'layer': 'household' to all existing edges
for u, v in G.edges():
    G.edges[u, v]['layer'] = 'household'
```

### 6.2 Generate SBM Edges

1. **Intra-block edges**: For each block, create edges between all pairs of nodes with probability $p_{in} = 0.15$
2. **Inter-block edges**: For each pair of different blocks, create edges between random node pairs with probability $p_{out} = 0.02$

### 6.3 Label Edge Context

When a probabilistic edge is formed, append it to an edge list with metadata:

- **Intra-block**: `(i, j, {'layer': 'institution', 'block_id': block_id})`
- **Inter-block**: `(i, j, {'layer': 'community'})`

### 6.4 Inject into Graph

```python
G.add_edges_from(sbm_edge_list)
```

## 7. Implementation Requirements

### 7.1 Required Functions

```python
def calculate_dissimilarity(node_i, node_j, graph, weights):
    """Calculate dissimilarity between two nodes based on their attributes"""

def generate_block_sizes(total_population):
    """Generate block sizes using one-inflated log-normal distribution"""

def initialize_blocks(node_ids, block_sizes):
    """Create initial random block assignment"""

def hill_climbing_optimization(graph, blocks, max_iterations):
    """Optimize block assignment using stochastic hill climbing"""

def add_sbm_edges(graph, blocks, p_in=0.15, p_out=0.02):
    """Add SBM edges to the existing household network"""
```

### 7.2 Integration with Existing Code

The SBM implementation should be added to `src/networking/_neighborhood.py` as the `link_neighborhood` function, which will be called after `link_households` in the main networking pipeline.

## 8. Validation and Testing

### 8.1 Expected Network Properties

- **Household layer**: Fully connected components (cliques)
- **Institution layer**: Dense connections within blocks, sparse between blocks
- **Community layer**: Sparse connections between different blocks

### 8.2 Quality Metrics

1. **Homophily score**: Measure average attribute similarity within vs between blocks
2. **Modularity**: Measure the strength of block structure
3. **Degree distribution**: Verify it follows expected patterns

## 9. Parameters Summary

| Parameter | Value | Description |
|-----------|-------|-------------|
| μ (log-normal mean) | 3.5 | Mean of log-normal distribution (log scale) |
| σ (log-normal std) | 0.8 | Standard deviation of log-normal distribution |
| p_1 (inflation prob) | 0.1 | Probability of size 1 blocks |
| p_solitary | 0.1 | Proportion of isolated individuals |
| p_in | 0.15 | Intra-block connection probability |
| p_out | 0.02 | Inter-block connection probability |
| K (patience) | 5×N | Termination threshold |
| min_block_size | 2 | Minimum block size (except size 1) |
| max_block_size | 30 | Maximum block size |
