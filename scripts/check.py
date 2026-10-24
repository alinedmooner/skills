#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Check the repository invariants listed in AGENTS.md. Standard library only.

Usage:
    python3 scripts/check.py [--root <repo>] [--today YYYY-MM-DD]

Prints one line per check and exits 1 when any check fails. Run it from anywhere:
the repository root is resolved from this file unless --root is given.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = "skills"
CONVENTIONS = "references/conventions.md"
LINT = "skills/realined-lint/scripts/lint.py"
DEMO_VAULT = "examples/demo-vault"
EXAMPLES_README = "examples/README.md"
BASELINE_TODAY = "2026-10-24"

MAX_NAME = 64
MAX_DESCRIPTION = 1024
FORBIDDEN_NAME_WORDS = ("anthropic", "claude")
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# Vault content is linted by lint.py, not by this script.
VAULT_DIRS = ("examples/demo-vault", "templates/vault")
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv"}
TEXT_SUFFIXES = {".md", ".py", ".yaml", ".yml", ".toml", ".txt", ".json", ".example", ".gitignore", ""}

# High-confidence secret shapes: a hit anywhere in the repository is a failure.
SECRET_PATTERNS = [
    ("anthropic key", re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}")),
    ("openai-style key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9]{32,}")),
    ("github token", re.compile(r"\b(?:ghp|gho|ghs|ghu)_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}")),
    ("aws access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}")),
    ("private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
]
# Generic assignment: checked everywhere except the demo vault, which seeds one on purpose
# (the lint baseline check proves lint.py reports it).
GENERIC_SECRET = re.compile(
    r"(?i)\b(?:api[_-]?key|secret|token|password|passwd)\b\s*[:=]\s*[\"']?[A-Za-z0-9_\-\.]{20,}")

FM_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)
MD_LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)")
BACKTICK_PATH_RE = re.compile(
    r"`((?:skills|scripts|examples|templates|agent|references|\.github)/[A-Za-z0-9_./\-]+)`")
BASELINE_RE = re.compile(r"\*\*(\d+) errores?, (\d+) avisos?\*\*")


class Checker:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.failures = 0

    def report(self, name: str, problems: list[str]) -> None:
        if problems:
            self.failures += 1
            print(f"FAIL {name}")
            for p in problems:
                print(f"     - {p}")
        else:
            print(f"ok   {name}")

    # --- helpers -----------------------------------------------------------------

    def skills(self) -> list[Path]:
        return sorted(p for p in (self.root / SKILLS_DIR).iterdir() if p.is_dir())

    def text_files(self):
        for p in sorted(self.root.rglob("*")):
            rel = p.relative_to(self.root)
            if any(part in SKIP_DIRS for part in rel.parts) or not p.is_file():
                continue
            if p.suffix.lower() in TEXT_SUFFIXES:
                yield p, rel

    @staticmethod
    def parse_frontmatter(text: str) -> dict[str, str] | None:
        """YAML subset: `key: value` and `key: >-` / `key: |` block scalars."""
        m = FM_RE.match(text)
        if not m:
            return None
        data: dict[str, str] = {}
        key, block = None, None
        for line in m.group(1).splitlines():
            if block is not None and (line.startswith("  ") or not line.strip()):
                block.append(line.strip())
                continue
            block = None
            if ":" not in line or line.startswith(" "):
                continue
            key, val = line.split(":", 1)
            key, val = key.strip(), val.strip()
            if val in (">-", ">", "|", "|-"):
                block = []
                data[key] = block  # type: ignore[assignment]
            else:
                data[key] = val.strip("\"'")
        for k, v in list(data.items()):
            if isinstance(v, list):
                data[k] = " ".join(x for x in v if x)
        return data

    # --- checks (numbered as in AGENTS.md) -----------------------------------------

    def check_frontmatter(self) -> None:
        problems = []
        for skill in self.skills():
            path = skill / "SKILL.md"
            if not path.is_file():
                problems.append(f"{skill.name}: SKILL.md missing")
                continue
            fm = self.parse_frontmatter(path.read_text(encoding="utf-8"))
            if fm is None:
                problems.append(f"{skill.name}: no YAML frontmatter")
                continue
            name = fm.get("name", "")
            if name != skill.name:
                problems.append(f"{skill.name}: name '{name}' != directory name")
            if not NAME_RE.match(name):
                problems.append(f"{skill.name}: name must be lowercase letters, digits and hyphens")
            if len(name) > MAX_NAME:
                problems.append(f"{skill.name}: name has {len(name)} characters (max {MAX_NAME})")
            for word in FORBIDDEN_NAME_WORDS:
                if word in name.lower():
                    problems.append(f"{skill.name}: name contains '{word}'")
            desc = fm.get("description", "")
            if not desc:
                problems.append(f"{skill.name}: description missing")
            elif len(desc) > MAX_DESCRIPTION:
                problems.append(f"{skill.name}: description has {len(desc)} characters (max {MAX_DESCRIPTION})")
        self.report("1. SKILL.md frontmatter (name = folder, description <= 1024)", problems)

    def check_skill_layout(self) -> None:
        problems = []
        names = [s.name for s in self.skills()]
        for skill in self.skills():
            if not (skill / "agents" / "openai.yaml").is_file():
                problems.append(f"{skill.name}: agents/openai.yaml missing")
            for md in sorted(skill.rglob("*.md")):
                text = md.read_text(encoding="utf-8")
                for other in names:
                    if other == skill.name:
                        continue
                    if re.search(rf"(?:\.\./|{SKILLS_DIR}/){re.escape(other)}/", text):
                        problems.append(f"{md.relative_to(self.root)}: links into {other}/ (name the skill instead)")
        self.report("2. agents/openai.yaml present; no links into another skill's folder", problems)

    def check_conventions_identical(self) -> None:
        problems = []
        copies = {s.name: s / CONVENTIONS for s in self.skills()}
        missing = [n for n, p in copies.items() if not p.is_file()]
        problems += [f"{n}: {CONVENTIONS} missing" for n in missing]
        present = [p for p in copies.values() if p.is_file()]
        if len(present) > 1:
            ref = present[0].read_bytes()
            for p in present[1:]:
                if p.read_bytes() != ref:
                    problems.append(f"{p.relative_to(self.root)} differs from {present[0].relative_to(self.root)}")
        self.report("3. references/conventions.md identical in every skill", problems)

    def check_lint_stdlib(self) -> None:
        problems = []
        path = self.root / LINT
        if not path.is_file():
            problems.append(f"{LINT} missing")
        else:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                mods = []
                if isinstance(node, ast.Import):
                    mods = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    mods = [node.module]
                for mod in mods:
                    if mod.split(".")[0] not in sys.stdlib_module_names:
                        problems.append(f"{LINT} imports '{mod}', not in the standard library")
        self.report("4. lint.py uses the standard library only", problems)

    def check_links(self) -> None:
        problems = []
        for p, rel in self.text_files():
            if p.suffix != ".md" or any(str(rel).startswith(v) for v in VAULT_DIRS):
                continue
            text = p.read_text(encoding="utf-8")
            targets = set()
            for t in MD_LINK_RE.findall(text):
                if "://" in t or t.startswith(("mailto:", "#")):
                    continue
                targets.add(t.split("#", 1)[0])
            for para in re.split(r"\n\s*\n", text):
                if "://" in para or "github.com" in para:
                    continue  # a path quoted next to a URL belongs to that other repository
                for t in BACKTICK_PATH_RE.findall(para):
                    if t.endswith(("/", "...")) or "<" in t or "*" in t:
                        continue
                    targets.add(t)
            # A skill-relative path (references/, scripts/) may be quoted from outside the skill:
            # accept it when any skill resolves it.
            bases = [p.parent, self.root, *self.skills()]
            for t in sorted(targets):
                if not any((b / t).exists() for b in bases):
                    problems.append(f"{rel}: '{t}' does not resolve")
        self.report("5. relative links and quoted repository paths resolve", problems)

    def check_lint_baseline(self, today: str) -> None:
        problems = []
        readme = self.root / EXAMPLES_README
        m = BASELINE_RE.search(readme.read_text(encoding="utf-8")) if readme.is_file() else None
        if not m:
            problems.append(f"{EXAMPLES_README}: no '**N errores, M avisos**' baseline line")
        else:
            want_err, want_warn = int(m.group(1)), int(m.group(2))
            cmd = [sys.executable, "-I", str(self.root / LINT), str(self.root / DEMO_VAULT),
                   "--format", "json", "--today", today]
            run = subprocess.run(cmd, capture_output=True, text=True)
            if run.returncode != 0:
                problems.append(f"lint.py exited {run.returncode}: {run.stderr.strip()[:200]}")
            else:
                counts = json.loads(run.stdout)["counts"]
                got = (counts["error"], counts["warn"])
                if got != (want_err, want_warn):
                    problems.append(f"lint.py --today {today}: {got[0]} errors, {got[1]} warnings; "
                                    f"{EXAMPLES_README} says {want_err}, {want_warn}")
        self.report(f"6. lint baseline on {DEMO_VAULT} matches {EXAMPLES_README}", problems)

    def check_secrets(self) -> None:
        problems = []
        for p, rel in self.text_files():
            if p.name == ".env" or (p.name.startswith(".env.") and p.name != ".env.example"):
                problems.append(f"{rel}: env file committed")
                continue
            text = p.read_text(encoding="utf-8", errors="replace")
            for label, rx in SECRET_PATTERNS:
                if rx.search(text):
                    problems.append(f"{rel}: possible {label}")
            if not str(rel).startswith(DEMO_VAULT) and rel != Path(LINT) and rel != Path("scripts/check.py"):
                if GENERIC_SECRET.search(text):
                    problems.append(f"{rel}: possible secret assignment")
        self.report("7. no secrets in the repository", problems)

    def run(self, today: str) -> int:
        self.check_frontmatter()
        self.check_skill_layout()
        self.check_conventions_identical()
        self.check_lint_stdlib()
        self.check_links()
        self.check_lint_baseline(today)
        self.check_secrets()
        print(f"\n{'All checks passed.' if not self.failures else f'{self.failures} check(s) failed.'}")
        return 1 if self.failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=Path, default=ROOT, help="repository root (default: resolved from this file)")
    ap.add_argument("--today", default=BASELINE_TODAY, help=f"date for the lint baseline (default {BASELINE_TODAY})")
    a = ap.parse_args()
    root = a.root.resolve()
    if not (root / "AGENTS.md").is_file():
        print(f"Not a realined repository (no AGENTS.md): {root}", file=sys.stderr)
        return 2
    return Checker(root).run(a.today)


if __name__ == "__main__":
    sys.exit(main())
