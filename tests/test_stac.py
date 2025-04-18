"""Tests for `stactools.hotosm.stac` module."""

import datetime as dt
from unittest.mock import patch

import numpy as np
import pytest
import rasterio
from pystac.utils import str_to_datetime
from rasterio.transform import from_bounds

from stactools.hotosm.constants import COLLECTION_ID
from stactools.hotosm.exceptions import AssetNotFoundError
from stactools.hotosm.oam_metadata import OamMetadata
from stactools.hotosm.stac import create_collection, create_item


def test_create_collection():
    """Test Collection creation."""
    collection = create_collection()
    collection.validate()


@pytest.fixture
def example_oam_image(example_oam_metadata: OamMetadata, tmp_path) -> OamMetadata:
    """Provision data for the example OAM metadata item."""
    data = np.random.randint(low=0, high=255, size=(3, 13, 42), dtype="uint8")
    profile = {
        "count": data.shape[0],
        "height": data.shape[1],
        "width": data.shape[2],
        "dtype": "uint8",
        "crs": rasterio.crs.CRS.from_string(example_oam_metadata.projection_wkt),
        "transform": from_bounds(*example_oam_metadata.bbox, *data.shape[1:]),
    }

    example_oam_metadata.image_url = str(tmp_path / example_oam_metadata.image_url)
    with rasterio.open(
        example_oam_metadata.image_url, "w", driver="COG", **profile
    ) as dst:
        dst.write(data)

    example_oam_metadata.thumbnail_url = str(
        tmp_path / example_oam_metadata.thumbnail_url
    )
    with rasterio.open(
        example_oam_metadata.thumbnail_url, "w", driver="PNG", **profile
    ) as dst:
        dst.write(data)

    return example_oam_metadata


def test_create_item(example_oam_image: OamMetadata):
    """Test Item creation."""
    item = create_item(example_oam_image)
    item.validate()

    assert item.collection_id == COLLECTION_ID

    for datetime_prop in {"start_datetime", "end_datetime"}:
        assert isinstance(str_to_datetime(item.properties[datetime_prop]), dt.datetime)

    assert set(item.assets) == {"image", "thumbnail", "metadata"}

    assert "file:size" in item.assets["image"].extra_fields
    for prop in {"code", "geometry", "bbox", "shape", "transform"}:
        assert f"proj:{prop}" in item.assets["image"].extra_fields

    assert "alternate" not in item.assets["image"].extra_fields


def test_create_item_raises_asset_not_found(example_oam_metadata: OamMetadata):
    """Test that create_item() raises AssetNotFoundError."""
    with pytest.raises(AssetNotFoundError, match=r"Asset does not exist.*"):
        create_item(example_oam_metadata)


@patch("stactools.hotosm.stac._add_projection_extension")
def test_create_item_creates_s3_alternate_assets(
    patch_add_proj_ext, example_oam_metadata: OamMetadata
):
    """Ensure create_item creates alternate assets references for AWS S3 hrefs.

    This test patches `_add_projection_extension` because it would otherwise make
    network requests to S3 that we want to avoid.
    """
    example_oam_metadata.image_url = "https://test-bucket.s3.amazonaws.com/test.tif"

    item = create_item(example_oam_metadata)

    image_asset = item.assets["image"]
    assert image_asset.extra_fields["alternate:name"] == "HTTPS"

    image_alt_assets = image_asset.extra_fields["alternate"]
    assert "s3" in image_alt_assets
    assert image_alt_assets["s3"] == {
        "alternate:name": "S3",
        "href": "s3://test-bucket/test.tif",
    }

    patch_add_proj_ext.assert_called()
