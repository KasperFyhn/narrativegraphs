import math
import plotly.graph_objects as go
import networkx as nx
import plotly.colors as pcolors

from narrativegraph.visualization.common import Node, Edge


# TODO: Hacky solution with Gemini; go through and rewrite

class GraphPlotter:
    def __init__(self, edges: list[Edge], nodes: list[Node]):
        self.edges = edges
        self.nodes = nodes
        self.G = nx.DiGraph()
        self.pos = {}

        # --- Dynamic Category Initialization ---
        self.all_unique_categories = set()
        for node in nodes:
            for cat in node.categories:
                self.all_unique_categories.add(cat)
        for edge in edges:
            for cat in edge.categories:
                self.all_unique_categories.add(cat)

        # Sort categories for consistent color assignment across runs
        self.sorted_categories = sorted(list(self.all_unique_categories))

        self.category_colors = {}
        color_palette = pcolors.qualitative.D3 + pcolors.qualitative.Alphabet + pcolors.qualitative.Dark24

        # Assign a color to each unique category
        for i, category in enumerate(self.sorted_categories):
            self.category_colors[category] = color_palette[i % len(color_palette)]

        # Add a default color for "Uncategorized" elements if they exist
        self.category_colors["Uncategorized"] = "#cccccc"

        self._initialize_graph()

    def _initialize_graph(self):
        """Initializes the NetworkX graph with nodes and edges."""
        for node in self.nodes:
            self.G.add_node(node.id, label=node.label, weight=node.weight, categories=node.categories)
        for edge in self.edges:
            self.G.add_edge(edge.source_id, edge.target_id, label=edge.label, weight=edge.weight,
                            categories=edge.categories)

        self.pos = nx.spring_layout(self.G, k=0.5, iterations=50)

    def _get_element_category(self, element_categories: list[str]) -> str:
        """Determines the primary category for an element. Now uses any category found."""
        # We now just use the first category in the list for coloring,
        # since all categories are dynamic.
        if element_categories:
            return element_categories[0]
        return "Uncategorized"

    def _create_edge_traces(self) -> dict[str, list[go.Scatter]]:
        category_edge_traces = {cat: [] for cat in self.sorted_categories + ["Uncategorized"]}

        # Estimate plot aspect ratio (assuming equal scale for now, or approximate based on layout)
        # You might make this dynamic by pulling from your layout if you vary plot size
        aspect_ratio = 1.0  # Set to y_range / x_range if known

        for u, v, data in self.G.edges(data=True):
            x0, y0 = self.pos[u]
            x1, y1 = self.pos[v]

            edge_category = self._get_element_category(data['categories'])
            edge_color = self.category_colors.get(edge_category, "#888")

            # Line trace
            edge_trace = go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                line=dict(width=data['weight'] * 2, color=edge_color),
                hoverinfo='text',
                text=f"Edge: {data['label']}<br>Weight: {data['weight']}<br>Categories: {', '.join(data['categories']) or 'None'}",
                mode='lines',
                showlegend=False,
                legendgroup=edge_category,
                name=edge_category,
            )
            category_edge_traces[edge_category].append(edge_trace)

            dx, dy = x1 - x0, y1 - y0
            length = math.hypot(dx, dy)
            if length == 0:
                continue
            ux, uy = dx / length, dy / length

            # Corrected perpendicular (adjust y for aspect ratio)
            px, py = -uy / aspect_ratio, ux * aspect_ratio
            perp_len = math.hypot(px, py)
            px /= perp_len
            py /= perp_len

            # Arrow base location
            offset_ratio = 0.55
            base_x = x0 + dx * offset_ratio
            base_y = y0 + dy * offset_ratio

            size = 0.02
            tip_x = base_x + ux * size
            tip_y = base_y + uy * size
            left_x = base_x + px * size / 2
            left_y = base_y + py * size / 2
            right_x = base_x - px * size / 2
            right_y = base_y - py * size / 2

            arrow_trace = go.Scatter(
                x=[left_x, tip_x, right_x, left_x],
                y=[left_y, tip_y, right_y, left_y],
                fill='toself',
                mode='lines',
                line=dict(color=edge_color, width=1),
                fillcolor=edge_color,
                hoverinfo='skip',
                showlegend=False,
                legendgroup=edge_category,
                name=edge_category,
            )
            category_edge_traces[edge_category].append(arrow_trace)

        return category_edge_traces

    def _create_edge_label_traces(self) -> list[go.Scatter]:
        """Generates go.Scatter traces for edge labels, one per category."""
        # Use all detected categories + 'Uncategorized' for dict initialization
        edge_label_data_by_category = {cat: {'x': [], 'y': [], 'text': []}
                                       for cat in self.sorted_categories + ["Uncategorized"]}

        for u, v, data in self.G.edges(data=True):
            edge_category = self._get_element_category(data['categories'])
            x0, y0 = self.pos[u]
            x1, y1 = self.pos[v]
            mid_x = (x0 + x1) / 2
            mid_y = (y0 + y1) / 2
            edge_label_data_by_category[edge_category]['x'].append(mid_x)
            edge_label_data_by_category[edge_category]['y'].append(mid_y)
            edge_label_data_by_category[edge_category]['text'].append(data['label'])

        edge_label_traces = []
        # Iterate over sorted_categories to ensure consistent ordering in legend
        for category in self.sorted_categories + ["Uncategorized"]:
            if edge_label_data_by_category[category]['x']:
                edge_label_trace = go.Scatter(
                    x=edge_label_data_by_category[category]['x'],
                    y=edge_label_data_by_category[category]['y'],
                    mode='text',
                    text=edge_label_data_by_category[category]['text'],
                    textposition="middle center",
                    hoverinfo='text',
                    showlegend=False,
                    textfont=dict(color='black', size=9),
                    legendgroup=category,
                    name=category
                )
                edge_label_traces.append(edge_label_trace)
        return edge_label_traces

    def _create_node_traces(self) -> list[go.Scatter]:
        """Generates go.Scatter traces for nodes, one per category."""
        # Use all detected categories + 'Uncategorized' for dict initialization
        node_data_by_category = {cat: {'x': [], 'y': [], 'size': [], 'color': [], 'hovertext': [], 'label': []}
                                 for cat in self.sorted_categories + ["Uncategorized"]}

        for node_id in self.G.nodes():
            node_data = self.G.nodes[node_id]
            x, y = self.pos[node_id]
            node_size = node_data['weight'] * 15
            node_category = self._get_element_category(node_data['categories'])
            # Get color from the dynamically created map
            node_color = self.category_colors.get(node_category, '#cccccc')


            node_data_by_category[node_category]['x'].append(x)
            node_data_by_category[node_category]['y'].append(y)
            node_data_by_category[node_category]['size'].append(node_size)
            node_data_by_category[node_category]['color'].append(node_color)
            node_data_by_category[node_category]['hovertext'].append(
                f"Node: {node_data['label']}<br>"
                f"Weight: {node_data['weight']}<br>"
                f"Categories: {', '.join(node_data['categories']) or 'None'}"
            )
            node_data_by_category[node_category]['label'].append(node_data['label'])

        node_traces = []
        # Iterate over sorted_categories to ensure consistent ordering in legend
        for category in self.sorted_categories + ["Uncategorized"]:
            if node_data_by_category[category]['x']:
                node_trace = go.Scatter(
                    x=node_data_by_category[category]['x'],
                    y=node_data_by_category[category]['y'],
                    mode='markers+text',
                    hoverinfo='text',
                    hovertext=node_data_by_category[category]['hovertext'],
                    marker=dict(
                        size=node_data_by_category[category]['size'],
                        color=node_data_by_category[category]['color'],
                        line_width=2,
                        line_color='black',
                    ),
                    text=node_data_by_category[category]['label'],
                    textposition="top center",
                    showlegend=False,
                    legendgroup=category,
                    name=category
                )
                node_traces.append(node_trace)
        return node_traces

    def _create_legend_traces(self, category_edge_traces: dict, node_traces: list) -> list[go.Scatter]:
        """Generates invisible traces for the legend, controlling category visibility."""
        legend_traces = []

        # Determine all categories that actually have elements to display in the legend
        categories_with_elements = set()
        for cat_list_dict in [category_edge_traces, {t.legendgroup: t for t in node_traces}]:  # Simplified check
            for cat, elements in cat_list_dict.items():
                if elements:  # Check if there are any elements (traces or data points) for this category
                    categories_with_elements.add(cat)

        # Ensure "Uncategorized" is added if it has elements
        if "Uncategorized" in categories_with_elements and "Uncategorized" not in self.sorted_categories:
            all_display_categories_sorted = self.sorted_categories + ["Uncategorized"]
        else:
            all_display_categories_sorted = self.sorted_categories

        for category in all_display_categories_sorted:
            # Only add to legend if it actually has elements associated with it
            if category in categories_with_elements:
                legend_traces.append(
                    go.Scatter(
                        x=[None], y=[None],
                        mode='markers',
                        marker=dict(size=10, color=self.category_colors[category], symbol='circle'),
                        name=category,
                        showlegend=True,
                        legendgroup=category,
                    )
                )
        return legend_traces

    def _build_figure_data(self) -> list:
        """Combines all individual traces into the final list for go.Figure."""
        category_edge_traces = self._create_edge_traces()
        edge_label_traces = self._create_edge_label_traces()
        node_traces = self._create_node_traces()
        legend_traces = self._create_legend_traces(category_edge_traces, node_traces)

        fig_data = []
        # Iterate over sorted_categories to maintain consistent ordering in the plot and legend
        for category in self.sorted_categories + ["Uncategorized"]:
            fig_data.extend(category_edge_traces.get(category, []))  # Use .get to handle categories with no edges
            fig_data.extend(t for t in edge_label_traces if t.legendgroup == category)
            fig_data.extend(t for t in node_traces if t.legendgroup == category)

        fig_data.extend(legend_traces)
        return fig_data

    def plot(self):
        """Creates and displays the Plotly graph."""
        fig_data = self._build_figure_data()

        fig = go.Figure(data=fig_data,
                        layout=go.Layout(
                            title=dict(
                                text="<br>Network Graph with Dynamic Category Filtering",
                                font=dict(size=16)
                            ),
                            showlegend=True,
                            hovermode='closest',
                            margin=dict(b=20, l=5, r=5, t=40),
                            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                            legend=dict(
                                itemclick="toggle",
                                itemdoubleclick="toggleothers"
                            )
                        ))

        fig.show()


# --- Example Usage ---
if __name__ == '__main__':
    sample_nodes = [
        Node(id=i, label=str(i), categories=["test"]) for i in range(100)
    ]

    sample_edges = [
        Edge(source_id=i, target_id=i+1, label=f"{i}>{i+1}", categories=["test"]) for i in range(99)
    ]

    GraphPlotter(sample_edges, sample_nodes).plot()
