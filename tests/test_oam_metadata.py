"""Tests for `stactools.hotosm.oam_metadata`."""

from stactools.hotosm.oam_metadata import OamMetadata


class TestOamMetadata:
    """Test OamMetadata data class."""

    def test_sanitize(self, example_oam_metadata: OamMetadata):
        """Test sanitize() method resolves identified metadata issues."""
        example_oam_metadata.platform = "UaV"
        example_oam_metadata.license = "CC-BY 4.0"
        example_oam_metadata.sensor = "Unknow"

        example_oam_metadata.sanitize()

        assert example_oam_metadata.platform == "UAV"
        assert example_oam_metadata.license == "CC-BY-4.0"
        assert example_oam_metadata.sensor is None
