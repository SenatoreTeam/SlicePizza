# 0010: The versions live in releases.toml, like the other projects

- **Status:** Accepted
- **Date:** 2026-11-17
- **Phase:** 4

## Context

[ADR 0009](0009-numbered-versions.md) made production run numbered versions, with the version in a `VERSION` file and the notes in a free-form `CHANGELOG.md`. The server administrator's other projects (Kaladrius, Farol de Obras) keep their history in one structured file instead, and their pipeline writes each GitHub release from it:

- every change is an item with a **kind** (new, improvement, fix, security) and an **area**, in the words of the people who use the system;
- an update proposed by **Dependabot** is marked as such, with its Pull Request, so the project's own changes and Dependabot's are told apart;
- the release gets a **title** (`0.72.2 – Libraries updated`), and the items read `**Security · System:** … (Dependabot, #107)`;
- the README says the current version, and the checks fail when it doesn't match.

Two files that must agree (`VERSION` and the first heading of `CHANGELOG.md`) are also one more thing to get wrong.

## Options considered

1. **Keep `VERSION` and `CHANGELOG.md`.** Already works, but releases differ from the other projects, and nothing says what kind of change each line is or which came from Dependabot.
2. **`releases.yaml`, exactly like the other projects.** Same format, but reading YAML needs PyYAML: it has no wheel for Python 3.15, and this project installs only hash-checked wheels ([api/README.md](../../api/README.md#dependencies)), so it would have to be built from source or installed unchecked, only for the pipeline.
3. **`releases.toml`**: the same structure, read with Python's own `tomllib`. No new package, no lock file to keep up to date.

## Decision

Option 3. `releases.toml`, at the repository's root, replaces `VERSION` and `CHANGELOG.md`:

```toml
[[release]]                    # newest first: a new version goes at the top
version = "1.1.0"
date = 2026-11-20
title.en = "Pizzas can be marked as sold out"
title.pt-br = "Pizzas podem ser marcadas como esgotadas"

[[release.item]]
kind = "new"                   # new | improvement | fix | security
area = "Menu"                  # Menu | Orders | Kitchen | Telegram | System
text.en = "The kitchen can mark a pizza as sold out, and the menu hides it until it is back."
text.pt-br = "A cozinha pode marcar uma pizza como esgotada, e o cardápio a esconde até ela voltar."

[[release.item]]
kind = "security"
area = "System"
source = "dependabot"          # an update proposed by Dependabot, with its Pull Request
pr = 52
text.en = "Libraries updated, with security fixes."
text.pt-br = "Bibliotecas atualizadas, com correções de segurança."
```

- **The lint** ([`releases.py`](../../.github/scripts/releases.py)) checks the format, the kinds and areas, both languages (`en` and `pt-br`, the project's two), versions newest first and each higher than the one below, dates in order, `source` and `pr` together, and that README.md's `**Current version:**` line says the newest version. On a Pull Request it refuses a version lower than `main`'s and says whether merging releases one.
- **The `release` job** works as in ADR 0009, and writes the GitHub release from the file: title `1.1.0 – Pizzas can be marked as sold out`, one line per item, `- **New · Menu:** …`, with `(Dependabot, #52)` on Dependabot's.
- Everything else in ADR 0009 stays: the version's tag on the tested images, no `latest`, the server installing the newest version.

## Consequences

- The releases look like the other projects', and Dependabot's updates are visible as such.
- A Pull Request that should reach production adds a `[[release]]` block at the top of `releases.toml` and updates the README line; the lint says what is missing.
- The texts are written twice, in English and Portuguese; the GitHub release uses the English ones.
- `releases.toml` is not `releases.yaml`: the structure is the same, the syntax is TOML's. If PyYAML ships wheels for the image's Python one day, switching is a small change to `releases.py`.
- Version 1.0.0 was released with ADR 0009's files; its GitHub release keeps that text.
