"""Test isolation, applied before any test module (and so any project module) is imported.

- Dummy configuration instead of real credentials; .env files are never loaded.
- Outbound network connections are blocked, including during collection.
  Loopback stays allowed: asyncio on Windows uses a local socket pair for its event loop.
- Each test runs in its own temporary folder, so relative paths (the Telegram
  "session" file, jobs_messages.csv) never touch the repo.
- The default profile path points to a missing temporary file, never the real profile.txt.
"""
import os
import socket

import dotenv
import pytest

# --- Dummy configuration (overrides anything set in the shell) -------------------------
os.environ["TELEGRAM_API_ID"] = "0"
os.environ["TELEGRAM_API_HASH"] = "dummy-hash-for-tests"
os.environ["OPENAI_API_KEY"] = "dummy-key-for-tests"

# config.py does `from dotenv import load_dotenv`, so patching the module attribute here
# (before config is imported) makes config's call a no-op as well
dotenv.load_dotenv = lambda *args, **kwargs: False

# --- Network guard ---------------------------------------------------------------------
_LOOPBACK = {"127.0.0.1", "::1", "localhost"}
_real_connect = socket.socket.connect
_real_connect_ex = socket.socket.connect_ex
_real_getaddrinfo = socket.getaddrinfo


def _check_host(host):
    if host not in _LOOPBACK:
        raise RuntimeError(f"Network access blocked in tests (host: {host})")


def _guarded_connect(self, address):
    if isinstance(address, tuple):
        _check_host(address[0])
    return _real_connect(self, address)


def _guarded_connect_ex(self, address):
    if isinstance(address, tuple):
        _check_host(address[0])
    return _real_connect_ex(self, address)


def _guarded_getaddrinfo(host, *args, **kwargs):
    if host is not None:
        _check_host(host.decode() if isinstance(host, bytes) else str(host))
    return _real_getaddrinfo(host, *args, **kwargs)


_guarded_connect.network_guard = True
socket.socket.connect = _guarded_connect
socket.socket.connect_ex = _guarded_connect_ex
socket.getaddrinfo = _guarded_getaddrinfo


# --- Per-test filesystem isolation -------------------------------------------------------
@pytest.fixture(autouse=True)
def _isolate_filesystem(tmp_path, monkeypatch):
    work_dir = tmp_path / "cwd"
    work_dir.mkdir()
    monkeypatch.chdir(work_dir)

    import llm_classifier
    missing_profile = tmp_path / "no-real-profile" / "profile.txt"
    monkeypatch.setattr(llm_classifier, "PROFILE_PATH", missing_profile)
    # load_profile's default argument was bound at definition time; redirect it too
    monkeypatch.setattr(llm_classifier.load_profile, "__defaults__", (missing_profile,))
