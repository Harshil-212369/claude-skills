# job-application: a Claude skill for job applications

A [Claude skill](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview) that turns a pasted job posting into a checked application package and keeps a record of every application.

- **Claude does the judgement:** fit check, picking the closest past applications, tailoring the resume and letter.
- **Scripts do the parts that must not drift:** folder layout, letter formatting, page and wording checks, PDF merging, and status tracking.

## What it produces

```
Fall 2026\Acme new grad 2027\
  Acme_Resume.pdf / .tex                     common resume (multi-role)
  Acme_Combined.docx / .pdf / _CV.pdf        short letter covering every role
  Software Developer (Toronto)\
    application.md                           job description + status + submitted date
    source\                                  letter .json/.docx
    final\                                   letter .pdf/.docx, resume, letter+resume CV
```

## Files

| File | Does |
|---|---|
| `SKILL.md` | The workflow Claude follows: build, record status, query / interview prep |
| `new_application.py` | Creates the role folder and `application.md` |
| `cover_letter.js` | JSON -> one-page .docx: justified, 0.5" first-line indents, hanging-indent bullets |
| `finalize.py` | Converts, checks (1 page each, required/forbidden phrases, date wording), merges the CV into `final\` |
| `applications.py` | `list`, `due`, `show`, `mark` across all term folders |
| `appdb.py` | Reads/writes `application.md` (standard library only) |
| `profile.example.jsonc`, `profile.example.md` | Templates for your private profile (comments allowed) |
| `examples/letter.example.json` | Letter content schema |

## Design choices

- **The description is the trigger.** `SKILL.md` describes when to use the skill; the steps live in the body.
- **Deterministic steps are scripts.** Formatting and checks are code, so they come out the same every run instead of being re-derived from a prompt.
- **Data lives with the work.** Each role folder carries its own `application.md`, so there is no separate tracker to drift out of date.
- **Status is never inferred.** `mark --status submitted` needs an explicit date from the applicant.
- **Private data stays out of git.** Personal details and rules live in `profile.jsonc` / `profile.md`, which are gitignored.

## Install

```bash
git clone https://github.com/Harshil-212369/claude-skills.git ~/projects/claude-skills
cd ~/projects/claude-skills/job-application && npm install && pip install pypdf
cp profile.example.jsonc profile.jsonc && cp profile.example.md profile.md   # fill these in
ln -s "$PWD" ~/.claude/skills/job-application                                # Claude Code
```

Set `job_root` in `profile.jsonc` (or `export JOB_ROOT=...`) to the folder holding your term folders.
Requires Python 3.9+, Node 18+, LibreOffice (`soffice`) and, for LaTeX resumes, `pdflatex`.

## License

MIT
