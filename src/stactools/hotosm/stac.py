"""Convert OAM metadata into STAC representation."""

import datetime as dt
from urllib.parse import urlparse

import rasterio
from pystac import (
    Asset,
    Collection,
    Extent,
    Item,
    Link,
    MediaType,
    Provider,
    ProviderRole,
    RelType,
    SpatialExtent,
    TemporalExtent,
)
from pystac.extensions.file import FileExtension
from pystac.extensions.item_assets import ItemAssetDefinition
from pystac.extensions.projection import ProjectionExtension
from pystac.extensions.render import Render, RenderExtension
from pystac.utils import datetime_to_str
from rasterio.errors import RasterioIOError
from rio_stac.stac import get_projection_info

from stactools.hotosm.constants import (
    COLLECTION_DESCRIPTION,
    COLLECTION_ID,
    COLLECTION_TITLE,
)
from stactools.hotosm.exceptions import AssetNotFoundError
from stactools.hotosm.oam_metadata import OamMetadata

ALTERNATE_ASSETS_VERSION = "v1.2.0"
ALTERNATE_ASSETS_SCHEMA = f"https://stac-extensions.github.io/alternate-assets/{ALTERNATE_ASSETS_VERSION}/schema.json"


def create_collection() -> Collection:
    """Create a STAC Collection of OAM imagery."""
    extent = Extent(
        SpatialExtent([[-180.0, -90.0, 180.0, 90.0]]),
        TemporalExtent([[dt.datetime(2000, 1, 1, tzinfo=dt.timezone.utc), None]]),
    )
    collection = Collection(
        id=COLLECTION_ID,
        title=COLLECTION_TITLE,
        description=COLLECTION_DESCRIPTION,
        extent=extent,
        license="CC-BY-4.0",
        providers=[
            Provider(
                name="OpenAerialMap",
                url="https://openaerialmap.org/",
                roles=[
                    ProviderRole.HOST,
                    ProviderRole.LICENSOR,
                ],
            )
        ],
    )

    collection.add_link(
        Link(
            rel=RelType.LICENSE,
            target="https://creativecommons.org/licenses/by/4.0/",
            media_type=MediaType.HTML,
            title="CC-BY-4.0 license",
        )
    )

    collection.item_assets = {
        "image": ItemAssetDefinition.create(
            title="Visual image",
            description=(
                "Visual imagery data acquired from satellite or unmanned aerial "
                "vehicle (UAV)"
            ),
            media_type=MediaType.COG,
            roles=["data"],
        ),
        "thumbnail": ItemAssetDefinition.create(
            title="Thumbnail",
            description="Thumbnail version of the image asset for browsing",
            media_type=MediaType.PNG,
            roles=["thumbnail"],
        ),
    }

    collection.ext.add("render")
    render = RenderExtension.ext(collection)
    render.apply(
        {
            "visual": Render.create(
                assets=[
                    "image",
                ],
                title="Visual image",
            )
        }
    )

    collection.validate()

    return collection


def create_item(oam_metadata: OamMetadata) -> Item:
    """Create a STAC Item for an OAM image.

    Args:
        oam_metadata: OpenAerialMap metadata describing a cataloged image.

    Returns:
        STAC Item describing the cataloged image.

    Raises:
        AssetNotFoundError: If an imagery asset does not exist.
    """
    item = Item(
        id=oam_metadata.id,
        geometry=oam_metadata.geojson,
        bbox=oam_metadata.bbox,
        datetime=None,
        properties={
            "title": oam_metadata.title,
            "provider": oam_metadata.provider,
            "platform": oam_metadata.platform,
            "start_datetime": datetime_to_str(oam_metadata.acquisition_start),
            "end_datetime": datetime_to_str(oam_metadata.acquisition_end),
            "gsd": oam_metadata.gsd,
        },
        extra_fields={
            "providers": [
                Provider(
                    name=oam_metadata.provider,
                    description=oam_metadata.contact,
                    roles=[
                        ProviderRole.PRODUCER,
                        ProviderRole.LICENSOR,
                    ],
                ).to_dict()
            ],
        },
    )

    if oam_metadata.license:
        item.properties["license"] = oam_metadata.license

    if oam_metadata.sensor:
        item.properties["instruments"] = [oam_metadata.sensor]

    item.add_asset(
        "image",
        Asset(
            href=oam_metadata.image_url,
            title=oam_metadata.title,
            media_type=MediaType.COG,
            roles=["data"],
        ),
    )

    item.ext.add("file")
    file_ext = FileExtension.ext(item.assets["image"])
    file_ext.apply(size=oam_metadata.image_file_size)

    item.add_asset(
        "thumbnail",
        Asset(
            href=oam_metadata.thumbnail_url,
            title="thumbnail",
            media_type=MediaType.PNG,
            roles=["thumbnail"],
        ),
    )

    item.add_asset(
        "metadata",
        Asset(
            href=oam_metadata.metadata_url,
            title="metadata",
            media_type=MediaType.JSON,
            roles=["metadata"],
        ),
    )

    _add_projection_extension(item, ["image"])
    _add_alternate_assets(item)

    item.validate()
    return item


def _add_projection_extension(item: Item, asset_keys: list[str]):
    """Modify Item in place by adding projection extension for assets."""
    item.ext.add("proj")
    for asset_key in asset_keys:
        ext = ProjectionExtension.ext(item.assets[asset_key])

        href = item.assets[asset_key].href
        try:
            with rasterio.open(href) as src:
                proj_info = get_projection_info(src)
        except RasterioIOError as e:
            raise AssetNotFoundError(f"Asset does not exist at {href}") from e
        ext.apply(**proj_info)


def _add_alternate_assets(item: Item) -> Item:
    """Modify Item in place by adding alternate-assets extension."""
    item.stac_extensions.append(ALTERNATE_ASSETS_SCHEMA)

    for asset in item.assets.values():
        parsed = urlparse(asset.href)
        if "amazonaws.com" in parsed.netloc:
            bucket = parsed.netloc.split(".")[0]
            s3_url = f"s3://{bucket}{parsed.path}"

            asset.extra_fields.update(
                {
                    "alternate:name": "HTTPS",
                    "alternate": {"s3": {"href": s3_url, "alternate:name": "S3"}},
                }
            )

    return item
