# Create and inspect

The basic workflow of creating and inspecting a narrative graph is:

1. Import `narrativegraphs`.
2. Prepare your documents as a list of strings.
3. Initialize a model and fit it on your docs.
4. Serve the visualizer, follow the link, and inspect your docs visually.

```python
from narrativegraphs import NarrativeGraph

docs: list[str] = [...]  # your list of documents
model = NarrativeGraph().fit(docs)
model.serve_visualizer()
```

Open the link in your terminal to explore the graph in your browser:

![visualizer-screenshot.png](https://raw.githubusercontent.com/KasperFyhn/narrativegraphs/refs/heads/main/assets/visualizer-screenshot.png)

