import os
from db.database import FinOpsDatabase

_db = None

def get_db():
    global _db
    if _db is None:
        _db = FinOpsDatabase(os.getenv("DATABASE_URL"))
    return _db