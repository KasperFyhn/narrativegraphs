# Micro-narrative analysis of _The Lord of the Rings_

In this analysis, we try to extract "micro-narratives" from _The Lord of the Rings_ (LotR). A narrative graph provides a macro-view of a text collection, in this case three books of one series. Using community detection on the graph with PMI as edge weightings, we can extract small communities where connections between rare entities are favored due to PMI's inflation of rare events.

Scripts run in order: `01` → `02` → `03` → `04` → `05` → `06` → `07`.

---

## Building the graph (`01_build_graph.py`)

Text sections are split on double line breaks surrounded by non-whitespace, which keeps poems and songs together as single units. The fitted `CooccurrenceGraph` is persisted to `lotr.db` via the built-in SQLite backend; subsequent runs call `.load()` to skip re-extraction.

---

## Distribution of entities (`02_entity_distribution.py`)

Below, we look at the distribution of extracted entities. As for single-word distributions, we expect to be in the central Large Number of Rare Events (LNRE) zone where we see a long tail of distinct, rare entities. The number of distinct entities (our vocabulary) grows with the size of the corpus. Additionally, according to Zipf's law, we should see that the most frequent entities make up a considerable portion of the total number of entity occurrences.

We look at both unresolved entity mentions and resolved entity mentions, but onwards we use the resolved entities.

Both roughly fit a Zipfian distribution. The resolved entities have a slightly steeper slope as "the rich get richer" by adding lower frequency counts of some entities to other entities. Hence, the ranked list becomes shorter, but the total number of entity occurrences are the same.

In this analysis, we are interested in the lower end of the tail: the large number of rare entities. We try to see how these many distinct but rare entities fit into the narrative.

We see a significant portion of hapax legomena – single occurrence entities. While these may also be meaningful, this is also where we see the most noise from extraction errors.

From here and onwards we will consider entities with a frequency above 1, i.e. `minimum_node_frequency=2` in `GraphFilter`.

---

## PMI weighting of entity cooccurrences (`03_pmi_analysis.py`)

In our fitted cooccurrence graph, we can calculate pointwise mutual information between entities $A$ and $B$:

$$PMI(A, B) = \log \frac{P(A, B)}{P(A)P(B)}$$

PMI is known to inflate for rare events. And more generally, it is higher for lower frequency items, as seen in the heatmap.

This means – one of the core hypotheses of this analysis – that if we weight edges in our graph with PMI and/or filter edges by PMI, we can surface the rare entity connections as well as particularly strong connections with the more frequent entities.

We can sort of eyeball which area we are interested in: anything above `min_weight = 2.5` will on average retain half of connections in the 200–300 frequency area and therefore even more in the lower end.

---

## Community detection (`04_community_detection.py`)

### K-clique

K-clique community detection finds all communities of k-cliques and further merges those that share k−1 nodes. It allows for overlapping communities.

There are two hyperparameters:

- **k**: the minimum size of a clique. The smaller, the more small cliques we get, but the more merged cliques in bigger communities we get.
- **w**: the minimum weight of an edge, in our case PMI.

A thing that tends to happen according to the authors of the method is that one giant community tends to show up that eats up a lot of smaller communities. This can be alleviated by tuning hyperparameters, but we may also interpret it differently: this giant community means that whatever micro-narratives are in there are not sufficiently delimited from the general narrative. We keep this community on the side and do not mix it in with the rest.

We let `k=4` to allow for small meaningful communities. `k=2` essentially yields connected components (since it merges all connected nodes) and is therefore too small. `k=3` also results in too many cliques being merged into one giant community.

### Louvain

Louvain community detection finds communities by optimizing towards modularity, merging smaller communities into bigger ones iteratively while modularity increases. It creates non-overlapping communities.

There are several hyperparameters, but we consider only:

- **resolution**: higher values result in smaller communities.

The NetworkX implementation of Louvain considers edge weights, so we need not filter by PMI but rather leave the weighting to the algorithm.

---

## Comparison of k-clique and Louvain (`05_community_comparison.py`)

After fiddling with hyperparameters, we land at a place where the sizes of the communities are comparable.

So why, when they are of comparable sizes, are there so many more k-clique communities? Due to overlap: entities can belong to multiple k-clique communities simultaneously, while Louvain is non-overlapping.

Quantifying overlap between the two methods shows that they produce quite different communities, suggesting they capture complementary structure in the graph.

---

## Typology of communities (`06_typology_analysis.py`, `07_explore_communities.py`)

Intuitively, micro-narratives can appear in a few ways, with these as reference points on a two-dimensional continuum:

1. Appear once
2. Appear a few times in close vicinity
3. Appear multiple times in close vicinity
4. Appear a few times with great distance
5. Appear multiple times with great distance

From the qualitative assessment, many communities appeared in just one short context snippet in one section of the book. These make up the bulk of the extracted micro-narratives.

We operationalize:

- **Spread**: floored log₁₀ of (max − min doc id + 1) — order of magnitude of the narrative span
- **Spikes**: floored log₂ of unique document count — pair / few / multiple / many

### Single-spike micro-narratives

These appear to be small clusters of rather specific mentions of rare entities. When one thinks about it, it makes sense that these surface as communities in a PMI-weighted graph: they are the rare connections of rare entities.

### Multi-spike micro-narratives

The spread of communities is highly comparable between methods, but Louvain communities tend to have fewer spikes than k-clique communities.

### Typology

Qualitative exploration of the spread × spikes matrix reveals three prototypical micro-narrative types:

| Type          | Spread | Spikes | Character                                                            |
| ------------- | ------ | ------ | -------------------------------------------------------------------- |
| **Episodic**  | low    | any    | Occur within a single section or brief passage                       |
| **Echoing**   | high   | few    | A re-activation of something from much earlier; cross-textual echoes |
| **Recurring** | high   | many   | Recurring narrative elements, motifs, and sub-plots                  |

High-spread, many-spike communities (k-clique only) tend to be noise: generic nouns that tie too many things together and push us out of the micro scale.
