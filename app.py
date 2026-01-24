import sys
import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ==========================================
# PASTE YOUR API KEY BELOW
# ==========================================
API_KEY = 'YOUR_API_KEY_HERE' 
# ==========================================

def get_service():
    if API_KEY == 'YOUR_API_KEY_HERE':
        print("\n[CRITICAL ERROR] You have not replaced the API Key!")
        print("Please open the script in a text editor and paste your Google API Key.")
        return None
    try:
        return build('youtube', 'v3', developerKey=API_KEY)
    except Exception as e:
        print(f"\n[ERROR] Could not connect to YouTube API. Details: {e}")
        return None

def search_channels(query, max_results):
    youtube = get_service()
    if not youtube:
        return []

    channels_data = []
    next_token = None
    
    print(f"\n--- Starting Search for: '{query}' ---")

    while len(channels_data) < max_results:
        try:
            # Determine how many to fetch (max 50 per request)
            fetch_count = min(max_results - len(channels_data), 50)
            
            request = youtube.search().list(
                q=query,
                type='channel',
                part='snippet',
                maxResults=fetch_count,
                pageToken=next_token
            )
            response = request.execute()

            items = response.get('items', [])
            if not items:
                print("No more results found by YouTube.")
                break

            for item in items:
                snippet = item['snippet']
                data = {
                    'Channel Name': snippet['channelTitle'],
                    'Channel ID': item['id']['channelId'],
                    'Description': snippet['description'],
                    'Published At': snippet['publishedAt'],
                    'URL': f"https://www.youtube.com/channel/{item['id']['channelId']}"
                }
                channels_data.append(data)

            # Check if there is a next page
            next_token = response.get('nextPageToken')
            if not next_token:
                break
                
        except HttpError as e:
            # This catches specific YouTube API errors (403, 400, etc.)
            error_reason = e.content.decode('utf-8')
            print(f"\n[API ERROR] YouTube refused the request.")
            if "quotaExceeded" in error_reason:
                print("Reason: You have used up your daily API Quota (10,000 units).")
            elif "API key not valid" in error_reason:
                print("Reason: Your API Key is invalid.")
            else:
                print(f"Details: {e}")
            break
        except Exception as e:
            print(f"\n[UNKNOWN ERROR] Something went wrong: {e}")
            break

    return channels_data

def main():
    # 1. Get User Input
    print("YouTube Channel Scraper (Safe Mode)")
    print("-----------------------------------")
    keyword = input("Enter keyword (e.g. 'Marketing'): ")
    
    try:
        limit = int(input("How many channels (e.g. 50): "))
    except ValueError:
        print("[ERROR] Please enter a number for the limit.")
        input("Press Enter to exit...")
        return

    # 2. Run Search
    results = search_channels(keyword, limit)

    # 3. Save Data
    if results:
        df = pd.DataFrame(results)
        # Clean filename to avoid errors
        clean_name = "".join([c for c in keyword if c.isalnum() or c in (' ','-','_')]).strip()
        filename = f"{clean_name.replace(' ', '_')}_channels.csv"
        
        try:
            df.to_csv(filename, index=False)
            print(f"\n[SUCCESS] Found {len(results)} channels.")
            print(f"Saved to file: {filename}")
        except PermissionError:
            print(f"\n[ERROR] Could not save file. Is '{filename}' already open in Excel?")
    else:
        print("\n[RESULT] No channels found or an error occurred.")

    # 4. Keep Window Open
    print("\n-----------------------------------")
    input("Press Enter to close this window...")

if __name__ == "__main__":
    main()
