---
name: context-handoff
description: Write a self-contained handoff file that lets a fresh Claude session pick up work cold — goal, decisions, verified state, file paths, dead ends, and the exact next step. Use whenever the user wants to summarize a chat or session so they can continue elsewhere (Claude Code, a new chat, another Project, a teammate), says the context is getting long, is about to /clear or /compact, or asks to "save where we are", "checkpoint this", "write a handoff", "summarize this chat for later" or "pick this up tomorrow" — even if they never say the word handoff.
---

# Context Handoff

A new Claude session starts with zero context. Chat links are opaque to it, Projects don't share history, and a vague summary gets re-interpreted from scratch. This skill turns the current conversation into one Markdown file that a cold session can load and act on immediately.

## Why handoffs usually fail

Keep these four failure modes in mind; every rule below exists to prevent one of them.

1. **Suggestions recorded as decisions.** Claude proposed X, the user said "interesting", and the summary says "decided X". The next session then builds on something nobody agreed to.
2. **Assumed shared context.** "The script", "that bug", "the approach we discussed" mean nothing to a reader who wasn't there.
3. **Leaked secrets.** Keys, tokens and wallet material pasted mid-session end up in a file that gets committed or shared.
4. **Buried next step.** The reader has to read 800 words to find out what to do first.

## Workflow

### 1. Pick the reader and destination

Default reader: the same user's next Claude session, most often in Claude Code. If the user names someone else (a teammate, another Project), write for that reader. Ask only if the destination genuinely changes the content; otherwise proceed and state your assumption in the file's header.

### 2. Gather ground truth

Read back through the conversation. If you have a shell in a repo, prefer what the tools say over what the chat remembers:

```bash
git rev-parse --abbrev-ref HEAD
git status --short
git log --oneline -5
```

Record exact branch names, file paths, versions and command names. A path the next session can `cd` into beats a description of where something lives.

### 3. Classify every item by provenance

This is the step that makes the handoff trustworthy. Sort each item into exactly one bucket:

| Bucket | Test | Example |
|---|---|---|
| **Decided** | The user stated or explicitly confirmed it | "We'll use SQLite, not Postgres" |
| **Proposed** | Claude suggested it; the user has not committed | Claude recommended adding retries |
| **Done** | A tool result, test run or file proves it happened | `pytest` passed, file written at path |
| **Open** | Unresolved question or pending choice | Which auth provider to use |

When unsure whether something was decided, put it in **Proposed**. Under-claiming costs the next session one question; over-claiming costs it a wrong build.

Quote the user's own wording for hard constraints and preferences ("never mention X in applications"). Paraphrase drifts; quotes don't.

### 4. Write the file

Use the template in `references/template.md`. Fill every section; write "None" rather than deleting a section, so the reader knows it was considered. Target 400–900 words: long enough to be self-contained, short enough to load cheaply.

- **Resume here** goes first: the single next action, concrete enough to execute without reading further.
- **Dead ends**: record approaches that failed *and why*, so they are not retried. Drop exploratory tangents that don't affect future work.
- **Secrets**: never copy a credential. Replace it with `<REDACTED:kind>` and say where the real value lives (e.g. "in `.env` as `ANTHROPIC_API_KEY`").
- **Links**: claude.ai chat URLs can't be read by another session. Carry the content over instead of the link.

### 5. Validate

Run the bundled checker on the file:

```bash
python3 scripts/validate_handoff.py <path-to-handoff.md>
```

It checks required sections, scans for credential patterns, flags unreadable chat links and leftover placeholders, and reports word count. Fix every **ERROR** before delivering. **WARN** lines need a judgment call; mention any you leave in place.

### 6. Save and hand over

- **Claude Code / shell:** save to `handoffs/YYYY-MM-DD-<short-slug>.md` in the project root, creating the folder if needed. Suggest adding `handoffs/` to `.gitignore` if the repo is public.
- **Chat:** write the file and deliver it to the user.

Finish by printing the one-line **resume prompt** from the file's last section, so the user can paste it into the next session.

## Reference files

- `references/template.md` — the handoff template with guidance per section. Read it at step 4.
- `scripts/validate_handoff.py` — standard-library Python checker. Run it at step 5.
