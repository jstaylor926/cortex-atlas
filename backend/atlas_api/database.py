"""
Database connection and session management
"""
import sqlite3
from pathlib import Path
from typing import Generator
from contextlib import contextmanager
from .config import settings, get_data_dir


def get_db_path() -> Path:
    """Get the database file path"""
    return Path(settings.database_path)


def init_db():
    """Initialize the database with schema"""
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Read and execute schema
    schema_path = Path(__file__).parent / "db" / "schema.sql"

    if not schema_path.exists():
        print(f"Warning: Schema file not found at {schema_path}")
        # Create basic schema inline for now
        create_basic_schema(db_path)
        return

    with open(schema_path, 'r') as f:
        schema_sql = f.read()

    conn = sqlite3.connect(str(db_path))
    conn.executescript(schema_sql)
    conn.commit()
    conn.close()

    print(f"Database initialized at {db_path}")


def create_basic_schema(db_path: Path):
    """Create a basic schema if schema.sql doesn't exist"""
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create basic tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            tags TEXT,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            data TEXT NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
    """)

    conn.commit()
    conn.close()
    print(f"Basic database schema created at {db_path}")


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Get a database connection context manager"""
    db_path = get_db_path()

    # Ensure database exists
    if not db_path.exists():
        init_db()

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row  # Enable column access by name

    try:
        yield conn
    finally:
        conn.close()


def get_db_connection() -> sqlite3.Connection:
    """Get a database connection (for dependency injection)"""
    db_path = get_db_path()

    if not db_path.exists():
        init_db()

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn
