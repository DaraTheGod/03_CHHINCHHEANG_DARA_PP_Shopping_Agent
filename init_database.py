"""Create the local SQLite catalog from the schema and seed SQL files."""

from database import DATABASE_PATH, initialize_database


if __name__ == "__main__":
    initialize_database()
    print(f"Database ready: {DATABASE_PATH}")