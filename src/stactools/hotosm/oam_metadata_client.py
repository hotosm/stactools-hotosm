"""Client for the OAM metadata API."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import ClassVar, Iterator

import requests

from stactools.hotosm.oam_metadata import OamMetadata


@dataclass(frozen=True)
class OamMetadataClient:
    """OpenAerialMap metadata API client."""

    DEFAULT_API_ROOT: ClassVar[str] = "https://api.openaerialmap.org/meta"

    session: requests.Session
    api_root: str

    @classmethod
    def new(
        cls, session: requests.Session | None = None, api_root: str = DEFAULT_API_ROOT
    ) -> OamMetadataClient:
        """Create a new OamMetadataClient."""
        return cls(
            session=session or requests.Session(),
            api_root=api_root,
        )

    def _parse_result(self, result: dict) -> OamMetadata:
        """Parse a metadata API result into our data class."""
        return OamMetadata(
            id=result["_id"],
            title=result["title"],
            contact=result["contact"],
            provider=result["provider"],
            platform=result["platform"],
            sensor=result["properties"].get("sensor"),
            license=result["properties"].get("license"),
            acquisition_start=dt.datetime.fromisoformat(result["acquisition_start"]),
            acquisition_end=dt.datetime.fromisoformat(result["acquisition_end"]),
            geojson=result["geojson"],
            bbox=result["bbox"],
            footprint_wkt=result["footprint"],
            projection_wkt=result["projection"],
            gsd=result["gsd"],
            image_url=result["uuid"],
            image_file_size=result["file_size"],
            thumbnail_url=result["properties"]["thumbnail"],
            metadata_url=result["meta_uri"],
        )

    def get_count(self) -> int:
        """Return the total count of items in the catalog."""
        req = self.session.get(
            self.api_root,
            params={
                "limit": 1,
            },
        )
        req.raise_for_status()
        return req.json()["meta"]["found"]

    def get_items(self, limit: int = 100, page_number: int = 1) -> list[OamMetadata]:
        """List OAM metadata items."""
        req = self.session.get(
            self.api_root,
            params={
                "limit": limit,
                "page": page_number,
            },
        )
        req.raise_for_status()

        results = []
        for result in req.json()["results"]:
            results.append(self._parse_result(result))
        return results

    def get_all_items(self, page_size: int = 500) -> Iterator[OamMetadata]:
        """Iterate through all images in the catalog."""
        page = 1
        while True:
            items = self.get_items(limit=page_size, page_number=page)
            if not items:
                break
            page += 1
            yield from items
