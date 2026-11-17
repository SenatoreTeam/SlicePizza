"""Check releases.toml, and print a version's number, GitHub release title or notes (ADR 0010).

    python3 -I .github/scripts/releases.py                 # the lint's check
    python3 -I .github/scripts/releases.py --base 1.2.0    # on a Pull Request: main's version
    python3 -I .github/scripts/releases.py --version       # the newest version, e.g. 1.3.0
    python3 -I .github/scripts/releases.py --title 1.3.0   # "1.3.0 – <its title>"
    python3 -I .github/scripts/releases.py --notes 1.3.0   # its items, as Markdown

releases.toml lists the versions, newest first, each with its date, an optional title
and its items (kind, area, text in English and Portuguese, and the Pull Request of an
update proposed by Dependabot). The check also requires README.md's "Current version"
line to say the newest version. With --base, the newest version must not be lower than
main's, and a notice says whether merging releases a new version (which then goes to
production) or not. --file reads another copy of the file (main's, for --base).

Exit code 0 when everything is right, 1 otherwise. Standard library only (tomllib).
"""

import argparse
import datetime
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERSION_RE = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")
README_RE = re.compile(r"^\*\*Current version:\*\* (\S+)", re.MULTILINE)
LANGUAGES = ("en", "pt-br")
KINDS = {"new": "New", "improvement": "Improvement", "fix": "Fix", "security": "Security"}
AREAS = ("Menu", "Orders", "Kitchen", "Telegram", "System")
SOURCES = {"dependabot": "Dependabot"}


class Invalid(Exception):
    pass


def parse_version(text, where):
    match = VERSION_RE.fullmatch(text) if isinstance(text, str) else None
    if not match:
        raise Invalid(f"{where}: {text!r} is not a version like \"1.2.0\" (MAJOR.MINOR.PATCH, no leading zeros)")
    return tuple(int(part) for part in match.groups())


def texts(value, where):
    """{"en": ..., "pt-br": ...}, each a non-empty line of text."""
    if not isinstance(value, dict) or set(value) != set(LANGUAGES):
        raise Invalid(f"{where} needs exactly these languages: {', '.join(LANGUAGES)}")
    for language, text in value.items():
        if not isinstance(text, str) or not text.strip():
            raise Invalid(f"{where}.{language} is empty")
    return {language: " ".join(text.split()) for language, text in value.items()}


def load(path):
    if not path.exists():
        raise Invalid(f"{path.name} is missing")
    try:
        data = tomllib.loads(path.read_text())
    except tomllib.TOMLDecodeError as error:
        raise Invalid(f"{path.name} is not valid TOML: {error}") from None
    releases = data.get("release")
    if set(data) != {"release"} or not isinstance(releases, list) or not releases:
        raise Invalid(f"{path.name} must hold only [[release]] blocks, at least one")

    checked = []
    for release in releases:
        where = f"[[release]] {release.get('version')!r}"
        unknown = set(release) - {"version", "date", "title", "item"}
        if unknown:
            raise Invalid(f"{where}: unknown field(s) {', '.join(sorted(unknown))}")
        number = parse_version(release.get("version"), where)
        date = release.get("date")
        if type(date) is not datetime.date:
            raise Invalid(f"{where}: date must be a date like 2026-11-17, without quotes")
        title = texts(release["title"], f"{where} title") if "title" in release else None
        items = release.get("item")
        if not isinstance(items, list) or not items:
            raise Invalid(f"{where}: at least one [[release.item]]")
        checked_items = []
        for n, item in enumerate(items, 1):
            at = f"{where} item {n}"
            unknown = set(item) - {"kind", "area", "text", "source", "pr"}
            if unknown:
                raise Invalid(f"{at}: unknown field(s) {', '.join(sorted(unknown))}")
            if item.get("kind") not in KINDS:
                raise Invalid(f"{at}: kind must be one of {', '.join(KINDS)}")
            if item.get("area") not in AREAS:
                raise Invalid(f"{at}: area must be one of {', '.join(AREAS)}")
            source, pr = item.get("source"), item.get("pr")
            if source is not None and source not in SOURCES:
                raise Invalid(f"{at}: source can only be {', '.join(SOURCES)}")
            if (source is None) != (pr is None) or (pr is not None and (type(pr) is not int or pr < 1)):
                raise Invalid(f"{at}: source and pr go together (pr = the Pull Request's number)")
            checked_items.append({**item, "text": texts(item.get("text"), f"{at} text")})
        checked.append({"version": release["version"], "number": number, "date": date, "title": title,
                        "items": checked_items})

    for newer, older in zip(checked, checked[1:], strict=False):
        if newer["number"] <= older["number"]:
            raise Invalid(f"{newer['version']} comes before {older['version']}: newest first, each version once")
        if newer["date"] < older["date"]:
            raise Invalid(f"{newer['version']} is dated before {older['version']}")
    return checked


def check_readme(newest):
    readme = (ROOT / "README.md").read_text()
    found = README_RE.findall(readme)
    if found != [newest]:
        said = found[0] if len(found) == 1 else f"{len(found)} lines"
        raise Invalid(f"README.md must have one line '**Current version:** {newest}' (it has {said})")


def find(releases, version):
    for release in releases:
        if release["version"] == version:
            return release
    raise Invalid(f"version {version} is not in releases.toml")


def title(release):
    if release["title"]:
        return f"{release['version']} – {release['title']['en']}"
    return release["version"]


def notes(release):
    lines = []
    for item in release["items"]:
        # Dependabot's updates say so; on GitHub, "#52" links to the Pull Request.
        source = f" ({SOURCES[item['source']]}, #{item['pr']})" if item.get("source") else ""
        lines.append(f"- **{KINDS[item['kind']]} · {item['area']}:** {item['text']['en']}{source}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--file", type=Path, default=ROOT / "releases.toml", help="the releases file to read")
    parser.add_argument("--base", help="the newest version of the branch this one merges into")
    what = parser.add_mutually_exclusive_group()
    what.add_argument("--version", action="store_true", help="print the newest version")
    what.add_argument("--title", metavar="VERSION", help="print the GitHub release title of VERSION")
    what.add_argument("--notes", metavar="VERSION", help="print the GitHub release notes of VERSION")
    args = parser.parse_args()
    try:
        releases = load(args.file)
        newest = releases[0]["version"]
        if args.version:
            print(newest)
            return 0
        if args.title:
            print(title(find(releases, args.title)))
            return 0
        if args.notes:
            print(notes(find(releases, args.notes)))
            return 0
        check_readme(newest)
        if args.base:
            if releases[0]["number"] < parse_version(args.base, "main's version"):
                raise Invalid(f"the newest version is {newest}, lower than main's {args.base}")
            if newest == args.base:
                print(f"::notice::The newest version stays {newest}: merging this does not change production.")
            else:
                print(f"::notice::This releases version {newest}: once merged, it goes to production.")
    except Invalid as error:
        print(f"::error::{error}")
        return 1
    print(f"releases.toml is right; the newest version is {newest}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
