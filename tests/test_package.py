import importlib.metadata


def test_package_import_version():
    # https://packaging.python.org/en/latest/discussions/single-source-version/
    from stactools.hotosm import __version__

    assert importlib.metadata.version("stactools.hotosm") == __version__
