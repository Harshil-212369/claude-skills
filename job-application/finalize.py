#!/usr/bin/env python3
"""Assemble a role's final\\ folder: letter PDF (+docx), resume PDF, merged CV.

Checks before anything is written to final\\:
  * letter and resume are exactly 1 page each
  * profile.json lint rules (required strings in the letter, forbidden strings
    everywhere, and grad-date strings by --mode coop|newgrad)
  * the record is still "drafted": a submitted package is never overwritten

Conversion runs in a temp folder outside OneDrive, so LibreOffice lock files
(.~lock.*) and lu*.tmp files never land in the job folders.

Example:
  python3 finalize.py "<term>\\<Company> new grad 2027\\<Job Title> (<City>)" \\
      --letter source/First_Last_Company_Role.docx \\
      --resume ../FirstLast_Company_Role.pdf --mode newgrad

  Combined letter for several roles (written next to the common resume):
  python3 finalize.py "<company folder>" --no-record --out "<company folder>" \\
      --letter First_Last_Company_Combined.docx --resume FirstLast_Company_Role.pdf --mode newgrad
"""
import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True  # keep __pycache__ out of OneDrive
import appdb  # noqa: E402

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:  # pragma: no cover
    PdfReader = PdfWriter = None


def pages(pdf: Path) -> int:
    if PdfReader:
        return len(PdfReader(str(pdf)).pages)
    out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, check=True).stdout
    return int(next(l.split()[-1] for l in out.splitlines() if l.startswith("Pages")))


def text_of(pdf: Path) -> str:
    try:
        return subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True,
                              text=True, check=True).stdout
    except (FileNotFoundError, subprocess.CalledProcessError):
        return "\n".join(p.extract_text() or "" for p in PdfReader(str(pdf)).pages)


def merge(parts: list[Path], out: Path) -> None:
    if PdfWriter:
        w = PdfWriter()
        for p in parts:
            w.append(str(p))
        with open(out, "wb") as fh:
            w.write(fh)
    else:
        subprocess.run(["pdfunite", *map(str, parts), str(out)], check=True)


def to_pdf(docx: Path, tmp: Path) -> Path:
    src = tmp / docx.name
    shutil.copy2(docx, src)
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        sys.exit("ERROR: LibreOffice (soffice) not found; convert the .docx to PDF in Word and pass --letter-pdf")
    subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(tmp), str(src)],
                   cwd=tmp, capture_output=True, check=True, timeout=150)
    pdf = src.with_suffix(".pdf")
    if not pdf.exists():
        sys.exit(f"ERROR: conversion produced no PDF for {docx}")
    return pdf


def lint(name: str, txt: str, rules: dict, mode: str, is_letter: bool) -> list[str]:
    errs = []
    flat = " ".join(txt.split())
    if is_letter:
        errs += [f"{name}: missing required text '{s}'" for s in rules.get("required_in_letter", []) if s not in flat]
    errs += [f"{name}: contains forbidden text '{s}'" for s in rules.get("forbidden_everywhere", []) if s in flat]
    if mode:
        errs += [f"{name}: '{s}' is not allowed in {mode} applications"
                 for s in rules.get("forbidden_by_mode", {}).get(mode, []) if s in flat]
    return errs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("role", type=Path, help="Role folder containing application.md")
    ap.add_argument("--letter", type=Path, help="Letter .docx (relative to the role folder or absolute)")
    ap.add_argument("--letter-pdf", type=Path, help="Use an existing letter PDF instead of converting")
    ap.add_argument("--resume", type=Path, required=True, help="Resume PDF")
    ap.add_argument("--extra", type=Path, nargs="*", default=[], help="Other package files (transcript, certificates)")
    ap.add_argument("--mode", choices=["coop", "newgrad"], required=True, help="Grad-date rule set to lint against")
    ap.add_argument("--cv-name", default="", help="Merged CV filename (default <letter stem>_CV.pdf)")
    ap.add_argument("--no-docx", action="store_true", help="Do not copy the letter .docx into final")
    ap.add_argument("--out", type=Path, help="Output folder (default <role>\\final). For a combined letter, the company folder")
    ap.add_argument("--no-record", action="store_true",
                    help="Folder has no application.md (e.g. a company _shared folder for a combined letter)")
    ap.add_argument("--force", action="store_true", help="Write even if the record is not 'drafted' or lint fails")
    a = ap.parse_args()

    role = a.role.resolve()
    rec = role / "application.md"
    if a.no_record:
        meta, body = {"status": "drafted"}, ""
    elif not rec.exists():
        sys.exit(f"ERROR: {rec} not found; run new_application.py first")
    else:
        meta, body = appdb.parse(rec)
    if meta.get("status", "drafted") != "drafted" and not a.force:
        sys.exit(f"ERROR: status is '{meta.get('status')}'. A submitted package is frozen; "
                 "write a dated copy instead, or pass --force.")
    resolve = lambda p: p if p.is_absolute() else (role / p).resolve()
    rules = appdb.load_profile()["lint"]
    final = resolve(a.out) if a.out else role / "final"
    final.mkdir(exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="jobfinal-") as td:
        tmp = Path(td)
        if a.letter_pdf:
            letter_pdf = resolve(a.letter_pdf)
            stem = letter_pdf.stem
        elif a.letter:
            letter_pdf = to_pdf(resolve(a.letter), tmp)
            stem = resolve(a.letter).stem
        else:
            sys.exit("ERROR: pass --letter or --letter-pdf")
        resume = resolve(a.resume)
        errs = []
        for label, pdf in (("letter", letter_pdf), ("resume", resume)):
            n = pages(pdf)
            if n != 1:
                errs.append(f"{label}: {n} pages (must be 1)")
        errs += lint("letter", text_of(letter_pdf), rules, a.mode, True)
        errs += lint("resume", text_of(resume), rules, a.mode, False)
        if errs and not a.force:
            print("NOT WRITTEN. Fix these first:", *errs, sep="\n  - ", file=sys.stderr)
            return 1

        written = []
        def put(src: Path, name: str):
            dst = final / name
            if dst.resolve() != src.resolve():   # resume may already sit in the output folder
                shutil.copy2(src, dst)
            written.append(name)
        put(letter_pdf, f"{stem}.pdf")
        if a.letter and not a.no_docx:
            put(resolve(a.letter), f"{stem}.docx")
        put(resume, resume.name)
        cv = a.cv_name or f"{stem}_CV.pdf"
        merge([letter_pdf, resume], tmp / cv)
        put(tmp / cv, cv)
        for x in a.extra:
            put(resolve(x), resolve(x).name)

    if not a.no_record:
        appdb.write(rec, meta, appdb.append_log(body, f"final package assembled ({', '.join(written)}); not submitted"))
    for w in errs:
        print(f"WARNING (forced): {w}")
    print(f"final\\ -> {final}")
    for n in written:
        print(f"  {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
