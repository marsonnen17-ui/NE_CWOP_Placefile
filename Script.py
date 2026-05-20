import requests
from datetime import datetime

# --- AUTHORIZED CONFIG ---
TOKEN = "024e1e15e3ad4650a5d36c5b37fe3095"
NETWORK = "65"  # CWOP Network
FILENAME = "CWOP_Full_ObsV1.txt"
ICON_URL = "https://raw.githubusercontent.com/marsonnen17-ui/NE_CWOP_Placefile/main/wind_barbs_V4_64.png"

# Priority Stations
TARGET_STIDS = ["E7235", "G4507", "C9774", "E7290", "D4989", "E3958"]

API_URL = f"https://api.synopticdata.com/v2/stations/latest?token={TOKEN}&networks={NETWORK}&units=english"

def get_barb_index(wind_speed_value_1):
    """
    Maps MPH to knots, then to the correct index.
    0-4 knots = Index 1 (Calm)
    5-9 knots = Index 2 (5kts)
    10-14 knots = Index 3 (10kts)
    """
    try:
        # 1. Convert MPH to Knots
        wspd_kts = float(wind_speed_value_1) * 0.868976

        # 2. Force Calm for anything 0-4 knots
        if wspd_kts < 4.5:
            return 2  # Index 1 is the Circle

        # 3. Calculate Index (The +1 ensures we skip the blank Index 0)
        # For 13 knots (15mph): (13 + 2.5) // 5 = 3.  3 + 1 = 4.
        index = int((wspd_kts + 2.5) // 5) + 2

        return min(index, 21)
    except:
        return 2


def build_placefile():
    try:
        # Fetching network data
        response = requests.get(API_URL, timeout=20)
        data = response.json()
        all_stations = data.get('STATION', [])

        # Filter post-API for your specific locations
        filtered_stations = [s for s in all_stations if s.get('STID') in TARGET_STIDS]

        with open(FILENAME, "w", encoding="utf-8") as f:
            # HEADER
            f.write("Title: NE CWOP - Full Observations\n")
            f.write("Refresh: 5\n")
            f.write("Threshold: 999\n")
            f.write(f'IconFile: 1, 64, 61, 32, 32, "{ICON_URL}"\n\n')

            for stn in filtered_stations:
                lat, lon = stn.get('LATITUDE'), stn.get('LONGITUDE')
                stid = stn.get('STID', 'UNK')
                obs = stn.get('OBSERVATIONS', {})

                # Extract Wind, Temp, and Dewpoint safely
                wspd = obs.get('wind_speed_value_1', {}).get('value', 0)
                wdir = obs.get('wind_direction_value_1', {}).get('value', 0)
                gust = obs.get('wind_gust_value_1', {}).get('value', wspd)
                temp = obs.get('air_temp_value_1', {}).get('value', "N/A")
                dewp = obs.get('dew_point_temperature_value_1d', {}).get('value', "N/A")

                # Timestamp Handling
                raw_time = obs.get('air_temp_value_1', {}).get('date_time')
                if raw_time:
                    dt = datetime.strptime(raw_time, "%Y-%m-%dT%H:%M:%SZ")
                    display_time = dt.strftime("%H:%M") + "z"
                else:
                    display_time = "N/A"

                if lat and lon:
                    idx = get_barb_index(wspd)
                    # Updated Label with Dewpoint
                    label = (f"{stn.get('NAME', stid)}\\n"
                             f"Temp: {temp}F / Dewp: {dewp}F\\n"
                             f"Wind: {int(float(wspd)*1.151)} G {int(float(gust)*1.151)} mph\\n"
                             f"Updated: {display_time}")

                    f.write("Color: 255 255 255\n")
                    f.write(f'Icon: {lat}, {lon}, {int(float(wdir))}, 1, {idx}, "{label}"\n')

            f.write("\nEnd:\n")
        print(f"Success! {FILENAME} updated with dewpoint data.")
        print(f"Success! Grabbed {len(all_stations)} stations, filtered down to {len(filtered_stations)}.")
    except Exception as e:
        print(f"Script Error: {e}")

if __name__ == "__main__":
    build_placefile()
