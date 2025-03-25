# STAC Tools for Humanitarian OpenStreetMap Team's OpenAerialMap

## Getting started

This project uses `uv` to manage our Python dependencies. Visit their
[documentation](https://docs.astral.sh/uv/getting-started/installation/) for
more information on how to install this tool.

This project uses [pre-commit](https://pre-commit.com/) to manage linting and
checks for code and commits. These checks require
[Commitizen](https://commitizen-tools.github.io/commitizen/) to lint code commits.

Before working on this project please install both `pre-commit` and `commitizen`
and ensure the Git hooks are setup for this repository by running,

```bash
pre-commit install
pre-commit install --hook-type commit-msg
```

### Tests

```bash
./scripts/test
```

### Formatting and Linting

This project uses `ruff` to format and lint our code.

To format code,

```bash
./scripts/format
```

To check for lint,

```bash
./scripts/lint
```
