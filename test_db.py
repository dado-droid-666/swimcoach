from backend.database import engine, Base
from backend import models

print('Tables in metadata:', list(Base.metadata.tables.keys()))
Base.metadata.create_all(bind=engine)
print('Tables created:', list(Base.metadata.tables.keys()))

import sqlite3
conn = sqlite3.connect('swim_coach.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('Actual tables:', cursor.fetchall())