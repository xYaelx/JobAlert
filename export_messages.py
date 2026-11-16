import asyncio
import csv
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


async def main() -> None:
    async with TelegramClient("session", API_ID, API_HASH) as client:
        rows = await fetch_rows(client, TARGET_CHANNELS)
    write_csv(rows, OUTPUT_PATH)
    print(f"Wrote {len(rows)} messages to {OUTPUT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
