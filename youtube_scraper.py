from googleapiclient.discovery import build
import pandas as pd

API_KEY = "AIzaSyChxQvJmHZzqlMYP-FNLT-ZhG3eja1hOHQ"

youtube = build("youtube", "v3", developerKey=API_KEY)

def search_channels(keyword, max_results=25):
    request = youtube.search().list(
        q=keyword,
        part="snippet",
        type="channel",
        maxResults=max_results
    )
    response = request.execute()

    return [item["snippet"]["channelId"] for item in response["items"]]

def get_channel_stats(channel_ids):
    request = youtube.channels().list(
        part="snippet,statistics",
        id=",".join(channel_ids)
    )
    response = request.execute()

    channels = []
    for item in response["items"]:
        channels.append({
            "Channel Name": item["snippet"]["title"],
            "Subscribers": item["statistics"].get("subscriberCount", 0),
            "Total Views": item["statistics"].get("viewCount", 0),
            "Video Count": item["statistics"].get("videoCount", 0),
            "Description": item["snippet"]["description"]
        })

    return channels

def run():
    niche = input("\nEnter industry / niche keyword: ").strip()

    print(f"\nSearching YouTube for: {niche}")
    channel_ids = search_channels(niche)
    data = get_channel_stats(channel_ids)

    df = pd.DataFrame(data)
    filename = f"{niche.replace(' ', '_')}_channels.csv"
    df.to_csv(filename, index=False)

    print(f"\nSUCCESS: Data saved to {filename}")
    print(df.head())

if __name__ == "__main__":
    run()
