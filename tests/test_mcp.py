
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient


async def main():

    client = MultiServerMCPClient(
        {
            "stock": {
                "command": "python",
                "args": ["-m", "src.mcp_servers.stock_server"],
                "transport": "stdio",
            }
        }
    )

    tools = await client.get_tools()

    # Find the stock price tool
    stock_tool = next(
        tool for tool in tools
        if tool.name == "get_stock_price"
    )

    # Execute the MCP tool
    result = await stock_tool.ainvoke({"symbol": "AAPL"})

    print("\nStock Price Tool Result:")
    print(result)


asyncio.run(main())
