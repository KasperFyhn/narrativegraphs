# Saving and loading

A model can be saved and loaded for later use, so you do not have to re-process documents every time.

To save:

```python
model.save_to_file("my_model.db")
```

To load it again

```python
NarrativeGraph.load("my_model.db")
```

A handy codeblock is:
```python
from narrativegraphs import NarrativeGraph
import os.path

model_name = "my_model.db"
docs: list[str] = [...]  # your list of documents

if os.path.exists(model_name):
    print("Loading model!")
    model = NarrativeGraph.load(model_name)
else:
    print("Creating and saving model!")
    model = NarrativeGraph().fit(docs)
    model.save_to_file(model_name)

model.serve_visualizer()
```