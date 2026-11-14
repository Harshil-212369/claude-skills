#!/usr/bin/env python3
"""Query and update application records (application.md in each role folder).

  python3 applications.py list [--term "Fall 2026"] [--status drafted]
  python3 applications.py due [--days 14]          unsubmitted, deadline within N days
  python3 applications.py show "acme developer"       record + job description + final\\ files
  python3 applications.py mark "acme developer" --status submitted --date 2026-11-20

'mark ... submitted' needs an explicit --date: a package is only recorded as
submitted when the applicant says so.
"""
import argparse
import datetime as dt
import sys

sys.dont_write_bytecode = True  # keep __pycache__ out of OneDrive
import appdb  # noqa: E402


def rows(term=None, status=None):
    for p in appdb.find_records():
        meta, _ = appdb.parse(p)
        rel = p.parent.relative_to(appdb.ROOT)
        if term and rel.parts[0].lower() != term.lower():
            continue
        if status and meta.get("status", "").lower() != status.lower():
            continue
        yield p, rel, meta


def table(items):
    hdr = ["Term", "Company", "Role", "Deadline", "Status", "Submitted"]
    data = [[rel.parts[0], m.get("company", ""), m.get("job_title", "") +
             (f" ({m['location']})" if m.get("location") else ""), m.get("deadline", ""),
             m.get("status", ""), m.get("submitted", "") or "-"] for _, rel, m in items]
    if not data:
        print("(no matching applications)")
        return
    w = [max(len(str(r[i])) for r in data + [hdr]) for i in range(len(hdr))]
    line = lambda r: " | ".join(str(c).ljust(w[i]) for i, c in enumerate(r))
    print(line(hdr)); print("-+-".join("-" * x for x in w))
    for r in data:
        print(line(r))


def pick(query):
    hits = appdb.match(query)
    if not hits:
        sys.exit(f"No application matches '{query}'")
    if len(hits) > 1:
        print(f"'{query}' matches {len(hits)} records; be more specific:", file=sys.stderr)
        for h in hits:
            print("  " + str(h.parent.relative_to(appdb.ROOT)), file=sys.stderr)
        sys.exit(1)
    return hits[0]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    l = sub.add_parser("list"); l.add_argument("--term"); l.add_argument("--status")
    d = sub.add_parser("due"); d.add_argument("--days", type=int, default=14)
    s = sub.add_parser("show"); s.add_argument("query")
    m = sub.add_parser("mark"); m.add_argument("query")
    m.add_argument("--status", required=True, choices=appdb.STATUSES)
    m.add_argument("--date", help="YYYY-MM-DD (required for submitted)")
    m.add_argument("--note", default="")
    a = ap.parse_args()

    if a.cmd == "list":
        table(list(rows(a.term, a.status)))
    elif a.cmd == "due":
        today = dt.date.today()
        soon = []
        for p, rel, meta in rows():
            if meta.get("status") != "drafted" or not meta.get("deadline"):
                continue
            try:
                days = (dt.date.fromisoformat(meta["deadline"]) - today).days
            except ValueError:
                continue
            if 0 <= days <= a.days:
                soon.append((days, p, rel, meta))
        table([(p, rel, meta) for _, p, rel, meta in sorted(soon, key=lambda x: x[0])])
    elif a.cmd == "show":
        p = pick(a.query)
        meta, body = appdb.parse(p)
        print(f"Folder: {p.parent}")
        for k in appdb.FIELDS:
            if meta.get(k):
                print(f"{k:>12}: {meta[k]}")
        fin = p.parent / "final"
        print("final\\ files: " + (", ".join(sorted(x.name for x in fin.iterdir())) if fin.exists() else "(none)"))
        print("\n" + body)
    elif a.cmd == "mark":
        p = pick(a.query)
        if a.status == "submitted" and not a.date:
            sys.exit("ERROR: --date is required when marking submitted")
        if a.date:
            dt.date.fromisoformat(a.date)
        meta, body = appdb.parse(p)
        meta["status"] = a.status
        if a.status == "submitted":
            meta["submitted"] = a.date
        line = f"status -> {a.status}" + (f" ({a.date})" if a.date else "") + (f"; {a.note}" if a.note else "")
        appdb.write(p, meta, appdb.append_log(body, line))
        print(f"{p.parent.relative_to(appdb.ROOT)}: {line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
