import pandas as pd
from googleapiclient.discovery import build

# --- CONFIGURATION ---
API_KEY = 'YOUR_API_KEY_HERE'  # Replace with your actual key
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

def get_youtube_service():
    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)

def search_channels(query, max_results=50):
    youtube = get_youtube_service()
    channels_data = []
    next_page_token = None
    
    print(f"Searching for channels related to '{query}'...")

    while len(channels_data) < max_results:
        # Calculate how many items to fetch this time (max 50)
        remaining = max_results - len(channels_data)
        fetch_count = min(remaining, 50)

        try:
            # SEARCH REQUEST - Note type='channel'
            request = youtube.search().list(
                q=query,
                type='channel',            # <--- THIS IS THE KEY CHANGE
                part='snippet',            # 'snippet' contains the channel name
                maxResults=fetch_count,
                pageToken=next_page_token
            )
            response = request.execute()

            for item in response.get('items', []):
                snippet = item['snippet']
                data = {
                    'Channel Name': snippet['channelTitle'],
                    'Channel ID': item['id']['channelId'],
                    'Description': snippet['description'],
                    'Published At': snippet['publishedAt'],
                    'Channel URL': f"https://www.youtube.com/channel/{item['id']['channelId']}"
                }
                channels_data.append(data)

            # Check for next page
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                print("No more pages available.")
                break
                
        except Exception as e:
            print(f"An error occurred: {e}")
            break

    return channels_data

def main():
    keyword = input("Enter keyword (e.g., 'Tech Reviews'): ")
    limit = int(input("How many channels to scrape? "))
    
    data = search_channels(keyword, limit)
    
    if data:
        df = pd.DataFrame(data)
        filename = f"{keyword.replace(' ', '_')}_channels.csv"
        df.to_csv(filename, index=False)
        print(f"\nSaved {len(data)} channels to '{filename}'")
        print(df[['Channel Name', 'Channel ID']].head())
    else:
        print("No channels found.")

if __name__ == "__main__":
    main()
