import sqlite3
import os
import datetime
from pathlib import Path

DB_PATH = os.path.expanduser("~/.safeexec.db")

def init_db(db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS command_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            command TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            risk_level TEXT,
            category TEXT,
            user_decision TEXT,
            cwd TEXT
        )
    ''')
    conn.commit()
    conn.close()

def log_command(command: str, risk_level: str, category: str, user_decision: str, cwd: str, db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO command_logs (command, risk_level, category, user_decision, cwd)
        VALUES (?, ?, ?, ?, ?)
    ''', (command, risk_level, category, user_decision, cwd))
    conn.commit()
    conn.close()

def get_stats(db_path: str = DB_PATH, for_date: str = None) -> dict:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    date_filter = ""
    params = ()
    if for_date:
        date_filter = "WHERE date(timestamp) = ?"
        params = (for_date,)
    
    cursor.execute(f'SELECT COUNT(*) FROM command_logs {date_filter}', params)
    total = cursor.fetchone()[0]
    
    where_blocked = "user_decision = 'abort' OR user_decision = 'hard_block'"
    where_blocked = f"({where_blocked}) AND date(timestamp) = ?" if for_date else where_blocked
    cursor.execute(f"SELECT COUNT(*) FROM command_logs WHERE {where_blocked}", params)
    blocked = cursor.fetchone()[0]
    
    where_edited = "user_decision = 'edit'"
    where_edited = f"{where_edited} AND date(timestamp) = ?" if for_date else where_edited
    cursor.execute(f"SELECT COUNT(*) FROM command_logs WHERE {where_edited}", params)
    edited = cursor.fetchone()[0]
    
    where_proceeded = "user_decision = 'proceed'"
    where_proceeded = f"{where_proceeded} AND date(timestamp) = ?" if for_date else where_proceeded
    cursor.execute(f"SELECT COUNT(*) FROM command_logs WHERE {where_proceeded}", params)
    proceeded = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "total_intercepted": total,
        "blocked": blocked,
        "edited": edited,
        "proceeded": proceeded
    }

if __name__ == "__main__":
    test_db = "test_safeexec.db"
    if os.path.exists(test_db):
        os.remove(test_db)
        
    init_db(test_db)
    log_command("rm -rf /", "CRITICAL", "DESTRUCTIVE", "hard_block", "/", test_db)
    log_command("rm -rf /var/log/app", "HIGH", "DESTRUCTIVE", "abort", "/var/log", test_db)
    log_command("chmod -R 777 /var/www", "HIGH", "PRIVILEGE_ESCALATION", "edit", "/home/user", test_db)
    log_command("git push --force", "MEDIUM", "IRREVERSIBLE_GIT", "proceed", "/project", test_db)
    
    stats = get_stats(test_db)
    print("--- Database Stats ---")
    for k, v in stats.items():
        print(f"{k}: {v}")
        
    if os.path.exists(test_db):
        os.remove(test_db)
