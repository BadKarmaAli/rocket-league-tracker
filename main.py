import requests
import os
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Configuration
PLAYER_ID = os.getenv("PLAYER_ID", "ali-_-032")
PLATFORM = os.getenv("PLATFORM", "psn")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "300"))

TRACKER_API_URL = f"https://api.tracker.gg/api/v2/rocket-league/standard/profile/{PLATFORM}/{PLAYER_ID}"

last_game_count = None

def get_player_stats():
    """Fetch player stats from Rocket League Tracker"""
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    try:
        response = requests.get(TRACKER_API_URL, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching player data: {e}")
        return None

def send_discord_notification(game_info):
    """Send notification to Discord webhook"""
    embed = {
        "title": f"🎮 {PLAYER_ID} just played a game!",
        "description": f"Game Time: {game_info.get('timestamp', 'N/A')}",
        "color": 3447003,
        "fields": [
            {
                "name": "Playlist",
                "value": game_info.get('playlist', 'Unknown'),
                "inline": True
            },
            {
                "name": "Result",
                "value": game_info.get('result', 'Unknown'),
                "inline": True
            },
            {
                "name": "Points",
                "value": str(game_info.get('points', 0)),
                "inline": True
            }
        ]
    }
    
    payload = {"embeds": [embed]}
    
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print(f"Discord notification sent: {game_info.get('timestamp')}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending Discord notification: {e}")

def monitor_player():
    """Main monitoring loop"""
    global last_game_count
    
    print(f"Starting to monitor {PLAYER_ID}...")
    print(f"Check interval: {CHECK_INTERVAL} seconds")
    
    while True:
        try:
            data = get_player_stats()
            
            if data and "data" in data:
                player_data = data["data"]
                stats = player_data.get("stats", {})
                
                current_game_count = stats.get("matchesPlayed", {}).get("value", 0)
                
                if last_game_count is not None and current_game_count > last_game_count:
                    game_info = {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "playlist": "Competitive",
                        "result": "Win/Loss",
                        "points": 0
                    }
                    send_discord_notification(game_info)
                
                last_game_count = current_game_count
                print(f"[{datetime.now()}] Checked - Games played: {current_game_count}")
            
            time.sleep(CHECK_INTERVAL)
            
        except Exception as e:
            print(f"Error in monitoring loop: {e}")
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    if not DISCORD_WEBHOOK_URL:
        print("ERROR: DISCORD_WEBHOOK_URL environment variable not set!")
        exit(1)
    
    monitor_player()