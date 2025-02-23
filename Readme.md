# Telegram MTProto Bot

This bot receives multiple files in private messages, creates password-protected ZIP files, and uploads them back to the user.

## Features:
- Works only in private messages (PM).
- Supports files up to 2 GB.
- Splits files >2 GB into smaller parts.
- Password-protected ZIP files.
- Custom ZIP file names.
- Automatic cleanup of temporary files.

## Deploy on Render

1. Fork this repo.
2. Create a new Web Service on Render.
3. Connect your GitHub repo.
4. Add the following environment variables:
   - `API_ID`: Your Telegram API ID.
   - `API_HASH`: Your Telegram API Hash.
   - `PHONE_NUMBER`: Your phone number (with country code).
5. Deploy!
