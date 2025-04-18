"""Tests for `stactools.hotosm.oam_metadata_client`."""

import logging
from math import ceil

import pytest
import requests
import responses
from responses.matchers import query_param_matcher

from stactools.hotosm.oam_metadata_client import OamMetadataClient


class TestOamMetadataClient:
    """Tests for OamMetadataClient."""

    def test_new(self):
        """Test new() classmethod."""
        client = OamMetadataClient.new()
        assert isinstance(client, OamMetadataClient)

        session = requests.Session()
        client = OamMetadataClient.new(session=session, api_root="test")
        assert client.session is session
        assert client.api_root == "test"

    @pytest.fixture
    def test_client(self) -> OamMetadataClient:
        """Test client."""
        return OamMetadataClient.new(api_root="http://test.test/test")

    @responses.activate
    def test_get_count(
        self, test_client: OamMetadataClient, example_oam_meta_api_response: dict
    ):
        """Test get_count() method."""
        resp = responses.get(
            url=test_client.api_root,
            json=example_oam_meta_api_response,
        )

        count = test_client.get_count()
        assert count == 17737
        assert resp.call_count == 1

    @responses.activate
    def test_get_items(
        self, test_client: OamMetadataClient, example_oam_meta_api_response: dict
    ):
        """Test get_items() method."""
        resp = responses.get(
            url=test_client.api_root,
            json=example_oam_meta_api_response,
        )

        items = test_client.get_items(raise_on_error=False)
        assert len(items) == 10
        assert resp.call_count == 1

    @responses.activate
    def test_get_items_raises_error(
        self,
        test_client: OamMetadataClient,
        example_oam_meta_api_response: dict,
        caplog,
    ):
        """Test get_items() method raises if metadata cannot be parsed."""
        # Some metadata entries have no acquisition start/end provided
        bad_id = example_oam_meta_api_response["results"][0]["_id"]
        example_oam_meta_api_response["results"][0]["acquisition_start"] = None

        resp = responses.get(
            url=test_client.api_root,
            json=example_oam_meta_api_response,
        )

        with pytest.raises(TypeError, match=r"fromisoformat: argument must be str"):
            test_client.get_items(raise_on_error=True)
        assert resp.call_count == 1
        assert len(caplog.record_tuples) == 1
        assert caplog.record_tuples[0][1] == logging.ERROR
        assert caplog.record_tuples[0][2] == f"Could not parse id={bad_id}"

    @responses.activate
    @pytest.mark.parametrize("n_per_page", [2, 3, 10])
    def test_get_all_items(
        self,
        n_per_page: int,
        test_client: OamMetadataClient,
        example_oam_meta_api_response: dict,
    ):
        """Test get_all_items() method works with different page count sizes."""
        resps = []
        pages = ceil(10 / n_per_page)
        for page in range(pages + 1):
            start = n_per_page * page
            end = n_per_page * (page + 1)
            data = {
                "meta": example_oam_meta_api_response["meta"],
                "results": example_oam_meta_api_response["results"][start:end],
            }
            resps.append(
                responses.get(
                    url=test_client.api_root,
                    json=data,
                    match=[query_param_matcher({"page": page + 1}, strict_match=False)],
                )
            )

        items = list(test_client.get_all_items(page_size=n_per_page))
        assert len(items) == 10
        for resp in resps:
            assert resp.call_count == 1
