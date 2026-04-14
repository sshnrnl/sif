from sif import *
import asyncio
import time
import random
import re
import html
from datetime import datetime, timezone
from TikTokApi import TikTokApi
import instaloader
from time import sleep
from yt_dlp import YoutubeDL
import requests


# --- SCRAPER HELPERS ---

def format_posted_date(value):
    if not value:
        return None

    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.strftime("%Y-%m-%d %H:%M:%S")
        return value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    if isinstance(value, str):
        stripped = value.strip()
        if stripped.isdigit():
            return datetime.fromtimestamp(int(stripped), tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        return stripped

    return str(value)


def format_yt_dlp_date(info):
    timestamp = info.get("timestamp") or info.get("release_timestamp")
    if timestamp:
        return format_posted_date(timestamp)

    upload_date = info.get("upload_date")
    if isinstance(upload_date, str) and len(upload_date) == 8 and upload_date.isdigit():
        return datetime.strptime(upload_date, "%Y%m%d").strftime("%Y-%m-%d 00:00:00")

    return format_posted_date(upload_date)


def parse_compact_number(value):
    if value is None:
        return None

    normalized = str(value).strip().upper().replace(",", "")
    multiplier = 1

    if normalized.endswith("K"):
        multiplier = 1_000
        normalized = normalized[:-1]
    elif normalized.endswith("M"):
        multiplier = 1_000_000
        normalized = normalized[:-1]
    elif normalized.endswith("B"):
        multiplier = 1_000_000_000
        normalized = normalized[:-1]

    try:
        return int(float(normalized) * multiplier)
    except ValueError:
        return None


def get_facebook_fallback_data(url):
    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept-Language": "en-US,en;q=0.9",
            },
            timeout=20,
        )
        response.raise_for_status()

        match = re.search(r'<meta property="og:title" content="([^"]+)"', response.text)
        if not match:
            return {}

        og_title = html.unescape(match.group(1))
        counts_match = re.search(
            r'(?P<views>[\d.]+[KMB]?)\s+views\s+[·|]\s+(?P<reactions>[\d.]+[KMB]?)\s+reactions?',
            og_title,
            re.IGNORECASE,
        )
        if not counts_match:
            return {}

        return {
            "likes": parse_compact_number(counts_match.group("reactions")),
            "views": parse_compact_number(counts_match.group("views")),
        }
    except Exception as e:
        print(f"[FACEBOOK FALLBACK ERROR] {url} -> {e}")
        return {}

def get_instagram_data(url):
    try:
        main_url = url
        url = url.split('?')[0].rstrip('/') + '/'
        url=url.replace("?img_index=1","")
        url=url.replace("/reel/","/p/")
        L = instaloader.Instaloader()
        shortcode = url.strip("/").split("/")[-1]
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        print("scrapping ",main_url)
        return {
            "platform": "instagram",
            "link": main_url,
            "likes": post.likes,
            "comments": post.comments,
            "views": getattr(post, "video_view_count", None),
            "shares": 0,
            "posted_date": format_posted_date(getattr(post, "date_utc", None) or getattr(post, "date", None)),
        }
    except Exception as e:
        print(f"[INSTAGRAM ERROR] {url} -> {e}")
        return {"platform": "instagram", "link": url, "likes": "", "comments": "", "views": "", "shares": "", "posted_date": ""}


async def get_tiktok_data(url, api):
    try:
        video = api.video(url=url)
        video_data = await video.info()
        posted_date = (
            video_data.get("createTime")
            or video_data.get("itemInfo", {}).get("itemStruct", {}).get("createTime")
        )
        return {
            "platform": "tiktok",
            "link": url,
            "likes": video_data["stats"].get("diggCount"),
            "comments": video_data["stats"].get("commentCount"),
            "views": video_data["stats"].get("playCount"),
            "shares": video_data["stats"].get("shareCount"),
            "posted_date": format_posted_date(posted_date),
        }
    except Exception as e:
        print(f"[TIKTOK ERROR] {url} -> {e}")
        return {"platform": "tiktok", "link": url, "likes": "", "comments": "", "views": "", "shares": "", "posted_date": ""}


def get_yt_dlp_data(url, platform):
    try:
        options = {
            "quiet": True,
            "skip_download": True,
            "no_warnings": True,
            "extract_flat": False,
        }
        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)

        data = {
            "platform": platform,
            "link": url,
            "likes": info.get("like_count"),
            "comments": info.get("comment_count"),
            "views": info.get("view_count"),
            "shares": info.get("repost_count") or info.get("share_count") or 0,
            "posted_date": format_yt_dlp_date(info),
        }
        if platform == "facebook" and (data["likes"] is None or data["views"] is None):
            fallback = get_facebook_fallback_data(url)
            for key, value in fallback.items():
                if data.get(key) is None:
                    data[key] = value

        return data
    except Exception as e:
        print(f"[{platform.upper()} ERROR] {url} -> {e}")
        return {"platform": platform, "link": url, "likes": "", "comments": "", "views": "", "shares": "", "posted_date": ""}


def scrape_url(url, tiktok_api=None):
    if "instagram.com" in url:
        return get_instagram_data(url)
    if "tiktok.com" in url:
        if tiktok_api is None:
            raise RuntimeError("TikTok API session is required for TikTok links")
        return get_tiktok_data(url, tiktok_api)
    if "youtube.com" in url or "youtu.be" in url:
        return get_yt_dlp_data(url, "youtube")
    if "facebook.com" in url or "fb.watch" in url:
        return get_yt_dlp_data(url, "facebook")

    print(f"[SKIP] Unknown platform: {url}")
    return {"platform": "unknown", "link": url, "likes": "", "comments": "", "views": "", "shares": "", "posted_date": ""}


# --- MAIN SCRAPER LOGIC ---

async def main():
    # 1. Fetch links from DBs
    links = vanilla_get_links()
    print("Fetched links:", links)

    # 2. Lock links
    lock_result = vanilla_lock_links([link["link"] for link in links])
    print("Locked:", lock_result)

    if not links:
        print("No links to scrape.")
        return

    # 3. Start scraping
    results = []
    has_tiktok_links = any("tiktok.com" in row["link"] for row in links)

    if has_tiktok_links:
        async with TikTokApi() as api:
            await api.create_sessions(num_sessions=1, sleep_after=3)

            for row in links:
                url = row["link"]
                data = scrape_url(url, api)
                if asyncio.iscoroutine(data):
                    data = await data
                results.append(data)
                await asyncio.sleep(random.uniform(2, 5))
    else:
        for row in links:
            url = row["link"]
            data = scrape_url(url)
            results.append(data)
            await asyncio.sleep(random.uniform(2, 5))

    # 4. Print all collected results
    print("\n=== SCRAPE RESULTS ===")
    for item in results:
        print(item)

    # Update scraped data into DB
    update_result = vanilla_update_links(results)
    print("Update result:", update_result)

    # Unlock the processed links
    unlock_result = vanilla_unlock_links([link["link"] for link in links])
    print("Unlock result:", unlock_result)

    print("\n✅ Scrape completed successfully.")



if __name__ == "__main__":
    while 1:
        asyncio.run(main())
        sleep(60)
