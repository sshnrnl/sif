# Patch Notes

## Summary

Added `posted_date` support across the scraper, database update flow, and API response.

## Files Changed

### `scrapper.py`

- Added `format_posted_date()` to normalize post publish times into MySQL-friendly `YYYY-MM-DD HH:MM:SS`.
- Instagram scraper now returns:
  - `posted_date` from `post.date_utc` or `post.date`
- TikTok scraper now returns:
  - `posted_date` from `createTime`
- Unknown/error fallback payloads now also include `posted_date`.

### `sif/__init__.py`

- Added `posted_date DATETIME NULL` to `links` table definitions.
- Updated `vanilla_update_links()` to write `posted_date`.
- Updated `metabase_update_links()` to write `posted_date`.

### `main.py`

- Updated `/get/post-links` response to include `posted_date`.

## SQL

Run once on existing databases:

```sql
ALTER TABLE links
ADD COLUMN posted_date DATETIME NULL AFTER shares;
```

## API Response

`POST /get/post-links`

Now returns:

```json
{
  "https://example.com/post": {
    "likes": 123,
    "comments": 4,
    "views": 567,
    "shares": 8,
    "posted_date": "2026-01-20 11:00:37",
    "updated_at": "2026-04-13 12:00:00"
  }
}
```

## Verification

- `python -m py_compile scrapper.py sif/__init__.py main.py`
- Live Instagram test returned a readable `posted_date`
- Live TikTok test returned a readable `posted_date`
