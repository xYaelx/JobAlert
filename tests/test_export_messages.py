import asyncio
import csv
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from export_messages import fetch_rows, write_csv, main


class FakeClient:
    """Stands in for TelegramClient.iter_messages."""

    def __init__(self, messages_by_channel):
        self.messages_by_channel = messages_by_channel
        self.limits = {}

    async def iter_messages(self, entity, limit):
        self.limits[entity] = limit
        for msg in self.messages_by_channel[entity][:limit]:
            yield msg


def make_msg(text, hour):
    return SimpleNamespace(text=text, date=datetime(2026, 11, 16, hour, 2, tzinfo=timezone.utc))


def test_fetch_rows_collects_text_messages_from_each_channel():
    client = FakeClient({
        "@jobs_a": [make_msg("CV engineer wanted", 13), make_msg(None, 12)],
        -100123: [make_msg("דרוש אלגוריתמיקאי", 9)],
    })
    channels = {"@jobs_a": "Jobs A", -100123: "Private Jobs"}

    rows = asyncio.run(fetch_rows(client, channels, limit=100))

    assert rows == [
        {"channel": "Jobs A", "date": "2026-11-16 13:02", "text": "CV engineer wanted", "label": ""},
        {"channel": "Private Jobs", "date": "2026-11-16 09:02", "text": "דרוש אלגוריתמיקאי", "label": ""},
    ]
    assert client.limits == {"@jobs_a": 100, -100123: 100}


def test_write_csv_has_expected_columns_and_keeps_hebrew_and_newlines(tmp_path):
    path = tmp_path / "jobs_messages.csv"
    rows = [{"channel": "Jobs A", "date": "2026-11-16 13:02", "text": "שורה 1\nline 2, with comma", "label": ""}]

    write_csv(rows, path)

    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == ["channel", "date", "text", "label"]
        assert list(reader) == rows


class FakeSessionClient:
    """Stands in for a connected TelegramClient used as `async with` in main()."""

    def __init__(self, fail=False):
        self.fail = fail
        self.fetched = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return False

    async def iter_messages(self, entity, limit):
        self.fetched.append(entity)
        if self.fail:
            raise ConnectionError("synthetic fetch failure")
        yield make_msg(f"synthetic post from {entity}", 10)


# Synthetic stand-in for a labeled export
EXISTING_EXPORT = "channel,date,text,label\r\nSynthetic,2026-01-01 00:00,synthetic post,relevant\r\n".encode("utf-8-sig")


def read_rows(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def test_main_refuses_to_overwrite_existing_output(tmp_path):
    output = tmp_path / "jobs_messages.csv"
    output.write_bytes(EXISTING_EXPORT)
    created = []

    def client_factory():
        created.append(True)
        return FakeSessionClient()

    with pytest.raises(SystemExit) as excinfo:
        asyncio.run(main([], output_path=output, client_factory=client_factory))

    message = str(excinfo.value.code)
    assert "already exists" in message and "--force" in message
    assert output.read_bytes() == EXISTING_EXPORT
    assert created == []  # Telegram is never contacted


def test_main_force_replaces_existing_output(tmp_path):
    output = tmp_path / "jobs_messages.csv"
    output.write_bytes(EXISTING_EXPORT)
    client = FakeSessionClient()

    asyncio.run(main(["--force"], output_path=output, client_factory=lambda: client))

    rows = read_rows(output)
    assert client.fetched and len(rows) == len(client.fetched)
    assert all(row["label"] == "" for row in rows)


def test_main_writes_output_when_none_exists(tmp_path):
    output = tmp_path / "jobs_messages.csv"
    client = FakeSessionClient()

    asyncio.run(main([], output_path=output, client_factory=lambda: client))

    assert len(read_rows(output)) == len(client.fetched) > 0


def test_failed_fetch_keeps_existing_output_even_with_force(tmp_path):
    output = tmp_path / "jobs_messages.csv"
    output.write_bytes(EXISTING_EXPORT)

    with pytest.raises(ConnectionError):
        asyncio.run(main(["--force"], output_path=output, client_factory=lambda: FakeSessionClient(fail=True)))

    assert output.read_bytes() == EXISTING_EXPORT
