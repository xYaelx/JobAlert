# Job monitor, round 2 fixes — plan

Follow-up fixes for the Telegram CV/ML job-post monitor.
All new code is test-first (test → watch it fail → implement). One commit per task.

1. `.gitignore`: GPT_key.txt, .env, *.session(-journal), profile.txt, jobs_messages.csv, local data files.
2. Rename tests to `test_*.py`; configure pytest to import project modules from the repo root.
3. `normalize_text`: replace non-word characters with a space instead of deleting them; simplify the job regex to plain phrases.
4. Move job keywords to `config.JOB_KEYWORDS`; build the regex from the list.
5. `notifier.py`: alert text shows label, channel, and posting date/time.
6. Read the candidate profile at runtime from gitignored `profile.txt`; ship `profile.example.txt`.
7. Resolve the private "Secret Data Jobs - Juniors" channel ID via `get_dialogs` and add it to config.
8. Export script: last ~100 messages per configured channel → `jobs_messages.csv` (channel, date, text, label).
