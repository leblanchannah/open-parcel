"""Evaluation: labelled questions -> retrieval and answer metrics.

Eval only talks to the ``Retriever`` and ``Generator`` protocols, so comparing techniques
is a config change. The question set lives in eval/questions.jsonl (format in eval/README.md).
"""

from open_parcel.eval.questions import EvalQuestion, load_questions

__all__ = ["EvalQuestion", "load_questions"]
