# narrativegraphs

A Python package for building and analyzing narrative graphs from text corpora.

## Installation
The package is available via `pip`.

```bash
pip install narrativegraphs
```

See the [Installation guide](getting-started/installation.md) for more options.

## Basic usage
Given just a list of strings (your input documents), you can easily create a model and inspect it with the interactive visualizer in just a few lines of code.

```
from narrativegraph import NarrativeGraph
docs = ...  # list[str], provided by user
model = NarrativeGraph()
model.fit(docs)
model.serve_visualizer()
```



## Features

- **Plug'n'play**: Get started with a few lines of code!
- **Interactive visualization**: The package is shipped with an interactive React app which can be hosted directly from Python and accessed in your browser.
- **Modular structure**: Switch out pipeline components to accommodate _your_ use case. Use ones shipped with the package or define your own after simple protocols.

## Citation

If you use this package in academic work, please cite:

```bibtex
@software{narrativegraphs,
  author = {Fyhn, Kasper},
  title = {narrativegraphs: A Python package for narrative graph analysis},
  year = {2026},
  url = {https://github.com/kasperfyhn/narrativegraphs}
}
```
