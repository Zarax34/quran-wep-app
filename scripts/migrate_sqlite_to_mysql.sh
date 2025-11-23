#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/migrate_sqlite_to_mysql.sh /path/to/quran_center.db "mysql+pymysql://user:pass@host/dbname"
SQLITE_DB_PATH="${1:-quran_center.db}"
MYSQL_URI="${2:-}"
TMP_SQL_DUMP="./tmp_sql_dump.sql"

if [ -z "$MYSQL_URI" ]; then
  echo "Usage: $0 /path/to/quran_center.db \"mysql+pymysql://user:pass@host/dbname\""
  exit 2
fi

echo "[1/6] Dumping SQLite schema+data to SQL..."
sqlite3 "$SQLITE_DB_PATH" .dump > "$TMP_SQL_DUMP"

echo "[2/6] Sanitizing dump for MySQL compatibility..."
# Basic replacements: remove sqlite_sequence, replace AUTOINCREMENT, tweak types
sed -E -e 's/BEGIN TRANSACTION;//g' \
  -e 's/COMMIT;//g' \
  -e 's/AUTOINCREMENT/ /g' \
  -e 's/INTEGER PRIMARY KEY/INTEGER PRIMARY KEY AUTO_INCREMENT/g' \
  "$TMP_SQL_DUMP" > "${TMP_SQL_DUMP}.mysql"

echo "[3/6] Creating MySQL schema and importing data..."
# Use mysql client to execute. MYSQL_URI must be in format user:pass@host/dbname
# Parse MYSQL_URI
# Example: mysql -u user -p'pass' -h host dbname < file.sql
python3 - <<PY
import sys, urllib.parse as u
uri = "$MYSQL_URI"
# Expect formats like mysql+pymysql://user:pass@host:3306/dbname
if "@" not in uri:
    print("Unsupported MYSQL_URI format:", uri)
    sys.exit(1)
# crude parse:
parsed = u.urlparse(uri)
user = parsed.username
passwd = parsed.password
host = parsed.hostname or "localhost"
port = parsed.port or 3306
dbname = parsed.path.lstrip('/')
print("Parsed MySQL connection:", user, "@", host, ":", port, "/", dbname)
PY

# Convert to mysql client command (assumes mysql client installed)
MYSQL_USER="$(python3 -c "import urllib.parse as u; print(u.urlparse('$MYSQL_URI').username)")"
MYSQL_PASS="$(python3 -c "import urllib.parse as u; print(u.urlparse('$MYSQL_URI').password)")"
MYSQL_HOST="$(python3 -c "import urllib.parse as u; print(u.urlparse('$MYSQL_URI').hostname or 'localhost')")"
MYSQL_PORT="$(python3 -c "import urllib.parse as u; print(u.urlparse('$MYSQL_URI').port or 3306)")"
MYSQL_DB="$(python3 -c "import urllib.parse as u; print(u.urlparse('$MYSQL_URI').path.lstrip('/'))")"

mysql -u"$MYSQL_USER" -p"$MYSQL_PASS" -h"$MYSQL_HOST" -P"$MYSQL_PORT" "$MYSQL_DB" < "${TMP_SQL_DUMP}.mysql"

echo "[4/6] Running SQLAlchemy/Flask-Migrate migrations (if present)..."
# Attempt to run flask db upgrade if app exposes manage script
if [ -f "./manage.py" ]; then
  echo "Running flask db upgrade via manage.py"
  ./manage.py db upgrade || true
fi

echo "[5/6] Post-import: ensure integrity and rehash plain passwords if needed..."
python3 scripts/rehash_plain_passwords.py "$MYSQL_URI" || true

echo "[6/6] Cleanup temporary files..."
rm -f "$TMP_SQL_DUMP" "${TMP_SQL_DUMP}.mysql"

echo "Migration finished. Verify application against MySQL."
