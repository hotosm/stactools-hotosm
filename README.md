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

### Formatting, Linting, and Type Checking

This project uses `ruff` to format and lint our code.

To format code,

```bash
./scripts/format
```

To check for lint,

```bash
./scripts/lint
```

We use `mypy` for static type checking,

```bash
./scripts/typecheck
```

## STAC Extension

This repository also defines a STAC extension describing specific OpenAerialMap
metadata requirements. This extension is described in the
[README](./stac-extension/README.md) and published to Github Pages
for reference by STAC metadata.

The STAC extension will be published by creating a tagged release that looks
like, `extension-v{major}.{minor}.{patch}` (e.g., `extension-v1.0.0`). The
Github Actions workflow will take care of parsing the version string from this
release name. This `extension-` prefix is required to differentiate releases
publishing the package versus releases publishing the STAC extension.
