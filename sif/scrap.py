from . import *
import asyncio
import time
import random
from TikTokApi import TikTokApi
import instaloader


# --- SCRAPER HELPERS ---

def get_instagram_data(url):
    try:
        url = url.split('?')[0].rstrip('/') + '/'
        url=url.replace("?img_index=1","")
        url=url.replace("/reel/","/p/")
        print(url)
        L = instaloader.Instaloader()
        shortcode = url.strip("/").split("/")[-1]
        post = instaloader.Post.from_shortcode(L.context, shortcode)

        return {
            "platform": "instagram",
            "link": url,
            "likes": post.likes,
            "comments": post.comments,
            "views": getattr(post, "video_view_count", None),
            "shares": 0,
        }
    except Exception as e:
        print(f"[INSTAGRAM ERROR] {url} -> {e}")
        return {"platform": "instagram", "link": url, "likes": "", "comments": "", "views": "", "shares": ""}


async def get_tiktok_data(url, api):
    try:
        video = api.video(url=url)
        video_data = await video.info()
        return {
            "platform": "tiktok",
            "link": url,
            "likes": video_data["stats"].get("diggCount"),
            "comments": video_data["stats"].get("commentCount"),
            "views": video_data["stats"].get("playCount"),
            "shares": video_data["stats"].get("shareCount"),
        }
    except Exception as e:
        print(f"[TIKTOK ERROR] {url} -> {e}")
        return {"platform": "tiktok", "link": url, "likes": "", "comments": "", "views": "", "shares": ""}


# --- MAIN SCRAPER LOGIC ---

async def scrap():
    # 1. Fetch links from DBs
    links = metabase_get_links()
    print("Fetched links:", links)

    # 2. Lock links
    lock_result = metabase_lock_links([link["link"] for link in links])
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
                data = {"platform": "unknown", "link": url, "likes": "", "comments": "", "views": "", "shares": ""}

            results.append(data)

            # Simulate rate limit delay
            await asyncio.sleep(random.uniform(2, 5))

    # 4. Print all collected results
    print("\n=== SCRAPE RESULTS ===")
    for item in results:
        print(item)

    # Update scraped data into DB
    update_result = metabase_update_links(results)
    print("Update result:", update_result)

    # Unlock the processed links
    unlock_result = metabase_unlock_links([link["link"] for link in links])
    print("Unlock result:", unlock_result)

    print("\n✅ Scrape completed successfully.")



if __name__ == "__main__":
    asyncio.run(scrap())
