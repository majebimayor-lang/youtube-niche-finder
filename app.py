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

# --- CUSTOM CSS FOR LINKS & TABLE ---
st.markdown("""
<style>
/* Link Styles */
a:link { color: #2980b9; text-decoration: none; font-weight: bold; }
a:visited { color: #8e44ad !important; } /* PURPLE FOR VISITED */
a:hover { color: #c0392b; text-decoration: underline; }

/* Table Styles to make it look like a Dataframe */
table {
    width: 100%;
    border-collapse: collapse;
    font-family: sans-serif;
    font-size: 14px;
}
th {
    background-color: #f0f2f6;
    color: #31333F;
    font-weight: bold;
    text-align: left;
    padding: 10px;
    border-bottom: 1px solid #ddd;
}
td {
    padding: 10px;
    border-bottom: 1px solid #eee;
    color: #31333F;
}
tr:hover { background-color: #f9f9f9; }
</style>
""", unsafe_allow_html=True)

st.title("🎯 Targeted YouTube Niche Finder")

# --- SIDEBAR CONFIG ---
with st.sidebar:
    st.header("🔑 API Settings")
    api_key = st.text_input("Enter Google API Key", type="password")
    
    st.divider()
    
    st.header("🌍 Location Filters")
    include_unknown = st.checkbox("Include 'Unknown' Locations?", value=True, help="Many channels do not set a country. Check this to include them.")
    target_locations = st.multiselect(
        "Select Target Locations:",
        options=["United States (US)", "United Kingdom (GB)", "Europe (All)", "Canada (CA)", "Australia (AU)"],
        default=["United States (US)", "United Kingdom (GB)"]
    )
    
    st.header("📊 Size Filters")
    max_subs = st.number_input("Max Subscribers", min_value=100, value=50000, step=1000)
    min_subs = st.number_input("Min Subscribers", min_value=0, value=100, step=100)
    
    st.divider()
    debug_mode = st.checkbox("Show Debug Logs", value=True, help="See why channels are being rejected.")

# --- FUNCTIONS ---

def get_youtube_service(api_key):
    return build('youtube', 'v3', developerKey=api_key)

def get_country_codes(selection):
    codes = []
    if "United States (US)" in selection: codes.append("US")
    if "United Kingdom (GB)" in selection: codes.append("GB")
    if "Canada (CA)" in selection: codes.append("CA")
    if "Australia (AU)" in selection: codes.append("AU")
    if "Europe (All)" in selection: codes.extend(EUROPE_CODES)
    return list(set(codes))

def fetch_channel_details(youtube, channel_ids):
    try:
        request = youtube.channels().list(
            part="snippet,statistics",
            id=','.join(channel_ids)
        )
        response = request.execute()
        return response.get('items', [])
    except HttpError as e:
        st.error(f"API Error: {e}")
        return []

def deep_search(youtube, query, target_count, allowed_countries, max_s, min_s, include_unknown, debug):
    valid_channels = []
    next_page_token = None
    search_attempts = 0
    max_search_depth = 15
    
    status_text = st.empty()
    debug_area = st.container() if debug else None
    progress_bar = st.progress(0)

    while len(valid_channels) < target_count and search_attempts < max_search_depth:
        search_attempts += 1
        status_text.info(f"🔍 Scanning Page {search_attempts}... (Found {len(valid_channels)}/{target_count} matches)")
        
        try:
            search_response = youtube.search().list(
                q=query, type='channel', part='id', maxResults=50, pageToken=next_page_token
            ).execute()
        except HttpError as e:
            st.error(f"Search failed: {e}")
            break

        items = search_response.get('items', [])
        if not items:
            st.warning("No more results available from YouTube.")
            break

        channel_ids = [item['id']['channelId'] for item in items]
        details = fetch_channel_details(youtube, channel_ids)
        
        for channel in details:
            try:
                title = channel['snippet']['title']
                subs = int(channel['statistics'].get('subscriberCount', 0))
                video_count = int(channel['statistics'].get('videoCount', 0))
                country = channel['snippet'].get('country', 'Unknown')
                channel_url = f"https://www.youtube.com/channel/{channel['id']}"
                
                # CHECKS
                is_size_good = min_s <= subs <= max_s
                
                is_loc_good = False
                if country == 'Unknown' and include_unknown:
                    is_loc_good = True
                elif country in allowed_countries:
                    is_loc_good = True
                
                if is_size_good and is_loc_good:
                    valid_channels.append({
                        'Channel Name': title,
                        'Subscribers': subs,
                        'Country': country,
                        'Video Count': video_count,
                        'Link': channel_url
                    })
                    if len(valid_channels) >= target_count: break
                
                # DEBUG LOGS
                elif debug: 
                    if search_attempts <= 2:
                        with debug_area:
                            if not is_size_good:
                                st.markdown(f"❌ **Skipped** [{title}]({channel_url}): Subs {subs} (Wanted {min_s}-{max_s})")
                            elif not is_loc_good:
                                st.markdown(f"❌ **Skipped** [{title}]({channel_url}): Location '{country}' not in target")

            except Exception:
                continue

        next_page_token = search_response.get('nextPageToken')
        progress_bar.progress(min(len(valid_channels) / target_count, 1.0))
        
        if not next_page_token:
            break
        time.sleep(0.1)

    status_text.empty()
    return valid_channels

# --- MAIN UI ---
col1, col2 = st.columns([3, 1])
with col1:
    query = st.text_input("Niche / Keyword", placeholder="e.g. 'Calisthenics for beginners'")
with col2:
    desired_count = st.number_input("Target Results", min_value=1, max_value=50, value=10)

if st.button("Find Channels", type="primary"):
    if not api_key:
        st.error("⚠️ Please enter your API Key in the sidebar.")
    elif not query:
        st.warning("⚠️ Please enter a Niche.")
    else:
        allowed_countries = get_country_codes(target_locations)
        
        with st.spinner("Hunting for channels..."):
            youtube = get_youtube_service(api_key)
            results = deep_search(
                youtube, query, desired_count, allowed_countries, 
                max_subs, min_subs, include_unknown, debug_mode
            )
            
            if results:
                st.success(f"Found {len(results)} channels!")
                
                # --- NEW DISPLAY METHOD (HTML TABLE) ---
                df = pd.DataFrame(results)
                
                # Create a copy for display so we don't mess up the download CSV
                display_df = df.copy()
                
                # Convert the 'Link' column into an actual HTML clickable link
                display_df['Link'] = display_df['Link'].apply(
                    lambda x: f'<a href="{x}" target="_blank">Open Channel 🔗</a>'
                )
                
                # Convert DataFrame to HTML (escape=False allows the links to work)
                html_table = display_df.to_html(escape=False, index=False)
                
                # Display the HTML table
                st.markdown(html_table, unsafe_allow_html=True)
                
                # Add a spacer
                st.markdown("<br>", unsafe_allow_html=True)
                
                # CSV Download Button (Using the original Clean DF)
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"{query}_channels.csv",
                    mime='text/csv',
                )

            else:
                st.error("No channels found. Try increasing 'Max Subscribers' or checking 'Include Unknown Locations'.")
