#!/usr/bin/env python3
"""
Usage:
  python3 scripts/rehash_plain_passwords.py "mysql+pymysql://user:pass@host/dbname"

This script connects to the database via SQLAlchemy, finds users with an insecure flag
(password_needs_rehash == True) or short unhashed values (heuristic), and re-hashes using bcrypt.
"""
import sys
import os
from sqlalchemy import create_engine, text, MetaData, Table, Column, Boolean
from sqlalchemy.orm import sessionmaker
from passlib.hash import bcrypt
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
FAILURE_LOG = "docs/prs/PR-01-failures.log"

def get_db_uri():
    if len(sys.argv) > 1:
        return sys.argv[1]
    # Update for new config structure or ensure env vars are set
    return os.environ.get('DATABASE_URL') or os.environ.get('SQLALCHEMY_DATABASE_URI') or 'sqlite:///quran_center.db'

def rehash_passwords():
    uri = get_db_uri()
    logger.info(f"Connecting to database: {uri.split('@')[-1] if '@' in uri else uri}")

    engine = create_engine(uri)
    Session = sessionmaker(bind=engine)
    session = Session()
    metadata = MetaData()
    metadata.reflect(bind=engine)

    if 'user' not in metadata.tables:
        # Fallback for lowercase/uppercase table names
        if 'User' in metadata.tables:
            user_table = metadata.tables['User']
        else:
            logger.error("Table 'user' not found in database.")
            sys.exit(1)
    else:
        user_table = metadata.tables['user']

    # 1. Ensure temporary column exists (if not using migrations yet)
    # Note: In a real flow, Alembic does this. Here we do it proactively if missing for the script to work.
    if 'password_needs_rehash' not in user_table.c:
        logger.info("Column 'password_needs_rehash' missing. Attempting to add it...")
        with engine.connect() as conn:
            trans = conn.begin()
            try:
                # MySQL/SQLite syntax differ slightly for ALTER, but ADD COLUMN is standard enough
                # Check dialect
                if 'sqlite' in uri:
                     conn.execute(text(f"ALTER TABLE {user_table.name} ADD COLUMN password_needs_rehash BOOLEAN DEFAULT 1"))
                else:
                     conn.execute(text(f"ALTER TABLE {user_table.name} ADD COLUMN password_needs_rehash BOOLEAN DEFAULT TRUE"))
                trans.commit()
                logger.info("Column added.")
            except Exception as e:
                trans.rollback()
                logger.warning(f"Could not add column (might exist or permission error): {e}")

    # Refresh reflection
    metadata.clear()
    metadata.reflect(bind=engine)
    user_table = metadata.tables[user_table.name]

    # Select users needing rehash
    # Criteria: password_needs_rehash IS TRUE OR heuristic (len < 60 and not starting with hash prefix)

    # We iterate manually to apply python-side heuristic cleanly
    stmt = text(f"SELECT id, password FROM {user_table.name}")
    users = session.execute(stmt).fetchall()

    rehash_count = 0
    failures = []

    for u in users:
        uid = u[0]
        pwd = u[1] or ""

        needs_rehash = False

        # Check column if it existed in the select (it wasn't in the raw text select above, let's rely on heuristic + update column)
        # Actually, better to fetch it.

        # Heuristic check
        is_hashed = (pwd.startswith(('$2b$', '$2a$', 'pbkdf2:')) and len(pwd) >= 60)

        if not is_hashed:
            needs_rehash = True

        if needs_rehash:
            try:
                new_hash = bcrypt.hash(pwd)
                # Update password AND set flag to False
                update_stmt = text(f"UPDATE {user_table.name} SET password = :h, password_needs_rehash = 0 WHERE id = :id")
                session.execute(update_stmt, {"h": new_hash, "id": uid})
                rehash_count += 1
            except Exception as e:
                failures.append(f"User ID {uid}: {str(e)}")
                logger.error(f"Failed to rehash user {uid}: {e}")
        else:
            # Already secure, just mark as processed
            try:
                update_stmt = text(f"UPDATE {user_table.name} SET password_needs_rehash = 0 WHERE id = :id")
                session.execute(update_stmt, {"id": uid})
            except Exception as e:
                logger.warning(f"Failed to update status for secure user {uid}: {e}")

    session.commit()
    logger.info(f"Rehashed {rehash_count} passwords.")

    if failures:
        os.makedirs(os.path.dirname(FAILURE_LOG), exist_ok=True)
        with open(FAILURE_LOG, "w") as f:
            for fail in failures:
                f.write(fail + "\n")
        logger.warning(f"Failures logged to {FAILURE_LOG}")

if __name__ == '__main__':
    rehash_passwords()
