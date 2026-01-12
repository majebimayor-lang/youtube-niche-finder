import streamlit as st
import pandas as pd
from googleapiclient.discovery import build

# 🔑 PUT YOUR API KEY HERE
API_KEY = st.secrets ["API_KEY"]

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
def search_channels(youtube, query, max_pages=5):
    channels = []
    next_page_token = None

    for _ in range(max_pages):
        request = youtube.search().list(
            part="snippet",
            q=query,
            type="channel",
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()

        for item in response["items"]:
            channels.append(item["snippet"]["channelId"])

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    return channels


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
