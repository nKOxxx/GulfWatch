import psycopg2

DATABASE_URL = "postgresql://gulf_watch_db_user:tfhqXXT4KA0PwyjvN3qheJun7r5cBvxT@dpg-d6i69q1drdic73d0g6m0-a/gulf_watch_db"

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

print("Enabling PostGIS...")
cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
cur.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
conn.commit()

cur.execute("SELECT PostGIS_Version();")
version = cur.fetchone()[0]
print(f"✅ PostGIS enabled: {version}")

cur.close()
conn.close()
