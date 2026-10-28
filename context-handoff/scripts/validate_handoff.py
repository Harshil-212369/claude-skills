#!/usr/bin/env python3
"""Validate a context-handoff Markdown file before it is delivered.

Checks:
  * all required ``##`` sections from references/template.md are present
  * no credential-shaped strings (API keys, tokens, private keys, JWTs)
  * no unfilled template placeholders or leftover italic guidance
  * no claude.ai chat links (another session cannot open them)
  * word count within the target budget

Usage:
    python3 validate_handoff.py HANDOFF.md [--json]

Exit status: 0 if there are no errors (warnings allowed), 1 if any error,
2 if the file cannot be read. Standard library only, so it runs anywhere
Python 3.8+ is installed.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional

REQUIRED_SECTIONS = [
    "Resume here",
    "Goal",
    "Decisions",
    "Proposed, not confirmed",
    "Current state",
    "Constraints and preferences",
    "Key files and artifacts",
    "Dead ends",
    "Open questions",
    "Resume prompt",
]

WORD_MIN, WORD_MAX = 150, 1200

# (label, pattern). Patterns are deliberately specific to keep false
# positives low; anything matched here is treated as an ERROR.
SECRET_PATTERNS = [
    ("Anthropic API key", re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}")),
    ("OpenAI-style API key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9]{32,}")),
    ("AWS access key ID", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36}\b")),
    ("GitHub fine-grained token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{50,}")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("PEM private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("JSON Web Token", re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}")),
    (
        "credential assignment",
        re.compile(
            r"(?i)\b(?:password|passwd|secret|api[_-]?key|token|private[_-]?key)\b\s*[:=]\s*"
            r"['\"]?(?!<REDACTED)[^\s'\"<>`]{8,}"
        ),
    ),
]

# A bare 64-hex string is a tx hash or a private key; context decides.
HEX64 = re.compile(r"\b(?:0x)?[a-fA-F0-9]{64}\b")
KEY_CONTEXT = re.compile(r"(?i)private|secret|seed|mnemonic|signing key|wallet key")

PLACEHOLDERS = [
    re.compile(r"<short title[^>]*>"),
    re.compile(r"\bYYYY-MM-DD\b(?!-<)"),
    re.compile(r"^\s*_[^_\n]{10,}_\s*$", re.MULTILINE),  # leftover italic guidance
    re.compile(r"\b(?:TODO|TBD|FIXME)\b"),
]

CHAT_LINK = re.compile(r"https?://claude\.ai/(?:chat|project)/[A-Za-z0-9\-]+")
HEADING = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
CODE_FENCE = re.compile(r"```.*?```", re.DOTALL)


@dataclass
class Finding:
    level: str  # "ERROR" or "WARN"
    check: str
    message: str
    line: Optional[int] = None


def _line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def _mask(value: str) -> str:
    """Show only enough of a match to locate it; never echo a full secret."""
    return value[:6] + "…" if len(value) > 6 else "…"


def check_sections(text: str) -> List[Finding]:
    found = {h.strip().lower() for h in HEADING.findall(text)}
    return [
        Finding("ERROR", "sections", f"missing required section '## {name}'")
        for name in REQUIRED_SECTIONS
        if name.lower() not in found
    ]


def check_section_order(text: str) -> List[Finding]:
    headings = [h.strip().lower() for h in HEADING.findall(text)]
    if headings and headings[0] != "resume here":
        return [Finding("WARN", "order", "'## Resume here' should be the first section")]
    return []


def check_secrets(text: str) -> List[Finding]:
    findings: List[Finding] = []
    for label, pattern in SECRET_PATTERNS:
        for m in pattern.finditer(text):
            findings.append(
                Finding("ERROR", "secrets", f"possible {label}: '{_mask(m.group(0))}'", _line_of(text, m.start()))
            )
    for m in HEX64.finditer(text):
        line_start = text.rfind("\n", 0, m.start()) + 1
        line_end = text.find("\n", m.end())
        line = text[line_start : line_end if line_end != -1 else len(text)]
        if KEY_CONTEXT.search(line):
            findings.append(
                Finding("ERROR", "secrets", f"64-hex value next to key wording: '{_mask(m.group(0))}'", _line_of(text, m.start()))
            )
        else:
            findings.append(
                Finding("WARN", "secrets", f"64-hex value '{_mask(m.group(0))}' — confirm it is a hash, not a key", _line_of(text, m.start()))
            )
    return findings


def check_placeholders(text: str) -> List[Finding]:
    prose = CODE_FENCE.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    findings = []
    for pattern in PLACEHOLDERS:
        for m in pattern.finditer(prose):
            findings.append(
                Finding("ERROR", "placeholders", f"unfilled template text: '{m.group(0).strip()[:40]}'", _line_of(prose, m.start()))
            )
    return findings


def check_links(text: str) -> List[Finding]:
    return [
        Finding("WARN", "links", "claude.ai link is unreadable to a new session; carry the content over", _line_of(text, m.start()))
        for m in CHAT_LINK.finditer(text)
    ]


def check_length(text: str) -> List[Finding]:
    words = len(re.findall(r"\S+", text))
    if words < WORD_MIN:
        return [Finding("WARN", "length", f"{words} words; likely too thin to resume cold (min {WORD_MIN})")]
    if words > WORD_MAX:
        return [Finding("WARN", "length", f"{words} words; trim to keep loading cheap (max {WORD_MAX})")]
    return []


def validate(text: str) -> List[Finding]:
    findings: List[Finding] = []
    for check in (check_sections, check_section_order, check_secrets, check_placeholders, check_links, check_length):
        findings.extend(check(text))
    return findings


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("path", type=Path, help="handoff Markdown file")
    parser.add_argument("--json", action="store_true", help="emit findings as JSON")
    args = parser.parse_args(argv)

    try:
        text = args.path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"ERROR: cannot read {args.path}: {exc}", file=sys.stderr)
        return 2

    findings = validate(text)
    errors = [f for f in findings if f.level == "ERROR"]
    words = len(re.findall(r"\S+", text))

    if args.json:
        print(json.dumps({"file": str(args.path), "words": words, "ok": not errors,
                          "findings": [asdict(f) for f in findings]}, indent=2))
    else:
        for f in findings:
            where = f" (line {f.line})" if f.line else ""
            print(f"{f.level:5} [{f.check}]{where} {f.message}")
        status = "PASS" if not errors else "FAIL"
        print(f"{status}: {len(errors)} error(s), {len(findings) - len(errors)} warning(s), {words} words")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
