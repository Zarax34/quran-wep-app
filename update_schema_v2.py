import sqlite3
import os

def update_schema():
    db_path = 'instance/quran_center.db'

    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print(f"Connected to database: {db_path}")

    # 1. Add status to holiday table
    try:
        cursor.execute("ALTER TABLE holiday ADD COLUMN status VARCHAR(20) DEFAULT 'Approved'")
        print("Added 'status' column to 'holiday' table.")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e):
            print("'status' column already exists in 'holiday' table.")
        else:
            print(f"Error adding 'status' to 'holiday': {e}")

    # 2. Add status to report table
    try:
        cursor.execute("ALTER TABLE report ADD COLUMN status VARCHAR(20) DEFAULT 'Pending'")
        print("Added 'status' column to 'report' table.")

        # Update existing reports to 'Approved' so they don't disappear
        cursor.execute("UPDATE report SET status = 'Approved'")
        print("Updated existing reports to 'Approved'.")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e):
            print("'status' column already exists in 'report' table.")
        else:
            print(f"Error adding 'status' to 'report': {e}")

    conn.commit()
    conn.close()
    print("Schema update completed.")

if __name__ == '__main__':
    update_schema()
