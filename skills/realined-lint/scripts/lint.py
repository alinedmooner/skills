#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Mechanical lint for a Markdown second brain (PARA + frontmatter + wikilinks).

Standard library only, so it runs in a Managed Agents sandbox, in Claude Code, or in CI
without installing anything. It reads files and never writes.

Usage:
    python3 lint.py <vault> [--format md|json] [--today YYYY-MM-DD] [--strict]

Exit code: 0, or 1 with --strict when an error-level finding exists.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

REQUIRED = ("type", "status", "summary", "updated")
TYPES = {"note", "prompt", "adr", "experiment", "concept", "model-card", "learning", "source",
         "brief", "index", "review", "moc", "snippet", "meeting", "skill"}
STATUSES = {"draft", "active", "deprecated", "archived", "inbox"}
SKIP_DIRS = {".git", ".obsidian", ".smart-env", "node_modules", "80-templates", ".trash"}
NO_FM_NEEDED = {"AGENTS.md", "CLAUDE.md", "README.md", "index.md", "log.md"}
ORPHAN_EXEMPT_DIRS = ("00-inbox", "99-archive", "30-resources/raw", "90-meta/reviews")
MAX_WORDS = 1500
MAX_AGENTS_LINES = 200
STALE_CHECKED_DAYS = 60
STALE_INBOX_DAYS = 14

SECRET_PATTERNS = [
    ("anthropic key", re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}")),
    ("openai-style key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9]{32,}")),
    ("github token", re.compile(r"\b(?:ghp|gho|ghs|ghu)_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}")),
    ("aws access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}")),
    ("private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("generic secret assignment", re.compile(
        r"(?i)\b(?:api[_-]?key|secret|token|password|passwd)\b\s*[:=]\s*[\"']?[A-Za-z0-9_\-\.]{20,}")),
]

FM_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)
LINK_RE = re.compile(r"(!?)\[\[([^\]\|#]+)(?:#[^\]\|]*)?(?:\|[^\]]*)?\]\]")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
FILE_DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-")
KEBAB_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
INLINE_TAG_RE = re.compile(r"(?<![\w/&])#([A-Za-zÀ-ÿ][\w\-/À-ÿ]*)")
CODE_RE = re.compile(r"```.*?```|`[^`\n]*`", re.S)


def parse_frontmatter(text: str) -> tuple[dict | None, str]:
    """Tiny YAML subset: `key: value`, `key: [a, b]` and `- item` lists. Enough for lint."""
    m = FM_RE.match(text)
    if not m:
        return None, text
    data: dict = {}
    key = None
    for raw in m.group(1).splitlines():
        line = raw.split(" #", 1)[0].rstrip() if not raw.strip().startswith(("\"", "'")) else raw.rstrip()
        if not line.strip():
            continue
        if line.lstrip().startswith("- ") and key:
            data.setdefault(key, [])
            if isinstance(data[key], list):
                data[key].append(line.lstrip()[2:].strip().strip("\"'"))
            continue
        if ":" in line and not line.startswith(" "):
            key, val = line.split(":", 1)
            key, val = key.strip(), val.strip()
            if val.startswith("[") and val.endswith("]"):
                data[key] = [v.strip().strip("\"'") for v in val[1:-1].split(",") if v.strip()]
            elif val == "":
                data[key] = []
            else:
                data[key] = val.strip("\"'")
    return data, text[m.end():]


def norm_tag(tag: str) -> str:
    t = unicodedata.normalize("NFKD", tag.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[\-_\s]", "", t)
    return t[:-1] if t.endswith("s") and len(t) > 3 else t


def parse_date(value) -> dt.date | None:
    if isinstance(value, str) and DATE_RE.match(value):
        try:
            return dt.date.fromisoformat(value)
        except ValueError:
            return None
    return None


def walk(vault: Path):
    for p in sorted(vault.rglob("*")):
        rel = p.relative_to(vault)
        if any(part in SKIP_DIRS for part in rel.parts) or not p.is_file():
            continue
        yield p, rel


def lint(vault: Path, today: dt.date) -> dict:
    findings: list[dict] = []

    def add(sev, code, rel, msg):
        findings.append({"severity": sev, "code": code, "file": str(rel), "message": msg})

    all_files = list(walk(vault))
    md_files = [(p, r) for p, r in all_files if p.suffix == ".md"]
    by_stem: dict[str, list[Path]] = defaultdict(list)
    by_name: dict[str, list[Path]] = defaultdict(list)
    for p, r in all_files:
        by_name[p.name.lower()].append(r)
        if p.suffix == ".md":
            by_stem[p.stem.lower()].append(r)
            by_stem[str(r.with_suffix("")).lower()].append(r)

    inbound: dict[str, int] = defaultdict(int)
    tags_seen: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    titles: dict[str, list[str]] = defaultdict(list)
    stats = {"notes": len(md_files), "files": len(all_files), "generated_unreviewed": 0}

    for p, rel in md_files:
        text = p.read_text(encoding="utf-8", errors="replace")
        in_raw = rel.parts[:2] == ("30-resources", "raw")

        for label, rx in SECRET_PATTERNS:
            if rx.search(text):
                add("error", "SC001", rel, f"Possible secret ({label}). Move it out of the vault and rotate it.")
                break
        if in_raw:
            continue  # raw sources are immutable: only the secret check applies

        fm, body = parse_frontmatter(text)
        is_root_meta = p.name in NO_FM_NEEDED

        if p.name == "AGENTS.md":
            n = text.count("\n") + 1
            if n > MAX_AGENTS_LINES:
                add("warn", "AG001", rel, f"{n} lines; keep instruction files under {MAX_AGENTS_LINES} (move procedures to skills).")

        if fm is None and not is_root_meta:
            add("error", "FM001", rel, "No YAML frontmatter.")
        elif fm is not None:
            missing = [k for k in REQUIRED if not fm.get(k)]
            if missing and not is_root_meta:
                add("error", "FM002", rel, f"Missing frontmatter fields: {', '.join(missing)}.")
            if fm.get("type") and fm["type"] not in TYPES:
                add("warn", "FM003", rel, f"Unknown type '{fm['type']}'.")
            if fm.get("status") and fm["status"] not in STATUSES:
                add("warn", "FM003", rel, f"Unknown status '{fm['status']}'.")
            for k in ("created", "updated", "checked"):
                if fm.get(k) and not parse_date(fm[k]):
                    add("warn", "FM004", rel, f"'{k}' is not an ISO date (YYYY-MM-DD): {fm[k]}.")
            checked = parse_date(fm.get("checked"))
            if checked and (today - checked).days > STALE_CHECKED_DAYS:
                add("warn", "ST001", rel, f"'checked' is {(today - checked).days} days old; re-verify against the official source.")
            if fm.get("generated_by") == "llm" and str(fm.get("reviewed", "")).lower() != "true":
                stats["generated_unreviewed"] += 1
                if fm.get("type") != "index" and not fm.get("source") and not fm.get("related"):
                    add("warn", "GN001", rel, "Generated note without 'source' or 'related': it cannot be audited.")
            tag_list = fm.get("tags") or []
            if isinstance(tag_list, str):
                tag_list = [t.strip() for t in tag_list.split(",")]
            for t in tag_list:
                tags_seen[norm_tag(t)][t].append(str(rel))
            title_key = norm_tag(str(fm.get("title") or p.stem))
            titles[title_key].append(str(rel))

        clean = CODE_RE.sub("", body if fm is not None else text)
        for t in INLINE_TAG_RE.findall(clean):
            tags_seen[norm_tag(t)][t].append(str(rel))

        words = len(clean.split())
        if words > MAX_WORDS:
            add("info", "SZ001", rel, f"{words} words; split notes over {MAX_WORDS}.")

        name_part = FILE_DATE_RE.sub("", p.stem)
        if not is_root_meta and not KEBAB_RE.match(name_part):
            add("info", "NM001", rel, "File name is not kebab-case.")

        if rel.parts[0] == "00-inbox":
            created = parse_date((fm or {}).get("created"))
            if not created:
                m = FILE_DATE_RE.match(p.name)
                created = parse_date(m.group(1)) if m else None
            if created and (today - created).days > STALE_INBOX_DAYS:
                add("warn", "IN001", rel, f"In the inbox for {(today - created).days} days.")

        for embed, target in LINK_RE.findall(clean):
            target = target.strip()
            key = target.lower()
            if embed or Path(target).suffix and Path(target).suffix != ".md":
                ok = Path(target).name.lower() in by_name or (vault / target).exists()
            else:
                key = key[:-3] if key.endswith(".md") else key
                ok = key in by_stem
                if ok and len(set(by_stem[key])) > 1:
                    add("warn", "LK003", rel, f"Ambiguous link [[{target}]]: matches {sorted(map(str, set(by_stem[key])))}. Use the full path.")
                if ok:
                    for r in set(by_stem[key]):
                        if r != rel:
                            inbound[str(r)] += 1
            if not ok:
                add("error", "LK001", rel, f"Broken link [[{target}]].")

    for p, rel in md_files:
        s = str(rel)
        if p.name in NO_FM_NEEDED or any(s.startswith(d) for d in ORPHAN_EXEMPT_DIRS):
            continue
        if inbound.get(s, 0) == 0:
            add("warn", "LK002", rel, "Orphan: no other note links here. Link it from an index or a related note.")

    for key, spellings in tags_seen.items():
        if len(spellings) > 1:
            files = sorted({f for fs in spellings.values() for f in fs})
            add("warn", "TG001", files[0], f"Tag variants {sorted(spellings)} in {len(files)} notes; pick one spelling.")

    for key, files in titles.items():
        if len(files) > 1:
            add("warn", "DU001", files[0], f"Possible duplicates: {files}.")

    order = {"error": 0, "warn": 1, "info": 2}
    findings.sort(key=lambda f: (order[f["severity"]], f["code"], f["file"]))
    counts = {s: sum(1 for f in findings if f["severity"] == s) for s in order}
    return {"vault": str(vault), "today": today.isoformat(), "stats": stats, "counts": counts, "findings": findings}


def to_markdown(report: dict) -> str:
    c, s = report["counts"], report["stats"]
    out = [f"# Lint report — {report['today']}", "",
           f"{s['notes']} notes, {s['files']} files. "
           f"Errors: {c['error']} · Warnings: {c['warn']} · Info: {c['info']} · "
           f"Generated and not reviewed: {s['generated_unreviewed']}", ""]
    if not report["findings"]:
        out.append("No findings.")
    out += ["| Severity | Code | File | Finding |", "|---|---|---|---|"] if report["findings"] else []
    for f in report["findings"]:
        out.append(f"| {f['severity']} | {f['code']} | `{f['file']}` | {f['message'].replace('|', '/')} |")
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("vault", type=Path)
    ap.add_argument("--format", choices=("md", "json"), default="md")
    ap.add_argument("--today", help="override today's date (YYYY-MM-DD) for reproducible runs")
    ap.add_argument("--strict", action="store_true", help="exit 1 when an error-level finding exists")
    a = ap.parse_args()
    if not a.vault.is_dir():
        print(f"Not a directory: {a.vault}", file=sys.stderr)
        return 2
    today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
    report = lint(a.vault.resolve(), today)
    print(json.dumps(report, ensure_ascii=False, indent=2) if a.format == "json" else to_markdown(report))
    return 1 if a.strict and report["counts"]["error"] else 0


if __name__ == "__main__":
    sys.exit(main())
