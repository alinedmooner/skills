# conventions.md — the default vault contract

The vault's own `AGENTS.md` wins over this file. Use these defaults only for what `AGENTS.md`
does not say. They come from the research brief "Segundo cerebro personal para trabajar con LLMs"
(October 2026): PARA + Markdown + YAML frontmatter + Git, with Karpathy's LLM Wiki layers.

## Layout

| Folder | Holds | Who writes |
|---|---|---|
| `00-inbox/` | Unprocessed captures | The person; the agent moves items out |
| `10-projects/<p>/` | Active projects: `brief.md`, `decisions/`, `experiments/`, `log.md` | Person and agent |
| `20-areas/` | Ongoing responsibilities, model and provider cards | Person and agent |
| `30-resources/raw/` | Immutable sources: clips, transcripts, PDFs, images, audio | The person only. Never modify, move or rename |
| `30-resources/sources/` | One source note per raw file | The agent |
| `30-resources/concepts/` | Atomic permanent notes | Agent drafts, person reviews |
| `30-resources/snippets/` | SDK snippets by task, with pinned versions | Person and agent |
| `40-prompts/` | Prompt library, one file per prompt | Person and agent |
| `45-skills/` | The person's own `SKILL.md` folders | The person |
| `50-learnings/` | Lessons and post-mortems | The person. The agent only proposes drafts |
| `80-templates/` | Note templates | The person |
| `90-meta/` | `perfil-para-llms.md`, glossary, conventions, `reviews/` | Person; agent writes `reviews/` |
| `99-archive/` | Inactive items. Archive, never delete | Agent moves on approval |

Root files: `AGENTS.md` (canonical agent manual, under 200 lines), `CLAUDE.md` (one line:
`@AGENTS.md`), `index.md` (one line per area, project and key note), `log.md` (append-only).

## Frontmatter

```yaml
---
type: note | prompt | adr | experiment | concept | model-card | learning | source | brief | moc | review | snippet | meeting
status: inbox | draft | active | deprecated | archived
summary: "One sentence an agent can read without opening the note"
created: 2026-10-24
updated: 2026-10-24
tags: [llm, extraction]
related: ["[[adr-0007-use-structured-outputs]]"]
source: "[[30-resources/raw/2026-10-24-talk.pdf]]"   # derived notes only
sensitivity: public | private | secret-free
generated_by: llm        # only on agent-written notes
reviewed: false          # the person flips it to true
summary_by: llm          # the agent wrote only the summary of a person's note
checked: 2026-10-24      # model cards and any fact that changes (prices, limits)
---
```

Required on every note except root files: `type`, `status`, `summary`, `updated`.

## Writing rules

- One topic per note. A 1-3 sentence summary first (`summary:` and a `## TL;DR` when long).
- Title is a claim or a concept, never "Notas varias". File names in kebab-case, one language.
  Dated notes start with the ISO date: `2026-10-24-reunion-cliente-x.md`.
- Relations are `[[wikilinks]]`. Tags only for cross-cutting state or type (`status/active`,
  `type/prompt`); do not repeat in a tag what the folder already says.
- Split notes over about 1,500 words. Headings are descriptive: chunkers cut on them.
- Every derived note links its source in `raw/`. Every fact that changes carries `checked:` and
  the official URL.
- No secrets anywhere in the vault. Only `.env.example` with variable names.

## log.md line format

```
## [2026-10-24] ingest | Charla sobre evals (30-resources/raw/2026-10-24-charla-evals.pdf)
## [2026-10-24] lint | 3 errors fixed, 5 proposals
## [2026-10-26] review | week 2026-W43
```
