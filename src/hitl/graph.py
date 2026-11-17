import sys
from pathlib import Path

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage

from src.common import get_llm
from src.graph_state import StockMindState
from src.hitl.tools import request_simulated_stock_purchase

PROJECT_ROOT = Path(__file__).resolve().parents[2]

async def build_stockmind_graph():
    # MCP client starts the stock server as a separate process.
    from langchain_mcp_adapters.client import MultiServerMCPClient

    mcp_client = MultiServerMCPClient({
        "stock": {
            "transport": "stdio",
            "command": sys.executable,
            "args": ["-m", "src.mcp_servers.stock_server"],
        }
    })

    mcp_tools = await mcp_client.get_tools()

    all_tools = []
    for stock_tool in mcp_tools:
        all_tools.append(stock_tool)

    all_tools.append(request_simulated_stock_purchase)

    llm = get_llm()
    llm_with_tools = llm.bind_tools(all_tools)

    system_message = SystemMessage(
        content=(
            "You are StockMind, an informational stock research assistant. "
            "Use the available tools when current company or market data is requested. "
            "Never invent prices or financial metrics. Mention when data is unavailable. "
            "You may explain financial information but do not give personalized investment advice. "
            "The purchase tool is simulation-only and requires human approval."
        )
    )

    async def chatbot(state: StockMindState):
        messages = [system_message]
        for message in state["messages"]:
            messages.append(message)
        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

    workflow = StateGraph(StockMindState)
    workflow.add_node("chatbot", chatbot)
    workflow.add_node("tools", ToolNode(all_tools))
    workflow.add_edge(START, "chatbot")
    workflow.add_conditional_edges("chatbot", tools_condition)
    workflow.add_edge("tools", "chatbot")

    memory = MemorySaver()
    graph = workflow.compile(checkpointer=memory)

    return graph, all_tools, mcp_client
