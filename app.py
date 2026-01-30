import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- PAGE SETUP ---
st.set_page_config(page_title="YouTube Scraper", page_icon="📹")
st.title("📹 YouTube Video Scraper")

# --- SIDEBAR: API KEY INPUT ---
# This is safer than putting the key in the code directly
api_key = st.sidebar.text_input("Enter Google API Key", type="password")

def get_youtube_service(api_key):
    return build('youtube', 'v3', developerKey=api_key)

def search_videos(query, max_results, api_key):
    youtube = get_youtube_service(api_key)
    video_ids = []
    
    try:
        search_response = youtube.search().list(
            q=query,
            type='video',
            part='id',
            maxResults=max_results
        ).execute()

        for item in search_response.get('items', []):
            video_ids.append(item['id']['videoId'])
    except HttpError as e:
        st.error(f"API Error: {e}")
        return []
        
    return video_ids

def get_video_details(video_ids, api_key):
    youtube = get_youtube_service(api_key)
    video_data = []
    
    # Process in chunks of 50
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

# --- MAIN APP UI ---
keyword = st.text_input("Search Keyword", placeholder="e.g. Python Tutorial")
count = st.number_input("Max Videos to Scrape", min_value=1, max_value=50, value=10)
start_scrape = st.button("Start Scraping")

if start_scrape:
    if not api_key:
        st.error("Please enter your API Key in the sidebar first!")
    elif not keyword:
        st.warning("Please enter a keyword.")
    else:
        with st.spinner(f"Searching for '{keyword}'..."):
            # 1. Get IDs
            ids = search_videos(keyword, count, api_key)
            
            if ids:
                # 2. Get Details
                st.write(f"Found {len(ids)} videos. Fetching details...")
                details = get_video_details(ids, api_key)
                
                # 3. Show Data
                df = pd.DataFrame(details)
                st.success("Scraping Complete!")
                st.dataframe(df)
                
                # 4. Download Button
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Data as CSV",
                    data=csv,
                    file_name=f"{keyword.replace(' ', '_')}_youtube_data.csv",
                    mime='text/csv',
                )
            else:
                st.warning("No videos found.")
