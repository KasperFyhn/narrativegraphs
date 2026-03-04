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
categories = sample["category"]
timestamps = sample["date"]
metadata = sample[
    [
        "link",
    ]
].to_dict("records")


model = NarrativeGraph()
model.fit(docs, categories=categories, timestamps=timestamps, metadata=metadata)
model.save_to_file("ignored/demo.db", overwrite=True)
