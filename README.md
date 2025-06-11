# Narrative Graph

## Basic usage

```python
from narrativegraph import NarrativeGraph
docs = ...  # list[str], provided by user
model = NarrativeGraph().fit(docs)
model.serve_visualizer()
```

See [demo notebook](demo.ipynb) for a working example.