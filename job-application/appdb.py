"""appdb.py: read/write the application.md record kept in every role folder.

application.md = a small front-matter header (key: value lines between two
'---' lines) + a status log + the job description pasted verbatim. Standard
library only, so it runs in WSL, the Cowork VM, or plain Windows Python.
"""
from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

FIELDS = ["company", "job_title", "job_id", "location", "posting_url", "posted",
          "deadline", "status", "submitted", "created", "shared_with", "notes"]
STATUSES = ["drafted", "submitted", "assessment", "interview", "offer",
            "rejected", "withdrawn", "skipped"]
WIN_BAD = re.compile(r'[<>:"/\\|?*]')


def strip_json_comments(text: str) -> str:
    """Remove // line and /* block */ comments outside strings, and trailing commas,
    so profile.json(c) can carry notes. URLs like https://... are inside strings and kept."""
    out, i, n, in_str = [], 0, len(text), False
    while i < n:
        ch = text[i]
        if in_str:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(text[i + 1]); i += 2; continue
            if ch == '"':
                in_str = False
            i += 1
        elif ch == '"':
            in_str = True; out.append(ch); i += 1
        elif text.startswith("//", i):
            while i < n and text[i] != "\n":
                i += 1
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            i = n if end == -1 else end + 2
        else:
            out.append(ch); i += 1
    return re.sub(r",(\s*[}\]])", r"\1", "".join(out))


def profile_path() -> Path:
    """The profile to use. $JOB_PROFILE wins, so personal details can live outside
    this folder (and outside any git clone); else profile.jsonc/.json next to the scripts."""
    import os
    if os.environ.get("JOB_PROFILE"):
        return Path(os.environ["JOB_PROFILE"]).expanduser()
    here = Path(__file__).resolve().parent
    for name in ("profile.jsonc", "profile.json"):
        if (here / name).exists():
            return here / name
    raise SystemExit(f"ERROR: no profile.jsonc or profile.json in {here} "
                     "(copy profile.example.jsonc, or set JOB_PROFILE)")


def load_profile() -> dict:
    """Load the profile from profile_path(); comments allowed."""
    import json
    p = profile_path()
    try:
        return json.loads(strip_json_comments(p.read_text(encoding="utf-8")))
    except OSError as e:
        raise SystemExit(f"ERROR: cannot read profile {p}: {e}")
    except json.JSONDecodeError as e:
        raise SystemExit(f"ERROR: {p} is not valid JSON(C): {e}")


def _job_root() -> Path:
    """Folder holding the term folders. $JOB_ROOT wins, then "job_root" in the profile,
    else the folder above this tools folder (the layout used when the tools sit next to the jobs)."""
    import os
    if os.environ.get("JOB_ROOT"):
        return Path(os.environ["JOB_ROOT"]).expanduser().resolve()
    try:
        jr = load_profile().get("job_root")
        if jr:
            return Path(jr).expanduser().resolve()
    except SystemExit:
        pass
    return Path(__file__).resolve().parent.parent


ROOT = _job_root()


def safe_name(name: str) -> str:
    """Make a string safe as a Windows folder/file name."""
    return WIN_BAD.sub("-", name).strip().rstrip(".")


def today() -> str:
    """Today's date in the applicant's time zone (the VM/WSL clock may be UTC)."""
    import os
    try:
        from zoneinfo import ZoneInfo
        return dt.datetime.now(ZoneInfo(os.environ.get("JOB_TZ", "America/Toronto"))).date().isoformat()
    except Exception:
        return dt.date.today().isoformat()


def parse(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not m:
        raise ValueError(f"{path}: no front-matter block")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, m.group(2)


def dump(meta: dict, body: str) -> str:
    keys = FIELDS + [k for k in meta if k not in FIELDS]
    head = "\n".join(f"{k}: {meta.get(k, '')}".rstrip() for k in keys)
    return f"---\n{head}\n---\n{body}"


def write(path: Path, meta: dict, body: str) -> None:
    path.write_text(dump(meta, body), encoding="utf-8")


def append_log(body: str, line: str) -> str:
    """Add a dated line under '## Status log' (created if missing)."""
    entry = f"- {today()}: {line}"
    if "## Status log" in body:
        head, rest = body.split("## Status log", 1)
        rest_lines = rest.split("\n")
        # insert after the existing log bullets
        i = 1
        while i < len(rest_lines) and rest_lines[i].startswith("- "):
            i += 1
        rest_lines.insert(i, entry)
        return head + "## Status log" + "\n".join(rest_lines)
    return f"## Status log\n{entry}\n\n{body}"


def find_records(root: Path = ROOT, max_depth: int = 5) -> list[Path]:
    out = []
    for p in root.rglob("application.md"):
        rel = p.relative_to(root)
        if len(rel.parts) <= max_depth and "_job-tools" not in rel.parts:
            out.append(p)
    return sorted(out)


def where() -> None:
    """Print the files and folder the scripts will use (python3 appdb.py)."""
    p = profile_path()
    print(f"profile:  {p}")
    print(f"rules:    {p.with_name('profile.md')}")
    print(f"job_root: {ROOT}")


def match(query: str, root: Path = ROOT) -> list[Path]:
    q = query.lower()
    hits = []
    for p in find_records(root):
        meta, _ = parse(p)
        hay = " ".join([str(p.parent.relative_to(root)), meta.get("company", ""),
                        meta.get("job_title", ""), meta.get("job_id", "")]).lower()
        if all(word in hay for word in q.split()):
            hits.append(p)
    return hits


if __name__ == "__main__":
    where()
