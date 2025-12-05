import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent


async def main():
    # Connect to the mcp-time server
    mcp_client = MultiServerMCPClient(
        {
            "time": {
                "transport": "stdio",
                "command": "npx",
                "args": ["-y", "@theo.foobar/mcp-time"],
            },
        },
    )

    # Load tools from the MCP server
    mcp_tools = await mcp_client.get_tools()
    
    print("Available MCP tools:")
    for tool in mcp_tools:
        print(f"\nTool: {tool.name}")
        print(f"Description: {tool.description}")
        if hasattr(tool, 'args_schema') and tool.args_schema:
            if isinstance(tool.args_schema, dict):
                print(f"Schema: {tool.args_schema}")
            else:
                print(f"Schema: {tool.args_schema.schema()}")

    llm = ChatOpenAI(
        model="qwen/qwen3-4b-2507", 
        base_url="http://127.0.0.1:1234/v1", 
        temperature=0.0, 
        api_key="11111111111111"
    )

    agent = create_agent(
        model=llm,
        tools=mcp_tools,
        system_prompt="You are a helpful assistant."
    )

    # Test with a simple time query
    result = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "What time is it in London?",
                }
            ],
        }
    )

    for msg in result["messages"]:
        msg.pretty_print()


if __name__ == "__main__":
    asyncio.run(main())
