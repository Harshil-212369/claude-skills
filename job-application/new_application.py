#!/usr/bin/env python3
"""Create the folder skeleton and application.md record for one role.

Layout created (under the job root, see appdb._job_root):
  <term>\\<company>\\<role folder>\\application.md   job description + status
  <term>\\<company>\\<role folder>\\source\\         editable sources (.tex, letter .json/.docx)
  <term>\\<company>\\<role folder>\\final\\          exactly what gets uploaded

Example:
  python3 new_application.py --term "Fall 2026" --company "Acme new grad 2027" \\
      --title "Software Developer" --location "Toronto, ON" \\
      --jd jd.txt --posted 2026-11-11 --deadline 2026-11-25
"""
import argparse
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # keep __pycache__ out of OneDrive
import appdb  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--term", required=True, help='Term folder, e.g. "Fall 2026"')
    ap.add_argument("--company", required=True)
    ap.add_argument("--title", required=True, help="Job title as posted")
    ap.add_argument("--location", default="")
    ap.add_argument("--job-id", default="")
    ap.add_argument("--folder", default="", help="Override the role folder name")
    ap.add_argument("--jd", help="Text file with the job description (pasted verbatim)")
    ap.add_argument("--posted", default="")
    ap.add_argument("--deadline", default="")
    ap.add_argument("--url", default="")
    ap.add_argument("--shared-with", default="", help="Other role folders in the same multi-role package")
    ap.add_argument("--force", action="store_true", help="Overwrite an existing application.md")
    a = ap.parse_args()

    loc_short = a.location.split(",")[0].strip()
    name = a.folder or (f"{a.job_id} - {a.title}" if a.job_id else a.title)
    if loc_short and not a.folder and loc_short.lower() not in name.lower():
        name += f" ({loc_short})"
    role = appdb.ROOT / appdb.safe_name(a.term) / appdb.safe_name(a.company) / appdb.safe_name(name)
    rec = role / "application.md"
    if rec.exists() and not a.force:
        print(f"ERROR: {rec} already exists (use --force to overwrite)", file=sys.stderr)
        return 1
    (role / "source").mkdir(parents=True, exist_ok=True)
    (role / "final").mkdir(parents=True, exist_ok=True)

    jd = Path(a.jd).read_text(encoding="utf-8").strip() if a.jd else "(paste the job description here)"
    meta = {"company": a.company, "job_title": a.title, "job_id": a.job_id, "location": a.location,
            "posting_url": a.url, "posted": a.posted, "deadline": a.deadline, "status": "drafted",
            "submitted": "", "created": appdb.today(), "shared_with": a.shared_with, "notes": ""}
    body = (f"# {a.company}: {a.title}{f' ({a.location})' if a.location else ''}\n\n"
            f"## Status log\n- {appdb.today()}: folder created; package not yet submitted\n\n"
            f"## Job description (verbatim)\n\n{jd}\n")
    appdb.write(rec, meta, body)
    print(role)
    return 0


if __name__ == "__main__":
    sys.exit(main())
