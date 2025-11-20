import sqlite3
import os

def check_db(path):
    if not os.path.exists(path):
        print(f"Database not found at: {path}")
        return

    print(f"Checking database: {path}")
    try:
        conn = sqlite3.connect(path)
        cursor = conn.cursor()

        # Check report table
        try:
            cursor.execute("PRAGMA table_info(report)")
            columns = cursor.fetchall()
            col_names = [c[1] for c in columns]
            print(f"Columns in 'report': {col_names}")
            if 'status' in col_names:
                print(" - 'status' column EXISTS in 'report'.")
            else:
                print(" - 'status' column MISSING in 'report'.")
        except Exception as e:
            print(f"Error checking report table: {e}")

        # Check holiday table
        try:
            cursor.execute("PRAGMA table_info(holiday)")
            columns = cursor.fetchall()
            col_names = [c[1] for c in columns]
            print(f"Columns in 'holiday': {col_names}")
            if 'status' in col_names:
                print(" - 'status' column EXISTS in 'holiday'.")
            else:
                print(" - 'status' column MISSING in 'holiday'.")
        except Exception as e:
            print(f"Error checking holiday table: {e}")

        conn.close()
    except Exception as e:
        print(f"Failed to connect to {path}: {e}")

print("--- Checking Root DB ---")
check_db("quran_center.db")

print("\n--- Checking Instance DB ---")
check_db("instance/quran_center.db")
