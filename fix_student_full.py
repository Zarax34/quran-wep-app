
import sqlite3

def fix_student_schema_full():
    conn = sqlite3.connect('instance/quran_center.db')
    cursor = conn.cursor()

    # Check for all columns in Student model
    expected_columns = {
        'student_phone': 'VARCHAR(20)',
        'parent_phone': 'VARCHAR(20)',
        'parent_id': 'INTEGER',
        'circle_id': 'INTEGER',
        'is_active': 'BOOLEAN',
        'photo': 'VARCHAR(200)',
        'academic_year': "VARCHAR(10) DEFAULT '2025'",
        'pending_approval': 'BOOLEAN DEFAULT 1',
        'last_recitation_date': 'DATE',
        'total_verses_since_year_start': 'INTEGER DEFAULT 0',
        'current_address': 'VARCHAR(200)',
        'previous_address': 'VARCHAR(200)',
        'governorate': 'VARCHAR(100)',
        'date_of_birth': 'DATE',
        'previous_memorization': 'VARCHAR(200)',
        'enrollment_date': 'DATE',
        'last_memorized_sura': "VARCHAR(100) DEFAULT 'الفاتحة'",
        'last_memorized_ayah': 'INTEGER DEFAULT 0',
        'memorization_direction': "VARCHAR(50) DEFAULT 'BaqarahToNas'",
    }

    cursor.execute("PRAGMA table_info(student)")
    existing_columns = {col[1] for col in cursor.fetchall()}

    for col, dtype in expected_columns.items():
        if col not in existing_columns:
            print(f"Adding missing column: {col}")
            try:
                cursor.execute(f"ALTER TABLE student ADD COLUMN {col} {dtype}")
            except Exception as e:
                print(f"Error adding {col}: {e}")

    conn.commit()
    conn.close()
    print("Student table schema check complete.")

if __name__ == "__main__":
    fix_student_schema_full()
