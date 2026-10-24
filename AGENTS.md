# Agent instructions

This repository is realined: Agent Skills, a vault template and fictional examples for a Claude
Managed Agent that maintains a Markdown second brain. `README.md` is the only file written for
humans (Spanish). Everything else is written for coding agents in English: imperative, concrete,
numbers over adjectives.

## Layout

```
skills/<skill>/        one skill per directory; everything it needs lives inside it
templates/vault/       the vault template people copy; its AGENTS.md is the vault schema
examples/              fictional demo vault and demo project with seeded faults (examples/README.md)
agent/BRIEF.md         design input for the managed-agents-wizard skill
scripts/check.py       checks the invariants below (standard library only); CI runs it on every push and pull request
agents/realined/       written by managed-agents-wizard (not hand-edited: agent.md, deployment-*.yaml are generated)
```

## Invariants

1. Frontmatter `name` equals the directory name, lowercase with hyphens, at most 64 characters,
   without "anthropic" or "claude"; `description` at most 1,024 characters.
2. Every skill has `agents/openai.yaml`. A skill never links into another skill's folder: name the
   other skill instead ("When the `realined-lint` skill is available...").
3. `references/conventions.md` is the same file in every skill. Change it in all three.
4. `skills/realined-lint/scripts/lint.py` uses the standard library only.
5. `examples/` holds fictional data only. No real names, no real keys, no personal data.
6. The lint baseline in `examples/README.md` matches the script:
   `python3 skills/realined-lint/scripts/lint.py examples/demo-vault --today 2026-10-24`.
7. No secrets anywhere. Credentials go to a Managed Agents vault, set by the person in a terminal.

Run `python3 scripts/check.py` before you finish a change. It exits 1 when an invariant fails.
