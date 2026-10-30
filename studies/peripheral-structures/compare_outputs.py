"""Compare CooccurrenceGraph outputs for the lotr vs. lotr_coref configs."""

import os
from contextlib import redirect_stdout

from sharedutils import (
    fit_and_visualize_entity_frequencies,
    overlay_zipf_comparison,
    scatter_frequency_shift,
)

from narrativegraphs import CooccurrenceGraph

# --- Config ---
CONFIG_A = "lotr"
CONFIG_B = "lotr_coref"

DB_A = f"output/{CONFIG_A}/{CONFIG_A}.db"
DB_B = f"output/{CONFIG_B}/{CONFIG_B}.db"

OUT_DIR = f"output/compare_{CONFIG_A}_vs_{CONFIG_B}"
os.makedirs(OUT_DIR, exist_ok=True)


def out(filename: str) -> str:
    return os.path.join(OUT_DIR, filename)


# --- Load models ---
model_a = CooccurrenceGraph.load(DB_A)
model_b = CooccurrenceGraph.load(DB_B)

# --- Prepare entity DataFrames ---
# entities_ has columns: id, label, frequency, doc_frequency, ...
# The sharedutils comparison helpers expect an "entity" column.
ents_a = model_a.entities_.rename(columns={"label": "entity"})
ents_b = model_b.entities_.rename(columns={"label": "entity"})

# --- Zipf overlay ---
overlay_zipf_comparison(
    ents_a,
    ents_b,
    save_path=out("zipf_overlay.png"),
)

# --- Per-config Zipf (for reference) ---
fit_and_visualize_entity_frequencies(
    ents_a,
    save_path=out(f"zipf_{CONFIG_A}.png"),
    label=CONFIG_A,
    color="steelblue",
)
fit_and_visualize_entity_frequencies(
    ents_b,
    save_path=out(f"zipf_{CONFIG_B}.png"),
    label=CONFIG_B,
    color="tomato",
)

# --- Frequency shift scatter ---
scatter_frequency_shift(
    ents_a,
    ents_b,
    save_path=out("frequency_shift.png"),
)

# --- Summary stats ---
coocs_a = model_a.cooccurrences_
coocs_b = model_b.cooccurrences_

hapax_a = ents_a[ents_a["frequency"] == 1]
hapax_b = ents_b[ents_b["frequency"] == 1]

merged = (
    ents_a[["entity", "frequency"]]
    .merge(
        ents_b[["entity", "frequency"]],
        on="entity",
        suffixes=("_a", "_b"),
        how="outer",
    )
    .fillna(0)
)

only_a = merged[merged["frequency_b"] == 0]
only_b = merged[merged["frequency_a"] == 0]
shared = merged[(merged["frequency_a"] > 0) & (merged["frequency_b"] > 0)]

with open(out("summary.txt"), "w") as f, redirect_stdout(f):
    col_a = CONFIG_A.rjust(12)
    col_b = CONFIG_B.rjust(14)
    print(f"{'Metric':<35} {col_a} {col_b}")
    print("-" * 65)
    print(
        f"{'Documents':<35} {len(model_a.documents_):>12} {len(model_b.documents_):>14}"
    )
    print(f"{'Entities':<35} {len(ents_a):>12} {len(ents_b):>14}")
    print(f"{'Cooccurrences':<35} {len(coocs_a):>12} {len(coocs_b):>14}")
    print(f"{'Hapax legomena (freq=1)':<35} {len(hapax_a):>12} {len(hapax_b):>14}")
    print()
    print(f"{'Shared entities':<35} {len(shared):>12}")
    print(f"{'Only in ' + CONFIG_A:<35} {len(only_a):>12}")
    print(f"{'Only in ' + CONFIG_B:<35} {len(only_b):>14}")
    print()

    # Top entities that gained or lost frequency with coref
    top_gained = merged.nlargest(10, "frequency_b").assign(
        shift=lambda d: d["frequency_b"] - d["frequency_a"]
    )
    top_lost = merged.assign(
        shift=lambda d: d["frequency_b"] - d["frequency_a"]
    ).nsmallest(10, "shift")

    print("Top 10 entities by absolute frequency gain (coref > baseline):")
    for _, row in top_gained.iterrows():
        print(
            f"  {row['entity']:<40} {int(row['frequency_a']):>6} -> "
            f"{int(row['frequency_b']):<6}  ({int(row['shift']):+})"
        )

    print()
    print("Top 10 entities by absolute frequency loss (baseline > coref):")
    for _, row in top_lost.iterrows():
        print(
            f"  {row['entity']:<40} {int(row['frequency_a']):>6} -> "
            f"{int(row['frequency_b']):<6}  ({int(row['shift']):+})"
        )
