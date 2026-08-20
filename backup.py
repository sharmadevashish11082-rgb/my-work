"""Back up / restore the Expense Tracker data (expenses.db + receipts/).

Pure standard library - no third-party packages needed.

Usage:
    python backup.py                  # create backup_YYYYMMDD_HHMMSS.zip
    python backup.py out.zip          # create a backup at a specific path
    python backup.py --restore x.zip  # restore from a backup (asks first)

Best practice: close the app before restoring, and keep the zip somewhere
safe (not inside the receipts folder).
"""

import os
import sys
import zipfile
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "expenses.db")
RECEIPTS_DIR = os.path.join(BASE_DIR, "receipts")


def create_backup(dest):
    count = 0
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        if os.path.exists(DB_PATH):
            z.write(DB_PATH, "expenses.db")
            count += 1
        if os.path.isdir(RECEIPTS_DIR):
            for root, _dirs, files in os.walk(RECEIPTS_DIR):
                for name in files:
                    full = os.path.join(root, name)
                    arc = os.path.relpath(full, BASE_DIR)
                    z.write(full, arc)
                    count += 1
    print(f"Backed up {count} file(s) to {dest}")
    return count


def restore(zip_path):
    if not os.path.exists(zip_path):
        print(f"Backup not found: {zip_path}")
        return False
    answer = input("Restore overwrites the current database and receipts. "
                   "Continue? [y/N] ").strip().lower()
    if answer != "y":
        print("Cancelled.")
        return False
    with zipfile.ZipFile(zip_path) as z:
        names = z.namelist()
        for name in names:
            normalized = name.replace("\\", "/")
            if normalized.startswith("/") or ".." in normalized.split("/"):
                raise SystemExit(f"Unsafe path in backup: {name}")
        z.extractall(BASE_DIR)
    print(f"Restored {len(names)} file(s) from {zip_path}.")
    print("Restart the app to see the restored data.")
    return True


def main():
    args = sys.argv[1:]
    if args and args[0] == "--restore":
        if len(args) != 2:
            print("Usage: python backup.py --restore <backup.zip>")
            return
        restore(args[1])
        return
    dest = (args[0] if args else
            os.path.join(BASE_DIR, f"backup_{datetime.now():%Y%m%d_%H%M%S}.zip"))
    create_backup(dest)


if __name__ == "__main__":
    main()
