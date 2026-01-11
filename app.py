import streamlit as st
import pandas as pd
from googleapiclient.discovery import build

# 🔑 PUT YOUR API KEY HERE
API_KEY = ""

youtube = build("youtube", "v3", developerKey=API_KEY)

st.set_page_config(page_title="YouTube Niche Finder", layout="wide")

st.title("🎙️ YouTube Channel Finder")
st.write("Search YouTube channels by niche and subscriber size")

# -----------------------------
# USER INPUTS
# -----------------------------
niche = st.text_input("Enter niche (e.g. podcast, real estate, fitness)")

min_subs = st.number_input("Minimum subscribers", min_value=0, value=0)
max_subs = st.number_input("Maximum subscribers", min_value=0, value=100000)

search_button = st.button("Search Channels")

# -----------------------------
# FUNCTIONS
# -----------------------------
def search_channels(keyword, max_results=30):
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

    results = []
    for item in response["items"]:
        subs = int(item["statistics"].get("subscriberCount", 0))
        views = int(item["statistics"].get("viewCount", 0))

        if subs < min_subs or subs > max_subs:
            continue

        results.append({
            "Channel Name": item["snippet"]["title"],
            "Subscribers": subs,
            "Total Views": views,
            "Videos": item["statistics"].get("videoCount", 0),
            "Channel URL": f"https://www.youtube.com/channel/{item['id']}"
        })

    return results

# -----------------------------
# RUN SEARCH
# -----------------------------
if search_button and niche:
    with st.spinner("Searching YouTube..."):
        channel_ids = search_channels(niche)
        data = get_channel_stats(channel_ids)

        if data:
            df = pd.DataFrame(data)
            st.success(f"Found {len(df)} channels")
            st.dataframe(df)

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download CSV",
                csv,
                file_name=f"{niche.replace(' ', '_')}_channels.csv",
                mime="text/csv"
            )
        else:
            st.warning("No channels found with these filters.")
