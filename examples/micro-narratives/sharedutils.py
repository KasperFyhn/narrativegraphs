import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from narrativegraphs.dto.graph import Community
from narrativegraphs.dto.tuplets import TupletGroup


def fit_and_visualize_entity_frequencies(df: pd.DataFrame):
    # Assuming df has columns 'entity' and 'frequency'
    df_sorted = df.sort_values("frequency", ascending=False).reset_index(drop=True)
    df_sorted["rank"] = df_sorted.index + 1

    fig, ax = plt.subplots()
    ax.loglog(df_sorted["rank"], df_sorted["frequency"], "o", markersize=3, alpha=0.7)

    # Fit a power law line for reference
    log_rank = np.log(df_sorted["rank"])
    log_freq = np.log(df_sorted["frequency"])
    slope, intercept = np.polyfit(log_rank, log_freq, 1)
    ax.loglog(
        df_sorted["rank"],
        np.exp(intercept) * df_sorted["rank"] ** slope,
        "r--",
        label=f"Fit: slope = {slope:.2f}",
    )

    ax.set_xlabel("Rank")
    ax.set_ylabel("Frequency")
    ax.set_title("Zipf's Law Check")
    ax.legend()
    plt.show()


def visualize_pmi_by_frequency(coocs: pd.DataFrame):
    # Create mirrored copy with swapped entity frequencies
    mirrored = coocs.rename(
        columns={
            "entity_one_frequency": "entity_two_frequency",
            "entity_two_frequency": "entity_one_frequency",
        }
    )

    # Concatenate and proceed with symmetric data
    coocs = pd.concat([coocs, mirrored], ignore_index=True)

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


def print_comm_with_contexts(comm: Community, contexts: list[TupletGroup]):
    print("COMMUNITY:", ", ".join(e.label for e in comm.members))
    for context in contexts:
        context.print_with_ansi_highlight()
    print()
