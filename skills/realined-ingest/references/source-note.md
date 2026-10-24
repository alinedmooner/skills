# source-note.md — one note per raw file

Path: `30-resources/sources/<raw file stem>.md`. Example: the raw file
`30-resources/raw/2026-10-20-pizarra-arquitectura.png` gets
`30-resources/sources/2026-10-20-pizarra-arquitectura.md`.

```markdown
---
type: source
status: draft
summary: "<one sentence: what this source is and why it matters to the vault>"
created: <today>
updated: <today>
source: "[[30-resources/raw/<file name with extension>]]"
media: text | pdf | image | audio | video | prompt | data
tags: [<from the vault taxonomy>]
related: ["[[<project brief or concept this feeds>]]"]
sensitivity: <inherit from the raw file or the folder; private when unsure>
generated_by: llm
reviewed: false
needs: <only when something could not be read: transcript | vision | a reader for .ext>
---

# <Title: what the source says, as a claim or concept>

## TL;DR
<1-3 sentences.>

## Key points
- <Claim> — <where: page 4 / 12:30 / top-left of the image>

## Extracted text
<OCR of an image, or the parts of a transcript that carry decisions. Verbatim, in a quote block.
Omit for long text sources: link them instead.>

## Decisions, actions, open questions
- Decision: <...> (proposed for `decisions/`, not written there)
- Action: <who> — <what> — <date>
- Question: <...>

## Touched notes
- [[<note updated by this ingest>]] — <what changed>
```

Rules:

- Every key point says where in the source it comes from. A point you cannot locate does not go in.
- Never invent a date, an author or a number. Unknown stays out.
- "Decisions" here are proposals. A decision note (ADR) is the person's; list it in the report.
