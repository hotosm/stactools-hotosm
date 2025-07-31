"""Command line interface for OAM STAC creation and syncing."""

import datetime as dt
from functools import partial
from typing import Any, Callable, Iterator, Literal, TypeVar

import click
import pystac
import requests
from pypgstac.db import PgstacDB
from pypgstac.load import Loader, Methods

uploaded_since_sec = click.option(
    "--uploaded-since",
    type=float,
    help="Find Items uploaded in last period provided in seconds.",
)
uploaded_after_dt = click.option(
    "--uploaded-after",
    type=click.DateTime(),
    help="Find Items uploaded after this date (UTC).",
)
handle_exceptions = click.option(
    "--handle-exceptions",
    type=click.Choice(["RAISE", "IGNORE"]),
    help="Behavior for exception handling when creating STAC Items.",
    default="RAISE",
    show_default=True,
)
HandleExceptionsType = Literal["RAISE", "IGNORE"]


def parse_uploaded_since(
    uploaded_since_sec: float | None,
    uploaded_after_dt: dt.datetime | None,
) -> dt.datetime:
    """Parse mutually exclusive arguments for finding Items uploaded since some time."""
    if (uploaded_after_dt is uploaded_since_sec) or (
        uploaded_since_sec and uploaded_after_dt
    ):
        raise click.BadParameter(
            "Must provide one of --uploaded-since or --uploaded-after"
        )

    if uploaded_since_sec is not None:
        return dt.datetime.now(tz=dt.UTC) - dt.timedelta(seconds=uploaded_since_sec)

    if uploaded_after_dt is not None:
        return uploaded_after_dt.replace(tzinfo=dt.UTC)

    raise click.BadParameter("Must provide one of --uploaded-since or --uploaded-after")


def create_pgstac_from_ctx(
    ctx: click.Context,
    _: click.Parameter,
    value: Any,
) -> PgstacDB:
    """Create PgSTAC connection."""
    dsn = "postgresql://{user}:{password}@{host}:{port}/{database}".format(
        user=ctx.params["pguser"],
        password=ctx.params["pgpassword"],
        host=ctx.params["pghost"],
        port=ctx.params["pgport"],
        database=value,
    )
    ctx.obj = ctx.obj or {}
    ctx.obj["pgstac"] = PgstacDB(dsn)
    return value


pgstac_username = click.option(
    "--pguser",
    envvar="PGUSER",
    help="Username for PgSTAC",
    required=True,
)
pgstac_password = click.option(
    "--pgpassword",
    envvar="PGPASSWORD",
    help="Password for PgSTAC",
    required=True,
)
pgstac_host = click.option(
    "--pghost",
    envvar="PGHOST",
    help="Host for PgSTAC",
    required=True,
)
pgstac_port = click.option(
    "--pgport",
    envvar="PGPORT",
    help="Port for PgSTAC",
    required=True,
)
pgstac_database = click.option(
    "--pgdatabase",
    envvar="PGDATABASE",
    help="Database for PgSTAC",
    required=True,
    callback=create_pgstac_from_ctx,
)


@click.group
def main():
    """STAC for Humanitarian OpenStreetMap Team OpenAerialMap."""


@main.command()
@uploaded_since_sec
@uploaded_after_dt
@handle_exceptions
@pgstac_username
@pgstac_password
@pgstac_host
@pgstac_port
@pgstac_database
@click.pass_context
def sync_oam(
    ctx: click.Context,
    uploaded_since: float | None,
    uploaded_after: dt.datetime | None,
    handle_exceptions: HandleExceptionsType,
    **_pgstac_options: Any,
):
    """Sync new STAC Items from OAM metadata API."""
    from stactools.hotosm.constants import COLLECTION_ID
    from stactools.hotosm.oam_metadata import OamMetadata
    from stactools.hotosm.oam_metadata_client import OamMetadataClient
    from stactools.hotosm.stac import create_item

    uploaded_after = parse_uploaded_since(uploaded_since, uploaded_after)
    loader = Loader(ctx.obj["pgstac"])
    client = OamMetadataClient.new()

    def get_all_items_sanitized(uploaded_after: dt.datetime) -> Iterator[OamMetadata]:
        for oam_metadata in client.get_all_items(uploaded_after):
            yield oam_metadata.sanitize()

    click.echo(f"Looking for OAM metadata entities added since {uploaded_after}")
    sync_handler(
        collection_id=COLLECTION_ID,
        raw_metadata_creator=get_all_items_sanitized,
        stac_item_creator=create_item,
        uploaded_after=uploaded_after,
        loader=loader,
        handle_exceptions=handle_exceptions,
    )


@main.command()
@uploaded_since_sec
@uploaded_after_dt
@pgstac_username
@pgstac_password
@pgstac_host
@pgstac_port
@pgstac_database
@click.pass_context
def sync_maxar(
    ctx: click.Context,
    uploaded_since: float | None,
    uploaded_after: dt.datetime | None,
    handle_exceptions: HandleExceptionsType,
    **_pgstac_options: Any,
) -> None:
    """Sync new Maxar Items from the open data bucket."""
    from stactools.hotosm.maxar.stac import COLLECTION_ID, create_item
    from stactools.hotosm.maxar.sync import new_stac_items

    uploaded_after = parse_uploaded_since(uploaded_since, uploaded_after)
    loader = Loader(ctx.obj["pgstac"])

    click.echo(f"Looking for STAC Items added since {uploaded_after}")
    sync_handler(
        collection_id=COLLECTION_ID,
        raw_metadata_creator=partial(
            new_stac_items, pystac.stac_io.RetryStacIO(), requests.Session()
        ),
        stac_item_creator=create_item,
        uploaded_after=uploaded_after,
        loader=loader,
        handle_exceptions=handle_exceptions,
    )


MetadataType = TypeVar("MetadataType")


def sync_handler(
    collection_id: str,
    raw_metadata_creator: Callable[[dt.datetime], Iterator[MetadataType]],
    stac_item_creator: Callable[[MetadataType], pystac.Item],
    uploaded_after: dt.datetime,
    loader: Loader,
    handle_exceptions: HandleExceptionsType,
) -> None:
    """Orchestrate creating STAC Items from a data provider."""
    raw_metadata = list(raw_metadata_creator(uploaded_after))
    click.echo(f"Found {len(raw_metadata)} metadata items added since {uploaded_after}")

    items_dict = []
    errors = []
    for raw_metadata_ in raw_metadata:
        try:
            item = stac_item_creator(raw_metadata_).to_dict()
        except Exception as e:
            if handle_exceptions == "RAISE":
                raise
            elif handle_exceptions == "IGNORE":
                errors.append(f"{raw_metadata_}: {e}")
        item["collection"] = collection_id
        items_dict.append(item)

    loader.load_items(
        iter(items_dict),
        insert_mode=Methods.upsert,
    )
    click.echo(f"Completed ingesting {len(items_dict)} STAC Items")

    if errors:
        click.echo(f"Encountered errors with {len(errors)} OAM catalog entries:")
        for error in errors:
            click.echo(error)
