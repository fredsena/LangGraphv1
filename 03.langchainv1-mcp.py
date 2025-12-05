import pathlib
import re

import requests
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_community.utilities import SQLDatabase
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import tool
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
import asyncio


async def main():
    # Connect to the mcp-time server
    mcp_client = MultiServerMCPClient(
        {
            "time": {
                "transport": "stdio",
                "command": "npx",
                "args": ["-y", "@theo.foobar/mcp-time"],
            },
            "msdocs": {
                "transport": "streamable_http",            
                "url": "https://learn.microsoft.com/api/mcp",
            }
        },
    )

    # Load tools from the MCP server (await the coroutine)
    mcp_tools = await mcp_client.get_tools()
    print(f"Loaded {len(mcp_tools)} MCP tools: {[t.name for t in mcp_tools]}")

    llm = ChatOpenAI(
        model="qwen/qwen3-4b-2507", 
        base_url="http://127.0.0.1:1234/v1", 
        temperature=0.0, 
        api_key="11111111111111"
    )

    agent = create_agent(
        system_prompt="You are a helpful assistant",
        model=llm,
        tools=mcp_tools,
    )

    # #token by token
    # for token, metadata in agent.stream(
    #     {"messages": [{"role": "user", "content": "Write me a family friendly poem."}]},
    #     stream_mode="messages",
    # ):
    #     print(f"{token.content}", end="")


    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "give me a simple example of python code to read a csv file"}]}
    )

    for msg in result["messages"]:
        msg.pretty_print()

    # # Stream = values
    # async for step in agent.astream(
    #     {"messages": [{"role": "user", "content": "tell me about your tools available and give me a simple example of c# code to read a csv file"}]},
    #     stream_mode="values",
    # ):
    #     step["messages"][-1].pretty_print()     

    # #token by token
    # async for token, metadata in agent.astream(
    #     {"messages": [{"role": "user", "content": "tell me about your tools available and give me a simple example of c# code with latest advanced syntax for async methods"}]},
    #     stream_mode="messages",
    # ):
    #     #print (f"metadata: {metadata}")
    #     print(f"{token.content}", end="")        


# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())





