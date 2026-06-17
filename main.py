import requests
import os
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Configuration - Support multiple accounts
ACCOUNTS = [
    {
        "player_id": os.getenv("PLAYER_ID_1", "ali-_-032"),
        "platform": os.getenv("PLATFORM_1", "psn"),
    },
    {
        "player_id": os.getenv("PLAYER_ID_2", ""),
        "platform": os.getenv("PLATFORM_2", "psn"),
    },
    {
        "player_id": os.getenv("PLAYER_ID_3", ""),
        "platform": os.getenv("PLATFORM_3", "psn"),
    }
]

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "300"))

last_game_counts = {}

def get_player_stats(player_id, platform):
    """Fetch player stats from Rocket League Tracker"""
    tracker_api_url = f"https://api.tracker.gg/api/v2/rocket-league/standard/profile/{platform}/{player_id}"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    try:
        response = requests.get(tracker_api_url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {player_id} data: {e}")
        return None

def send_discord_notification(player_id, game_info):
    """Send notification to Discord webhook"""
    embed = {
        "title": f"🎮 {player_id} just played a game!",
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
        print(f"Discord notification sent for {player_id}: {game_info.get('timestamp')}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending Discord notification: {e}")

def monitor_players():
    """Main monitoring loop for all accounts"""
    print(f"Starting to monitor {len([a for a in ACCOUNTS if a['player_id']])} accounts...")
    
    # Filter out empty accounts
    active_accounts = [a for a in ACCOUNTS if a['player_id']]
    
    while True:
        try:
            for account in active_accounts:
                player_id = account['player_id']
                platform = account['platform']
                
                data = get_player_stats(player_id, platform)
                
                if data and "data" in data:
                    player_data = data["data"]
                    stats = player_data.get("stats", {})
                    
                    current_game_count = stats.get("matchesPlayed", {}).get("value", 0)
                    
                    # Check if new game was played
                    if player_id in last_game_counts and current_game_count > last_game_counts[player_id]:
                        game_info = {
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "playlist": "Competitive",
                            "result": "Win/Loss",
                            "points": 0
                        }
                        send_discord_notification(player_id, game_info)
                    
                    last_game_counts[player_id] = current_game_count
                    print(f"[{datetime.now()}] {player_id} - Games played: {current_game_count}")
            
            time.sleep(CHECK_INTERVAL)
            
        except Exception as e:
            print(f"Error in monitoring loop: {e}")
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    if not DISCORD_WEBHOOK_URL:
        print("ERROR: DISCORD_WEBHOOK_URL environment variable not set!")
        exit(1)
    
    monitor_players()