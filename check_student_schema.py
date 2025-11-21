import sqlite3

def check_schema():
    conn = sqlite3.connect('instance/quran_center.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(student)")
    columns = cursor.fetchall()
    print("Columns in student table:")
    for col in columns:
        print(col)

    # Check specifically for 'age'
    has_age = any(c[1] == 'age' for c in columns)
    if not has_age:
        print("\n'age' column is MISSING in student table!")
        try:
             cursor.execute("ALTER TABLE student ADD COLUMN age INTEGER")
             print("Added 'age' column to student table.")
             conn.commit()
        except Exception as e:
             print(f"Failed to add age column: {e}")
    else:
        print("\n'age' column exists.")

    conn.close()

if __name__ == "__main__":
    check_schema()
