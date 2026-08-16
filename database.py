import sqlite3 

DB = "leads.db"

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
                CREATE TABLE IF NOT EXISTS leads(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    company TEXT,
                    web_site_url TEXT,
                    sector TEXT,
                    notes TEXT,
                    score_reasoning TEXT,
                    score NUMERIC CHECK( score >= 1 AND score <= 5),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
                    """)
    conn.commit()
    conn.close()