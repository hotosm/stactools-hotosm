"""Test fixtures."""

import datetime as dt
import json
from pathlib import Path

import pyproj
import pytest
import shapely
from shapely.wkt import dumps as wkt_dumps

from stactools.hotosm.oam_metadata import OamMetadata

DATA = Path(__file__).parent / "data"


@pytest.fixture
def example_oam_item_metadata() -> OamMetadata:
    """Example OamItemMetadata for testing."""
    now = dt.datetime.now(tz=dt.timezone.utc)
    bbox = [-80.4248105, -0.980146199999, -80.418725308, -0.9748217]
    geojson = {
        "coordinates": [
            [
                [-80.4248105, -0.9748217],
                [-80.418725308, -0.9748217],
                [-80.418725308, -0.980146199999],
                [-80.4248105, -0.980146199999],
                [-80.4248105, -0.9748217],
            ]
        ],
        "type": "Polygon",
    }

    return OamMetadata(
        id="foo",
        title="Foo",
        contact="foo@openaerialmap.org",
        provider="openaerialmap",
        platform="uav",
        sensor="camera",
        license="CC-BY-4.0",
        acquisition_start=now,
        acquisition_end=now + dt.timedelta(seconds=1),
        geojson=geojson,
        bbox=bbox,
        footprint_wkt=wkt_dumps(shapely.geometry.shape(geojson)),
        projection_wkt=pyproj.CRS.from_epsg(4326).to_wkt(),
        gsd=1.857e-7,
        image_url="image.tif",
        image_file_size=12345,
        thumbnail_url="thumb.png",
        metadata_url="metadata.json",
    )


@pytest.fixture
def example_oam_meta_api_response() -> dict:
    """Example OAM Metadata API response."""
    return json.loads((DATA / "oam_meta_api_response10.json").read_text())
