
import asyncio

from langchain_core.messages import HumanMessage
from langgraph.types import Command

from src.hitl.graph import build_stockmind_graph


async def test_purchase(graph, decision):

    thread_id = f"hitl-{decision}"
    config = {"configurable": {"thread_id": thread_id}}

    print(f"\n{'=' * 45}")
    print(f"Testing purchase: {decision.upper()}")
    print("=" * 45)

    # 1. Ask Gemini to request a simulated purchase
    result = await graph.ainvoke(
        {
            "messages": [
                HumanMessage(
                    content=(
                        "Use the request_simulated_stock_purchase tool "
                        "to request a simulated purchase of 2 AAPL shares "
                        "at an estimated price of 100 USD. "
                        "Do not use any other tool."
                    )
                )
            ]
        },
        config=config
    )

    # 2. Check whether the graph was interrupted
    interrupts = result.get("__interrupt__", [])

    if not interrupts:
        print("\nFAILED: No human approval interrupt was received.")
        print("Last message:", result["messages"][-1].content)
        return

    print("\nHuman approval requested:")
    print(interrupts[0].value)

    # 3. Resume the graph with human decision
    print(f"\nSubmitting human decision: {decision}")

    result = await graph.ainvoke(
        Command(resume={"decision": decision}),
        config=config
    )

    # 4. Display final result
    print("\nFinal StockMind response:")

    messages = result.get("messages", [])

    if messages:
        print(messages[-1].content)

    print(f"\n{decision.upper()} scenario completed.")


async def main():

    # Build LangGraph workflow
    graph, tools, mcp_client = await build_stockmind_graph()

    print("StockMind graph initialized successfully.")

    print("\nAvailable tools:")
    for tool in tools:
        print("-", tool.name)

    # Test approval
    await test_purchase(graph, "approve")

    # Test rejection
    await test_purchase(graph, "reject")


if __name__ == "__main__":
    asyncio.run(main())
