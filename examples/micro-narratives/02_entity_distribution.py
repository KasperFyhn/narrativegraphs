"""Analyse the frequency distribution of extracted entities."""

from contextlib import redirect_stdout

from config import DB_PATH
from sharedutils import fit_and_visualize_entity_frequencies, output_path

from narrativegraphs import CooccurrenceGraph

model = CooccurrenceGraph.load(DB_PATH)

unresolved_ents_df = (
    model.entity_mentions_.groupby("entity_span_text")
    .size()
    .reset_index(name="frequency")
)
resolved_ents_df = model.entities_

fit_and_visualize_entity_frequencies(
    unresolved_ents_df,
    save_path=output_path("02_zipf_unresolved_entities.png"),
)
fit_and_visualize_entity_frequencies(
    resolved_ents_df,
    save_path=output_path("02_zipf_resolved_entities.png"),
)

with open(output_path("02_hapax_legomena.txt"), "w") as f, redirect_stdout(f):
    hapax = model.entities_[model.entities_.frequency == 1]
    print(f"Hapax legomena (frequency == 1): {len(hapax)}\n")
    print(hapax.to_string())
