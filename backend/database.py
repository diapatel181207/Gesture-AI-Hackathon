import sqlite3

class DatabaseManager:
    def __init__(self, db_path="gestures.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('DROP TABLE IF EXISTS gestures')
            cursor.execute('''
                CREATE TABLE gestures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    action TEXT,
                    shortcut TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            defaults = [
                ('Open Palm',       'none',          ''),
                ('Closed Fist',     'play_pause',    ''),
                ('Pointing Finger', 'cursor_move',   ''),
                ('Pinch',           'left_click',    ''),
                ('Victory Sign',    'next_slide',    ''),
                ('Thumbs Up',       'volume_up',     ''),
                ('Thumbs Down',     'volume_down',   ''),
                ('Three Fingers',   'open_chrome',   ''),
                ('Rock Sign',       'mute',          ''),
            ]
            cursor.executemany(
                "INSERT INTO gestures (name, action, shortcut) VALUES (?, ?, ?)",
                defaults
            )

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    gesture_name TEXT,
                    action_executed TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            conn.commit()

    def get_mappings(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, action, shortcut FROM gestures")
            return {
                row[0]: {'action': row[1], 'shortcut': row[2]}
                for row in cursor.fetchall()
            }

    def update_mapping(self, gesture_name, action, shortcut=''):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO gestures (name, action, shortcut) VALUES (?, ?, ?) "
                "ON CONFLICT(name) DO UPDATE SET action=excluded.action, shortcut=excluded.shortcut",
                (gesture_name, action, shortcut)
            )
            conn.commit()

    def log_history(self, gesture, action):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO history (gesture_name, action_executed) VALUES (?, ?)",
                (gesture, action)
            )
            conn.commit()

    def get_setting(self, key, default=None):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else default

    def set_setting(self, key, value):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, str(value))
            )
            conn.commit()

    def get_history(self, limit=50):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT gesture_name, action_executed, timestamp FROM history ORDER BY id DESC LIMIT ?",
                (limit,)
            )
            return [
                {"gesture": r[0], "action": r[1], "time": r[2]}
                for r in cursor.fetchall()
            ]
