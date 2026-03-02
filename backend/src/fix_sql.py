import re

with open('api_v2.py', 'r') as f:
    content = f.read()

# Fix the db.execute calls to use text()
content = content.replace(
    'result = db.execute(\n            "SELECT ST_Y(location::GEOMETRY) as lat, ST_X(location::GEOMETRY) as lng FROM incidents WHERE id = :id",\n            {\'id\': i.id}\n        )',
    'from sqlalchemy import text\n            result = db.execute(\n                text("SELECT ST_Y(location::GEOMETRY) as lat, ST_X(location::GEOMETRY) as lng FROM incidents WHERE id = :id"),\n                {\'id\': i.id}\n            )'
)

with open('api_v2.py', 'w') as f:
    f.write(content)

print("Fixed!")
