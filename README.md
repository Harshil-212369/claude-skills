# claude-skills

Skills I've written for [Claude Code](https://docs.claude.com/en/docs/claude-code) and claude.ai. Each folder is one self-contained skill with its own README, scripts and evals.

| Skill | What it does |
|---|---|
| [context-handoff](context-handoff/) | Turns a long chat or session into one handoff file that a fresh Claude session can resume from cold. It ships with a secret-scanning validator and evals. |
| [job-application](job-application/) | Turns a pasted job posting into a checked application package (tailored resume, cover letter, merged CV) and tracks each application's status. |

## Install one skill

```bash
git clone https://github.com/Harshil-212369/claude-skills ~/projects/claude-skills
ln -s ~/projects/claude-skills/context-handoff ~/.claude/skills/context-handoff
```

The symlink keeps the skill current: a `git pull` updates it in place. To pin a version, use `cp -r` instead of `ln -s`.

For claude.ai, download the skill's `.skill` file from [Releases](https://github.com/Harshil-212369/claude-skills/releases) and upload it under Settings → Capabilities → Skills.

## Layout

Every skill follows the same structure:

```
<skill>/
├── SKILL.md      # what Claude reads; the frontmatter description controls auto-triggering
├── README.md     # for humans
├── references/   # loaded only when needed
├── scripts/      # deterministic work, so the model doesn't redo it
└── evals/        # test cases in the layout `claude plugin eval` reads
```

## License

MIT. See [LICENSE](LICENSE).
