import os, sqlite3


class SQLiteProvider:
    def __init__(self, db_name: str, directory_path: str = "data"):
        if not db_name.endswith(".db"):
            db_name += ".db"

        self.directory_path = directory_path
        self.db_path = os.path.join(directory_path, db_name)

        os.makedirs(self.directory_path, exist_ok=True)

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        return conn
