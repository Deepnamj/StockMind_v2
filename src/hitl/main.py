import asyncio
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from src.hitl.graph import build_stockmind_graph

async def main():
    graph, tools, mcp_client = await build_stockmind_graph()
    thread_id = "stockmind-cli-session"
    config = {"configurable": {"thread_id": thread_id}}

    print("StockMind CLI. Type 'exit' to stop.")
    while True:
        question = input("\nYou: ").strip()
        if question.lower() == "exit":
            break
        if not question:
            print("Please enter a question.")
            continue

        result = await graph.ainvoke(
            {"messages": [HumanMessage(content=question)]},
            config=config
        )

        interrupts = result.get("__interrupt__", [])
        if interrupts:
            print("\nApproval request:", interrupts[0].value)
            decision = input("Approve? (yes/no): ").strip().lower()
            resume_value = "approve" if decision == "yes" else "reject"
            result = await graph.ainvoke(
                Command(resume={"decision": resume_value}),
                config=config
            )

        messages = result.get("messages", [])
        if messages:
            print("\nStockMind:", messages[-1].content)

if __name__ == "__main__":
    asyncio.run(main())
