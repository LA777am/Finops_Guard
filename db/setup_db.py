import os
from db.database import FinOpsDatabase  

db = FinOpsDatabase(os.getenv("DATABASE_URL"))

db.create_tables()

print("✅ Tables created successfully")