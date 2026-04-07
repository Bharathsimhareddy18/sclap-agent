import yfinance as yf
from langchain.tools import tool
from db import insert_trade, log_agent, get_holdings, get_cash, update_holdings, update_cash

@tool
def get_stock_data(ticker: str) -> dict:
    """Fetch current price, 1-day high/low, volume, and 5-period momentum for a ticker."""
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="1d", interval="1m")
        if hist.empty:
            return {"error": f"No data for {ticker}"}

        current_price = float(hist["Close"].iloc[-1])
        day_high = float(hist["High"].max())
        day_low = float(hist["Low"].min())
        volume = int(hist["Volume"].sum())

        if len(hist) >= 5:
            momentum = float(hist["Close"].iloc[-1] - hist["Close"].iloc[-5])
        else:
            momentum = 0.0

        return {
            "ticker": ticker.upper(),
            "current_price": round(current_price, 4),
            "day_high": round(day_high, 4),
            "day_low": round(day_low, 4),
            "volume": volume,
            "momentum_5": round(momentum, 4),
        }
    except Exception as e:
        return {"error": str(e)}

@tool
def execute_trade(ticker: str, action: str, quantity: int, strategy: str, reasoning: str) -> str:
    """
    Execute a paper trade in INR (USD price * 83.5). 
    Action must be BUY, SELL, or HOLD.
    """
    action = action.upper()
    if action not in ("BUY", "SELL", "HOLD"):
        return f"Invalid action '{action}'."
    if action == "HOLD":
        return f"Holding {ticker}. No trade executed."

    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="1d", interval="1m")
        price = float(hist["Close"].iloc[-1]) if not hist.empty else 0.0
        
        # Use fixed conversion rate
        value_inr = price * quantity * 83.5 

        if action == "BUY":
            cash = get_cash()
            if value_inr > cash:
                return f"Insufficient capital. Need ₹{value_inr:,.0f}, have ₹{cash:,.0f}."
            update_cash(-value_inr)
            update_holdings(ticker, quantity, price)

        elif action == "SELL":
            held = get_holdings(ticker)
            if held < quantity:
                return f"Cannot sell {quantity} {ticker} — only holding {held}."
            update_holdings(ticker, -quantity, price)
            update_cash(+value_inr)

        insert_trade(ticker, action, price, quantity, strategy, reasoning)
        log_agent(f"Trade executed: {action} {quantity} {ticker} @ {price:.4f} [{strategy}]")
        return f"Paper trade recorded: {action} {quantity} x {ticker} @ ${price:.4f}"
    except Exception as e:
        return f"Trade failed: {str(e)}"