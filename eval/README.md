# Eval question set

`questions.jsonl` is the labelled question set every experiment is scored against. It is
version-controlled so results stay comparable: if you change a question, note it in the
experiments log.

One JSON object per line:

| field         | required | meaning                                                                 |
| ------------- | -------- | ----------------------------------------------------------------------- |
| `id`          | yes      | stable id, e.g. `q-012`                                                 |
| `question`    | yes      | the question as a user would ask it                                     |
| `relevant`    | yes      | chunk ids or section paths a good retriever should return (recall, MRR) |
| `answer`      | no       | short reference answer, for judging generation                          |
| `tags`        | no       | slices for reporting: `definition`, `table`, `multi-hop`, `geo`, ...    |
| `placeholder` | no       | `true` for example rows; skipped by `load_questions`                    |

The two rows in the file now are placeholders showing the format. Replace them with real
questions whose answers you have checked in the PDF. Aim for a spread across tags so a
technique that only helps one kind of question shows up as such.
