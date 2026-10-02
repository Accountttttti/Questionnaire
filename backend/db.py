import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "questionnaire.db"

SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        token TEXT,
        avatar TEXT DEFAULT '',
        email TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS questionnaires (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        type TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT DEFAULT '',
        status TEXT NOT NULL DEFAULT 'draft',
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now')),
        published_at TEXT,
        full_score INTEGER,
        result_mode TEXT NOT NULL DEFAULT 'score'
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        questionnaire_id INTEGER NOT NULL,
        type TEXT NOT NULL,
        title TEXT NOT NULL,
        order_index INTEGER NOT NULL DEFAULT 0,
        score INTEGER NOT NULL DEFAULT 0,
        answer TEXT DEFAULT ''
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS options (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER NOT NULL,
        text TEXT NOT NULL,
        score INTEGER NOT NULL DEFAULT 0,
        order_index INTEGER NOT NULL DEFAULT 0,
        is_correct INTEGER NOT NULL DEFAULT 0,
        jump_to TEXT NOT NULL DEFAULT ''
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS result_cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        questionnaire_id INTEGER NOT NULL,
        min_score INTEGER NOT NULL,
        max_score INTEGER NOT NULL,
        text TEXT NOT NULL,
        order_index INTEGER NOT NULL DEFAULT 0,
        label TEXT NOT NULL DEFAULT ''
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS user_actions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        questionnaire_id INTEGER NOT NULL,
        action TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now')),
        UNIQUE(user_id, questionnaire_id, action)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS responses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        questionnaire_id INTEGER NOT NULL,
        user_id INTEGER,
        answers TEXT NOT NULL,
        total_score INTEGER NOT NULL,
        result_text TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS email_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        email TEXT NOT NULL,
        code TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now'))
    )
    """,
]


def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=20000")
    return conn


def init_db():
    conn = get_db()
    conn.execute("PRAGMA journal_mode=WAL")
    for stmt in SCHEMA:
        conn.execute(stmt)
    cols = [r["name"] for r in conn.execute("PRAGMA table_info(questionnaires)").fetchall()]
    if "description" not in cols:
        conn.execute("ALTER TABLE questionnaires ADD COLUMN description TEXT DEFAULT ''")
    if "published_at" not in cols:
        conn.execute("ALTER TABLE questionnaires ADD COLUMN published_at TEXT")
    if "full_score" not in cols:
        conn.execute("ALTER TABLE questionnaires ADD COLUMN full_score INTEGER")
    if "result_mode" not in cols:
        conn.execute("ALTER TABLE questionnaires ADD COLUMN result_mode TEXT NOT NULL DEFAULT 'score'")

    qcols = [r["name"] for r in conn.execute("PRAGMA table_info(questions)").fetchall()]
    if "score" not in qcols:
        conn.execute("ALTER TABLE questions ADD COLUMN score INTEGER NOT NULL DEFAULT 0")
    if "answer" not in qcols:
        conn.execute("ALTER TABLE questions ADD COLUMN answer TEXT DEFAULT ''")

    ocols = [r["name"] for r in conn.execute("PRAGMA table_info(options)").fetchall()]
    if "is_correct" not in ocols:
        conn.execute("ALTER TABLE options ADD COLUMN is_correct INTEGER NOT NULL DEFAULT 0")
    if "jump_to" not in ocols:
        conn.execute("ALTER TABLE options ADD COLUMN jump_to TEXT NOT NULL DEFAULT ''")

    rcols = [r["name"] for r in conn.execute("PRAGMA table_info(result_cards)").fetchall()]
    if "label" not in rcols:
        conn.execute("ALTER TABLE result_cards ADD COLUMN label TEXT NOT NULL DEFAULT ''")
    conn.execute(
        "UPDATE questionnaires SET published_at = updated_at "
        "WHERE status = 'published' AND published_at IS NULL"
    )
    conn.commit()
    conn.close()
