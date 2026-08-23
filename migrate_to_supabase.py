import sqlite3
import os
from sqlalchemy import create_engine
from app.database import Base, engine, DATABASE_URL
from app.models import User, HealthProfile, ScanHistory, MedicineScan

def sync_sqlite_to_supabase():
    sqlite_db_path = "healthshield.db"
    if not os.path.exists(sqlite_db_path):
        print(f"SQLite database '{sqlite_db_path}' not found.")
        return

    print("Creating tables in target database...")
    Base.metadata.create_all(bind=engine)

    if DATABASE_URL.startswith("sqlite"):
        print("Target is local SQLite. Set DATABASE_URL in .env to point to your Supabase PostgreSQL instance.")
        return

    print("Connecting to local SQLite database to read existing data...")
    conn = sqlite3.connect(sqlite_db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    from app.database import SessionLocal
    db = SessionLocal()

    try:
        # Sync Users
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        for u in users:
            existing = db.query(User).filter(User.id == u['id']).first()
            if not existing:
                user = User(
                    id=u['id'],
                    name=u['name'],
                    email=u['email'],
                    password=u['password']
                )
                db.add(user)
        db.commit()
        print(f"Synced {len(users)} users.")

        # Sync HealthProfiles
        cursor.execute("SELECT * FROM health_profiles")
        profiles = cursor.fetchall()
        for p in profiles:
            existing = db.query(HealthProfile).filter(HealthProfile.id == p['id']).first()
            if not existing:
                prof = HealthProfile(
                    id=p['id'],
                    user_id=p['user_id'],
                    diabetes=bool(p['diabetes']),
                    hypertension=bool(p['hypertension']),
                    lactose_intolerant=bool(p['lactose_intolerant']),
                    gluten_allergy=bool(p['gluten_allergy']),
                    nut_allergy=bool(p['nut_allergy'])
                )
                db.add(prof)
        db.commit()
        print(f"Synced {len(profiles)} health profiles.")

        # Sync ScanHistory
        cursor.execute("SELECT * FROM scan_history")
        scans = cursor.fetchall()
        for s in scans:
            existing = db.query(ScanHistory).filter(ScanHistory.id == s['id']).first()
            if not existing:
                scan = ScanHistory(
                    id=s['id'],
                    user_id=s['user_id'],
                    product_name=s['product_name'],
                    safety_score=s['safety_score'],
                    risk_message=s['risk_message']
                )
                db.add(scan)
        db.commit()
        print(f"Synced {len(scans)} scan history items.")

        # Sync MedicineScans
        cursor.execute("SELECT * FROM medicine_scans")
        med_scans = cursor.fetchall()
        for m in med_scans:
            existing = db.query(MedicineScan).filter(MedicineScan.id == m['id']).first()
            if not existing:
                med_scan = MedicineScan(
                    id=m['id'],
                    user_id=m['user_id'],
                    medicine_name=m['medicine_name'],
                    batch_number=m['batch_number'],
                    qr_verified=bool(m['qr_verified']),
                    packaging_score=m['packaging_score']
                )
                db.add(med_scan)
        db.commit()
        print(f"Synced {len(med_scans)} medicine scan items.")

        print("Data migration to Supabase completed successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error during migration: {e}")
    finally:
        db.close()
        conn.close()

if __name__ == "__main__":
    sync_sqlite_to_supabase()
