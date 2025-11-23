-- Migration to add password_needs_rehash column
-- This is run automatically by scripts/rehash_plain_passwords.py if missing,
-- but provided here for manual execution or record keeping.

-- MySQL
ALTER TABLE user ADD COLUMN password_needs_rehash BOOLEAN DEFAULT TRUE;

-- SQLite (if needed)
-- ALTER TABLE user ADD COLUMN password_needs_rehash BOOLEAN DEFAULT 1;
