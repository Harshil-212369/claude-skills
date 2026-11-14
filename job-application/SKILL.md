---
name: job-application
description: Turn a pasted job posting into a tailored, checked application package (cover letter, resume, merged CV) in a fixed folder layout, and track applications - status, submitted dates, job descriptions for interview prep.
---

# Job application workflow

Three modes:
- **A. Build:** a job posting was pasted, or a role was named.
- **B. Record status:** the applicant says they submitted, got an assessment or interview, were rejected, or got an offer.
- **C. Query / interview prep:** "what did I apply to", "show me that posting", "prep me for the interview".

The scripts in this skill's folder do the steps that must come out the same every time: folder setup, letter formatting, checks, PDF merging, and the application records. Claude does the judgement: fit, choosing past material, and writing.

## Setup (once)

- Copy `profile.example.jsonc` to `profile.jsonc` and `profile.example.md` to `profile.md`, then fill both in. Both are gitignored. `//` comments are allowed in the JSON.
- `job_root` in `profile.jsonc` (or the `JOB_ROOT` environment variable) points at the folder holding term folders such as `Fall 2026`. If neither is set, the scripts use the folder one level above this one.
- Needs: Python 3.9+ with `pypdf` (or poppler's `pdfunite`), Node with the `docx` package (`npm install` here), LibreOffice for .docx to PDF, `pdflatex` for LaTeX resumes.

**Step 0, every time:** read `profile.md` and `profile.jsonc`. They hold the applicant's facts and standing rules: date wording by role type, claims that are verified or must never be made, skills not held, voice, and addresses used before. They beat anything recalled from older letters.

## Folder layout

```
<job_root>\<term>\<Company> <program> <year>\      e.g. "Acme new grad 2027", "Acme co-op Winter 2027"
  <resume>.pdf / .tex                               multi-role only: common resume at the top
  <Combined letter>.json / .docx / .pdf / _CV.pdf   multi-role only: short letter naming every role
  <Job ID> - <Job Title> (<City>)\                  or "<Job Title> (<City>)" without an ID
    application.md     job description verbatim + status + dates (the record)
    source\            editable: letter .json/.docx, resume .tex (single-role)
    final\             exactly what gets uploaded: letter .pdf/.docx, resume .pdf, letter+resume CV,
                       and any transcript or certificates the posting asks for
```

Never delete or overwrite the applicant's earlier versions, folders or hand-edited files to tidy up. Keep the previous version unless they ask for it to go. A file that will not move is usually open in Word: ask them to close it.

## A. Build an application

1. **Capture the posting.** Save the job description verbatim to a temp file. Pull out company, exact title, job ID, location, posting and closing dates, URL, travel and salary.
2. **Check fit before writing.** Compare the requirements with the profile: GPA bar, graduation window, experience cap, location (ask before claiming they will relocate), licences, work authorization, required tools they lack. Report blockers and weak fits in a short table.
3. **Scaffold** one folder per role:
   `python3 new_application.py --term "<term>" --company "<Company> <program> <year>" --title "<Title>" --location "<City, ON>" [--job-id ID] --jd <jd.txt> --posted YYYY-MM-DD --deadline YYYY-MM-DD --url <url> [--shared-with "<other roles>"]`
4. **Pick the closest past applications** by role type and industry, not by recency. Search `applications.py list`, the term folders, and any notes kept on past applications. Say which ones you used and why.
5. **Resume.** Start from the newest resume source (newest modified `.tex`), so recently learned skills carry over. Bring in bullets from the closest past application where they fit better. Use the posting's keywords only where they are true. Set education dates by role type. One page, ATS-parseable (no tables, columns or graphics). Compile in a scratch folder, then save `.tex` + `.pdf` to `source\` (multi-role: the company folder).
6. **Cover letter.** Write the content as JSON (schema in `examples/letter.example.json`) and run `node cover_letter.js <content.json> <out.docx>`. The format is fixed by the script:
   - Calibri 10pt
   - justified body paragraphs, each with a 0.5 in first-line indent
   - bold-lead bullets with a hanging indent
   - a header built from the profile, with links shown as their own text (e.g. `example.com`, never "Website")

   Usual shape: why this role (one concrete, sourced detail about the employer) -> 3 to 5 bullets mapped to the posting's duties -> an honest "Where I am still learning" paragraph -> a short human closer. Every claim must appear on the resume sent with it.
   **Multi-role:** a short combined letter (about 200-250 words, 3 bullets, names every posting) in the company folder, for portals that keep one letter per profile, plus a full letter for each role.
7. **Finalize** each role:
   `python3 finalize.py "<role folder>" --letter source/<letter>.docx --resume <resume.pdf> --mode coop|newgrad`
   For a combined letter: `python3 finalize.py "<company folder>" --no-record --out "<company folder>" --letter <combined>.docx --resume <resume>.pdf --mode ...`
   It checks that the letter and resume are one page each and that the profile's required and forbidden phrases are respected (including date wording by mode). Only then does it write the letter PDF + docx, the resume and the merged CV. Fix what it reports; never use `--force` without the applicant's say-so.
8. **Look at it.** Render each letter and the resume to an image and check them visually.
9. **Report.** List the files, which past applications were used, the inside address used, fit flags, and notes for the form answers. The record stays `drafted`.

## B. Record status (never assume)

Only when the applicant says it happened:
`python3 applications.py mark "<company role words>" --status submitted --date YYYY-MM-DD`
Other statuses: `assessment`, `interview`, `offer`, `rejected`, `withdrawn`, `skipped` (add `--note`). Building a package does not mean it was submitted. Once submitted, `final\` is frozen: changes go in a dated copy.

## C. Query and interview prep

- `applications.py list [--term "<term>"] [--status drafted]` shows term, company, role, deadline, status and submitted date.
- `applications.py due --days 14` shows unsubmitted applications closing soon.
- `applications.py show "<words>"` prints the record, the job description and the `final\` files.
- **Interview prep:** read the job description and the letter and resume in `final\`. Map each duty to a story they already told, draft likely questions with STAR answers in their voice, and flag claims they must be ready to defend.

Folders made before this workflow have no `application.md`. Offer to backfill one (job description if it can be found, status unknown) rather than guessing.

## Done checklist

- [ ] Profile read; fit table given
- [ ] One folder per role; `application.md` holds the verbatim job description
- [ ] Resume built from the newest source, one page, dates match the role type
- [ ] Letter(s) built with `cover_letter.js`; short combined letter if multi-role
- [ ] `finalize.py` passed for every role; pages checked visually
- [ ] Earlier versions and hand edits kept
- [ ] Status left as `drafted`
