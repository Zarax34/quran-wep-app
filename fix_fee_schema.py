import sqlite3
import os

# Database path
DB_PATH = 'instance/quran_center.db'

def fix_fee_table():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        print("Starting Fee table migration...")

        # 1. Rename existing table
        cursor.execute("ALTER TABLE fee RENAME TO fee_old")

        # 2. Create new table with nullable date_paid
        # Note: explicit schema definition based on the app.py model
        create_table_sql = """
        CREATE TABLE fee (
            id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            amount FLOAT NOT NULL,
            date_paid DATE,
            status VARCHAR(20),
            title VARCHAR(100),
            notes TEXT,
            PRIMARY KEY (id),
            FOREIGN KEY(student_id) REFERENCES student (id)
        )
        """
        cursor.execute(create_table_sql)

        # 3. Copy data
        # We select columns explicitly to ensure mapping is correct
        cursor.execute("""
            INSERT INTO fee (id, student_id, amount, date_paid, status, title, notes)
            SELECT id, student_id, amount, date_paid, status, title, notes FROM fee_old
        """)

        # 4. Drop old table
        cursor.execute("DROP TABLE fee_old")

        conn.commit()
        print("Successfully migrated Fee table. 'date_paid' is now nullable.")

    except Exception as e:
        conn.rollback()
        print(f"An error occurred: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    fix_fee_table()
