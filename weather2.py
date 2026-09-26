import requests
import sqlite3
from datetime import datetime
from config import API_KEY
import matplotlib.pyplot as plt


class WeatherTracker:
    def show_chart(self, city):
        """Plot temperature history for a city."""
        history = self.get_history(city)

        if not history:
            print("No history found for this city yet.")
            return

        timestamps = [row[4] for row in history]
        temps = [row[0] for row in history]

        plt.figure(figsize=(10, 5))
        plt.plot(timestamps, temps, marker="o")
        plt.title(f"Temperature History: {city}")
        plt.xlabel("Time")
        plt.ylabel("Temperature (°C)")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    def __init__(self, db_name="weather_history.db"):
        """Runs automatically when we create a WeatherTracker.
        Connects to the database and makes sure the table exists."""
        self.db_name = db_name
        self._create_table()

    def _create_table(self):
        """Create the weather_history table if it doesn't already exist."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weather_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT,
                temp REAL,
                feels_like REAL,
                humidity INTEGER,
                condition TEXT,
                timestamp TEXT
            )
        """)
        conn.commit()
        conn.close()

    def get_weather(self, city):
        """Fetch current weather for a given city from OpenWeatherMap."""
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"q": city, "appid": API_KEY, "units": "metric"}

        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            return {
                "city": data["name"],
                "temp": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "humidity": data["main"]["humidity"],
                "condition": data["weather"][0]["description"]
            }
        else:
            return None

    def save_weather(self, weather):
        """Save a weather reading into the database."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO weather_history (city, temp, feels_like, humidity, condition, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            weather["city"],
            weather["temp"],
            weather["feels_like"],
            weather["humidity"],
            weather["condition"],
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()
        conn.close()

    def get_history(self, city):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT temp, feels_like, humidity, condition, timestamp
            FROM weather_history
            WHERE city = ? COLLATE NOCASE
            ORDER BY timestamp
        """, (city,))
        rows = cursor.fetchall()
        conn.close()
        return rows


if __name__ == "__main__":
    tracker = WeatherTracker()

    while True:
        print("\n--- Weather Dashboard ---")
        print("1. Check current weather")
        print("2. View history for a city")
        print("3. Show temperature chart")
        print("4. Quit")

        choice = input("Choose an option (1-4): ")

        if choice == "1":
            city = input("Enter a city name: ")
            weather = tracker.get_weather(city)

            if weather:
                print(f"\nWeather in {weather['city']}:")
                print(f"Temperature: {weather['temp']}°C (feels like {weather['feels_like']}°C)")
                print(f"Condition: {weather['condition']}")
                print(f"Humidity: {weather['humidity']}%")
                tracker.save_weather(weather)
                print("(Saved to database)")
            else:
                print("City not found or API error.")

        elif choice == "2":
            city = input("Enter a city name: ")
            history = tracker.get_history(city)
            if history:
                print(f"\n--- History for {city} ---")
                for row in history:
                    temp, feels_like, humidity, condition, timestamp = row
                    print(f"{timestamp} | {temp}°C, feels {feels_like}°C, {condition}, humidity {humidity}%")
            else:
                print("No history found for this city yet.")

        elif choice == "3":
            city = input("Enter a city name: ")
            tracker.show_chart(city)

        elif choice == "4":
            print("Goodbye!")
            break

        else:
            print("Invalid choice, try again.")