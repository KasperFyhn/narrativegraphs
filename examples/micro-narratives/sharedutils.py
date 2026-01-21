from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from scipy.spatial import ConvexHull


def create_narrative_graph_visualization(
    salient_nodes: List[str],
    micro_nodes: List[str],
    edges: List[Tuple[str, str]],
    communities: Optional[Dict[int, List[str]]] = None,
    figsize: Tuple[float, float] = (14, 10),
    salient_color: str = "#d62728",
    salient_edge_color: str = "#8b0000",
    micro_color: str = "#1f77b4",
    salient_marker: str = "^",
    salient_size: int = 120,
    micro_size: int = 25,
    edge_alpha: float = 0.4,
    highlight_communities: bool = False,
    community_alpha: float = 0.15,
    layout: str = "spring",
    layout_params: Optional[Dict] = None,
    seed: Optional[int] = None,
    output_path: Optional[str] = None,
    dpi: int = 300,
    title: Optional[str] = None,
) -> Optional[nx.Graph]:
    """
    Create a visualization of narrative graph structure showing micro-narratives
    connected to salient entities.

    Parameters
    ----------
    salient_nodes : List[str]
        List of node IDs for salient entities
    micro_nodes : List[str]
        List of node IDs for micro-narrative nodes
    edges : List[Tuple[str, str]]
        List of edges as (source, target) tuples
    communities : Optional[Dict[int, List[str]]], default=None
        Dictionary mapping community IDs to lists of micro-narrative node IDs.
        If None, communities are auto-detected using connected components.
    figsize : Tuple[float, float], default=(14, 10)
        Figure size in inches
    salient_color : str, default='#d62728'
        Color for salient entity nodes
    salient_edge_color : str, default='#8b0000'
        Edge color for salient entity nodes
    micro_color : str, default='#1f77b4'
        Color for micro-narrative nodes
    salient_marker : str, default='^'
        Marker style for salient nodes (matplotlib marker)
    salient_size : int, default=120
        Size of salient node markers
    micro_size : int, default=25
        Size of micro-narrative node markers
    edge_alpha : float, default=0.4
        Alpha transparency for edges
    highlight_communities : bool, default=False
        If True, draw convex hulls around each micro-narrative community
    community_alpha : float, default=0.15
        Alpha transparency for community highlighting
    layout : str, default='spring'
        Layout algorithm: 'spring', 'circular', 'kamada_kawai', or 'spectral'
    layout_params : Optional[Dict], default=None
        Additional parameters to pass to the layout algorithm
    seed : Optional[int], default=None
        Random seed for reproducibility in layout algorithms
    output_path : Optional[str], default=None
        Path to save the figure. If None, figure is not saved
    dpi : int, default=300
        DPI for saved figure
    title : Optional[str], default=None
        Custom title for the plot

    Returns
    -------
    nx.Graph
        NetworkX graph object

    Examples
    --------
    >>> # Basic usage with your own data
    >>> salient = ['S1', 'S2', 'S3']
    >>> micro = ['M1', 'M2', 'M3', 'M4']
    >>> edges = [('M1', 'S1'), ('M2', 'S1'), ('M1', 'M2'), ('M3', 'S2'), ('M4', 'S3')]
    >>> create_narrative_graph_visualization(
    ...     salient_nodes=salient,
    ...     micro_nodes=micro,
    ...     edges=edges,
    ...     output_path='my_graph.png'
    ... )

    >>> # With community highlighting
    >>> communities = {0: ['M1', 'M2'], 1: ['M3'], 2: ['M4']}
    >>> create_narrative_graph_visualization(
    ...     salient_nodes=salient,
    ...     micro_nodes=micro,
    ...     edges=edges,
    ...     communities=communities,
    ...     highlight_communities=True
    ... )

    >>> # Return graph for further analysis
    >>> G = create_narrative_graph_visualization(
    ...     salient_nodes=salient,
    ...     micro_nodes=micro,
    ...     edges=edges,
    ... )
    """
    # Set random seed if provided
    if seed is not None:
        np.random.seed(seed)

    # Create figure
    fig, ax = plt.subplots(figsize=figsize, facecolor="white")

    # Create the graph
    G = nx.Graph()

    # Add nodes with types
    for node in salient_nodes:
        G.add_node(node, node_type="salient")
    for node in micro_nodes:
        G.add_node(node, node_type="micro")

    # Add edges
    G.add_edges_from(edges)

    # Auto-detect communities if not provided
    if communities is None:
        # Create subgraph of only micro-narrative nodes
        micro_subgraph = G.subgraph(micro_nodes).copy()
        # Find connected components as communities
        communities = {
            i: list(component)
            for i, component in enumerate(nx.connected_components(micro_subgraph))
        }

    # Compute layout
    if layout_params is None:
        layout_params = {}

    if layout == "spring":
        pos = nx.spring_layout(G, seed=seed, **layout_params)
    elif layout == "circular":
        pos = nx.circular_layout(G, **layout_params)
    elif layout == "kamada_kawai":
        pos = nx.kamada_kawai_layout(G, **layout_params)
    elif layout == "spectral":
        pos = nx.spectral_layout(G, **layout_params)
    else:
        raise ValueError(
            f"Unknown layout: {layout}. Use 'spring', 'circular', 'kamada_kawai', or 'spectral'"
        )

    # Draw community highlights if requested
    if highlight_communities:
        # Generate colors for communities
        n_communities = len(communities)
        colors = plt.cm.Set3(np.linspace(0, 1, n_communities))

        for comm_id, (comm_nodes) in enumerate(communities.items()):
            nodes = comm_nodes[1]  # Extract node list from tuple
            if len(nodes) < 3:
                continue  # Need at least 3 points for convex hull

            # Get positions of nodes in this community
            points = np.array([pos[node] for node in nodes if node in pos])

            if len(points) >= 3:
                try:
                    # Compute convex hull
                    hull = ConvexHull(points)
                    hull_points = points[hull.vertices]

                    # Add padding to hull
                    center = points.mean(axis=0)
                    hull_points_padded = center + 1.15 * (hull_points - center)

                    # Create polygon patch
                    polygon = mpatches.Polygon(
                        hull_points_padded,
                        closed=True,
                        facecolor=colors[comm_id % len(colors)],
                        edgecolor="none",
                        alpha=community_alpha,
                        zorder=0,
                    )
                    ax.add_patch(polygon)
                except:
                    # Skip if convex hull computation fails (e.g., collinear points)
                    pass

    # Separate edge types
    micro_edges = [
        (u, v)
        for u, v in G.edges()
        if G.nodes[u]["node_type"] == "micro" and G.nodes[v]["node_type"] == "micro"
    ]
    bridge_edges = [
        (u, v)
        for u, v in G.edges()
        if (G.nodes[u]["node_type"] == "micro" and G.nodes[v]["node_type"] == "salient")
        or (G.nodes[u]["node_type"] == "salient" and G.nodes[v]["node_type"] == "micro")
    ]

    # Draw edges within micro-communities
    nx.draw_networkx_edges(
        G,
        pos,
        edgelist=micro_edges,
        width=0.5,
        alpha=edge_alpha * 0.75,
        edge_color="#cccccc",
        ax=ax,
    )

    # Draw edges from micro to salient
    nx.draw_networkx_edges(
        G,
        pos,
        edgelist=bridge_edges,
        width=0.8,
        alpha=edge_alpha,
        edge_color="#888888",
        ax=ax,
    )

    # Draw salient nodes
    salient_coords = np.array([pos[n] for n in salient_nodes if n in pos])
    if len(salient_coords) > 0:
        ax.scatter(
            salient_coords[:, 0],
            salient_coords[:, 1],
            marker=salient_marker,
            s=salient_size,
            c=salient_color,
            edgecolors=salient_edge_color,
            linewidths=1.5,
            zorder=3,
            alpha=0.9,
            label="Salient entities",
        )

    # Draw micro-narrative nodes
    micro_coords = np.array([pos[n] for n in micro_nodes if n in pos])
    if len(micro_coords) > 0:
        ax.scatter(
            micro_coords[:, 0],
            micro_coords[:, 1],
            marker="o",
            s=micro_size,
            c=micro_color,
            edgecolors="none",
            zorder=2,
            alpha=0.6,
            label="Micro-narrative nodes",
        )

    # Styling
    ax.set_aspect("equal")
    ax.axis("off")
    ax.legend(
        loc="upper right", frameon=True, fontsize=11, markerscale=1.5, framealpha=0.9
    )

    # Set title
    if title is None:
        title = (
            "Narrative Graph Structure:\nMicro-narratives Connected to Salient Entities"
        )
    plt.title(title, fontsize=14, pad=20, fontweight="bold")

    plt.tight_layout()

    # Save if output path provided
    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=dpi, bbox_inches="tight", facecolor="white")
        print(f"Figure saved to: {output_path}")

    plt.show()

    # Print statistics
    print(
        f"Graph created with {len(salient_nodes)} salient nodes and {len(micro_nodes)} micro-narrative nodes"
    )
    print(f"Total edges: {G.number_of_edges()}")
    print(f"Communities: {len(communities)}")

    return G


def visualize_pmi_by_frequency(coocs: pd.DataFrame):
    # Create frequency bins
    max_freq = max(
        coocs["entity_one_frequency"].max(), coocs["entity_two_frequency"].max()
    )
    freq_bins = [0] + [2**i for i in range(0, int(np.log2(max_freq)) + 1)]

    df = pd.DataFrame()

    # Bin the data
    df["x_bin"] = pd.cut(coocs.entity_one_frequency, bins=freq_bins)
    df["y_bin"] = pd.cut(coocs.entity_two_frequency, bins=freq_bins)
    df["pmi"] = coocs.pmi

    # Calculate mean PMI for each cell
    heatmap_data = df.groupby(["x_bin", "y_bin"], observed=True)["pmi"].mean().unstack()

    # Create labels from bin edges
    def format_bin_label(val):
        if val < 1000:
            return str(int(val))
        else:
            return f"{int(val / 1000)}k"

    bin_labels = [
        format_bin_label(b) for b in freq_bins[1 : len(heatmap_data.columns) + 1]
    ]  # skip 0

    # Plot
    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(heatmap_data, cmap="grey", aspect="auto", origin="lower")

    # Labels
    ax.set_xlabel("Frequency of entity 1", fontsize=20)
    ax.set_ylabel("Frequency of entity 2", fontsize=20)
    ax.set_xticks(range(len(heatmap_data.columns)))
    ax.set_yticks(range(len(heatmap_data.index)))
    ax.set_xticklabels(bin_labels)
    ax.set_yticklabels(bin_labels)

    # Colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label("Mean PMI", rotation=270, labelpad=20, fontsize=20)

    plt.tight_layout()
    plt.show()
