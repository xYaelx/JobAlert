import argparse
import asyncio
import csv
import os
from telethon import TelegramClient
from config import TARGET_CHANNELS, API_ID, API_HASH

OUTPUT_PATH = "jobs_messages.csv"
FIELDNAMES = ["channel", "date", "text", "label"]


async def fetch_rows(client, channels: dict, limit: int = 100) -> list[dict]:
    """Fetch the latest messages from each channel as CSV rows.

    Args:
        client: Connected TelegramClient (anything with async iter_messages).
        channels: {channel_id_or_username: friendly_name}, as in config.TARGET_CHANNELS.
        limit: Number of most recent messages to read per channel.

    Returns:
        One row per text message, with an empty 'label' to fill in by hand.
        Dates are UTC.
    """
    rows = []
    for channel, name in channels.items():
        async for msg in client.iter_messages(channel, limit=limit):
            if not msg.text:
                continue
            rows.append({
                "channel": name,
                "date": msg.date.strftime("%Y-%m-%d %H:%M"),
                "text": msg.text,
                "label": "",
            })
    return rows


def write_csv(rows: list[dict], path: str) -> None:
    """Write rows to CSV. utf-8-sig so Excel shows Hebrew correctly."""
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def make_client() -> TelegramClient:
    return TelegramClient("session", API_ID, API_HASH)


async def main(argv: list[str] | None = None, output_path=OUTPUT_PATH, client_factory=make_client) -> None:
    parser = argparse.ArgumentParser(description="Export recent channel messages for manual labeling.")
    parser.add_argument("--force", action="store_true", help=f"overwrite an existing {OUTPUT_PATH}")
    args = parser.parse_args(argv)

    # An existing export may hold hand-written labels: refuse before contacting Telegram
    if os.path.exists(output_path) and not args.force:
        raise SystemExit(
            f"{output_path} already exists and may contain your labels. "
            "Move or rename it first, or rerun with --force to overwrite it."
        )

    async with client_factory() as client:
        rows = await fetch_rows(client, TARGET_CHANNELS)
    # Written only after a successful fetch, so a failed fetch leaves the existing file untouched
    write_csv(rows, output_path)
    print(f"Wrote {len(rows)} messages to {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
