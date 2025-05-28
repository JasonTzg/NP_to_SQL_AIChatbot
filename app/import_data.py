# Database June 27 expires
# Database name: nptosqlwork, user: nptosqlwork_user

import os
import csv
import psycopg
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL")

## Fleet & Admin 
# fleet_id 🔑 , name, country, time_zone 
create_fleets_table = """
CREATE TABLE IF NOT EXISTS fleets (
    fleet_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    country TEXT NOT NULL,
    time_zone TEXT NOT NULL
);
"""

## Vehicle registry 
# vehicle_id 🔑, vin (UNIQ), fleet_id↗fleets, model, make, variant, registration_no, purchase_date
create_vehicles_table = """
CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id SERIAL PRIMARY KEY,
    vin TEXT UNIQUE NOT NULL,
    fleet_id INTEGER REFERENCES fleets(fleet_id) ON DELETE CASCADE,
    model TEXT,
    make TEXT,
    variant TEXT,
    registration_no TEXT,
    purchase_date DATE
);
"""

## Real‑time Telemetry 
# ts 🔑, vehicle_id↗vehicles, soc_pct, pack_voltage_v, pack_current_a, batt_temp_c, latitude, longitude, speed_kph, odo_km 
create_real_time_telemetry_table = """
CREATE TABLE IF NOT EXISTS raw_telemetry (
    ts TIMESTAMPTZ,
    vehicle_id INTEGER REFERENCES vehicles(vehicle_id) ON DELETE CASCADE,
    soc_pct FLOAT CHECK (soc_pct >= 0 AND soc_pct <= 100),
    pack_voltage_v FLOAT,
    pack_current_a FLOAT,
    batt_temp_c FLOAT,
    latitude FLOAT,
    longitude FLOAT,
    speed_kph FLOAT,
    odo_km FLOAT,
    PRIMARY KEY (ts, vehicle_id)
);
"""

# Processed Metrics
# ts🔑, vehicle_id↗vehicles,avg_speed_kph_15m, distance_km_15m,energy_kwh_15m, battery_health_pct, soc_band (enum)
create_processed_metrics_table = """
CREATE TABLE IF NOT EXISTS processed_metrics (
    ts TIMESTAMPTZ,
    vehicle_id INTEGER REFERENCES vehicles(vehicle_id) ON DELETE CASCADE,
    avg_speed_kph_15m FLOAT,
    distance_km_15m FLOAT,
    energy_kwh_15m FLOAT,
    battery_health_pct FLOAT CHECK (battery_health_pct >= 0 AND battery_health_pct <= 100),
    soc_band TEXT CHECK (soc_band IN ('0-20', '20-40', '40-60', '60-80', '80-100')),
    PRIMARY KEY (ts, vehicle_id)
);
"""

# Charging &Energy
# session_id🔑, vehicle_id↗vehicles,start_ts, end_ts, start_soc, end_soc, energy_kwh, location
create_charging_sessions_table = """
CREATE TABLE IF NOT EXISTS charging_sessions (
    session_id SERIAL PRIMARY KEY,
    vehicle_id INTEGER REFERENCES vehicles(vehicle_id) ON DELETE CASCADE,
    start_ts TIMESTAMPTZ NOT NULL,
    end_ts TIMESTAMPTZ NOT NULL,
    start_soc FLOAT CHECK (start_soc >= 0 AND start_soc <= 100),
    end_soc FLOAT CHECK (end_soc >= 0 AND end_soc <= 100),
    energy_kwh FLOAT CHECK (energy_kwh >= 0),
    location TEXT
);
"""

# Trips &Utilisation
# trip_id🔑, vehicle_id↗vehicles,start_ts, end_ts, distance_km, energy_kwh, idle_minutes, avg_temp_c
create_trips_table = """
CREATE TABLE IF NOT EXISTS trips (
    trip_id SERIAL PRIMARY KEY,
    vehicle_id INTEGER REFERENCES vehicles(vehicle_id) ON DELETE CASCADE,
    start_ts TIMESTAMPTZ NOT NULL,
    end_ts TIMESTAMPTZ NOT NULL,
    distance_km FLOAT CHECK (distance_km >= 0),
    energy_kwh FLOAT CHECK (energy_kwh >= 0),
    idle_minutes INT CHECK (idle_minutes >= 0),
    avg_temp_c FLOAT
);
"""

# Alerts & Safety 
# alert_id🔑, vehicle_id↗vehicles, alert_type, severity (enum), alert_ts,value, threshold, resolved_bool,resolved_ts
create_alerts_table = """
CREATE TABLE IF NOT EXISTS alerts (
    alert_id SERIAL PRIMARY KEY,
    vehicle_id INTEGER REFERENCES vehicles(vehicle_id) ON DELETE CASCADE,
    alert_type TEXT NOT NULL,
    severity TEXT CHECK (severity IN ('Low', 'Medium', 'High')),
    alert_ts TIMESTAMPTZ NOT NULL,
    value FLOAT,
    threshold FLOAT,
    resolved_bool BOOLEAN DEFAULT FALSE,
    resolved_ts TIMESTAMPTZ
);
"""

# Battery Health 
# cycle_id🔑, vehicle_id↗vehicles, ts,dod_pct, soh_pct
create_battery_health_table = """
CREATE TABLE IF NOT EXISTS battery_cycles (
    cycle_id SERIAL PRIMARY KEY,
    vehicle_id INTEGER REFERENCES vehicles(vehicle_id) ON DELETE CASCADE,
    ts TIMESTAMPTZ NOT NULL,
    dod_pct FLOAT CHECK (dod_pct >= 0 AND dod_pct <= 100),
    soh_pct FLOAT CHECK (soh_pct >= 0 AND soh_pct <= 100)
);
"""

# Maintenance 
# maint_id🔑, vehicle_id↗vehicles, maint_type, start_ts, end_ts, cost_sgd, notes
create_maintenance_table = """
CREATE TABLE IF NOT EXISTS maintenance_logs (
    maint_id SERIAL PRIMARY KEY,
    vehicle_id INTEGER REFERENCES vehicles(vehicle_id) ON DELETE CASCADE,
    maint_type TEXT NOT NULL,
    start_ts TIMESTAMPTZ NOT NULL,
    end_ts TIMESTAMPTZ NOT NULL,
    cost_sgd FLOAT CHECK (cost_sgd >= 0),
    notes TEXT
);
"""

# Driver Behaviour
# driver_id🔑, fleet_id↗fleets, name, license_no, hire_date
create_drivers_table = """
CREATE TABLE IF NOT EXISTS drivers (
    driver_id SERIAL PRIMARY KEY,
    fleet_id INTEGER REFERENCES fleets(fleet_id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    license_no TEXT UNIQUE NOT NULL,
    hire_date DATE NOT NULL
);
"""

# Driver–Trip link 
# trip_id↗trips, driver_id↗drivers, primary_bool (default TRUE)
create_driver_trip_link_table = """
CREATE TABLE IF NOT EXISTS driver_trip_map (
    trip_id INTEGER REFERENCES trips(trip_id) ON DELETE CASCADE,
    driver_id INTEGER REFERENCES drivers(driver_id) ON DELETE CASCADE,
    primary_bool BOOLEAN DEFAULT TRUE
);
"""

# Geospatial 
# event_id🔑, vehicle_id↗vehicles, geofence_name, enter_ts, exit_ts
create_geofence_events_table = """
CREATE TABLE IF NOT EXISTS geofence_events (
    event_id SERIAL PRIMARY KEY,
    vehicle_id INTEGER REFERENCES vehicles(vehicle_id) ON DELETE CASCADE,
    geofence_name TEXT NOT NULL,
    enter_ts TIMESTAMPTZ NOT NULL,
    exit_ts TIMESTAMPTZ
);
"""

# fleet_daily_summary Reports & Exports (materialised)
# fleet_id↗fleets, date, total_distance_km, total_energy_kwh, active_vehicles, avg_soc_pct
create_fleet_daily_summary_table = """
CREATE TABLE IF NOT EXISTS fleet_daily_summary (
    fleet_id INTEGER REFERENCES fleets(fleet_id) ON DELETE CASCADE,
    date DATE NOT NULL,
    total_distance_km FLOAT CHECK (total_distance_km >= 0),
    total_energy_kwh FLOAT CHECK (total_energy_kwh >= 0),
    active_vehicles INT CHECK (active_vehicles >= 0),
    avg_soc_pct FLOAT CHECK (avg_soc_pct >= 0 AND avg_soc_pct <= 100)
);
"""

# data csv given in a folder
csv_folder = "./Datakrew_Assignment_Sample_Data" 
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

def sanitize_row(row):
    return [None if v == '' else v for v in row]

def init_schema():
    try:
        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                # Create all tables in the correct order
                cur.execute(create_fleets_table)
                cur.execute(create_vehicles_table)
                cur.execute(create_real_time_telemetry_table)
                cur.execute(create_processed_metrics_table)
                cur.execute(create_charging_sessions_table)
                cur.execute(create_trips_table)
                cur.execute(create_alerts_table)
                cur.execute(create_battery_health_table)
                cur.execute(create_maintenance_table)
                cur.execute(create_drivers_table)
                cur.execute(create_driver_trip_link_table)
                cur.execute(create_geofence_events_table)
                cur.execute(create_fleet_daily_summary_table)
                print("✅ Tables created or already exist.")
    except Exception as e:
        print("❌ Error during schema initialization:")
        print(e)

def bulk_load_csv_to_table(cur, csv_path, table_name):
    print(f"📥 Loading {csv_path} into {table_name}...")
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)  # skip header line
        for row in reader:
            print(row)  # For debugging: list of column values
            # Prepare a parameterized query with the right number of %s placeholders
            placeholders = ", ".join(["%s"] * len(row))
            query = f"INSERT INTO {table_name} VALUES ({placeholders})"
            cleaned_row = sanitize_row(row)
            cur.execute(query, cleaned_row)

def main():
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            for table_name in data_table_insert_order:
                csv_path = os.path.join(csv_folder, f"{table_name}.csv")
                if os.path.exists(csv_path):
                    bulk_load_csv_to_table(cur, csv_path, table_name)
                else:
                    print(f"⚠️  CSV not found: {csv_path}")
        conn.commit()
        print("✅ All tables inserted successfully.")
        
if __name__ == "__main__":
    init_schema()  # Initialize schema first
    main()
