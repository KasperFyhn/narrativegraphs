# Installation

## From PyPI (Recommended)

```bash
pip install narrativegraphs
```

## From Source

For the latest development version:

```bash
pip install git+https://github.com/kasperfyhn/narrativegraphs.git
```

Or clone and install in editable mode for development:

```bash
git clone https://github.com/kasperfyhn/narrativegraphs.git
cd narrativegraphs
pip install -e ".[dev]"
```

## Setting Up spaCy Models

After installation, download the spaCy model(s) you need:

```bash
python -m spacy download en_core_web_sm  # English, small
python -m spacy download da_core_news_sm  # Danish, small
```
