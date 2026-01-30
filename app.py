import os
from googleapiclient.discovery import build
import pandas as pd

# --- CONFIGURATION ---
API_KEY = 'YOUR_API_KEY_HERE'  # Replace with your actual API Key
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

def get_youtube_service():
    """Builds and returns the YouTube API service."""
    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)

def search_videos(query, max_results=10):
    """
    Searches for videos by keyword.
    Returns a list of video IDs.
    Note: A search request costs 100 quota units.
    """
    youtube = get_youtube_service()
    
    # Search for videos
    search_response = youtube.search().list(
        q=query,
        type='video',
        part='id',
        maxResults=max_results
    ).execute()

    video_ids = []
    for item in search_response.get('items', []):
        video_ids.append(item['id']['videoId'])
        
    return video_ids

def get_video_details(video_ids):
    """
    Fetches detailed statistics for a list of video IDs.
    Returns a list of dictionaries containing video data.
    Note: A videos.list request costs 1 quota unit.
    """
    youtube = get_youtube_service()
    video_data = []
    
    # The API can handle up to 50 IDs at a time
    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i:i+50]
        
        request = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=','.join(chunk)
        )
        response = request.execute()

        for video in response.get('items', []):
            snippet = video['snippet']
            stats = video['statistics']
            
            data = {
                'Title': snippet['title'],
                'Published At': snippet['publishedAt'],
                'Channel': snippet['channelTitle'],
                'Views': stats.get('viewCount', 0),
                'Likes': stats.get('likeCount', 0),
                'Comment Count': stats.get('commentCount', 0),
                'Video URL': f"https://www.youtube.com/watch?v={video['id']}"
            }
            video_data.append(data)
            
    return video_data

def main():
    keyword = input("Enter a keyword to search for: ")
    count = int(input("How many videos to scrape? (Max 50 for this demo): "))
    
    print(f"Searching for '{keyword}'...")
    try:
        # 1. Get Video IDs
        video_ids = search_videos(keyword, max_results=count)
        
        # 2. Get Video Details
        print(f"Fetching details for {len(video_ids)} videos...")
        details = get_video_details(video_ids)
        
        # 3. Save to CSV
        df = pd.DataFrame(details)
        filename = f"{keyword.replace(' ', '_')}_youtube_data.csv"
        df.to_csv(filename, index=False)
        
        print(f"Success! Data saved to '{filename}'")
        print(df.head())
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
