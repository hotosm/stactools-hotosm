# Changelog

## Unreleased

### Feat

- First commit with license and developer setup ([#1](https://github.com/hotosm/stactools-hotosm/pull/1))
- Create STAC Collection and Items from existing catalog ([#2](https://github.com/hotosm/stactools-hotosm/pull/2))
- Add "created" based on "uploaded_at" OAM metadata ([#4](https://github.com/hotosm/stactools-hotosm/pull/4))
- Add functions to create OAM-flavored STAC from Maxar's open data catalog ([#5](https://github.com/hotosm/stactools-hotosm/pull/5))

### Fixed

- Include Collection ID in Items to support ingest via `pypgstac load` ([#3](https://github.com/hotosm/stactools-hotosm/pull/3))
- Ensure acquisition start comes before end. Populate Item datetime or start/end_datetime properly ([#4](https://github.com/hotosm/stactools-hotosm/pull/4))
