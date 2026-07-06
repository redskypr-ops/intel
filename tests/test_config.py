from pathlib import Path

from pipeline.config import load_client_config, load_client_configs

CLIENTS_DIR = Path(__file__).resolve().parent.parent / "config" / "clients"


def test_loads_ifsd91_config():
    config = load_client_config("ifsd91", CLIENTS_DIR)
    assert config.client == "Idaho Falls School District 91"
    assert config.slack_channel_id == "C0BFDPWBUTE"
    assert "Karla LaOrange" in config.contacts
    assert "vote of no confidence" in config.risk_keywords
    assert config.slug == "ifsd91"


def test_match_terms_combines_contacts_and_reddit_keywords():
    config = load_client_config("ifsd91", CLIENTS_DIR)
    assert set(config.contacts).issubset(set(config.match_terms))
    assert set(config.reddit_keywords).issubset(set(config.match_terms))


def test_load_all_client_configs_finds_ifsd91():
    configs = load_client_configs(CLIENTS_DIR)
    slugs = [c.slug for c in configs]
    assert "ifsd91" in slugs
