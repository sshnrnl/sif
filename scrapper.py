from sif import *
import asyncio
import time 
import random
from datetime import datetime, timezone
from TikTokApi import TikTokApi
import instaloader
from time import sleep


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
    async with TikTokApi() as api:
        await api.create_sessions(num_sessions=1, sleep_after=3)

        for row in links:
            url = row["link"]

            if "instagram.com" in url:
                data = get_instagram_data(url)
            elif "tiktok.com" in url:
                data = await get_tiktok_data(url, api)
            else:
                print(f"[SKIP] Unknown platform: {url}")
                data = {"platform": "unknown", "link": url, "likes": "", "comments": "", "views": "", "shares": "", "posted_date": ""}

            results.append(data)

            # Simulate rate limit delay
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
