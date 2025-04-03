"""Convert OAM metadata into STAC representation."""

import datetime as dt

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
from pystac.extensions.render import Render, RenderExtension
from pystac.utils import datetime_to_str

from stactools.hotosm.constants import (
    COLLECTION_DESCRIPTION,
    COLLECTION_ID,
    COLLECTION_TITLE,
)
from stactools.hotosm.oam_metadata import OamMetadata


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

    return collection


def create_item(oam_item: OamMetadata) -> Item:
    """Create a STAC Item for an OAM image."""
    # TODO: add projection extension

    item = Item(
        id=oam_item.id,
        geometry=oam_item.geojson,
        bbox=oam_item.bbox,
        datetime=None,
        properties={
            "title": oam_item.title,
            "provider": oam_item.provider,
            "platform": oam_item.platform,
            "start_datetime": datetime_to_str(oam_item.acquisition_start),
            "end_datetime": datetime_to_str(oam_item.acquisition_end),
            "gsd": oam_item.gsd,
        },
        extra_fields={
            "providers": [
                Provider(
                    name=oam_item.provider,
                    description=oam_item.contact,
                    roles=[
                        ProviderRole.PRODUCER,
                        ProviderRole.LICENSOR,
                    ],
                ).to_dict()
            ],
        },
    )

    if oam_item.license:
        item.properties["license"] = oam_item.license

    if oam_item.sensor:
        item.properties["instruments"] = [oam_item.sensor]

    item.ext.add("file")

    item.add_asset(
        "image",
        Asset(
            href=oam_item.image_url,
            title=oam_item.title,
            media_type=MediaType.COG,
            roles=["data"],
        ),
    )

    file_ext = FileExtension.ext(item.assets["image"])
    file_ext.apply(size=oam_item.image_file_size)

    item.add_asset(
        "thumbnail",
        Asset(
            href=oam_item.thumbnail_url,
            title="thumbnail",
            media_type=MediaType.PNG,
            roles=["thumbnail"],
        ),
    )

    item.add_asset(
        "metadata",
        Asset(
            href=oam_item.metadata_url,
            title="metadata",
            media_type=MediaType.JSON,
            roles=["metadata"],
        ),
    )

    item.validate()
    return item


def _add_alternate_assets(item: Item) -> Item:
    # TODO: add alternate-assets extension
    return item
