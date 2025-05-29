from app.auth_utils import get_current_fleet_id, check_sql


# Usage example:

sql = """
SELECT * FROM vehicles
WHERE fleet_id = 3 and 
GROUP BY vehicle_type
ORDER BY created_at DESC
"""

example_injection_sql = """
SELECT * FROM vehicles
WHERE fleet_id = 3 OR 1=1; -- 
"""

example_injection_sql_2 = """
SELECT * FROM vehicles
WHERE fleet_id = 3 AND (vehicle_type = 'car' OR vehicle_type = 'truck')
"""

example_injection_sql_3_DELECT = """
SELECT * FROM vehicles
WHERE fleet_id = 3 AND vehicle_type = 'car'; DELETE FROM vehicles WHERE fleet_id = 3;
"""

allowed_fleet_id = 2

try:
    where_clause = check_sql(sql, allowed_fleet_id)
    print(f"SQL is safe. WHERE clause: {where_clause}")
except ValueError as e:
    print(f"SQL check failed: {e}")
