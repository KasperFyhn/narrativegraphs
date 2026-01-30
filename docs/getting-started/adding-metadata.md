# Metadata
The `NarrativeGraph.fit()` method takes a few extra **optional** parameters that serve as metadata for your docs. These are document IDs, timestamps and categories.

If available for your data, it can be valuable. Timestamps and categories will give some more options for slicing the graph data in the visualizer. IDs are mostly a reference point if you are looking for a specific document.

They should be served as lists of the same length.

```python
from narrativegraphs import NarrativeGraph
from datetime import date

docs: list[str] = [...]  # your list of documents
doc_ids: list[int] = [...]  # your list of document IDs
timestamps: list[date] = [...]  # your list of dates
categories: list[str] = [...]  # your list of categories as a string
model = NarrativeGraph().fit(
    docs,
    doc_ids=doc_ids,
    timestamps=timestamps,
    categories=categories
)
model.serve_visualizer()
```

