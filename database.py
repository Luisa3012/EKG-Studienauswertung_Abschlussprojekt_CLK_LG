import sqlite3
import json
import os
from datetime import datetime

DB_PATH = "data/ekg_study.db"
JSON_PATH = "data/person_db.json"


class DatabaseManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role     TEXT NOT NULL,
                person_id INTEGER
            );
            CREATE TABLE IF NOT EXISTS persons (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                firstname     TEXT NOT NULL,
                lastname      TEXT NOT NULL,
                date_of_birth INTEGER,
                email         TEXT,
                gender        TEXT,
                picture_path  TEXT DEFAULT 'data/pictures/none.jpg',
                weight        REAL,
                fitness_level TEXT,
                status        TEXT DEFAULT 'pending',
                created_at    TEXT
            );
            CREATE TABLE IF NOT EXISTS tests (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id   INTEGER NOT NULL,
                date        TEXT NOT NULL,
                result_link TEXT NOT NULL,
                notes       TEXT,
                FOREIGN KEY (person_id) REFERENCES persons(id)
            );
        """)
        conn.commit()
        conn.close()
        self._migrate_from_json_if_needed()

    def _migrate_from_json_if_needed(self):
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users")
        already_seeded = c.fetchone()[0] > 0
        conn.close()
        if already_seeded:
            return

        # Seed Studienleiter
        self._insert_user("leiter", "abcd", "leiter", None)

        if not os.path.exists(JSON_PATH):
            return

        with open(JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        conn = self._get_conn()
        c = conn.cursor()
        now = datetime.now().isoformat()
        for p in data:
            c.execute("""
                INSERT INTO persons
                    (id, firstname, lastname, date_of_birth, email, gender, picture_path, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                p["id"], p["firstname"], p["lastname"], p["date_of_birth"],
                p.get("email"), p.get("gender"),
                p.get("picture_path", "data/pictures/none.jpg"),
                p.get("status", "pending"), now,
            ))
            for t in p.get("ekg_tests", []):
                c.execute("""
                    INSERT INTO tests (id, person_id, date, result_link)
                    VALUES (?, ?, ?, ?)
                """, (t["id"], p["id"], t["date"], t["result_link"]))
        conn.commit()
        conn.close()

        # Bestehenden Test-Proband übernehmen
        self._insert_user("proband1", "1234", "proband", 1)

    def _insert_user(self, username, password, role, person_id):
        try:
            conn = self._get_conn()
            conn.execute(
                "INSERT INTO users (username, password, role, person_id) VALUES (?, ?, ?, ?)",
                (username, password, role, person_id),
            )
            conn.commit()
            conn.close()
        except sqlite3.IntegrityError:
            pass

    # ------------------------------------------------------------------ Auth

    def get_user_by_credentials(self, username, password):
        from log_in import User
        conn = self._get_conn()
        c = conn.cursor()
        c.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password),
        )
        row = c.fetchone()
        conn.close()
        if row is None:
            return None
        return User(row["username"], row["password"], row["role"], row["person_id"])

    def add_user(self, username, password, role, person_id=None):
        self._insert_user(username, password, role, person_id)

    def username_exists(self, username):
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("SELECT 1 FROM users WHERE username = ?", (username,))
        result = c.fetchone()
        conn.close()
        return result is not None

    # ---------------------------------------------------------------- Persons

    def _row_to_person(self, row):
        from person import Person
        return Person(
            id=row["id"],
            date_of_birth=row["date_of_birth"],
            firstname=row["firstname"],
            lastname=row["lastname"],
            picture_path=row["picture_path"],
            gender=row["gender"],
            email=row["email"],
            status=row["status"],
            weight=row["weight"],
            fitness_level=row["fitness_level"],
        )

    def get_all_persons(self):
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM persons ORDER BY id").fetchall()
        conn.close()
        return [self._row_to_person(r) for r in rows]

    def get_person_by_id(self, person_id):
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM persons WHERE id = ?", (person_id,)).fetchone()
        conn.close()
        return self._row_to_person(row) if row else None

    def get_pending_persons(self):
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM persons WHERE status = 'pending' ORDER BY id"
        ).fetchall()
        conn.close()
        return [self._row_to_person(r) for r in rows]

    def add_person(self, firstname, lastname, date_of_birth, email, gender,
                   picture_path="data/pictures/none.jpg",
                   weight=None, fitness_level=None, status="pending"):
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("""
            INSERT INTO persons
                (firstname, lastname, date_of_birth, email, gender, picture_path, weight, fitness_level, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (firstname, lastname, date_of_birth, email, gender, picture_path,
              weight, fitness_level, status, datetime.now().isoformat()))
        new_id = c.lastrowid
        conn.commit()
        conn.close()
        return new_id

    def update_person_name(self, person_id, firstname, lastname):
        """Aktualisiert Vor- und Nachname einer Person (z.B. nach Heirat)."""
        conn = self._get_conn()
        conn.execute(
            "UPDATE persons SET firstname = ?, lastname = ? WHERE id = ?",
            (firstname, lastname, person_id),
        )
        conn.commit()
        conn.close()

    def update_person(self, person_id, firstname, lastname, date_of_birth,
                      email, gender, weight, fitness_level, picture_path=None):
        """Aktualisiert alle editierbaren Felder einer Person.

        Args:
            person_id: ID der zu aktualisierenden Person.
            firstname: Vorname.
            lastname: Nachname.
            date_of_birth: Geburtsjahr (int).
            email: E-Mail-Adresse.
            gender: Geschlecht ('Male', 'Female', 'Divers').
            weight: Körpergewicht in kg.
            fitness_level: Sportlicher Zustand.
            picture_path: Pfad zum Profilbild (None = unveränderter Wert).
        """
        conn = self._get_conn()
        if picture_path is not None:
            conn.execute("""
                UPDATE persons
                SET firstname=?, lastname=?, date_of_birth=?, email=?,
                    gender=?, weight=?, fitness_level=?, picture_path=?
                WHERE id=?
            """, (firstname, lastname, date_of_birth, email,
                  gender, weight, fitness_level, picture_path, person_id))
        else:
            conn.execute("""
                UPDATE persons
                SET firstname=?, lastname=?, date_of_birth=?, email=?,
                    gender=?, weight=?, fitness_level=?
                WHERE id=?
            """, (firstname, lastname, date_of_birth, email,
                  gender, weight, fitness_level, person_id))
        conn.commit()
        conn.close()

    def approve_person(self, person_id):
        conn = self._get_conn()
        conn.execute("UPDATE persons SET status = 'approved' WHERE id = ?", (person_id,))
        conn.commit()
        conn.close()

    def reject_person(self, person_id):
        conn = self._get_conn()
        conn.execute("UPDATE persons SET status = 'rejected' WHERE id = ?", (person_id,))
        conn.commit()
        conn.close()

    def delete_person(self, person_id):
        """Löscht eine Person samt allen Tests und User-Account."""
        conn = self._get_conn()
        conn.execute("DELETE FROM tests WHERE person_id = ?", (person_id,))
        conn.execute("DELETE FROM users WHERE person_id = ?", (person_id,))
        conn.execute("DELETE FROM persons WHERE id = ?", (person_id,))
        conn.commit()
        conn.close()

    def delete_test(self, test_id):
        """Löscht einen einzelnen Test."""
        conn = self._get_conn()
        conn.execute("DELETE FROM tests WHERE id = ?", (test_id,))
        conn.commit()
        conn.close()

    # ------------------------------------------------------------------ Tests

    def _row_to_test(self, row):
        from test import Test
        return Test(
            test_id=row["id"],
            person_id=row["person_id"],
            date=row["date"],
            result_link=row["result_link"],
        )

    def get_all_tests(self):
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM tests ORDER BY id").fetchall()
        conn.close()
        return [self._row_to_test(r) for r in rows]

    def get_tests_by_person(self, person_id):
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM tests WHERE person_id = ? ORDER BY id", (person_id,)
        ).fetchall()
        conn.close()
        return [self._row_to_test(r) for r in rows]

    def get_test_by_id(self, test_id):
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM tests WHERE id = ?", (test_id,)).fetchone()
        conn.close()
        return self._row_to_test(row) if row else None

    def add_test(self, person_id, date, result_link, notes=None):
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("""
            INSERT INTO tests (person_id, date, result_link, notes)
            VALUES (?, ?, ?, ?)
        """, (person_id, date, result_link, notes))
        new_id = c.lastrowid
        conn.commit()
        conn.close()
        return new_id

    # ----------------------------------------------------------- Statistiken

    def get_total_persons(self):
        conn = self._get_conn()
        count = conn.execute("SELECT COUNT(*) FROM persons").fetchone()[0]
        conn.close()
        return count

    def get_total_tests(self):
        conn = self._get_conn()
        count = conn.execute("SELECT COUNT(*) FROM tests").fetchone()[0]
        conn.close()
        return count

    def get_average_hr_all_tests(self):
        tests = self.get_all_tests()
        values = [t.avg_hr() for t in tests if t.avg_hr() is not None]
        return sum(values) / len(values) if values else None
