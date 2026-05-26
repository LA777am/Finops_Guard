import os
from dotenv import load_dotenv
load_dotenv()

from db.database import FinOpsDatabase  

db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("❌ Error: DATABASE_URL environment variable is not set.")
    exit(1)

db = FinOpsDatabase(db_url)

if db.create_tables():
    print("✅ Tables and indexes created successfully in database.")
else:
    print("❌ Error: Failed to create database tables.")
    exit(1)