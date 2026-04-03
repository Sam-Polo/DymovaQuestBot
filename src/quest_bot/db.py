import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from quest_bot.time_util import msk_date_str, utc_iso_now

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    tg_user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    first_started_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS question_threads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    psych_chat_id INTEGER NOT NULL,
    psych_message_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    user_message_id INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    question_msk_date TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(psych_chat_id, psych_message_id)
);

CREATE INDEX IF NOT EXISTS idx_q_threads_user_msk
ON question_threads(user_id, question_msk_date);
""".strip()


@dataclass(frozen=True)
class QuestionThread:
    user_id: int
    user_message_id: int
    question_text: str


@dataclass(frozen=True)
class UserRow:
    tg_user_id: int
    username: str | None
    first_name: str | None
    questions_total: int


class Database:
    def __init__(self, path: str) -> None:
        self._path = path

    def init(self) -> None:
        Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(SCHEMA)
            conn.commit()

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self._path, timeout=30)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA foreign_keys = ON;")
            yield conn
        finally:
            conn.close()

    def upsert_user_start(self, tg_user_id: int, username: str | None, first_name: str | None) -> None:
        now = utc_iso_now()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO users (tg_user_id, username, first_name, first_started_at, last_seen_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(tg_user_id) DO UPDATE SET
                    username = excluded.username,
                    first_name = excluded.first_name,
                    last_seen_at = excluded.last_seen_at
                """,
                (tg_user_id, username, first_name, now, now),
            )
            conn.commit()

    def touch_user(self, tg_user_id: int, username: str | None, first_name: str | None) -> None:
        now = utc_iso_now()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE users SET username = ?, first_name = ?, last_seen_at = ?
                WHERE tg_user_id = ?
                """,
                (username, first_name, now, tg_user_id),
            )
            conn.commit()

    def has_started(self, tg_user_id: int) -> bool:
        with self._connect() as conn:
            cur = conn.execute("SELECT 1 FROM users WHERE tg_user_id = ? LIMIT 1", (tg_user_id,))
            return cur.fetchone() is not None

    def count_questions_today_msk(self, user_id: int) -> int:
        day = msk_date_str()
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT COUNT(*) AS c FROM question_threads WHERE user_id = ? AND question_msk_date = ?",
                (user_id, day),
            )
            row = cur.fetchone()
            return int(row["c"]) if row else 0

    def insert_question_thread(
        self,
        *,
        psych_chat_id: int,
        psych_message_id: int,
        user_id: int,
        user_message_id: int,
        question_text: str,
    ) -> None:
        day = msk_date_str()
        now = utc_iso_now()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO question_threads
                (psych_chat_id, psych_message_id, user_id, user_message_id, question_text,
                 question_msk_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    psych_chat_id,
                    psych_message_id,
                    user_id,
                    user_message_id,
                    question_text,
                    day,
                    now,
                ),
            )
            conn.commit()

    def get_thread_by_psych_message(self, psych_chat_id: int, psych_message_id: int) -> QuestionThread | None:
        with self._connect() as conn:
            cur = conn.execute(
                """
                SELECT user_id, user_message_id, question_text
                FROM question_threads
                WHERE psych_chat_id = ? AND psych_message_id = ?
                """,
                (psych_chat_id, psych_message_id),
            )
            row = cur.fetchone()
            if not row:
                return None
            return QuestionThread(
                user_id=int(row["user_id"]),
                user_message_id=int(row["user_message_id"]),
                question_text=str(row["question_text"]),
            )

    def stats(self) -> dict[str, int]:
        with self._connect() as conn:
            users = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
            questions = conn.execute("SELECT COUNT(*) AS c FROM question_threads").fetchone()["c"]
        return {"users": int(users), "questions": int(questions)}

    def list_users_with_counts(self) -> list[UserRow]:
        with self._connect() as conn:
            cur = conn.execute(
                """
                SELECT u.tg_user_id, u.username, u.first_name,
                       COALESCE(COUNT(q.id), 0) AS qc
                FROM users u
                LEFT JOIN question_threads q ON q.user_id = u.tg_user_id
                GROUP BY u.tg_user_id
                ORDER BY u.tg_user_id
                """
            )
            rows = []
            for r in cur.fetchall():
                rows.append(
                    UserRow(
                        tg_user_id=int(r["tg_user_id"]),
                        username=r["username"],
                        first_name=r["first_name"],
                        questions_total=int(r["qc"]),
                    )
                )
            return rows
