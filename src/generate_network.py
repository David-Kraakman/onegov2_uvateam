"""Phase 4: Network Generation - Create social networks from microdata.

This script completes the pipeline by:
1. Loading microdata from Phase 3
2. Creating household connections using simulated annealing
3. Adding neighborhood (SBM) connections
4. Visualizing the resulting multi-layer network
5. Saving the network for epidemiological modeling

Run:
    python src/generate_network.py --buurt BU16800000 --microdata_dir data/microdata --network_dir data/network
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, Any, Tuple
import json
import datetime

import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__)))

from networking._household import link_household
from networking._neighborhood import link_neighborhood

def parseargs() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Phase 4: Network Generation - Create social networks from microdata"
    )
    parser.add_argument(
        "--buurt",
        type=str,
        required=True,
        help="CBS buurt code (format: BUXXXXYYYY), human-readable name, or numeric ID"
    )
    parser.add_argument(
        "--microdata_dir",
        type=Path,
        default=Path("data") / "microdata",
        help="Directory containing microdata from Phase 3 (default: data/microdata)"
    )
    parser.add_argument(
        "--network_dir",
        type=Path,
        default=Path("data") / "network",
        help="Output directory for network results (default: data/network)"
    )
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Generate visualization of the network"
    )
    parser.add_argument(
        "--sample_size",
        type=int,
        default=50,
        help="Number of nodes to sample for visualization (default: 50)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed processing information"
    )
    return parser.parse_args()

def find_microdata_file(microdata_dir: Path, buurt_identifier: str) -> Path:
    """
    Find microdata file for the specified buurt.

    Args:
        microdata_dir: Directory containing microdata files
        buurt_identifier: Buurt identifier (code, name, or ID)

    Returns:
        Path to the microdata file

    Raises:
        FileNotFoundError: If no matching microdata file is found
    """
    # Look for files matching the buurt identifier
    patterns = [
        f"*{buurt_identifier}*_microdata.parquet",
        f"buurt_{buurt_identifier}_*_microdata.parquet",
        f"buurt_{buurt_identifier}_microdata.parquet"
    ]

    for pattern in patterns:
        files = list(microdata_dir.glob(pattern))
        if files:
            return files[0]

    raise FileNotFoundError(
        f"No microdata found for buurt {buurt_identifier} in {microdata_dir}. "
        f"Available files: {[f.name for f in microdata_dir.glob('*.parquet')]}"
    )

def load_microdata(microdata_path: Path) -> pd.DataFrame:
    """
    Load microdata from parquet file.

    Args:
        microdata_path: Path to the microdata file

    Returns:
        DataFrame containing the microdata
    """
    print(f"Loading microdata from {microdata_path}...")
    df = pd.read_parquet(microdata_path)
    print(f"  ✓ Loaded {len(df)} individuals")
    return df

def create_network_from_microdata(df: pd.DataFrame) -> nx.Graph:
    """
    Create a NetworkX graph from microdata.

    Args:
        df: DataFrame containing microdata

    Returns:
        NetworkX graph with node attributes from microdata
    """
    print("Creating network from microdata...")

    # Create graph
    g = nx.Graph()

    # Add nodes with attributes
    for index, row in df.iterrows():
        g.add_node(index)
        for col in df.columns:
            g.nodes[index][col] = row[col]

    print(f"  ✓ Created graph with {len(g.nodes())} nodes")
    return g

def generate_network_pipeline(g: nx.Graph, verbose: bool = False) -> Dict[str, Any]:
    """
    Run the complete network generation pipeline.

    Args:
        g: NetworkX graph with microdata attributes
        verbose: Whether to show detailed information

    Returns:
        Dictionary containing pipeline results and statistics
    """
    results = {
        'initial_nodes': len(g.nodes()),
        'initial_edges': len(g.edges()),
        'household_stats': {},
        'sbm_stats': {},
        'final_stats': {}
    }

    # Step 1: Link households
    print("\n[1/2] Generating household connections...")
    try:
        if verbose:
            print("  Starting household linking with simulated annealing...")

        link_household(g)

        # Calculate household statistics
        household_edges = [e for e in g.edges() if g.edges[e].get('layer') == 'household']
        household_components = list(nx.connected_components(nx.subgraph(g, household_edges)))

        results['household_stats'] = {
            'edges': len(household_edges),
            'components': len(household_components),
            'size_distribution': sorted([len(c) for c in household_components]),
            'average_degree': sum(dict(nx.degree(nx.subgraph(g, household_edges))).values()) / len(g.nodes())
        }

        print(f"  ✓ Household generation complete")
        print(f"    - Household edges: {len(household_edges)}")
        print(f"    - Household components: {len(household_components)}")

    except Exception as e:
        print(f"  ❌ Household generation failed: {e}")
        raise

    # Step 2: Link neighborhood (SBM)
    print("\n[2/2] Generating neighborhood (SBM) connections...")
    try:
        if verbose:
            print("  Starting SBM neighborhood linking...")

        link_neighborhood(g)

        # Calculate SBM statistics
        institution_edges = [e for e in g.edges() if g.edges[e].get('layer') == 'institution']
        community_edges = [e for e in g.edges() if g.edges[e].get('layer') == 'community']

        results['sbm_stats'] = {
            'institution_edges': len(institution_edges),
            'community_edges': len(community_edges),
            'total_sbm_edges': len(institution_edges) + len(community_edges)
        }

        print(f"  ✓ SBM generation complete")
        print(f"    - Institution edges: {len(institution_edges)}")
        print(f"    - Community edges: {len(community_edges)}")

    except Exception as e:
        print(f"  ❌ SBM generation failed: {e}")
        raise

    # Calculate final statistics
    results['final_stats'] = {
        'total_nodes': len(g.nodes()),
        'total_edges': len(g.edges()),
        'average_degree': sum(dict(g.degree()).values()) / len(g.nodes()),
        'edge_layers': {}
    }

    # Count edges by layer
    edge_layers = [g.edges[e].get('layer', 'unknown') for e in g.edges()]
    layer_counts = {}
    for layer in edge_layers:
        layer_counts[layer] = layer_counts.get(layer, 0) + 1

    results['final_stats']['edge_layers'] = layer_counts

    return results

def visualize_network(g: nx.Graph, sample_size: int = 50, output_path: Path = None) -> None:
    """
    Create a visualization of the network.

    Args:
        g: NetworkX graph
        sample_size: Number of nodes to sample for visualization
        output_path: Path to save the visualization (optional)
    """
    print(f"\nGenerating network visualization...")

    # Sample nodes for visualization (to keep it manageable)
    all_nodes = list(g.nodes())
    if len(all_nodes) > sample_size:
        sample_nodes = np.random.choice(all_nodes, size=sample_size, replace=False)
        subgraph = g.subgraph(sample_nodes)
        print(f"  - Visualizing sample of {len(sample_nodes)} nodes")
    else:
        subgraph = g.copy()
        print(f"  - Visualizing full network of {len(all_nodes)} nodes")

    # Create figure with more space
    plt.figure(figsize=(14, 12))

    # Use a looser layout algorithm for better spacing
    pos = nx.spring_layout(subgraph, seed=42, k=0.8, iterations=200)

    # Draw nodes with smaller size for better visibility
    nx.draw_networkx_nodes(subgraph, pos, node_size=30, node_color='lightblue', alpha=0.8)

    # Get edge colors and draw edges by layer for better control
    household_edges = [(u, v) for u, v in subgraph.edges() if subgraph.edges[u, v].get('layer') == 'household']
    institution_edges = [(u, v) for u, v in subgraph.edges() if subgraph.edges[u, v].get('layer') == 'institution']
    community_edges = [(u, v) for u, v in subgraph.edges() if subgraph.edges[u, v].get('layer') == 'community']

    # Draw edges with different colors and widths
    if household_edges:
        nx.draw_networkx_edges(subgraph, pos, edgelist=household_edges, edge_color='red', width=1.5, alpha=0.7)
    if institution_edges:
        nx.draw_networkx_edges(subgraph, pos, edgelist=institution_edges, edge_color='blue', width=1.2, alpha=0.7)
    if community_edges:
        nx.draw_networkx_edges(subgraph, pos, edgelist=community_edges, edge_color='green', width=1.0, alpha=0.7)

    # Add legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color='red', lw=2, label='Household'),
        Line2D([0], [0], color='blue', lw=2, label='Institution'),
        Line2D([0], [0], color='green', lw=2, label='Community')
    ]
    plt.legend(handles=legend_elements, loc='upper right', fontsize=12)

    plt.title(f"Multi-Layer Social Network ({len(subgraph.nodes())} nodes, {len(subgraph.edges())} edges)", fontsize=14)
    plt.axis('off')

    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"  ✓ Saved visualization to {output_path}")
    else:
        plt.show()

    plt.close()

def save_network(g: nx.Graph, network_dir: Path, buurt_identifier: str, metadata: Dict[str, Any]) -> Dict[str, Path]:
    """
    Save the network and metadata to files.

    Args:
        g: NetworkX graph
        network_dir: Output directory
        buurt_identifier: Buurt identifier
        metadata: Metadata dictionary

    Returns:
        Dictionary of saved file paths
    """
    print(f"\nSaving network files...")

    # Create output directory
    network_dir.mkdir(parents=True, exist_ok=True)

    # Generate safe filename
    safe_name = f"buurt_{buurt_identifier.replace(' ', '_')}"
    safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in safe_name)[:100]

    # Save network in GraphML format (preserves all attributes)
    network_path = network_dir / f"{safe_name}_network.graphml"
    nx.write_graphml(g, network_path)
    print(f"  ✓ Saved network: {network_path.name}")

    # Add network statistics to metadata
    metadata['network_file'] = network_path.name
    metadata['timestamp'] = datetime.datetime.now().isoformat()

    # Save metadata
    metadata_path = network_dir / f"{safe_name}_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"  ✓ Saved metadata: {metadata_path.name}")

    return {
        'network': network_path,
        'metadata': metadata_path
    }

def create_metadata(df: pd.DataFrame, buurt_row: pd.Series, pipeline_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create comprehensive metadata for the generated network.

    Args:
        df: Original microdata DataFrame
        buurt_row: Buurt data row
        pipeline_results: Results from network generation pipeline

    Returns:
        Dictionary containing comprehensive metadata
    """
    metadata = {
        'buurt': {
            'identifier': str(buurt_row.get('Codering_3', 'unknown')),
            'name': str(buurt_row.get('WijkenEnBuurten', 'unknown')),
            'population': int(buurt_row.get('AantalInwoners_5', 0)),
            'households': int(buurt_row.get('HuishoudensTotaal_29', 0))
        },
        'microdata': {
            'individuals': len(df),
            'attributes': list(df.columns),
            'attribute_distributions': {}
        },
        'network_generation': pipeline_results,
        'statistics': {}
    }

    # Add attribute distributions
    for col in df.columns:
        value_counts = df[col].value_counts().to_dict()
        metadata['microdata']['attribute_distributions'][col] = value_counts

    # Calculate additional statistics
    metadata['statistics']['population_coverage'] = (
        len(df) / metadata['buurt']['population'] if metadata['buurt']['population'] > 0 else 0
    )

    return metadata

def main(args: argparse.Namespace) -> int:
    """
    Main entry point for Phase 4 network generation.
    """
    print("=" * 80)
    print("Phase 4: Network Generation")
    print("=" * 80)

    try:
        # Step 1: Find and load microdata
        print(f"\n[1/4] Loading microdata for buurt: {args.buurt}")

        try:
            microdata_path = find_microdata_file(args.microdata_dir, args.buurt)
            df = load_microdata(microdata_path)
        except Exception as e:
            print(f"  ❌ Error loading microdata: {e}")
            return 1

        # Step 2: Create network from microdata
        print(f"\n[2/4] Creating network from microdata")
        g = create_network_from_microdata(df)

        # Step 3: Generate network pipeline
        print(f"\n[3/4] Running network generation pipeline")
        pipeline_results = generate_network_pipeline(g, verbose=args.verbose)

        # Step 4: Create metadata
        print(f"\n[4/4] Creating metadata and saving results")

        # For now, create basic metadata (we'll enhance this later)
        basic_metadata = {
            'buurt_identifier': args.buurt,
            'microdata_individuals': len(df),
            'network_generation': pipeline_results,
            'timestamp': datetime.datetime.now().isoformat()
        }

        # Save network
        saved_files = save_network(g, args.network_dir, args.buurt, basic_metadata)

        # Step 5: Visualization (optional)
        if args.visualize:
            try:
                viz_path = args.network_dir / f"buurt_{args.buurt}_visualization.png"
                visualize_network(g, sample_size=args.sample_size, output_path=viz_path)
            except Exception as e:
                print(f"  ⚠️  Visualization failed: {e}")

        # Print summary
        print(f"\n{'='*80}")
        print("✅ Phase 4 Complete: Network generation successful")
        print(f"{'='*80}")

        print(f"\n📊 Summary:")
        print(f"  - Buurt: {args.buurt}")
        print(f"  - Microdata individuals: {len(df)}")
        print(f"  - Final network: {pipeline_results['final_stats']['total_nodes']} nodes, {pipeline_results['final_stats']['total_edges']} edges")
        print(f"  - Edge layers: {pipeline_results['final_stats']['edge_layers']}")
        print(f"  - Files saved: {saved_files['network'].name}, {saved_files['metadata'].name}")

        return 0

    except Exception as e:
        print(f"\n❌ Error during network generation: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    # Set random seeds for reproducibility
    import random
    random.seed(42)
    np.random.seed(42)

    args = parseargs()
    exit(main(args))