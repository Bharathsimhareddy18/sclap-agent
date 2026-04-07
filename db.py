import sqlite3
from datetime import datetime

DB_PATH = "trades.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            action TEXT NOT NULL,
            price REAL,
            quantity INTEGER,
            strategy TEXT,
            reasoning TEXT,
            timestamp TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS agent_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            level TEXT DEFAULT 'INFO',
            timestamp TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS holdings (
            ticker TEXT PRIMARY KEY,
            quantity INTEGER DEFAULT 0,
            avg_price REAL DEFAULT 0.0
        )
    """)
    # New table for persistent cash tracking
    c.execute("""
        CREATE TABLE IF NOT EXISTS portfolio_state (
            id INTEGER PRIMARY KEY,
            cash REAL DEFAULT 100000.0
        )
    """)
    # Insert initial capital if not exists
    c.execute("INSERT OR IGNORE INTO portfolio_state (id, cash) VALUES (1, 100000.0)")
    
    conn.commit()
    conn.close()

def log_agent(message, level="INFO"):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO agent_log (message, level, timestamp) VALUES (?, ?, ?)",
        (message, level, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def insert_trade(ticker, action, price, quantity, strategy, reasoning):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """INSERT INTO trades (ticker, action, price, quantity, strategy, reasoning, timestamp)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (ticker, action, price, quantity, strategy, reasoning, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    
def get_cash():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT cash FROM portfolio_state WHERE id = 1")
    res = c.fetchone()
    conn.close()
    return res[0] if res else 100000.0 

def update_cash(amount):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE portfolio_state SET cash = cash + ? WHERE id = 1", (amount,))
    conn.commit()
    conn.close()
    log_agent(f"Cash updated by ₹{amount:.2f}", "DEBUG")

def get_holdings(ticker):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT quantity FROM holdings WHERE ticker = ?", (ticker,))
    res = c.fetchone()
    conn.close()
    return res[0] if res else 0

def update_holdings(ticker, quantity, price):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO holdings (ticker, quantity, avg_price) 
        VALUES (?, ?, ?)
        ON CONFLICT(ticker) DO UPDATE SET 
            avg_price = (avg_price * quantity + excluded.avg_price * excluded.quantity) / (quantity + excluded.quantity),
            quantity = quantity + excluded.quantity
    """, (ticker, quantity, price))
    conn.commit()
    conn.close()