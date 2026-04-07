import time
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from tools import get_stock_data, execute_trade
from db import log_agent

INTERVAL_SECONDS = 300
TICKERS = ["DOGE-USD", "XRP-USD", "ADA-USD", "TRX-USD", "XLM-USD"]

SYSTEM_PROMPT = """You are a scalp trading agent running on a 5-minute cycle.
You have a starting capital of ₹1,00,000.

Each cycle you must:
1. Call get_stock_data for ALL tickers: {tickers}
2. Analyze momentum and price position.
3. For EACH ticker, decide to BUY, SELL, or HOLD.

Strategy rules (Crypto Adjusted):
- HIGH-VALUE COINS (BTC, ETH, SOL):
  - SCALP: momentum_5 > 10.0 & price within 1% of day_high → SELL (if holding).
  - SCALP: momentum_5 < -10.0 & price within 1% of day_low → BUY (if cash available).
  - MOMENTUM: momentum_5 > 10.0 → BUY, if < -10.0 → SELL.

- LOW-VALUE COINS (DOGE, XRP):
  - SCALP: momentum_5 > 0.00001 & price within 1% of day_high → SELL (if holding).
  - SCALP: momentum_5 < -0.00001 & price within 1% of day_low → BUY (if cash available).
  - MOMENTUM: momentum_5 > 0.00001 → BUY, if < -0.00001 → SELL.

Constraints:
- Max quantity per ticker: 50 coins total.
- If you already have a large position, do not BUY more.
- Always provide a clear reasoning string including the current momentum value.
- quantity should always be 10 coins per trade.""".format(tickers=", ".join(TICKERS))

agent_executor = None

def build_agent():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    tools = [get_stock_data, execute_trade]
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])
    agent = create_tool_calling_agent(llm, tools, prompt)
    # Increased max_iterations to allow full 5-ticker loop
    return AgentExecutor(agent=agent, tools=tools, verbose=False, max_iterations=40)

def run_agent_cycle():
    global agent_executor
    if agent_executor is None:
        log_agent("Initialising agent...", "INFO")
        try:
            agent_executor = build_agent()
            log_agent("Agent ready.", "INFO")
        except Exception as e:
            log_agent(f"Agent init failed: {e}", "ERROR")
            return

    log_agent("Starting new 5-minute cycle.", "INFO")
    try:
        result = agent_executor.invoke({
            "input": "Run your full scalp analysis cycle now. Analyse all tickers and execute trades."
        })
        log_agent(f"Cycle complete. Output: {result.get('output', '')[:200]}", "INFO")
    except Exception as e:
        log_agent(f"Cycle error: {e}", "ERROR")

def agent_loop():
    while True:
        run_agent_cycle()
        time.sleep(INTERVAL_SECONDS)