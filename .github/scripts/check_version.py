"""Check VERSION and CHANGELOG.md, and print a version's notes (ADR 0009).

    python3 -I .github/scripts/check_version.py               # the lint's check
    python3 -I .github/scripts/check_version.py --base 1.2.0  # on a Pull Request: main's VERSION
    python3 -I .github/scripts/check_version.py --notes       # the notes of VERSION's section

VERSION holds the system's version, MAJOR.MINOR.PATCH. CHANGELOG.md has one
section per version, newest first, headed `## [1.2.0] - 2026-11-17`; the first
one must be VERSION's, with at least one line of notes. With --base, VERSION
must not be lower than main's, and the check says whether merging releases a
new version (which then goes to production) or not.

Exit code 0 when everything is right, 1 otherwise. Standard library only.
"""

import argparse
import datetime
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERSION_RE = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")
HEADING_RE = re.compile(r"## \[(?P<version>[^\]]+)\] - (?P<date>\S+)")


class Invalid(Exception):
    pass


def parse_version(text, where):
    match = VERSION_RE.fullmatch(text)
    if not match:
        raise Invalid(f"{where}: '{text}' is not a version like 1.2.0 (MAJOR.MINOR.PATCH, no leading zeros)")
    return tuple(int(part) for part in match.groups())


def read_version():
    path = ROOT / "VERSION"
    if not path.exists():
        raise Invalid("VERSION is missing")
    return path.read_text().strip()


def read_sections():
    """[(version, date, notes)] from CHANGELOG.md, in the file's order."""
    path = ROOT / "CHANGELOG.md"
    if not path.exists():
        raise Invalid("CHANGELOG.md is missing")
    sections = []
    for line in path.read_text().splitlines():
        if line.startswith("## "):
            heading = HEADING_RE.fullmatch(line.rstrip())
            if not heading:
                raise Invalid(f"CHANGELOG.md: '{line}' is not a heading like '## [1.2.0] - 2026-11-17'")
            parse_version(heading["version"], "CHANGELOG.md")
            try:
                datetime.date.fromisoformat(heading["date"])
            except ValueError:
                raise Invalid(f"CHANGELOG.md: '{heading['date']}' in '{line}' is not a date (YYYY-MM-DD)") from None
            sections.append([heading["version"], heading["date"], []])
        elif sections:
            sections[-1][2].append(line)
    return [(version, date, "\n".join(notes).strip()) for version, date, notes in sections]


def check(version, sections):
    parse_version(version, "VERSION")
    if not sections:
        raise Invalid("CHANGELOG.md has no version section ('## [1.2.0] - 2026-11-17')")
    if sections[0][0] != version:
        raise Invalid(f"VERSION is {version}, but the first section of CHANGELOG.md is [{sections[0][0]}]")
    if not sections[0][2]:
        raise Invalid(f"CHANGELOG.md: the section [{version}] has no notes")
    numbers = [parse_version(v, "CHANGELOG.md") for v, _, _ in sections]
    for i in range(1, len(sections)):
        if numbers[i - 1] <= numbers[i]:
            raise Invalid(
                f"CHANGELOG.md: [{sections[i - 1][0]}] comes before [{sections[i][0]}]: newest first, each version once"
            )


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--base", help="the VERSION of the branch this one merges into")
    parser.add_argument("--notes", action="store_true", help="print the notes of VERSION's section")
    args = parser.parse_args()
    try:
        version = read_version()
        sections = read_sections()
        check(version, sections)
        if args.notes:
            print(sections[0][2])
            return 0
        if args.base:
            current, base = parse_version(version, "VERSION"), parse_version(args.base, "main's VERSION")
            if current < base:
                raise Invalid(f"VERSION is {version}, lower than main's {args.base}")
            if current == base:
                print(f"::notice::VERSION stays {version}: merging this does not change production.")
            else:
                print(f"::notice::This releases version {version}: once merged, it goes to production.")
    except Invalid as error:
        print(f"::error::{error}")
        return 1
    print(f"VERSION {version} and CHANGELOG.md agree.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
