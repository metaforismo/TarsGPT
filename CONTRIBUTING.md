# Contributing to TarsGPT

Thanks for helping TARS walk better. A few ground rules keep the project
healthy.

## Project scope

- **No arms.** This build doesn't grasp anything: contributions should serve
  balance, locomotion (forward, turns, lateral strafing), voice/AI or the
  builder experience. Arm-related code is kept for compatibility but is not
  developed further.
- **Verifiable over plausible.** Movement changes should come with a way to
  check them: a test in simulation, a measured result, or both.
- **Graceful degradation.** Every feature must work (or politely disable
  itself) without API keys, without hardware and without optional deps.

## Development setup

```bash
git clone https://github.com/metaforismo/TarsGPT
cd TarsGPT
python -m venv .venv && source .venv/bin/activate
pip install -e . ruff
pip install numpy            # speaker-ID / gait tests
pre-commit install           # optional: lint on every commit
```

## Before opening a PR

```bash
ruff check tars/ tests/ servo_tester.py   # must be clean
python tests/run_tests.py                 # must say N/N passed
python -m tars.app --sim --no-voice       # boots and serves the dashboard
```

CI runs the same three steps on Python 3.11 and 3.12 — green CI is required
to merge.

- One topic per PR, with tests for new behavior and edge cases.
- Update the **bilingual docs** (`docs/en` + `docs/it`) when you change
  behavior, and add a line to `CHANGELOG.md` under the next version.
- New skills go in `tars/skills/` as a single `@skill`-decorated function —
  see "Writing a skill" in [docs/en/SOFTWARE.md](docs/en/SOFTWARE.md).

## Releases (maintainers)

Releases are automatic: bump `__version__` in `tars/__init__.py` and
`pyproject.toml`, add the matching CHANGELOG section, merge to `main` — the
**Release** workflow creates the tag and the GitHub Release with the
CHANGELOG notes (and skips silently if that version is already released).
Manual dispatch from the Actions tab also works.

**Codenames**: each minor release carries a name from the *Interstellar*
universe, set in `__codename__` (it shows up in the release title, `tars
--version`, `/api/status`, the onboard display and the OS MOTD). The queue:
Endurance → Gargantua → Lazarus → Miller → Mann → Edmunds → Cooper → Murph.
