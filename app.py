import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import time

# --- CONSTANTS ---
EUROPE_CODES = [
    'AD', 'AL', 'AT', 'BA', 'BE', 'BG', 'BY', 'CH', 'CY', 'CZ', 'DE', 'DK', 'EE', 'ES', 'FI', 
    'FO', 'FR', 'GB', 'GG', 'GI', 'GR', 'HR', 'HU', 'IE', 'IM', 'IS', 'IT', 'JE', 'LI', 'LT', 
    'LU', 'LV', 'MC', 'MD', 'ME', 'MK', 'MT', 'NL', 'NO', 'PL', 'PT', 'RO', 'RS', 'RU', 'SE', 
    'SI', 'SK', 'SM', 'UA', 'VA'
]

# --- PAGE CONFIG ---
st.set_page_config(page_title="YouTube Niche Finder", page_icon="🎯", layout="wide")

st.title("🎯 Targeted YouTube Niche Finder")
st.markdown("""
This tool finds channels based on **Niche**, **Location**, and **Subscriber Size**.
*Note: Searching filters consume more quota because we must scan many channels to find matches.*
""")

# --- SIDEBAR CONFIG ---
with st.sidebar:
    st.header("🔑 API Settings")
    api_key = st.text_input("Enter Google API Key", type="password")
    
    st.divider()
    
    st.header("🌍 Location Filters")
    target_locations = st.multiselect(
        "Select Target Locations:",
        options=["United States (US)", "United Kingdom (GB)", "Europe (All)", "Canada (CA)", "Australia (AU)"],
        default=["United States (US)", "United Kingdom (GB)"]
    )
    
    st.header("📊 Size Filters")
    max_subs = st.number_input("Max Subscribers", min_value=100, value=15000, step=1000)
    min_subs = st.number_input("Min Subscribers", min_value=0, value=100, step=100)

# --- FUNCTIONS ---

def get_youtube_service(api_key):
    return build('youtube', 'v3', developerKey=api_key)

def get_country_codes(selection):
    """Converts user selection into a list of 2-letter country codes."""
    codes = []
    if "United States (US)" in selection:
        codes.append("US")
    if "United Kingdom (GB)" in selection:
        codes.append("GB")
    if "Canada (CA)" in selection:
        codes.append("CA")
    if "Australia (AU)" in selection:
        codes.append("AU")
    if "Europe (All)" in selection:
        codes.extend(EUROPE_CODES)
    # Remove duplicates
    return list(set(codes))

def fetch_channel_details(youtube, channel_ids):
    """Fetches details (Subs, Country) for a list of IDs."""
    try:
        request = youtube.channels().list(
            part="snippet,statistics",
            id=','.join(channel_ids)
        )
        response = request.execute()
        return response.get('items', [])
    except HttpError as e:
        st.error(f"API Error during detail fetch: {e}")
        return []

def deep_search(youtube, query, target_count, allowed_countries, max_s, min_s):
    """
    Searches -> Fetches Details -> Filters -> Repeats until target_count is met.
    """
    valid_channels = []
    next_page_token = None
    search_attempts = 0
    max_search_depth = 10  # SAFETY: Stop after searching 10 pages (approx 500 channels scanned)
    
    status_text = st.empty()
    progress_bar = st.progress(0)

    while len(valid_channels) < target_count and search_attempts < max_search_depth:
        search_attempts += 1
        status_text.write(f"🔍 Scanning page {search_attempts}... Found {len(valid_channels)} matches so far.")
        
        # 1. Search for generic channels (Cost: 100 units)
        try:
            search_response = youtube.search().list(
                q=query,
                type='channel',
                part='id',
                maxResults=50,
                pageToken=next_page_token
            ).execute()
        except HttpError as e:
            st.error(f"Search failed: {e}")
            break

        items = search_response.get('items', [])
        if not items:
            break

        # Extract IDs
        channel_ids = [item['id']['channelId'] for item in items]
        
        # 2. Get Details to check Country & Subs (Cost: 1 unit)
        details = fetch_channel_details(youtube, channel_ids)
        
        # 3. Filter Results
        for channel in details:
            try:
                # Get Stats
                subs = int(channel['statistics'].get('subscriberCount', 0))
                video_count = int(channel['statistics'].get('videoCount', 0))
                
                # Get Location (Some channels don't set a country)
                country = channel['snippet'].get('country', 'Unknown')
                
                # --- FILTER LOGIC ---
                is_correct_size = min_s <= subs <= max_s
                is_correct_location = country in allowed_countries
                
                if is_correct_size and is_correct_location:
                    valid_channels.append({
                        'Channel Name': channel['snippet']['title'],
                        'Subscribers': subs,
                        'Country': country,
                        'Video Count': video_count,
                        'Description': channel['snippet']['description'],
                        'Channel URL': f"https://www.youtube.com/channel/{channel['id']}"
                    })
                    
                    # Stop immediately if we have enough
                    if len(valid_channels) >= target_count:
                        break
            
            except Exception:
                continue # Skip channels with missing data

        # Check pagination
        next_page_token = search_response.get('nextPageToken')
        progress_bar.progress(min(len(valid_channels) / target_count, 1.0))
        
        if not next_page_token:
            break
            
        # Modest sleep to avoid rate limits
        time.sleep(0.2)

    status_text.empty()
    progress_bar.empty()
    return valid_channels

# --- MAIN UI ---
col1, col2 = st.columns([3, 1])
with col1:
    query = st.text_input("Niche / Keyword", placeholder="e.g. Streetwear Fashion")
with col2:
    desired_count = st.number_input("Target Results", min_value=1, max_value=50, value=10)

if st.button("Find Channels", type="primary"):
    if not api_key:
        st.error("⚠️ Please enter your API Key in the sidebar.")
    elif not query:
        st.warning("⚠️ Please enter a Niche.")
    else:
        # Build Country List
        allowed_countries = get_country_codes(target_locations)
        
        if not allowed_countries:
            st.error("Please select at least one location.")
        else:
            with st.spinner("Processing... This performs a deep scan, please wait."):
                youtube = get_youtube_service(api_key)
                
                # Run the Deep Search
                results = deep_search(
                    youtube, 
                    query, 
                    desired_count, 
                    allowed_countries, 
                    max_subs, 
                    min_subs
                )
                
                if results:
                    st.success(f"Found {len(results)} channels matching your criteria!")
                    df = pd.DataFrame(results)
                    
                    # Display Data
                    st.dataframe(
                        df, 
                        column_config={
                            "Channel URL": st.column_config.LinkColumn("Link"),
                            "Subscribers": st.column_config.NumberColumn(format="%d")
                        }
                    )
                    
                    # CSV Download
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name=f"{query}_filtered_channels.csv",
                        mime='text/csv',
                    )
                else:
                    st.warning("No channels found matching these strict criteria. Try increasing the Max Subscribers or adding more locations.")
