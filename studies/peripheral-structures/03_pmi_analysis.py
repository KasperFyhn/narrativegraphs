"""Visualise how PMI varies with entity frequency."""

from config import DB_PATH
from sharedutils import output_path, visualize_pmi_by_frequency

from narrativegraphs import CooccurrenceGraph

model = CooccurrenceGraph.load(DB_PATH)

visualize_pmi_by_frequency(
    model.cooccurrences_,
    save_path=output_path("03_pmi_by_frequency.png"),
)
