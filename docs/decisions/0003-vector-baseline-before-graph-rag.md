# 0003: Vector baseline before graph RAG

- **Status:** Accepted
- **Date:** 2026-11-02

## Context

The bylaw is heavily cross-referenced (provisions point to definitions, tables, other
sections and zone exceptions), which makes graph RAG and agentic retrieval appealing. But
without a working pipeline and an eval set, there is no way to tell whether a more complex
technique actually helps.

## Decision

Build a deliberately simple vector-RAG baseline end to end first: fixed chunking rules, one
embedding model, top-k cosine retrieval, a simple prompt, scored on a labelled question set.
Then add techniques one at a time, each as a new `Retriever` implementation, in this order:
hybrid → graph RAG → agentic → geo (address → parcel → zone).

## Alternatives considered

- **Start with graph RAG:** more interesting, but building the graph, the retriever and the
  eval at the same time makes it hard to know what is working.

## Consequences

- The baseline's job is to be beaten. Its results go in the README as the first row.
- Every later technique must be compared on the same question set and config format, which
  is why the stage interfaces are fixed early (see docs/architecture.md).
- Weak spots the baseline shows (for example cross-reference questions) become the
  motivation for graph RAG, rather than assuming it up front.
