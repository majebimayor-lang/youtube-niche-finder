import sys
import time

# Try to import libraries and warn if missing
try:
    import pandas as pd
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError as e:
    print("CRITICAL ERROR: A required library is missing.")
    print(f"Missing library: {e.name}")
    print("Please run: pip install google-api-python-client pandas")
    input("Press Enter to exit...")
    sys.exit()

# --- CONFIGURATION ---
# PASTE YOUR KEY INSIDE THE QUOTES BELOW
API_KEY = 'YOUR_API_KEY_HERE' 

def search_channels_safe(query, max_results=50):
    """
    Searches for channels with error handling.
    """
    try:
        youtube = build('youtube', 'v3', developerKey=API_KEY)
    except Exception as e:
        print(f"\n[!] Error connecting to API: {e}")
        return []

    channels_data = []
    next_page_token = None
    
    print(f"\n--- Searching for: '{query}' ---")

    while len(channels_data) < max_results:
        try:
            remaining = max_results - len(channels_data)
            fetch_count = min(remaining, 50)
            
            request = youtube.search().list(
                q=query,
                type='channel',
                part='snippet',
                maxResults=fetch_count,
                pageToken=next_page_token
            )
            response = request.execute()
            
            items = response.get('items', [])
            if not items:
                print("No more items found.")
                break

            for item in items:
                snippet = item['snippet']
                data = {
                    'Channel Name': snippet['channelTitle'],
                    'Channel ID': item['id']['channelId'],
                    'Description': snippet['description'],
                    'Published At': snippet['publishedAt'],
                    'Link': f"https://www.youtube.com/channel/{item['id']['channelId']}"
                }
                channels_data.append(data)

            print(f"Fetched {len(channels_data)} / {max_results} channels...")
            
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
            
            # Sleep briefly to be nice to the API
            time.sleep(0.5)

        except HttpError as e:
            print(f"\n[!] API Error: {e.reason}")
            # If quota exceeded, stop trying
            if e.resp.status in [403, 429]:
                print("Quota exceeded or rate limit hit. Stopping search.")
                break
            else:
                break
        except Exception as e:
            print(f"\n[!] Unexpected Error: {e}")
            break

    return channels_data

def main():
    try:
        # Check if API Key is still default
        if API_KEY == 'YOUR_API_KEY_HERE':
            print("\n[!] ERROR: You did not put your API Key in the code!")
            print("Please open the file and paste your key in line 8.")
        else:
            keyword = input("Enter keyword to search (e.g. 'Fitness'): ")
            limit_input = input("How many channels (e.g. 10): ")
            
            # specific check for number input
            if not limit_input.isdigit():
                print("Please enter a number for the count.")
                limit = 10
            else:
                limit = int(limit_input)

            results = search_channels_safe(keyword, limit)

            if results:
                df = pd.DataFrame(results)
                # Clean filename
                clean_name = "".join([c for c in keyword if c.isalnum() or c in (' ','-','_')]).strip()
                filename = f"{clean_name.replace(' ', '_')}_channels.csv"
                
                df.to_csv(filename, index=False)
                print(f"\n[SUCCESS] Saved {len(results)} channels to: {filename}")
            else:
                print("\n[!] No data found or search failed.")

    except Exception as e:
        print(f"\n[!] Critical Script Error: {e}")

    # --- THIS LINE KEEPS THE WINDOW OPEN ---
    print("\n------------------------------------------------")
    input("Process finished. Press Enter to close this window...")

if __name__ == "__main__":
    main()
