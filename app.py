import streamlit as st
import pandas as pd
from googleapiclient.discovery import build

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(page_title="YouTube Niche Finder", layout="wide")

API_KEY = st.secrets["API_KEY"]

youtube = build("youtube", "v3", developerKey=API_KEY)

st.title("🎙️ YouTube Channel Finder")
st.write("Search YouTube channels by niche, subscribers, and location")

# -----------------------------
# USER INPUTS
# -----------------------------
niche = st.text_input("Enter niche (e.g. podcast, real estate, fitness)")

min_subs = st.number_input("Minimum subscribers", min_value=0, value=0)
max_subs = st.number_input("Maximum subscribers", min_value=0, value=100)

pages = st.slider("How deep should we search?", 1, 10, 3)

locations = st.multiselect(
    "Channel locations",
    ["All", "US", "GB", "CA", "NG", "AU", "DE", "FR"],
    default=["All"]
)

search_button = st.button("Search Channels")

# -----------------------------
# FUNCTIONS
# -----------------------------
def search_channels(youtube, query, max_pages):
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

    return list(set(channels))


def get_channel_stats(youtube, channel_ids):
    data = []

    for i in range(0, len(channel_ids), 50):
        request = youtube.channels().list(
            part="snippet,statistics",
            id=",".join(channel_ids[i:i+50])
        )
        response = request.execute()

        for item in response["items"]:
            subs = int(item["statistics"].get("subscriberCount", 0))
            country = item["snippet"].get("country", "Unknown")
            url = f"https://www.youtube.com/channel/{item['id']}"

            data.append({
                "Channel Name": item["snippet"]["title"],
                "Subscribers": subs,
                "Videos": int(item["statistics"].get("videoCount", 0)),
                "Views": int(item["statistics"].get("viewCount", 0)),
                "Country": country,
                "Channel URL": f'<a href="{url}" target="_blank">Visit Channel</a>'
            })

    return data

# -----------------------------
# RUN SEARCH
# -----------------------------
if search_button and niche:
    with st.spinner("Searching YouTube..."):
        channel_ids = search_channels(youtube, niche, pages)
        stats = get_channel_stats(youtube, channel_ids)

        def location_match(country):
            return (
                "All" in locations
                or country in locations
            )

        filtered = [
            c for c in stats
            if min_subs <= c["Subscribers"] <= max_subs
            and location_match(c["Country"])
        ]

        if filtered:
            df = (
                pd.DataFrame(filtered)
                .sort_values(["Country", "Subscribers"])
            )

            st.success(f"Found {len(df)} channels")

            # Render HTML links safely
            st.markdown(
                df.to_html(escape=False, index=False),
                unsafe_allow_html=True
            )

            csv = df.drop(columns=["Channel URL"]).to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download CSV",
                csv,
                file_name=f"{niche.replace(' ', '_')}_channels.csv",
                mime="text/csv"
            )
        else:
            st.warning("No channels found with these filters.")
