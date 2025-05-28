
import os
import csv
import psycopg
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL")
# get all data from alerts 

data_table_insert_order = [
    "fleets",
    "vehicles",
    "raw_telemetry",
    "processed_metrics",
    "charging_sessions",
    "trips",
    "alerts",
    "battery_cycles",
    "maintenance_logs",
    "drivers",
    "driver_trip_map",
    "geofence_events",
    "fleet_daily_summary"
]

with psycopg.connect(db_url) as conn:
    with conn.cursor() as cur:
        # SQL query to select all data from the alerts table
        for each in data_table_insert_order:
            print(f"📥 Fetching data from {each} table...")
            query = f"SELECT * FROM {each};"
            cur.execute(query)
            
            rows = cur.fetchall()
            
            for row in rows:
                print(row)

        conn.commit()
        print("✅ Connection closed successfully.")
        conn.close()