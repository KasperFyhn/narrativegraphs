# Narrative Graph

## Basic usage

```python
from narrativegraphs import NarrativeGraph
docs = ...  # list[str], provided by user
model = NarrativeGraph().fit(docs)
model.serve_visualizer()
```

You can then access the visualizer in your browser which looks like this.

![visualizer-screenshot.png](assets/visualizer-screenshot.png)

See [demo notebook](demo.ipynb) for a working example.