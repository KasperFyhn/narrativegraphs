# NLP Layer

This guide provides an overview of the NLP layer in `narrativegraphs/nlp/`.

## Pipelines

The NLP layer provides two main pipelines that orchestrate the full extraction workflow:

| Pipeline                 | Purpose                              | Extracts                 |
| ------------------------ | ------------------------------------ | ------------------------ |
| **Pipeline**             | Full narrative graph extraction      | Triplets + cooccurrences |
| **CooccurrencePipeline** | Simpler cooccurrence-only extraction | Entities + cooccurrences |

Both pipelines handle:

1. Adding documents to the database
2. Extracting and storing annotations
3. Mapping surface forms to canonical entities/predicates
4. Calculating statistics

### Pipeline (Full)

Uses a `TripletExtractor` to extract subject-predicate-object triplets, then derives entities from those triplets. Also extracts cooccurrences between entities.

Default components:

- Triplet extraction: `DependencyGraphExtractor` (default; `EntityPairDependencyExtractor` is an alternative)
- Cooccurrence extraction: `ChunkCooccurrenceExtractor`
- Entity mapping: `SubgramLemmatizationMapper("noun")`
- Predicate mapping: `SubgramLemmatizationMapper("verb")`

### CooccurrencePipeline

Uses an `EntityExtractor` directly to find entities, then extracts cooccurrences between them. Skips triplet extraction entirely.

Default components:

- Entity extraction: `SpacyEntityExtractor`
- Cooccurrence extraction: `ChunkCooccurrenceExtractor`
- Entity mapping: `SubgramLemmatizationMapper("noun")`

## Extraction Components

### Entity Extraction (`entities/`)

| Class                    | Description                                                        |
| ------------------------ | ------------------------------------------------------------------ |
| **EntityExtractor**      | Abstract base class                                                |
| **SpacyEntityExtractor** | Uses spaCy NER and/or noun chunks with configurable length filters |

`SpacyEntityExtractor` features:

- Configurable NER and noun chunk extraction
- Token length filtering (min/max tokens)
- Greedy non-overlapping span selection (NER takes priority)
- Pronoun filtering
- Parallel batch processing

### Triplet Extraction (`triplets/`)

| Class                             | Description                                                                             |
| --------------------------------- | --------------------------------------------------------------------------------------- |
| **TripletExtractor**              | Abstract base class                                                                     |
| **DependencyGraphExtractor**      | Verb-first (top-down from ROOT); fine-grained boolean flags per relation type           |
| **EntityPairDependencyExtractor** | Entity-pair (bottom-up, path matching); declarative `PathPattern` list; sentence guards |
| **LlmTripletExtractor**           | Prompts an LLM with a plain-language instruction; one request per document              |
| **LlmBatchTripletExtractor**      | The same, through the Message Batches API: half the price, asynchronous                 |

Triplets consist of:

- `subj`: Subject entity (SpanAnnotation)
- `pred`: Predicate/verb (SpanAnnotation)
- `obj`: Object entity (SpanAnnotation)
- `context`: Optional sentence context (AnnotationContext)

Extractors expose one batch method: `batch_extract` yields one result list per document,
in input order, and that is what `Pipeline` zips with its documents. A backend that
finishes documents out of order — as an LLM backend does — puts them back in order
itself, so nothing in the pipeline has to track which document a result belongs to. For
a batch run that is not to be waited on, that reordering is `collect`'s job, and its
result goes back in as pre-computed annotations (see below).

### Cooccurrence Extraction (`tuplets/`)

| Class                             | Description                           |
| --------------------------------- | ------------------------------------- |
| **CooccurrenceExtractor**         | Abstract base class                   |
| **ChunkCooccurrenceExtractor**    | Sentence-based windowed cooccurrences |
| **DocumentCooccurrenceExtractor** | All entity pairs within a document    |

`ChunkCooccurrenceExtractor` features:

- Configurable sentence window size
- Custom boundary patterns (regex or callable)
- Sentence-level context capture

Tuplets consist of:

- `entity_one`, `entity_two`: Entity pair (SpanAnnotation)
- `context`: Optional context window (AnnotationContext)

## Mapping Components (`mapping/`)

Mappers normalize surface forms to canonical labels, creating a `dict[str, str]` mapping.

| Class                          | Description                                |
| ------------------------------ | ------------------------------------------ |
| **Mapper**                     | Abstract base class                        |
| **StemmingMapper**             | Groups by Porter stemmed form              |
| **SubgramStemmingMapper**      | Stemming + subgram matching for head words |
| **SubgramLemmatizationMapper** | Lemma + subgram matching for head words    |

`SubgramLemmatizationMapper` (default):

- First applies lemma normalization
- Then matches shorter forms to longer ones containing them
- Configurable for nouns or verbs via `head_word_type`
- Ranking by shortest label or most frequent

## LLM-Based Components

Where the rule-based components derive relations from the dependency parse, the LLM-based
ones take a plain-language instruction stating what to extract:

```python
from narrativegraphs.nlp.triplets import LlmTripletExtractor

extractor = LlmTripletExtractor(
    "Extract relations between characters and the places they travel to."
)
pipeline = Pipeline(engine, triplet_extractor=extractor)
```

### Which model answers

The components are provider-agnostic. They depend only on `LlmClient`, an interface that
takes a system prompt, a user prompt and a JSON schema and returns the object the model
produced. Structured output is the only thing providers genuinely disagree about, so it is
the only thing abstracted.

Two implementations ship:

| Client                     | Covers                                                           |
| -------------------------- | ---------------------------------------------------------------- |
| **AnthropicClient**        | Claude, immediate or batched                                     |
| **OpenAiCompatibleClient** | OpenAI, LM Studio, Ollama, vLLM — anything speaking its chat API |

Both SDKs are ordinary dependencies rather than extras: they are thin HTTP clients next
to spaCy and scikit-learn, and an extra to install before a model can be prompted costs
more than it saves.

`AnthropicClient` is the default, so the common case needs no client at all. A different
model or a local server is one argument:

```python
from narrativegraphs.nlp.common.llm import AnthropicClient, OpenAiCompatibleClient

# Claude, the default
LlmTripletExtractor("Extract relations between ...")

# a cheaper Claude model
LlmTripletExtractor("...", llm=AnthropicClient(model="claude-haiku-4-5"))

# a local model through Ollama
LlmTripletExtractor(
    "...", llm=OpenAiCompatibleClient("llama3.1:8b", base_url="http://localhost:11434/v1")
)
```

Credentials come from the environment (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`); local
servers ignore the key, so none is needed. Both clients accept a pre-configured SDK client
as `client=`, which is also how the tests inject fakes.

The two differ in what they can do beyond a single request:

- **Effort and prompt caching** are Anthropic features; `AnthropicClient` takes `effort`
  and caches the system prompt. There is no equivalent to map onto a generic server, and
  sampling parameters such as `temperature` are rejected by current Claude models, so
  `temperature` lives on `OpenAiCompatibleClient` only.
- **Batching** is `BatchLlmClient`, a narrower interface that only `AnthropicClient`
  implements. `LlmBatchTripletExtractor` requires it and raises `TypeError` at
  construction otherwise, since most OpenAI-compatible servers have no batch API at all.
- **Sloppy output**: small local models wrap JSON in code fences even when given a schema,
  so `OpenAiCompatibleClient` strips them. `strict` schema adherence is off by default
  because not every compatible server implements it; hosted OpenAI does, and the schemas
  used here are strict-compatible.

### Span alignment

The rest of the package addresses entities by their character offsets in the document,
but a model returns strings. Every returned surface form is therefore located in the
source text again (`common/llm.py`):

1. The quoted evidence sentence is located and becomes the search window as well as the
   triplet's `context`, so that a repeated entity is anchored in the sentence the model
   actually meant.
2. Within that window, the parts are matched in order — verbatim first, then ignoring
   case and whitespace differences — falling back to the whole document and to
   order-independent matching.
3. Triplets with a part that cannot be found, or with overlapping parts, are dropped.
   Hallucinated and paraphrased spans do not reach the database.

The response is declared as a Pydantic model, from which the JSON schema sent to the
model is derived, so the schema and the validation of what comes back cannot drift apart.
Each triplet is validated separately, so one malformed triplet costs only itself.

### Alignment is a quality signal

Dropping what cannot be aligned is also a measurement. `extractor.alignment_stats`
carries `returned`, `kept`, `dropped` and `drop_rate`, and a summary is logged when a
batch run finishes — at WARNING above a 20% drop rate, since that means the model is
paraphrasing rather than quoting and the extraction is not measuring what it appears to.

```python
extractor.alignment_stats.summary()
# '482/500 triplets aligned to the text (3.6% dropped)'
```

### Every mention, not only the ones in a relation

Extractors report the entities of the relations they found, and a generative model
consolidates: a relation stated three times comes back once. Recording only those
entities understates the text, and the mention counts behind co-occurrence, PMI and
community detection are skewed by the shortfall.

`Pipeline` therefore always records every mention of an extracted entity in its
document. Matching is case-insensitive, tolerates differing whitespace, and respects word
boundaries, so "ring" does not match inside "ringing"; added mentions never overlap one
another or an extractor's own spans, and longer surface forms claim their text first. The
entities an extractor reported are always kept exactly as given, since population
resolves triplets by their spans.

What this does not yet catch is pronouns and other referring expressions, which need
coreference resolution during extraction.

### Live or batched

`LlmTripletExtractor` sends one request per document and answers immediately, with
`max_concurrent_requests` in flight at a time, each stored as it returns.

`LlmBatchTripletExtractor` sends the same requests through the Message Batches API at
**half the price**. That work is asynchronous: most batches finish within an hour, the
limit is 24 hours, and a batch hands over nothing until it has ended in full. Documents
are therefore submitted in chunks of `chunk_size`, so that results start landing before
the whole corpus is done. Used as a drop-in extractor, `fit` simply blocks until it is.

### Submitting one day, collecting the next

Batch results stay retrievable for 29 days, so the wait need not be sat through. `submit`
returns the batch IDs and exits; `collect` turns them back into triplets later, which
`fit` accepts as pre-computed annotations:

```python
extractor = LlmBatchTripletExtractor("Extract relations between ...")
batch_ids = extractor.submit(docs)      # write these down, turn the machine off
# ... another day ...
triplets = extractor.collect(batch_ids, docs)
ng = NarrativeGraph().fit(docs, triplets=triplets)
```

`collect` needs the same documents in the same order, because aligning a triplet requires
its source text, and because each request is identified by its document's index. Chunks
end in whatever order the provider finishes them; `collect` puts the results back into
input order, and a document whose request errored or expired comes back as an empty list
rather than going missing.

The same `triplets=` argument serves any pre-computed annotations — extracting once and
fitting several times, for instance to compare mappers over identical triplets.
`CooccurrenceGraph.fit` takes `entities=` in the same way, and both are `annotations=` on
`Pipeline.run`.

### Cost and robustness

- Structured outputs (`output_config.format`) guarantee schema-valid JSON.
- The default `effort="low"` suits bounded extraction at corpus scale; raise it for
  instructions that call for genuine judgement.
- `max_tokens` caps the whole completion, and a thinking model spends that same budget on
  its reasoning before it writes a single triplet. Claude runs adaptive thinking by
  default, and local hybrid-thinking models (Qwen3, DeepSeek-R1-style servers) think by
  default too, so a response can run out of room mid-object. What was complete up to that
  point is kept rather than thrown away, and the cap is logged as a warning naming the
  limit — raise `max_tokens` or send shorter documents if it recurs.
- Refusals, truncated responses and genuinely transient failures — a dropped connection,
  a rate limit, an overloaded server — skip the document with a warning. Everything else
  raises `LlmError`, since every later document would fail the same way: unresolved
  credentials (which the Anthropic SDK reports as a `TypeError`, not an
  `AuthenticationError`, because no request is ever sent), an unknown model, a malformed
  request. Classifying it this way round means an unforeseen failure stops the run rather
  than being swallowed once per document, leaving an empty graph behind.
- A batch request that errored or expired yields no triplets for that document and is
  logged with a summary count at the end, so one bad document does not cost the run.

## Supporting Components

### Common Utilities (`common/`)

| Module            | Purpose                                                                |
| ----------------- | ---------------------------------------------------------------------- |
| **annotation.py** | Data models: `SpanAnnotation`, `AnnotationContext`                     |
| **spacy.py**      | spaCy utilities: model loading, batch size calculation, span filtering |

### Shared vocabularies

`ensure_spacy_model` is the single entry point for loading a spaCy model, and pipelines
loaded from the same model share one `Vocab`.

spaCy deliberately does not cache loaded models, and this package is a good example of
why: a `Language` object is mutable, and the call sites reconfigure it in conflicting
ways — `build_spacy_pipeline` adds a sentencizer and needs the parser enabled, while
`spacy_normalizer` disables the parser. Handing out a shared `Language` would let one of
those silently reconfigure the other.

The `Vocab` is a different matter: it holds the expensive part, it is identical for a
given model, and pipelines only ever add to it. spaCy's `vocab` argument exists precisely
so it can be shared. A `NarrativeGraph` loads `en_core_web_sm` three times over — once for
the triplet extractor and once per mapper — so sharing it cuts construction from about
83 MB to 30 MB, with every pipeline still free to be reconfigured independently.

`clear_shared_vocabs()` drops the cache, which is only needed to isolate tests.
| **transformcategories.py** | Normalizes various category input formats |
| **llm.py** | LLM utilities: JSON requests, concurrency, span alignment |

`SpanAnnotation` represents a text span with:

- `text`: Surface form
- `start_char`, `end_char`: Character offsets
- `normalized_text`: Optional lemma

### Filtering (`filtering/`)

| Class            | Description                                    |
| ---------------- | ---------------------------------------------- |
| **BigramFilter** | PMI-based bigram filtering for quality control |

`BigramFilter` can be used to filter out low-quality multi-word spans based on bigram co-occurrence statistics.

## Architecture Diagram

```
Pipeline / CooccurrencePipeline
    │
    ├── Document ingestion
    │
    ├── Extraction
    │   ├── TripletExtractor ──► Triplet (subj, pred, obj)
    │   │   └── DependencyGraphExtractor (spaCy)
    │   │
    │   ├── EntityExtractor ──► SpanAnnotation
    │   │   └── SpacyEntityExtractor (NER + noun chunks)
    │   │
    │   └── CooccurrenceExtractor ──► Tuplet (entity_one, entity_two)
    │       ├── ChunkCooccurrenceExtractor (sentence window)
    │       └── DocumentCooccurrenceExtractor (all pairs)
    │
    ├── Mapping
    │   └── Mapper ──► dict[str, str]
    │       ├── StemmingMapper
    │       ├── LemmatizationMapper
    │       └── SubgramStemmingMapper (default)
    │       └── SubgramLemmatizationMapper
    │
    └── Stats calculation (via service layer)
```

## Extensibility

All extraction and mapping components use abstract base classes, making it easy to implement custom:

- Entity extractors (e.g., domain-specific NER)
- Triplet extractors (e.g., rule-based, LLM-based)
- Cooccurrence extractors (e.g., paragraph-level, custom boundaries)
- Mappers (e.g., embedding-based clustering, knowledge base linking)
