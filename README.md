# StockMind

AI-powered stock research and agentic decision-support demo.

## Features
- Company search and company overview dashboard
- Stock price, company profile, fundamentals, history and news via MCP tools
- Gemini-powered conversational assistant orchestrated by LangGraph
- Human approval before a **simulated** stock purchase
- LangSmith tracing (optional)
- FastAPI backend and HTML/CSS/JavaScript frontend

## Model
The configured model is `gemini-3.6-flash`. Confirm that this model is enabled for your Google AI API project.

## Setup (Windows PowerShell)
```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```
Edit `.env` and add your `GEMINI_API_KEY`.

## Run
From the project root:
```powershell
uvicorn src.hitl.api:app --reload
```
Open http://127.0.0.1:8000

## MCP tools
The MCP server exposes:
- `search_companies`
- `get_stock_price`
- `get_company_profile`
- `get_company_fundamentals`
- `get_stock_history`
- `get_stock_news`

The dashboard endpoint calls the MCP tools and combines their results. The agent can also discover and call these tools through LangGraph.

## Important limitations
- Market data comes from Yahoo Finance through the `yfinance` package. It may be delayed, incomplete, rate-limited, or unavailable. It is not an exchange-grade real-time feed.
- Financial metrics and company news depend on provider availability.
- The purchase tool is a demonstration only. It does not place real trades or connect to a brokerage.
- `MemorySaver` stores checkpoints in process memory. Restarting the server loses those checkpoints. Use a persistent LangGraph checkpointer before relying on long-running production workflows.
- This starter project has not been run against your API keys or your machine. Install dependencies and test each feature locally before deployment.

## Project structure
```text
StockMind/
├── src/
│   ├── common.py
│   ├── graph_state.py
│   ├── hitl/
│   │   ├── graph.py
│   │   ├── main.py
│   │   ├── tools.py
│   │   ├── api.py
│   │   └── static/index.html
│   └── mcp_servers/stock_server.py
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```
