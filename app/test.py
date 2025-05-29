import json

{"sql":"SELECT * FROM raw_telemetry WHERE vehicle_id = (SELECT vehicle_id FROM vehicles WHERE registration_no = 'GBM6296G') ORDER BY ts DESC LIMIT 1;","results":[{"ts":"2025-05-14T09:00:00+00:00","vehicle_id":1,"soc_pct":57.0,"pack_voltage_v":356.9,"pack_current_a":-86.1,"batt_temp_c":32.3,"latitude":1.3273068340788692,"longitude":103.84852215206607,"speed_kph":0.0,"odo_km":10000.0}]}

format_prompt = f"""You are a helpful assistant.
The user asked the following question:
"{prompt}"

The database returned the following results:
{json.dumps(results, indent=2)}

Please write a clear and concise summary of the result for the user.
"""

response2 = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You're a helpful data summarizer."},
        {"role": "user", "content": format_prompt}
    ],
    temperature=0,
)

final_answer = response2.choices[0].message.content