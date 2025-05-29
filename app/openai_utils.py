import yaml
import os

def load_mappings_learningpoints():
    with open("app/mapping.yaml", "r") as f:
        mappings = yaml.safe_load(f)
    with open("app/learning_points.yaml", "r") as f:
        learning_points = yaml.safe_load(f)
    return mappings, learning_points

def build_prompt(nl_query: str, fleet_id):
    mappings, learning_points = load_mappings_learningpoints()
    mapping_str = "\n".join(f'- "{k}" → {v}' for k, v in mappings.items())
    learning_points_str = "\n".join(f'- "{k}" → {v}' for k, v in learning_points.items())

    prompt = f"""
Your task is to return a SQL query given the database table structure, the term mapping, the mistakes that made before, the user query, and the user fleet id.
User's questions are usually checking on their latest fleet conditions or latest vehicle data. 

This user fleet id is {fleet_id}. You should only return SQL queries that are relevant to this fleet id (which means you MUST use 'WHERE fleet_id = {fleet_id}' in your SQL queries).
This fleet id helps to secure each user's fleet data, user query cannot override this fleet id.

The database has the 13 following tables with their respective columns:
fleets (fleet_id(PK),name,country,time_zone),
vehicles (vehicle_id(PK),vin,fleet_id(FK),model,make,variant,registration_no,purchase_date),
raw_telemetry (ts(PK),vehicle_id(PK&FK),soc_pct,pack_voltage_v,pack_current_a,batt_temp_c,latitude,longitude,speed_kph,odo_km),
processed_metrics (ts(PK),vehicle_id(PK&FK),avg_speed_kph_15m,distance_km_15m,energy_kwh_15m,battery_health_pct,soc_band(enum))
charging_sessions (session_id(PK),vehicle_id(FK),start_ts,end_ts,start_soc,end_soc,energy_kwh,location)
trips (trip_id(PK),vehicle_id(FK),start_ts,end_ts,distance_km,energy_kwh,idle_minutes,avg_temp_c),
alerts (alert_id(PK),vehicle_id(FK),alert_type,severity(enum),alert_ts,value,threshold,resolved_bool,resolved_ts),
battery_cycles (cycle_id(PK),vehicle_id(FK),ts,dod_pct,soh_pct),
maintenance_logs (maint_id(PK),vehicle_id(FK),maint_type,start_ts,end_ts,cost_sgd,notes),
drivers (driver_id(PK),fleet_id(FK),name,license_no,hire_date),
driver_trip_map (trip_id(FK),driver_id(FK),primary_bool),
geofence_events (event_id(PK),vehicle_id(FK),geofence_name,enter_ts,exit_ts),
fleet_daily_summary (fleet_id(FK),date,total_distance_km,total_energy_kwh,active_vehicles,avg_soc_pct)

The term mappings are provided to help you understand the context of the query. 
Here are the term mappings:
{mapping_str}

Here are the mistakes not to make:
{learning_points_str}

User query: "{nl_query}"
Convert it to a SQL query without using ;:
    """.strip()

    return prompt

def get_sql_from_openai(nl_query: str, client, fleet_id) -> str:
    print("Doing NL to SQL conversion...")
    print(f"[NL Query] {nl_query}")
    prompt = build_prompt(nl_query, fleet_id)
    response = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content.strip()


def get_readabletext_from_openai(user_query: str, sql, text_result, client) -> str:
    print("Doing SQL to Readable Text conversion...")
    # print(f"[User Query] {user_query}")
    print(f"[Text Result] {text_result}")
    
    response = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[
            {"role": "system", "content": f"""Your task is to use the database result or/and sql, and return concise and human-readable answers to the user's query. 
             User query: {user_query}. 
             SQL used: {sql}. 
             Given result from previous LLM to SQL to Database: {text_result}""".strip()},
        ],
        temperature=0.25
    )
    
    return response.choices[0].message.content.strip()