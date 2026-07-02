# test_connection.py
from app.core.database import engine 
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT 1"))
    print("Connexion réussie ✅", result.scalar())