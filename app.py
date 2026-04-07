import threading
import sqlite3
from flask import Flask, jsonify, render_template, request
from db import init_db, DB_PATH, log_agent
from agent import agent_loop, run_agent_cycle

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/trades")
def api_trades():
    limit = request.args.get("limit", 50, type=int)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM trades ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    cols = ["id", "ticker", "action", "price", "quantity", "strategy", "reasoning", "timestamp"]
    return jsonify([dict(zip(cols, r)) for r in rows])

@app.route("/api/logs")
def api_logs():
    limit = request.args.get("limit", 30, type=int)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM agent_log ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    cols = ["id", "message", "level", "timestamp"]
    return jsonify([dict(zip(cols, r)) for r in rows])

@app.route("/api/stats")
def api_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM trades")
    total = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM trades WHERE action='BUY'")
    buys = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM trades WHERE action='SELL'")
    sells = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM trades WHERE action='HOLD'")
    holds = c.fetchone()[0]

    # Fetch actual cash from DB
    c.execute("SELECT cash FROM portfolio_state WHERE id = 1")
    cash_row = c.fetchone()
    current_cash = cash_row[0] if cash_row else 100000.0
    
    pnl = current_cash - 100000.0

    conn.close()
    return jsonify({
        "total": total,
        "buys": buys,
        "sells": sells,
        "holds": holds,
        "current_cash": round(current_cash, 2),
        "pnl": round(pnl, 2)
    })

@app.route("/api/force_cycle", methods=["POST"])
def force_cycle():
    t = threading.Thread(target=run_agent_cycle, daemon=True)
    t.start()
    return jsonify({"status": "cycle triggered"})

if __name__ == "__main__":
    init_db()
    log_agent("Server started. Launching agent loop.", "INFO")
    t = threading.Thread(target=agent_loop, daemon=True)
    t.start()
    app.run(debug=False, port=5000)