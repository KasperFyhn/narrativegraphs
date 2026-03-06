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
        if last_size and size > 2 * last_size or size > 100:
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


def spike_analysis(comms_with_contexts, model):
    docs = model.documents_
    if "timestamp_ordinal" in docs.columns and docs["timestamp_ordinal"].notna().all():
        doc_id_to_timestamp = dict(zip(docs.id, docs.timestamp_ordinal))
    else:
        doc_id_to_timestamp = dict(zip(docs.id, docs.timestamp))

    spike_values, spread_values = [], []
    for comm, contexts in comms_with_contexts:
        timestamps = [doc_id_to_timestamp[c.doc_id] for c in contexts]
        spike_values.append(len({c.doc_id for c in contexts}))
        delta = max(timestamps) - min(timestamps)
        spread = delta.days + 1 if hasattr(delta, "days") else int(delta) + 1
        spread_values.append(spread)
    return spike_values, spread_values


def fit_and_visualize_entity_frequencies(
    df: pd.DataFrame,
    save_path: str,
    label: str = "Baseline",
    color: str = "steelblue",
    ax: plt.Axes = None,
) -> plt.Axes:
    """Zipf's law check for a single distribution. Can plot onto an existing axis for
    overlay."""
    df_sorted = df.sort_values("frequency", ascending=False).reset_index(drop=True)
    df_sorted["rank"] = df_sorted.index + 1

    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots()

    ax.loglog(
        df_sorted["rank"],
        df_sorted["frequency"],
        "o",
        markersize=3,
        alpha=0.7,
        color=color,
        label=label,
    )

    log_rank = np.log(df_sorted["rank"])
    log_freq = np.log(df_sorted["frequency"])
    slope, intercept = np.polyfit(log_rank, log_freq, 1)
    ax.loglog(
        df_sorted["rank"],
        np.exp(intercept) * df_sorted["rank"] ** slope,
        "--",
        color=color,
        alpha=0.5,
        label=f"{label} fit: slope = {slope:.2f}",
    )

    ax.set_xlabel("Rank")
    ax.set_ylabel("Frequency")
    ax.set_title("Zipf's Law Check")
    ax.legend()

    if standalone:
        fig = ax.get_figure()
        fig.savefig(save_path, bbox_inches="tight")
        plt.close(fig)

    return ax


def overlay_zipf_comparison(
    df_baseline: pd.DataFrame,
    df_coref: pd.DataFrame,
    save_path: str,
) -> None:
    """Overlay Zipf plots for baseline and coref distributions."""
    fig, ax = plt.subplots()
    ax = fit_and_visualize_entity_frequencies(
        df_baseline, save_path=None, label="Baseline", color="steelblue", ax=ax
    )
    ax = fit_and_visualize_entity_frequencies(
        df_coref, save_path=None, label="Coref", color="tomato", ax=ax
    )
    ax.set_title("Zipf's Law: Baseline vs. Coref")
    fig.savefig(save_path, bbox_inches="tight")
    plt.close(fig)


def scatter_frequency_shift(
    df_baseline: pd.DataFrame,
    df_coref: pd.DataFrame,
    save_path: str,
    annotate_top_n: int = 10,
) -> None:
    """
    Scatter plot of entity frequencies: baseline (x) vs coref (y).
    Points below the diagonal gained counts; points above lost counts.
    Annotates the top_n entities by absolute shift.
    """
    merged = df_baseline.merge(
        df_coref, on="entity", suffixes=("_baseline", "_coref"), how="outer"
    ).fillna(0)
    merged["abs_shift"] = (
        merged["frequency_coref"] - merged["frequency_baseline"]
    ).abs()

    fig, ax = plt.subplots()

    scatter = ax.scatter(
        merged["frequency_baseline"] + 1,  # +1 to avoid log(0)
        merged["frequency_coref"] + 1,
        c=merged["abs_shift"],
        cmap="RdYlGn_r",
        alpha=0.6,
        s=20,
        norm=plt.matplotlib.colors.LogNorm(),
    )
    fig.colorbar(scatter, ax=ax, label="Absolute frequency shift")

    # Diagonal reference line
    max_val = (
        max(merged["frequency_baseline"].max(), merged["frequency_coref"].max()) + 1
    )
    ax.plot([1, max_val], [1, max_val], "k--", linewidth=0.8, label="No change")

    # Annotate top shifted entities
    top = merged.nlargest(annotate_top_n, "abs_shift")
    for _, row in top.iterrows():
        ax.annotate(
            row["entity"],
            xy=(row["frequency_baseline"] + 1, row["frequency_coref"] + 1),
            fontsize=7,
            alpha=0.8,
        )

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Baseline frequency")
    ax.set_ylabel("Coref frequency")
    ax.set_title("Entity frequency shift: Baseline vs. Coref")
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
