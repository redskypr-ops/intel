from pipeline.config import ClientConfig
from pipeline.filter.matcher import filter_items, matches_client, risk_tripped
from pipeline.models import RawItem


def make_config(**overrides) -> ClientConfig:
    defaults = dict(
        client="Test Client",
        contacts=["Karla LaOrange", "District 91"],
        risk_keywords=["vote of no confidence", "resign"],
    )
    defaults.update(overrides)
    return ClientConfig(**defaults)


def make_item(headline="", snippet="", **overrides) -> RawItem:
    defaults = dict(
        client_slug="test",
        source_type="RSS",
        source_channel="https://example.com/feed",
        headline=headline,
        link="https://example.com/a",
        snippet=snippet,
    )
    defaults.update(overrides)
    return RawItem(**defaults)


def test_matches_on_contact_name():
    config = make_config()
    item = make_item(headline="Karla LaOrange faces board scrutiny")
    assert matches_client(item, config)


def test_matches_is_case_insensitive():
    config = make_config()
    item = make_item(headline="district 91 superintendent under fire")
    assert matches_client(item, config)


def test_no_match_when_no_contact_mentioned():
    config = make_config()
    item = make_item(headline="City council approves new budget")
    assert not matches_client(item, config)


def test_match_checks_snippet_too():
    config = make_config()
    item = make_item(headline="Local news roundup", snippet="...Karla LaOrange announced...")
    assert matches_client(item, config)


def test_risk_tripped_on_keyword():
    config = make_config()
    item = make_item(headline="Board schedules vote of no confidence on LaOrange")
    assert risk_tripped(item, config)


def test_risk_not_tripped_without_keyword():
    config = make_config()
    item = make_item(headline="Karla LaOrange attends ribbon cutting")
    assert not risk_tripped(item, config)


def test_filter_items_excludes_non_matching_and_flags_risk():
    config = make_config()
    items = [
        make_item(headline="Karla LaOrange faces vote of no confidence"),
        make_item(headline="Unrelated city council story"),
        make_item(headline="District 91 budget meeting recap"),
    ]
    filtered = filter_items(items, config)
    assert len(filtered) == 2
    assert filtered[0].risk_tripped is True
    assert filtered[1].risk_tripped is False


def test_empty_contacts_matches_nothing():
    config = make_config(contacts=[])
    item = make_item(headline="Anything at all")
    assert not matches_client(item, config)
