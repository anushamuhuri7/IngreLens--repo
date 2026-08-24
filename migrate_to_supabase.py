import sqlite3
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SQLITE_DB = "healthshield.db"

def migrate():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Supabase URL or Key missing in .env file.")
        return

    if not os.path.exists(SQLITE_DB):
        print(f"ℹ️ No local SQLite database ({SQLITE_DB}) found to migrate.")
        return

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    conn = sqlite3.connect(SQLITE_DB)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]
        print(f"Found SQLite tables: {tables}")

        if "scans" in tables or "scanned_products" in tables:
            tbl = "scanned_products" if "scanned_products" in tables else "scans"
            cursor.execute(f"SELECT product_name, raw_ingredients, safety_score, overall_verdict FROM {tbl}")
            rows = cursor.fetchall()
            for row in rows:
                data = {
                    "product_name": row[0],
                    "raw_ingredients": row[1],
                    "safety_score": row[2],
                    "overall_verdict": row[3],
                    "analysis_json": {}
                }
                supabase.table("scanned_products").insert(data).execute()
            print(f"✅ Successfully migrated {len(rows)} scans to Supabase.")
    except Exception as e:
        print(f"Migration error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()