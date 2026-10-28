# context-handoff

A Claude skill that turns a long chat or coding session into one self-contained Markdown file, so a fresh Claude session can resume the work cold.

New sessions start with zero context. Chat links can't be read across sessions, and a loose summary gets reinterpreted from scratch. This skill writes a handoff with a fixed structure, checks it with a script, and ends with a one-line prompt to paste into the next session.

## What makes it different from "summarize this chat"

| Problem with ad-hoc summaries | What this skill does |
|---|---|
| Claude's suggestions get recorded as the user's decisions | Classifies every item by provenance: **Decided**, **Proposed**, **Done**, **Open** |
| "The script", "that bug" mean nothing to a new reader | Requires exact paths, branches, commits and versions |
| API keys and tokens pasted mid-session leak into the file | Validator scans for credential patterns; secrets become `<REDACTED:kind>` |
| The next step is buried in prose | `## Resume here` is always the first section |
| Failed approaches get retried | `## Dead ends` records what was tried and why it failed |

## Install

**Claude Code (personal, all projects):**

```bash
git clone https://github.com/Harshil-212369/claude-skills ~/projects/claude-skills
ln -s ~/projects/claude-skills/context-handoff ~/.claude/skills/context-handoff
```

**Claude Code (one repo):** copy this folder to `.claude/skills/context-handoff/` in that repo.

**claude.ai:** zip the folder (or use the packaged `.skill` file from Releases) and upload it as a skill.

## Use

It triggers on its own when you say things like:

- "summarize this chat so I can continue in Claude Code"
- "I'm about to /clear, checkpoint where we are"
- "write a handoff for my teammate"

Or invoke it directly with `/context-handoff`.

In a repo, output goes to `handoffs/YYYY-MM-DD-<slug>.md`. Resume with:

```
Read handoffs/2026-10-27-scheduler-flake.md and start with "Resume here".
```

## Validator

`scripts/validate_handoff.py` is standard-library Python 3.8+.

```bash
python3 scripts/validate_handoff.py handoffs/2026-10-27-scheduler-flake.md        # human-readable
python3 scripts/validate_handoff.py handoffs/2026-10-27-scheduler-flake.md --json # for CI
```

| Check | Level |
|---|---|
| All 10 required sections present | ERROR |
| Credential patterns (Anthropic/OpenAI/AWS/GitHub/Slack/Google keys, PEM, JWT, `password=` assignments) | ERROR |
| 64-hex value next to "private"/"seed"/"mnemonic" wording | ERROR |
| Unfilled template placeholders, `TODO`/`TBD` | ERROR |
| Bare 64-hex value (could be a tx hash or a key) | WARN |
| claude.ai chat links | WARN |
| Word count outside 150–1200 | WARN |

Exit codes: `0` pass, `1` errors found, `2` unreadable file. Matched secrets are masked in output, never echoed in full.

## Evals

Three test cases live in `evals/`, in the layout `claude plugin eval` reads:

| Case | What it checks |
|---|---|
| `separates-decisions-from-suggestions` | User choices vs Claude's unconfirmed ideas land in the right sections |
| `redacts-pasted-credentials` | Pasted passwords and tokens never reach the handoff |
| `records-dead-ends` | Failed approaches are recorded with reasons; unverified fixes aren't claimed as done |

Run them with and without the skill (real, billed model runs):

```bash
cd ~/.claude/skills/context-handoff
claude plugin eval . --allow-tools Write,Edit,Bash --scaffold
```

The fixtures contain **fake** credentials on purpose. If GitHub push protection flags one, it is a test value.

## Layout

```
context-handoff/
├── SKILL.md                    # workflow Claude follows
├── references/template.md      # handoff template, loaded only when writing
├── scripts/validate_handoff.py # deterministic checks
└── evals/                      # 3 test cases with graders
```

## License

MIT
