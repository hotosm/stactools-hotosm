"""Create STAC records for HOT OSM from Maxar's public catalog."""

import datetime as dt

from pystac import (
    Catalog,
    Collection,
    Extent,
    Item,
    Link,
    MediaType,
    RelType,
    SpatialExtent,
    TemporalExtent,
)
from pystac.extensions.item_assets import ItemAssetDefinition
from pystac.extensions.render import Render, RenderExtension

from stactools.hotosm.stac_common import add_alternate_assets

COLLECTION_ID = "maxar-opendata"
COLLECTION_DESCRIPTION = (
    "Maxar Open Data Catalog, formatted for Humanitarian OpenStreetMap "
    "Team's OpenAerialMap project"
)


def create_collection(catalog: Catalog, event_dates: list[dt.datetime]) -> Collection:
    """Rewrite Maxar root Catalog into a Collection for HOT OAM."""
    catalog_as_dict = catalog.to_dict()

    collection = Collection(
        id=COLLECTION_ID,
        title=catalog_as_dict["description"],
        description=COLLECTION_DESCRIPTION,
        extent=Extent(
            spatial=SpatialExtent([[-180.0, -90.0, 180.0, 90.0]]),
            temporal=TemporalExtent([min(event_dates), None]),
        ),
        license=catalog_as_dict["license"],
    )

    if (catalog_self_link := catalog.get_self_href()) is not None:
        collection.add_link(
            Link(
                rel=RelType.DERIVED_FROM,
                target=catalog_self_link,
                media_type=MediaType.JSON,
            )
        )

    collection.item_assets = {
        "visual": ItemAssetDefinition.create(
            title="Visual image",
            description=(
                "Imagery appropriate for visualization from this acquisition."
            ),
            media_type=MediaType.COG,
            roles=["data"],
        )
    }

    # Add render extension
    collection.ext.add("render")
    render = RenderExtension.ext(collection)
    render.apply(
        {
            "visual": Render.create(
                assets=[
                    "visual",
                ],
                title="Visual image",
            )
        }
    )

    collection.validate()

    return collection


def create_item(item: Item) -> Item:
    """Rewrite Maxar STAC Item."""
    oam_item = item.clone()

    # The ID is unique but contains "/" that interfere with access via API
    oam_item.id = item.id.replace("/", "-")

    # This Item is in an ARD tile sub-Collection. The "title" we want to use
    # is from the parent of the ARD tile Collection which is organized based
    # on the "event"
    if (item_parent := item.get_collection()) is None:
        raise ValueError(f"Cannot get parent collection for Item={item.id}")

    if (event_collection := item_parent.get_parent()) is None:
        raise ValueError(f"Cannot get parent collection for Item={item.id}")

    # Resolve HREFs relative to the Item HREF since Maxar uses relative HREFs
    oam_item.make_asset_hrefs_absolute()

    # Add some OAM properties
    oam_item.properties["provider"] = "Maxar"
    oam_item.properties["oam:platform_type"] = "satellite"

    # Update "title" to be less duplicative, baking in either,
    #     * grid code
    #     * catalog ID
    # since each Maxar collection has >=1 Item
    if "grid:code" in item.properties:
        title_suffix = item.properties["grid:code"]
    else:
        title_suffix = item.properties["catalog_id"]

    oam_item.properties["title"] = f"{event_collection.title} - {title_suffix}"

    # Clear existing links and add DERIVED_FROM
    oam_item.clear_links()

    if item_href := item.get_self_href():
        oam_item.add_link(
            Link(
                rel=RelType.DERIVED_FROM,
                target=item_href,
                media_type=MediaType.JSON,
            )
        )

    # Update Collection ID
    oam_item.collection_id = COLLECTION_ID
    oam_item.add_link(
        Link(
            rel=RelType.COLLECTION,
            target="collection.json",
            media_type=MediaType.JSON,
        )
    )

    # Add alternate assets info
    add_alternate_assets(oam_item)

    return oam_item
