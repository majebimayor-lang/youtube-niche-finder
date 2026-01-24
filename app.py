import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ==============================
# ADD YOUR API KEY HERE
# ==============================
API_KEY = "PASTE_YOUR_API_KEY_HERE"
# ==============================


def get_youtube_service():
    if not API_KEY or API_KEY == "PASTE_YOUR_API_KEY_HERE":
        raise ValueError("❌ API key is missing. Paste your YouTube API key.")

    return build("youtube", "v3", developerKey=API_KEY)


def search_channels(keyword, max_results=50):
    youtube = get_youtube_service()
    channels = []
    next_page_token = None

    print(f"\n🔍 Searching channels for: '{keyword}'")

    while len(channels) < max_results:
        try:
            request = youtube.search().list(
                q=keyword,
                part="snippet",
                type="channel",
                maxResults=min(50, max_results - len(channels)),
                pageToken=next_page_token,
            )

            response = request.execute()

            for item in response.get("items", []):
                channels.append({
                    "Channel Name": item["snippet"]["channelTitle"],
                    "Channel ID": item["id"]["channelId"],
                    "Description": item["snippet"]["description"],
                    "Published At": item["snippet"]["publishedAt"],
                    "URL": f"https://www.youtube.com/channel/{item['id']['channelId']}"
                })

            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break

        except HttpError as e:
            print("❌ YouTube API Error:")
            print(e)
            break

    return channels


def main():
    print("\nYouTube Channel Scraper")
    print("----------------------")

    keyword = input("Enter keyword (example: marketing): ").strip()
    if not keyword:
        print("❌ Keyword cannot be empty.")
        return

    try:
        limit = int(input("How many channels? (max 500): "))
    except ValueError:
        print("❌ Please enter a valid number.")
        return

    results = search_channels(keyword, limit)

    if not results:
        print("⚠️ No channels found.")
        return

    df = pd.DataFrame(results)
    filename = f"{keyword.replace(' ', '_')}_channels.csv"
    df.to_csv(filename, index=False)

    print(f"\n✅ Success!")
    print(f"Channels found: {len(results)}")
    print(f"Saved file: {filename}")


if __name__ == "__main__":
    main()

