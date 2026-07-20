import time
import random
import pandas as pd
from curl_cffi import requests

# General settings for all requests
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Referer": "https://www.sofascore.com/",
}

# ==========================================
# Step 1: Collect Match IDs and Team Names
# ==========================================
print("--- Step 1: Starting to collect the list of matches and teams ---")

matches_data = []
all_match_ids = []
page = 0
has_next_page = True

while has_next_page:
    url = f"https://www.sofascore.com/api/v1/unique-tournament/16/season/58210/events/last/{page}"
    try:
        response = requests.get(url, headers=HEADERS, impersonate="chrome110")

        if response.status_code == 200:
            data = response.json()
            events = data.get("events", [])

            for event in events:
                match_id = event.get("id")
                if match_id:
                    # Save match metadata
                    matches_data.append({
                        "match_id": match_id,
                        "home_team": event.get("homeTeam", {}).get("name"),
                        "away_team": event.get("awayTeam", {}).get("name"),
                        "slug": event.get("slug")
                    })
                    all_match_ids.append(match_id)

            has_next_page = data.get("hasNextPage", False)
            page += 1
            time.sleep(1)  # Short delay between page navigations
        else:
            print(f"Communication error with page {page}: {response.status_code}")
            break

    except Exception as e:
        print(f"Unexpected error on page {page}: {e}")
        break

# Save teams lookup table
df_teams = pd.DataFrame(matches_data)
df_teams.to_csv("world_cup_teams_lookup.csv", index=False)
print(f"V Collected {len(all_match_ids)} matches and saved to 'world_cup_teams_lookup.csv'\n")

# ==========================================
# Step 2: Collect Attack Momentum Data
# ==========================================
print(f"--- Step 2: Starting to pull momentum data for {len(all_match_ids)} matches ---")

all_graph_data = []

for idx, match_id in enumerate(all_match_ids, 1):
    url = f"https://www.sofascore.com/api/v1/event/{match_id}/graph"
    try:
        response = requests.get(url, headers=HEADERS, impersonate="chrome110")

        if response.status_code == 200:
            data = response.json()
            graph_points = data.get("graphPoints", [])

            if graph_points:
                df_match = pd.DataFrame(graph_points)
                df_match["match_id"] = match_id
                all_graph_data.append(df_match)
                print(f"  [{idx}/{len(all_match_ids)}] Match {match_id}: Collected {len(df_match)} points.")
            else:
                print(f"  [{idx}/{len(all_match_ids)}] Match {match_id}: No momentum data available.")
        else:
            print(f"  [{idx}/{len(all_match_ids)}] Match {match_id}: Error {response.status_code}")

    except Exception as e:
        print(f"  > Unexpected error in match {match_id}: {e}")

    # Mandatory: Random delay to prevent rate limiting
    time.sleep(random.uniform(2.5, 4.5))

# Merge and save all momentum data
if all_graph_data:
    df_momentum = pd.concat(all_graph_data, ignore_index=True)
    df_momentum.to_csv("world_cup_momentum_dataset.csv", index=False)
    print(f"V Momentum dataset saved! ({len(df_momentum)} rows)\n")

# ==========================================
# Step 3: Collect Match Events (Drinks breaks and Goals)
# ==========================================
print(f"--- Step 3: Starting to extract events for {len(all_match_ids)} matches ---")

all_events_data = []

for idx, match_id in enumerate(all_match_ids, 1):
    url = f"https://www.sofascore.com/api/v1/event/{match_id}/comments"
    try:
        response = requests.get(url, headers=HEADERS, impersonate="chrome110")

        if response.status_code == 200:
            data = response.json()
            comments = data.get("comments", [])

            # Reverse the list to chronological order (from start to end of match)
            comments.reverse()

            events_found = 0
            for order_idx, comment in enumerate(comments):
                text_lower = comment.get("text", "").lower()
                minute = comment.get("time")
                event_type = None

                # Event classification
                if "drinks break" in text_lower:
                    event_type = "drinks_break"
                elif "attempt missed" in text_lower:
                    event_type = "shot_missed"
                elif "goal!" in text_lower:
                    event_type = "goal"

                if event_type:
                    all_events_data.append({
                        "match_id": match_id,
                        "minute": minute,
                        "event_type": event_type,
                        "chronological_index": order_idx,
                    })
                    events_found += 1

            print(f"  [{idx}/{len(all_match_ids)}] Match {match_id}: Extracted {events_found} events.")

    except Exception as e:
        print(f"  > Unexpected error in match {match_id}: {e}")

    # Mandatory: Random delay to prevent rate limiting
    time.sleep(random.uniform(2.0, 3.5))

# Create events DataFrame and save
if all_events_data:
    df_events = pd.DataFrame(all_events_data)
    df_events.to_csv("world_cup_match_events.csv", index=False)
    print(f"V Events dataset saved! ({len(df_events)} rows)\n")

print("--- Data collection completed successfully! All files are ready for analysis. ---")

# ==========================================
# Step 4: Collect Pre-Match Betting Odds
# ==========================================
match_ids = all_match_ids


# Helper function to convert fractional odds (e.g., "5/2") to decimal odds (3.5)
def fraction_to_decimal(fraction_str):
    if not fraction_str or "/" not in fraction_str:
        return None
    try:
        num, den = fraction_str.split("/")
        return (float(num) / float(den)) + 1.0
    except:
        return None


odds_data = []

print(f"Starting to pull betting odds for {len(match_ids)} matches...")

for idx, match_id in enumerate(match_ids, 1):
    url = f"https://www.sofascore.com/api/v1/event/{match_id}/odds/1/all"
    print(f"[{idx}/{len(match_ids)}] Checking match {match_id}...")

    try:
        response = requests.get(url, headers=HEADERS, impersonate="chrome110")

        if response.status_code == 200:
            data = response.json()
            markets = data.get("markets", [])

            home_odds = None
            draw_odds = None
            away_odds = None

            # Search for the "Full time" market (1X2)
            for market in markets:
                # Sometimes identified by market name or market ID
                if market.get("marketName") == "Full time" or market.get("marketId") == 1:
                    choices = market.get("choices", [])
                    for choice in choices:
                        name = choice.get("name")
                        decimal_val = fraction_to_decimal(choice.get("fractionalValue"))

                        if name == "1":
                            home_odds = decimal_val
                        elif name == "X":
                            draw_odds = decimal_val
                        elif name == "2":
                            away_odds = decimal_val
                    break  # Found the main market, break out of the inner loop

            if home_odds and away_odds:
                # Determine the favorite and underdog
                if home_odds < away_odds:
                    favorite_side = "home"
                    underdog_side = "away"
                elif away_odds < home_odds:
                    favorite_side = "away"
                    underdog_side = "home"
                else:
                    favorite_side = "even"
                    underdog_side = "even"

                odds_data.append({
                    "match_id": match_id,
                    "odds_1_home": round(home_odds, 2),
                    "odds_X_draw": round(draw_odds, 2) if draw_odds else None,
                    "odds_2_away": round(away_odds, 2),
                    "favorite_side": favorite_side,
                    "underdog_side": underdog_side
                })
                print(
                    f"  > V Odds: Home {round(home_odds, 2)} | Away {round(away_odds, 2)} -> Favorite: {favorite_side}")
            else:
                print("  > X No Full time odds found for this match.")

        elif response.status_code == 404:
            print(f"  > Odds not found on server (404).")
        else:
            print(f"  > Error {response.status_code}")

    except Exception as e:
        print(f"  > Unexpected error in match {match_id}: {e}")

    # Random delay between requests to avoid being blocked
    time.sleep(random.uniform(2.0, 3.5))

# Create and save the table
if odds_data:
    df_odds = pd.DataFrame(odds_data)
    df_odds.to_csv("world_cup_match_odds.csv", index=False)
    print("\n--- Collection completed! File 'world_cup_match_odds.csv' created ---")
else:
    print("No betting odds collected.")

# ==========================================
# Step 5: Update Odds Logic (Clear Favorites)
# ==========================================
# Load the existing odds file
df_odds = pd.read_csv("world_cup_match_odds.csv")


# Function applying the strict logic for defining a clear favorite
def get_clear_favorite(row):
    home_odds = row['odds_1_home']
    away_odds = row['odds_2_away']

    # Check if the home team is a clear favorite (odds <= 2.0)
    if pd.notna(home_odds) and home_odds <= 2.0:
        return pd.Series(['home', 'away'])

    # Check if the away team is a clear favorite (odds <= 2.0)
    elif pd.notna(away_odds) and away_odds <= 2.0:
        return pd.Series(['away', 'home'])

    # If neither team has odds of 2.0 or less, the match is considered even
    else:
        return pd.Series([None, None])


# Apply the function to the dataset to update columns
df_odds[['favorite_side', 'underdog_side']] = df_odds.apply(get_clear_favorite, axis=1)

# Save the updated file
df_odds.to_csv("world_cup_match_odds.csv", index=False)

# Print a brief summary to see how many matches remain with a clear favorite
matches_with_favorite = df_odds['favorite_side'].notna().sum()
total_matches = len(df_odds)

print(f"File updated successfully!")
print(
    f"Out of {total_matches} matches, {matches_with_favorite} matches with a clear favorite (odds <= 2.0) were filtered.")