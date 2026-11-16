import asyncio
import csv
from datetime import datetime, timezone
from types import SimpleNamespace
from export_messages import fetch_rows, write_csv


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
