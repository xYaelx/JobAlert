import os
import socket
from pathlib import Path

import pytest

# Captured at import, i.e. during collection, before any test runs
GUARD_ACTIVE_DURING_COLLECTION = getattr(socket.socket.connect, "network_guard", False)

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_network_guard_active_during_collection():
    assert GUARD_ACTIVE_DURING_COLLECTION


def test_outbound_connections_are_blocked():
    # Check the guard is installed first, so a missing guard never attempts a real connection
    assert getattr(socket.socket.connect, "network_guard", False), "network guard not installed"
    with pytest.raises(RuntimeError, match="blocked"):
        socket.create_connection(("192.0.2.1", 9), timeout=0.01)  # RFC 5737 documentation address
    with pytest.raises(RuntimeError, match="blocked"):
        socket.getaddrinfo("api.telegram.org", 443)


def test_config_uses_dummy_settings():
    import config
    assert config.API_ID == 0
    assert config.API_HASH == "dummy-hash-for-tests"
    assert config.GPT_API_KEY == "dummy-key-for-tests"


def test_dotenv_files_are_not_loaded(tmp_path, monkeypatch):
    import dotenv
    monkeypatch.delenv("MEDALERT_ISOLATION_SENTINEL", raising=False)  # restored after the test
    env_file = tmp_path / ".env"
    env_file.write_text("MEDALERT_ISOLATION_SENTINEL=loaded\n", encoding="utf-8")
    dotenv.load_dotenv(env_file)
    # Compare only the sentinel, so a failure never prints the environment
    assert os.getenv("MEDALERT_ISOLATION_SENTINEL") is None


def test_default_profile_path_is_redirected_away_from_repo():
    from llm_classifier import load_profile
    with pytest.raises(FileNotFoundError) as excinfo:
        load_profile()
    assert str(REPO_ROOT / "profile.txt") not in str(excinfo.value)


def test_tests_run_outside_the_repo_folder():
    # Relative paths such as the "session" file or jobs_messages.csv must not land in the repo
    assert Path.cwd().resolve() != REPO_ROOT
