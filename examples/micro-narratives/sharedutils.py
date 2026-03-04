import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from narrativegraphs.dto.graph import Community
from narrativegraphs.dto.tuplets import TupletGroup


def output_path(filename: str) -> str:
    from config import OUTPUT_DIR

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return os.path.join(OUTPUT_DIR, filename)


def compute_communities(model):
    """Compute (or load from cache) both k-clique and Louvain communities.

    Results are pickled to COMMUNITIES_CACHE_PATH. Delete the file to recompute
    (e.g. after changing hyperparameters in config.py).
    """
    import os
    import pickle

    from config import (
        COMMUNITIES_CACHE_PATH,
        K_CLIQUE_K,
        LOUVAIN_RESOLUTION,
        MIN_NODE_FREQUENCY,
        MIN_WEIGHT,
    )

    if os.path.exists(COMMUNITIES_CACHE_PATH):
        with open(COMMUNITIES_CACHE_PATH, "rb") as f:
            return pickle.load(f)

    from narrativegraphs import GraphFilter

    graph_filter = GraphFilter(minimum_node_frequency=MIN_NODE_FREQUENCY)

    k_clique_comms_raw = model.graph.find_communities(
        graph_filter=graph_filter,
        min_weight=MIN_WEIGHT,
        community_detection_method_args=dict(k=K_CLIQUE_K),
    )

    k_clique_comms_with_contexts = []
    k_clique_big_comms = []
    last_size = None
    for comm in sorted(k_clique_comms_raw, key=lambda c: len(c.members)):
        size = len(comm.members)
        if size < 2:
            continue
        if last_size and size > 2 * last_size:
            k_clique_big_comms.append(comm)
            continue
        contexts = model.tuplets.get_contexts_by_entity_ids(comm.member_ids)
        contexts.sort(key=lambda c: c.doc_id)
        k_clique_comms_with_contexts.append((comm, contexts))
        last_size = size

    louvain_comms_raw = model.graph.find_communities(
        graph_filter=graph_filter,
        min_weight=None,
        community_detection_method="louvain",
        community_detection_method_args=dict(resolution=LOUVAIN_RESOLUTION),
    )

    louvain_comms_with_contexts = []
    for comm in sorted(louvain_comms_raw, key=lambda c: c.score, reverse=True):
        size = len(comm.members)
        if size < 2 or size > 1000:
            continue
        contexts = model.tuplets.get_contexts_by_entity_ids(comm.member_ids)
        contexts.sort(key=lambda c: c.doc_id)
        louvain_comms_with_contexts.append((comm, contexts))

    result = (
        k_clique_comms_with_contexts,
        k_clique_big_comms,
        louvain_comms_with_contexts,
    )
    os.makedirs(os.path.dirname(COMMUNITIES_CACHE_PATH), exist_ok=True)
    with open(COMMUNITIES_CACHE_PATH, "wb") as f:
        pickle.dump(result, f)

    return result


def spike_analysis(comms_with_contexts):
    spike_values, spread_values = [], []
    for comm, contexts in comms_with_contexts:
        ids = {c.doc_id for c in contexts}
        spike_values.append(len(ids))
        spread_values.append(max(ids) - min(ids) + 1)
    return spike_values, spread_values


def fit_and_visualize_entity_frequencies(df: pd.DataFrame, save_path: str):
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
    fig.savefig(save_path, bbox_inches="tight")
    plt.close(fig)


def visualize_pmi_by_frequency(coocs: pd.DataFrame, save_path: str):
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
    fig.savefig(save_path, bbox_inches="tight")
    plt.close(fig)


def print_comm_with_contexts(comm: Community, contexts: list[TupletGroup]):
    print("COMMUNITY:", ", ".join(e.label for e in comm.members))
    for context in contexts:
        context.print_with_ansi_highlight()
    print()


#######################################
# MULTISPIKE MICRO-NARRATIVE ANALYSIS #
#######################################


def multi_spike_df(spike_values, spread_values):
    df = pd.DataFrame(dict(spikes=spike_values, spread=spread_values))
    # remove single spikes
    df = df[df.spikes > 1]
    return df


def multi_spike_heatmap(df, save_path: str):
    fig, ax = plt.subplots(figsize=(14, 5))
    log_base = 10
    df["floored_log_spread"] = np.floor(np.emath.logn(log_base, df.spread))
    df["floored_log_spikes"] = np.floor(np.log2(df.spikes))

    # Pivot to a 2D count matrix
    heat = (
        df.groupby(["floored_log_spread", "floored_log_spikes"], observed=True)
        .size()
        .unstack(fill_value=0)
    )

    # Readable tick labels: use bin midpoints
    x_labels = [f"{int(2**b)}" for b in heat.columns]
    y_labels = [f"{int(log_base**b)}" for b in heat.index]

    sns.heatmap(
        heat,
        ax=ax,
        cmap="YlOrRd",
        xticklabels=x_labels,
        yticklabels=y_labels,
        linewidths=0.3,
        linecolor="white",
        cbar_kws={"label": "# communities"},
        annot=True,
        fmt="d",
    )

    ax.set_xlabel("Spikes (unique documents)")
    ax.set_ylabel("Spread (max − min doc id)")
    ax.tick_params(axis="x", rotation=45)
    ax.tick_params(axis="y", rotation=0)

    plt.suptitle("Community spread vs. spikes", fontsize=14)
    plt.tight_layout()
    fig.savefig(save_path, bbox_inches="tight")
    plt.close(fig)


def activation_score(comm, contexts):
    """A score function to surface those micro-narratives that are the strongest
    activated across their contexts"""
    members = {e.id for e in comm.members}
    scores = []
    for context in contexts:
        activated = {
            e.id
            for tuplet in context.tuplets
            for e in [tuplet.entity_one, tuplet.entity_two]
        }
        scores.append(len(activated) / len(members))
    return np.mean(scores)


def slice_micro_narratives(
    comms_with_contexts, df, min_spread, max_spread, min_spikes, max_spikes
):
    sliced_df = df[
        (min_spread <= df.spread)
        & (df.spread < max_spread)
        & (min_spikes <= df.spikes)
        & (df.spikes < max_spikes)
    ]
    print("Number of comms:", len(sliced_df))
    micro_narratives = [comms_with_contexts[row[0]] for row in sliced_df.iterrows()]
    micro_narratives.sort(key=lambda tpl: activation_score(*tpl), reverse=True)
    return micro_narratives


def print_micro_narratives(
    comms_with_contexts, df, min_spread, max_spread, min_spikes, max_spikes
):
    for comm, context in slice_micro_narratives(
        comms_with_contexts, df, min_spread, max_spread, min_spikes, max_spikes
    ):
        print_comm_with_contexts(comm, context)
