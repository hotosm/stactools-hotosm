# Changelog

## [Unreleased]

### Added

-

### Changed

-

### Fixed

-

### Removed

-

## [0.2.0]

### Added

- Allow ignoring exceptions in Item sync CLI ([#16](https://github.com/hotosm/stactools-hotosm/pull/16))
- Synchronize Collections in CLI ([#16](https://github.com/hotosm/stactools-hotosm/pull/16))
- Dump STAC Items to NDJSON in CLI ([#16](https://github.com/hotosm/stactools-hotosm/pull/16))

## [0.1.0]

### Added

- First commit with license and developer setup ([#1](https://github.com/hotosm/stactools-hotosm/pull/1))
- Create STAC Collection and Items from existing catalog ([#2](https://github.com/hotosm/stactools-hotosm/pull/2))
- Add "created" based on "uploaded_at" OAM metadata ([#4](https://github.com/hotosm/stactools-hotosm/pull/4))
- Add functions to create OAM-flavored STAC from Maxar's open data catalog ([#5](https://github.com/hotosm/stactools-hotosm/pull/5))
- Add CLI to perform batch synchronization of STAC against OAM API and Maxar's open data catalog ([#10](https://github.com/hotosm/stactools-hotosm/pull/10))

### Fixed

- Include Collection ID in Items to support ingest via `pypgstac load` ([#3](https://github.com/hotosm/stactools-hotosm/pull/3))
- Ensure acquisition start comes before end. Populate Item datetime or start/end_datetime properly ([#4](https://github.com/hotosm/stactools-hotosm/pull/4))
- Use the same asset key ("visual") for visual assets in OAM and Maxar STAC Catalogs ([#10](https://github.com/hotosm/stactools-hotosm/pull/10))
- Ensure `oam:platform_type` is lower cased ([#12](https://github.com/hotosm/stactools-hotosm/pull/12))
- Ingest dependencies should be defined as an optional dependency, not extra ([#15](https://github.com/hotosm/stactools-hotosm/pull/15))
