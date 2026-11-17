import json
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from src.hitl.graph import build_stockmind_graph

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    thread_id: str | None = None

class ApprovalRequest(BaseModel):
    thread_id: str
    decision: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    graph, tools, mcp_client = await build_stockmind_graph()
    app.state.graph = graph
    app.state.tools = tools
    app.state.mcp_client = mcp_client
    yield

app = FastAPI(title="StockMind API", version="1.0.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
async def home():
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/health")
async def health():
    return {"status": "ok", "application": "StockMind"}

@app.get("/api/search")
async def search_companies(q: str):
    if not q.strip():
        return {"matches": []}
    tool = find_tool("search_companies")
    result = await tool.ainvoke({"query": q})
    return parse_tool_result(result)

@app.get("/api/company/{symbol}")
async def company_overview(symbol: str):
    symbol = symbol.upper().strip()
    if not symbol.replace(".", "").replace("-", "").isalnum():
        raise HTTPException(status_code=400, detail="Invalid ticker symbol.")

    tool_names = [
        "get_company_profile",
        "get_stock_price",
        "get_company_fundamentals",
        "get_stock_history",
        "get_stock_news",
    ]

    results = {}
    for name in tool_names:
        tool = find_tool(name)
        try:
            if name == "get_stock_history":
                value = await tool.ainvoke({"symbol": symbol, "period": "6mo", "interval": "1d"})
            else:
                value = await tool.ainvoke({"symbol": symbol})
            results[name] = parse_tool_result(value)
        except Exception as error:
            results[name] = {"error": str(error)}

    return {"symbol": symbol, "data": results}

@app.post("/api/chat")
async def chat(request: ChatRequest):
    thread_id = request.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    try:
        result = await app.state.graph.ainvoke(
            {"messages": [HumanMessage(content=request.message)]},
            config=config
        )
        interrupts = result.get("__interrupt__", [])
        if interrupts:
            interrupt_value = interrupts[0].value
            return {
                "thread_id": thread_id,
                "status": "approval_required",
                "approval": interrupt_value,
                "reply": "This action needs your approval before it can continue."
            }

        messages = result.get("messages", [])
        reply = messages[-1].content if messages else "I could not generate a response."
        return {"thread_id": thread_id, "status": "completed", "reply": reply}
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Agent request failed: {error}")

@app.post("/api/approve")
async def approve(request: ApprovalRequest):
    if request.decision not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="Decision must be approve or reject.")

    config = {"configurable": {"thread_id": request.thread_id}}
    try:
        result = await app.state.graph.ainvoke(
            Command(resume={"decision": request.decision}),
            config=config
        )
        interrupts = result.get("__interrupt__", [])
        if interrupts:
            return {
                "thread_id": request.thread_id,
                "status": "approval_required",
                "approval": interrupts[0].value
            }
        messages = result.get("messages", [])
        reply = messages[-1].content if messages else "Workflow resumed."
        return {"thread_id": request.thread_id, "status": "completed", "reply": reply}
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Could not resume workflow: {error}")

def find_tool(name: str):
    
    for tool in app.state.tools:
        if tool.name == name or tool.name.endswith("__" + name):
            return tool
    raise HTTPException(status_code=500, detail=f"MCP tool not found: {name}")


def parse_tool_result(result):
    if isinstance(result, str):
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"result": result}

    if isinstance(result, list):
        for item in result:
            if isinstance(item, dict):
                item_type = item.get("type")
                item_text = item.get("text")
            else:
                item_type = getattr(item, "type", None)
                item_text = getattr(item, "text", None)

            if item_type == "text" and item_text:
                try:
                    return json.loads(item_text)
                except json.JSONDecodeError:
                    return {"result": item_text}

    if isinstance(result, dict):
        return result

    return {"result": str(result)}
