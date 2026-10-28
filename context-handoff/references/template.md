# Handoff template

Copy the block below. Keep the `##` headings exactly as written; the validator checks for them. Replace the italic guidance with content, or write "None".

```markdown
# Handoff: <short title of the work>

- **Date:** YYYY-MM-DD
- **From:** <where this came from, e.g. "claude.ai chat in Project X", "Claude Code session in ~/repo">
- **For:** <who resumes, e.g. "next Claude Code session in ~/repo">

## Resume here

_The single next action, executable without reading further. Include the command, file, or question._

## Goal

_One or two sentences: what the user is ultimately trying to achieve, and why._

## Decisions

_User-stated or user-confirmed choices only. One bullet each. Quote the user where wording matters._

## Proposed, not confirmed

_Claude's suggestions the user hasn't committed to. The next session may raise them, not assume them._

## Current state

_What is done and verified. Cite the evidence: test result, file path, commit hash, tool output._

## Constraints and preferences

_Hard rules, environment details (OS, shell, versions), and how the user wants to work. Quote where possible._

## Key files and artifacts

_Absolute or repo-relative paths, with one line on what each is. No chat links._

## Dead ends

_Approaches tried and abandoned, each with the reason, so they are not retried._

## Open questions

_Unresolved items, each phrased as a question the user can answer._

## Resume prompt

_One line the user pastes into the next session, e.g.:_
`Read handoffs/2026-10-27-auth-refactor.md and start with "Resume here".`
```

## Section notes

| Section | Common mistake | Fix |
|---|---|---|
| Resume here | "Continue working on the feature" | "Run `pytest tests/test_auth.py`; fix the 2 failing token-expiry tests" |
| Decisions | Includes Claude's recommendations | Move to Proposed unless the user said yes |
| Current state | "Mostly works" | "3/5 endpoints pass integration tests; `/refresh` and `/logout` untested" |
| Key files | "the config file" | `config/settings.toml` |
| Dead ends | Omitted | "Tried `requests` with HTTP/2 — unsupported; switched to `httpx`" |
