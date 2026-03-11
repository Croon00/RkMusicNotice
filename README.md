# RkMusicNotice

RK Music BOOTH item monitor with Discord notifications.

## Behavior

- First run: sends `NEW` alerts only for items currently purchasable.
- Later runs:
  - `NEW` when a new item appears.
  - `D-1` once when sale end is within 24 hours (if end date can be parsed).
  - `SOLD OUT` when an item changes to sold-out.
  - `END` when an item changes to end-of-sale.

State is saved in `state_seen_urls.json`.

## Local run

1. Install dependencies:
   - `pip install -r requirements.txt`
2. Set env vars:
   - `DEFAULT_DISCORD_WEBHOOK_URL`
   - optional `DISCORD_WEBHOOK_URLS` (JSON object string)
3. Run:
   - `python app.py`

## GitHub Actions (every 20 minutes)

Workflow file: `.github/workflows/rkmusic-notice.yml`

Required repo secrets:
- `DEFAULT_DISCORD_WEBHOOK_URL`
- optional `DISCORD_WEBHOOK_URLS` (JSON object string)

The workflow restores and saves `state_seen_urls.json` via GitHub Actions cache so state is kept across scheduled runs.
