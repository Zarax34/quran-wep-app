import pytest
import sqlite3
import os
from passlib.hash import bcrypt
from unittest.mock import patch, MagicMock

# We need to test the logic of rehash_plain_passwords.py.
# Since it's a script, we can import its functions or run it as a subprocess.
# Importing is cleaner if we refactor, but for now subprocess is safer given the script structure.
# Alternatively, we can replicate the logic test.

def test_dump_sqlite_py_sanitization(tmp_path):
    """
    Test that dump_sqlite_py.py correctly sanitizes output for MySQL.
    """
    # Setup SQLite DB
    db_path = tmp_path / "test.db"
    dump_path = tmp_path / "dump.sql"

    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)")
    conn.execute("INSERT INTO test (name) VALUES ('foo'), ('bar')")
    conn.commit()
    conn.close()

    # Run script
    import subprocess
    subprocess.check_call(["python3", "scripts/dump_sqlite_py.py", str(db_path), str(dump_path)])

    # Check output
    with open(dump_path, 'r') as f:
        content = f.read()

    assert "AUTO_INCREMENT" in content
    assert "AUTOINCREMENT" not in content
    assert "INSERT INTO `test` VALUES" in content
    # Depending on quoting, check basic string existence
    assert "'foo'" in content

def test_rehash_logic_integration(tmp_path):
    """
    Test that rehash_plain_passwords.py:
    1. Adds the column.
    2. Hashes plain passwords.
    3. Updates status for already hashed passwords.
    """
    db_path = tmp_path / "rehash_test.db"
    # Create a DB with users: 1 plain, 1 hashed
    conn = sqlite3.connect(db_path)
    hashed_pw = bcrypt.hash("secret")
    conn.execute("CREATE TABLE user (id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT, name TEXT, is_active BOOLEAN)")
    conn.execute("INSERT INTO user (username, password) VALUES ('plain', 'plain123')")
    conn.execute(f"INSERT INTO user (username, password) VALUES ('hashed', '{hashed_pw}')")
    conn.commit()
    conn.close()

    # Run Script
    import subprocess
    # We need to ensure the script can find requirements (sqlalchemy, passlib)
    env = os.environ.copy()
    # Using sqlite URL
    db_url = f"sqlite:///{db_path}"

    subprocess.check_call(["python3", "scripts/rehash_plain_passwords.py", db_url], env=env)

    # Verify
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM user").fetchall()
    conn.close()

    plain_user = next(r for r in rows if r['username'] == 'plain')
    hashed_user = next(r for r in rows if r['username'] == 'hashed')

    # 1. Check column existence (implied by select *)
    assert 'password_needs_rehash' in plain_user.keys()

    # 2. Check plain user rehashed
    assert plain_user['password'].startswith('$2')
    assert plain_user['password'] != 'plain123'
    assert plain_user['password_needs_rehash'] == 0 # False in SQLite is 0

    # 3. Check hashed user untouched but marked processed
    assert hashed_user['password'] == hashed_pw
    assert hashed_user['password_needs_rehash'] == 0
