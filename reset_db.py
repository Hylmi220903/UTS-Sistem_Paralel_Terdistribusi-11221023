"""
Quick script untuk reset database
Run: python reset_db.py
"""
import sqlite3
import os

db_path = "data/dedup_store.db"

def reset_database():
    """Reset database dengan menghapus semua events"""
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        print("   Database akan dibuat otomatis saat server dijalankan.")
        return
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get count before delete
        cursor.execute("SELECT COUNT(*) FROM events")
        count_before = cursor.fetchone()[0]
        
        # Delete all events
        cursor.execute("DELETE FROM events")
        conn.commit()
        
        # Verify deletion
        cursor.execute("SELECT COUNT(*) FROM events")
        count_after = cursor.fetchone()[0]
        
        conn.close()
        
        print("✅ Database reset successfully!")
        print(f"   Events deleted: {count_before}")
        print(f"   Events remaining: {count_after}")
        print(f"   Database: {db_path}")
        
    except Exception as e:
        print(f"❌ Error resetting database: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("DATABASE RESET TOOL")
    print("=" * 50)
    reset_database()
    print("=" * 50)
    print("\nTip: Restart server untuk melihat perubahan")
    print("     (.venv\\Scripts\\python.exe -m uvicorn src.main:app --host 0.0.0.0 --port 8080)")
