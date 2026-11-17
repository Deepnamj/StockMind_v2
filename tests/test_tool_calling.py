
import asyncio
import sys

from src.common import get_llm
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.messages import HumanMessage, ToolMessage


async def main():

    # 1. Connect to MCP stock server
    client = MultiServerMCPClient({
        "stock": {
            "transport": "stdio",
            "command": sys.executable,
            "args": ["-m", "src.mcp_servers.stock_server"],
        }
    })

    # 2. Discover MCP tools
    tools = await client.get_tools()

    print("\nDiscovered MCP tools:")
    for tool in tools:
        print("-", tool.name)

    # 3. Initialize Gemini
    llm = get_llm()

    # 4. Bind MCP tools to Gemini
    llm_with_tools = llm.bind_tools(tools)

    # 5. Ask Gemini to retrieve Apple's stock price
    messages = [
        HumanMessage(
            content="Get the current stock price of Apple using the stock tool."
        )
    ]

    response = await llm_with_tools.ainvoke(messages)

    print("\nGemini tool selection:")
    print(response.tool_calls)

    if not response.tool_calls:
        print("\nGemini did not select a tool.")
        print("Response:", response.content)
        return

    # 6. Execute the selected MCP tool
    for tool_call in response.tool_calls:

        selected_tool = next(
            (tool for tool in tools if tool.name == tool_call["name"]),
            None
        )

        if selected_tool is None:
            raise ValueError(
                f"Unknown tool selected: {tool_call['name']}"
            )

        print("\nExecuting tool:", selected_tool.name)

        result = await selected_tool.ainvoke(tool_call["args"])

        print("\nMCP tool result:")
        print(result)

        # 7. Send tool result back to Gemini
        messages.append(response)

        messages.append(
            ToolMessage(
                content=str(result),
                tool_call_id=tool_call["id"]
            )
        )

    # 8. Gemini generates final response
    final_response = await llm.ainvoke(messages)

    print("\nFinal Gemini response:")
    print(final_response.content)


if __name__ == "__main__":
    asyncio.run(main())
