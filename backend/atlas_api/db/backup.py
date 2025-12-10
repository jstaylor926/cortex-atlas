import shutil
from pathlib import Path
from datetime import datetime
import os

from atlas_api.config import settings, get_data_dir
from atlas_api.database import get_db_path

def perform_backup(backup_dir: Path, timestamp: bool = True) -> Path:
    """
    Performs a backup of the main SQLite database file.

    Args:
        backup_dir: The directory where the backup should be stored.
        timestamp: If True, appends a timestamp to the backup filename.

    Returns:
        The path to the created backup file.
    """
    db_path = get_db_path()
    
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found at {db_path}")

    backup_dir.mkdir(parents=True, exist_ok=True)

    if timestamp:
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"atlas_backup_{timestamp_str}.db"
    else:
        backup_filename = "atlas_backup.db"

    backup_path = backup_dir / backup_filename
    shutil.copy2(db_path, backup_path)
    print(f"Database backed up to: {backup_path}")
    return backup_path


def restore_from_backup(backup_path: Path) -> Path:
    """
    Restores the main SQLite database from a specified backup file.

    Args:
        backup_path: The path to the backup file to restore from.

    Returns:
        The path to the restored database file (original location).
    """
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found at {backup_path}")

    db_path = get_db_path()
    
    # Ensure the database directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    shutil.copy2(backup_path, db_path)
    print(f"Database restored from: {backup_path} to {db_path}")
    return db_path


if __name__ == '__main__':
    # Example usage:
    # Set up a dummy data directory for testing
    temp_data_dir = Path("temp_test_data")
    temp_data_dir.mkdir(exist_ok=True)
    temp_db_path = temp_data_dir / "atlas.db"

    # Create a dummy database file
    with sqlite3.connect(temp_db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT)")
        cursor.execute("INSERT INTO test_table (name) VALUES (?)", ("Test entry",))
        conn.commit()
    print(f"Dummy database created at {temp_db_path}")

    # Override settings for this test
    old_db_path = settings.database_path
    settings.database_path = str(temp_db_path)

    try:
        backup_target_dir = get_data_dir() / "backups_test"
        
        print("\nPerforming backup...")
        backup_file = perform_backup(backup_target_dir)
        
        print("\nModifying original DB...")
        with sqlite3.connect(temp_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO test_table (name) VALUES (?)", ("Another entry",))
            conn.commit()
        
        # Verify modification
        with sqlite3.connect(temp_db_path) as conn:
            cursor = conn.cursor()
            rows = cursor.execute("SELECT * FROM test_table").fetchall()
            print(f"Original DB entries after modification: {rows}")

        print("\nRestoring from backup...")
        restore_from_backup(backup_file)

        # Verify restore
        with sqlite3.connect(temp_db_path) as conn:
            cursor = conn.cursor()
            rows = cursor.execute("SELECT * FROM test_table").fetchall()
            print(f"Original DB entries after restore: {rows}")
            assert len(rows) == 1, "Restore failed: Expected 1 entry"
            assert rows[0][1] == "Test entry", "Restore failed: Incorrect data"
        print("Backup and restore test successful!")

    finally:
        # Clean up
        settings.database_path = old_db_path
        if temp_data_dir.exists():
            shutil.rmtree(temp_data_dir)
        if backup_target_dir.exists():
            shutil.rmtree(backup_target_dir)
        print("\nCleaned up temporary test files.")
