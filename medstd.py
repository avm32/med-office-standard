#!/usr/bin/env python3
"""MED office standard tool.

Creates and maintains project folder structures to the practice standard.
Stdlib only - no third-party packages, so it keeps working.

    medstd.py new 26014 "Szemlohegy utca" --lang hu --client "..."
    medstd.py update "../../02-Projects/26014-Szemlohegy_utca"
    medstd.py docs
    medstd.py check "../../02-Projects/26014-Szemlohegy_utca"

Every command is idempotent: it creates what is missing and never overwrites
content you have edited. `update` is safe to run on an existing project.
"""

import argparse
import csv
import datetime as _dt
import json
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
STANDARD = HERE / "standard.json"
SEEDS = HERE / "seeds"

# Seeds regenerated on every `update` - these are standard-derived, not user content.
MANAGED_SEEDS = {"CLAUDE.md", "OFFICE-STANDARD.md"}
# Seeds written once and then left alone - these accumulate user content.
ONCE_SEEDS = {"PROJECT.md", "DECISIONS.md", "REGISTER.csv"}

ACCENTS = str.maketrans({
    "á": "a", "é": "e", "í": "i", "ó": "o", "ö": "o", "ő": "o",
    "ú": "u", "ü": "u", "ű": "u",
    "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ö": "O", "Ő": "O",
    "Ú": "U", "Ü": "U", "Ű": "U",
})


def load_standard():
    try:
        with STANDARD.open(encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        sys.exit("error: standard.json not found next to medstd.py")
    except json.JSONDecodeError as exc:
        sys.exit(
            "error: standard.json is not valid JSON\n"
            "  line %d, column %d: %s\n"
            "  (usual cause: a trailing comma, or a missing quote)"
            % (exc.lineno, exc.colno, exc.msg)
        )


def strip_accents(text):
    text = text.translate(ACCENTS)
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c))


def slugify(name):
    """Project name -> folder-safe token. ASCII only: accented paths cause
    trouble in CAD tools, zip files and cross-platform sync."""
    name = strip_accents(name).strip()
    name = re.sub(r"[^A-Za-z0-9]+", "_", name)
    return re.sub(r"_+", "_", name).strip("_")


def folder_name(node, lang):
    label = node.get(lang) or node["en"]
    return "%s-%s" % (node["num"], label)


def iter_tree(tree, lang, base=Path(".")):
    """Yield (path, node) for every folder in the standard tree."""
    for node in tree:
        path = base / folder_name(node, lang)
        yield path, node
        for child in node.get("children", []):
            yield path / folder_name(child, lang), child


# --------------------------------------------------------------------------
# readmes for folders whose convention is not self-evident
# --------------------------------------------------------------------------

README_TEXT = {
    "date_prefixed": (
        "# Naming convention for this folder\n\n"
        "Subfolders here are **events, not categories**, so they take a date\n"
        "prefix instead of a number:\n\n"
        "    260910-Design_Team_Meeting\n"
        "    261104-Client_Review\n\n"
        "Format is `YYMMDD-Short_Description`. Sorts chronologically, stays\n"
        "greppable, and never collides.\n"
    ),
    "outgoing": (
        "# 08-Outgoing\n\n"
        "One frozen folder per issue event. **This folder is the issue record** -\n"
        "it is the practice's substitute for a CDE audit trail, so nothing in a\n"
        "dated subfolder is ever edited after the issue goes out.\n\n"
        "    260910-S3-Client_review/\n"
        "    261104-A1-Building_control/\n\n"
        "Format is `YYMMDD-<status>-<Recipient_or_purpose>`.\n\n"
        "Live working files stay in `06-Drawings` and `04-Calculations`. Only\n"
        "issued copies (normally PDF) come here, named with the full container ID\n"
        "including the status and revision suffix:\n\n"
        "    26014-MED-ZZ-02-D-S-0104-S3-P04.pdf\n\n"
        "Log every issue in `REGISTER.csv` at the project root.\n"
    ),
    "superseded": (
        "# XX-Superseded\n\n"
        "Never delete anything. Move it here instead.\n\n"
        "Subfolders are named for the **event that caused the supersession**, not\n"
        "for the document type:\n\n"
        "    260910-Foundation_redesign/\n"
        "    261104-Grid_shift_600mm/\n\n"
        "Format is `YYMMDD-Reason`. The reason is the point: the question you\n"
        "actually ask months later is \"what did we have before the foundation\n"
        "redesign?\", not \"which drawings were superseded in September?\".\n\n"
        "Inside a dated folder, keep the original relative path only if the batch\n"
        "is large enough to need it. A handful of files can sit loose.\n\n"
        "Rules:\n\n"
        "- Nothing in here is ever edited. It is a record, not a workspace.\n"
        "- Superseded is not the same as archive. This is live-project history;\n"
        "  the whole project folder gets archived on completion.\n"
        "- Files keep the name they had when superseded, revision suffix and all.\n"
        "  Do not rename to \"old\" or \"backup\".\n"
    ),
}


def readmes_for(node):
    out = []
    if node.get("date_prefixed") or node.get("date_prefixed_children"):
        out.append(README_TEXT["date_prefixed"])
    key = node.get("readme")
    if key:
        out = [README_TEXT[key]]
    return out


# --------------------------------------------------------------------------
# create / update
# --------------------------------------------------------------------------

def build_tree(root, std, lang, dry_run=False):
    created = []
    for rel, node in iter_tree(std["tree"], lang):
        path = root / rel
        if not path.exists():
            created.append(path)
            if not dry_run:
                path.mkdir(parents=True, exist_ok=True)
        texts = readmes_for(node)
        if texts and not dry_run:
            readme = path / "_README.md"
            if not readme.exists():
                path.mkdir(parents=True, exist_ok=True)
                readme.write_text(texts[0], encoding="utf-8")
    return created


def context_for(std, code, name, lang, client, address, stage):
    today = _dt.date.today()
    return {
        "PROJECT_CODE": code,
        "PROJECT_NAME": name,
        "PROJECT_SLUG": slugify(name),
        "CLIENT": client or "TBC",
        "ADDRESS": address or "TBC",
        "STAGE": stage or "TBC",
        "ORIGINATOR": std["originator"],
        "PRACTICE": std["practice"],
        "LANG": lang,
        "DATE": today.isoformat(),
        "DATE_SHORT": today.strftime(std["date_prefix"]["format"]),
        "EXAMPLE_ID": "%s-%s-ZZ-00-D-S-0100-S3-P01" % (code, std["originator"]),
        "OFFICE_STANDARD_TABLES": render_tables(std, lang),
    }


def substitute(text, ctx):
    for key, val in ctx.items():
        text = text.replace("{{%s}}" % key, str(val))
    return text


def write_seeds(root, ctx, dry_run=False, refresh=False):
    """Copy seed files in, substituting tokens.

    refresh=False : write anything missing (first run)
    refresh=True  : additionally regenerate MANAGED_SEEDS, leave ONCE_SEEDS alone
    """
    written, skipped = [], []
    if not SEEDS.is_dir():
        return written, skipped
    for src in sorted(SEEDS.iterdir()):
        if not src.is_file():
            continue
        dest = root / src.name
        managed = src.name in MANAGED_SEEDS
        if dest.exists() and not (refresh and managed):
            skipped.append(dest)
            continue
        written.append(dest)
        if not dry_run:
            dest.write_text(
                substitute(src.read_text(encoding="utf-8"), ctx), encoding="utf-8"
            )
    return written, skipped


def cmd_new(args, std):
    lang = args.lang or std["default_language"]
    if not re.fullmatch(r"[0-9]{5}", args.code):
        print("warning: project code %r does not match the YYNNN pattern" % args.code)
    slug = slugify(args.name)
    dest_root = Path(args.dest) if args.dest else (HERE / ".." / ".." / std["projects_root"])
    root = (dest_root / ("%s-%s" % (args.code, slug))).resolve()

    if root.exists() and not args.dry_run:
        print("project folder already exists: %s" % root)
        print("running update instead (idempotent)")
    ctx = context_for(std, args.code, args.name, lang, args.client, args.address, args.stage)

    created = build_tree(root, std, lang, args.dry_run)
    written, skipped = write_seeds(root, ctx, args.dry_run, refresh=False)

    tag = "[dry run] " if args.dry_run else ""
    print("%sproject root: %s" % (tag, root))
    print("%s  language: %s" % (tag, lang))
    print("%s  folders created: %d" % (tag, len(created)))
    print("%s  files written:   %d" % (tag, len(written)))
    if skipped:
        print("%s  left untouched:  %d" % (tag, len(skipped)))
    if not args.dry_run:
        register_project(std, args.code, args.name, ctx)
        print("  registered in %s" % (HERE / "projects.csv"))
        print("\nNext: fill in PROJECT.md, then open the folder with Claude Code.")


def cmd_update(args, std):
    root = Path(args.path).resolve()
    if not root.is_dir():
        sys.exit("error: not a directory: %s" % root)
    lang = args.lang or detect_language(root, std) or std["default_language"]
    code, name = read_project_facts(root, std)
    ctx = context_for(std, code, name, lang, args.client, args.address, args.stage)

    created = build_tree(root, std, lang, args.dry_run)
    written, skipped = write_seeds(root, ctx, args.dry_run, refresh=True)

    tag = "[dry run] " if args.dry_run else ""
    print("%supdated: %s (language: %s)" % (tag, root, lang))
    print("%s  folders added:      %d" % (tag, len(created)))
    for path in created:
        print("%s    + %s" % (tag, path.relative_to(root)))
    print("%s  seeds regenerated:  %d" % (tag, len(written)))
    print("%s  user files kept:    %d" % (tag, len(skipped)))


def detect_language(root, std):
    """Guess a project's language from folder names already on disk."""
    names = {p.name for p in root.iterdir() if p.is_dir()}
    for lang in std["languages"]:
        expected = {folder_name(n, lang) for n in std["tree"]}
        if len(names & expected) >= 3:
            return lang
    return None


def read_project_facts(root, std):
    """Recover code and name from the folder name, or PROJECT.md if present."""
    match = re.match(r"([0-9A-Za-z]+)-(.+)", root.name)
    if match:
        return match.group(1), match.group(2).replace("_", " ")
    return root.name, root.name


def register_project(std, code, name, ctx):
    path = HERE / "projects.csv"
    new = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        if new:
            writer.writerow(["code", "name", "client", "language", "created", "path"])
        writer.writerow([
            code, name, ctx["CLIENT"], ctx["LANG"], ctx["DATE"],
            "%s/%s-%s" % (std["projects_root"], code, slugify(name)),
        ])


# --------------------------------------------------------------------------
# docs
# --------------------------------------------------------------------------

def render_code_table(title, mapping, lang):
    rows = ["| Code | Meaning |", "|------|---------|"]
    for key, val in mapping.items():
        if key.startswith("_") or not isinstance(val, dict):
            continue
        label = val.get(lang) or val.get("en") or ""
        rows.append("| `%s` | %s |" % (key, label))
    return "**%s**\n\n%s\n" % (title, "\n".join(rows))


def render_tables(std, lang):
    codes = std["codes"]
    parts = [
        render_code_table("Form (NA.3.6)", codes["form"], lang),
        render_code_table("Discipline (NA.3.7)", codes["discipline"], lang),
        render_code_table("Status (NA.4.2)", codes["status"], lang),
        render_code_table("Spatial breakdown - practice defaults", codes["spatial"], lang),
        render_code_table("Functional breakdown - practice defaults", codes["functional"], lang),
        render_code_table("Drawing number series", codes["drawing_series"], lang),
    ]
    return "\n".join(parts)


def render_tree_block(std, lang):
    lines = []
    for rel, node in iter_tree(std["tree"], lang):
        depth = len(rel.parts) - 1
        lines.append("%s%s/" % ("    " * depth, rel.parts[-1]))
    return "\n".join(lines)


def cmd_docs(args, std):
    out = HERE / "docs" / "OFFICE-STANDARD.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    blocks = ["# %s - Office Standard\n" % std["practice"],
              "> Generated from `standard.json` by `medstd.py docs`. Do not edit by hand -",
              "> edit `standard.json` and regenerate.\n",
              "Originator code: **%s**  ·  Project code pattern: **%s**\n"
              % (std["originator"], std["project_code"]["pattern"]),
              "## Container ID\n",
              "```\n%s\n```\n" % " - ".join(std["container_id"]["fields"]),
              "Delimiter `%s`, characters `%s`. Status and revision are always suffixed:\n"
              % (std["delimiter"], std["container_id"]["charset"]),
              "```\n%s\n```\n" % std["container_id"]["example"]]
    for lang in std["languages"]:
        blocks.append("## Folder structure (%s)\n" % lang)
        blocks.append("```\n%s\n```\n" % render_tree_block(std, lang))
    blocks.append("## Codes\n")
    blocks.append(render_tables(std, std["default_language"]))
    out.write_text("\n".join(blocks), encoding="utf-8")
    print("wrote %s" % out)


# --------------------------------------------------------------------------
# check
# --------------------------------------------------------------------------

ID_RE = re.compile(
    r"^(?P<project>[A-Za-z0-9]+)-(?P<originator>[A-Za-z0-9]+)"
    r"-(?P<functional>[A-Za-z0-9]+)-(?P<spatial>[A-Za-z0-9]+)"
    r"-(?P<form>[A-Za-z0-9]+)-(?P<discipline>[A-Za-z0-9]+)"
    r"-(?P<number>[0-9]+)"
    r"(?:-(?P<status>[A-Za-z][0-9])-(?P<revision>P[0-9]{2}(?:\.[0-9]{2})?|C[0-9]{2}))?$"
)

CHECK_DIRS = ("Outgoing", "Kimeno")


def cmd_check(args, std):
    root = Path(args.path).resolve()
    if not root.is_dir():
        sys.exit("error: not a directory: %s" % root)
    targets = [p for p in root.iterdir() if p.is_dir() and any(k in p.name for k in CHECK_DIRS)]
    if not targets:
        targets = [root]
    bad, good = [], 0
    for target in targets:
        for path in target.rglob("*"):
            if not path.is_file() or path.name.startswith("_") or path.name.startswith("."):
                continue
            match = ID_RE.match(path.stem)
            if match:
                good += 1
                problems = validate_fields(match.groupdict(), std)
                if problems:
                    bad.append((path.relative_to(root), "; ".join(problems)))
            else:
                bad.append((path.relative_to(root), "does not parse as a container ID"))
    print("checked %s" % root)
    print("  conforming: %d" % good)
    print("  problems:   %d" % len(bad))
    for rel, why in bad:
        print("    ! %s\n        %s" % (rel, why))
    return 1 if bad else 0


def validate_fields(fields, std):
    codes = std["codes"]
    problems = []
    if fields["originator"] != std["originator"]:
        problems.append("originator %r is not %r" % (fields["originator"], std["originator"]))
    for field, table in (("form", "form"), ("discipline", "discipline")):
        val = fields[field]
        if val not in codes[table]:
            problems.append("%s code %r not in the standard" % (field, val))
    status = fields.get("status")
    if status and status not in codes["status"]:
        problems.append("status %r not in the standard" % status)
    expected = std["container_id"]["number_length"]
    if len(fields["number"]) != expected:
        problems.append("number %r is not %d digits" % (fields["number"], expected))
    return problems


# --------------------------------------------------------------------------

def main(argv=None):
    std = load_standard()
    parser = argparse.ArgumentParser(prog="medstd", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    subs = parser.add_subparsers(dest="cmd", required=True)

    def add_common(sp):
        sp.add_argument("--lang", choices=std["languages"], help="folder-name language")
        sp.add_argument("--client", help="client name")
        sp.add_argument("--address", help="site address")
        sp.add_argument("--stage", help="current work stage")
        sp.add_argument("--dry-run", action="store_true", help="show what would happen")

    sp = subs.add_parser("new", help="create a new project folder structure")
    sp.add_argument("code", help="project code, e.g. 26014")
    sp.add_argument("name", help="project name, e.g. \"Szemlohegy utca\"")
    sp.add_argument("--dest", help="parent folder (default: ../../%s)" % std["projects_root"])
    add_common(sp)
    sp.set_defaults(func=cmd_new)

    sp = subs.add_parser("update", help="bring an existing project up to standard")
    sp.add_argument("path", help="existing project folder")
    add_common(sp)
    sp.set_defaults(func=cmd_update)

    sp = subs.add_parser("docs", help="render docs/OFFICE-STANDARD.md from standard.json")
    sp.set_defaults(func=cmd_docs)

    sp = subs.add_parser("check", help="report files that do not follow the naming convention")
    sp.add_argument("path", help="project folder to check")
    sp.set_defaults(func=cmd_check)

    args = parser.parse_args(argv)
    return args.func(args, std) or 0


if __name__ == "__main__":
    sys.exit(main())
