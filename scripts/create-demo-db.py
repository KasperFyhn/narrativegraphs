import kagglehub
from kagglehub import KaggleDatasetAdapter

from narrativegraphs import NarrativeGraph

data = kagglehub.dataset_load(
    KaggleDatasetAdapter.PANDAS,
    "rmisra/news-category-dataset",
    "News_Category_Dataset_v3.json",
    pandas_kwargs=dict(lines=True),
)

# create a sample
sample = data[data["category"].isin(["U.S. NEWS", "POLITICS"])].sample(
    5000, random_state=42
)
docs = sample["headline"] + "\n\n" + sample["short_description"]
ids = sample["link"].replace(
    "https://www.huffpost.com/entry/", ""
)  # get rit of the first part of the URL
categories = sample["category"]
timestamps = sample["date"]


model = NarrativeGraph()
model.fit(docs, doc_ids=ids, categories=categories, timestamps=timestamps)
model.save_to_file("ignored/demo.db", overwrite=True)
