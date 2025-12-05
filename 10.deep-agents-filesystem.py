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

"""
Agent setup with TODO usage instructions, virtual file system state, and mock tools.
"""

#from IPython.display import Image, display
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langchain.agents import create_agent

from utility import format_messages
from utils.prompts import TODO_USAGE_INSTRUCTIONS, FILE_USAGE_INSTRUCTIONS
from utils.state import DeepAgentState
from utils.todo_tools import read_todos, write_todos
from langchain_mcp_adapters.client import MultiServerMCPClient
from utils.file_tools import ls, read_file, write_file


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



    # Mock search result
    search_result = """The Model Context Protocol (MCP) is an open standard protocol developed 
    by Anthropic to enable seamless integration between AI models and external systems like 
    tools, databases, and other services. It acts as a standardized communication layer, 
    allowing AI models to access and utilize data from various sources in a consistent and 
    efficient manner. Essentially, MCP simplifies the process of connecting AI assistants 
    to external services by providing a unified language for data exchange.
    """


    # Mock search tool
    @tool(parse_docstring=True)
    def web_search(query: str):
        """Search the web for information on a specific topic.

        This tool performs web searches and returns relevant results
        for the given query. Use this when you need to gather information from
        the internet about any topic.

        Args:
            query: The search query string.

        Returns:
            Search results from search engine.
        """
        return search_result


    # Create the agent
    #model = init_chat_model(model="anthropic:claude-sonnet-4-20250514", temperature=0.0)

    llm = ChatOpenAI(
        model="qwen/qwen3-4b-2507", 
        base_url="http://127.0.0.1:1234/v1", 
        temperature=0.0, 
        api_key="11111111111111"
    )

    tools = [ls, read_file, write_file, web_search]
    #tools = [write_todos, web_search, read_todos, *mcp_tools]
    #tools = [write_todos, web_search, read_todos]

    # Mock research instructions
    SIMPLE_RESEARCH_INSTRUCTIONS = (
        "IMPORTANT: Just make a single call to the web_search tool and use the result to answer."
    )

    # MCP Time tool instructions
    MCP_TIME_INSTRUCTIONS = """
## MCP Time Tool Usage

When working with time-related queries:

1. **To get the current time** in any timezone, use the `current_time` tool:
   - Example: current_time(timezone="Europe/London")
   - Example: current_time(format="RFC3339")

2. **To convert between timezones**, use `convert_timezone` with an ACTUAL time string (NOT "now"):
   - Example: convert_timezone(time="2024-01-15T10:30:00Z", output_timezone="Europe/London")

3. **NEVER** pass "now" as the `time` parameter - it will fail. Always use `current_time` first to get the actual current time.

4. **For relative time**, use `relative_time`:
   - Example: relative_time(text="yesterday")
   - Example: relative_time(text="5 minutes ago")
"""

    # Full prompt
    INSTRUCTIONS = (
        #FILE_USAGE_INSTRUCTIONS + "\n\n" + "=" * 80 + "\n\n" + MCP_TIME_INSTRUCTIONS
        FILE_USAGE_INSTRUCTIONS + "\n\n" + "=" * 80 + "\n\n" 
    )

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=INSTRUCTIONS
        + "\n\n"
        + "=" * 80
        + "\n\n",
        #+ SIMPLE_RESEARCH_INSTRUCTIONS,
        state_schema=DeepAgentState,
    )

    # Show graph visualization
    #display(Image(agent.get_graph(xray=True).draw_mermaid_png()))

    # "todos": [],

    # Example usage - Testing file system functionality
    result = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Give me a short summary of the Model Context Protocol (MCP).",
                }
            ],            
            "files": {},
        }
    )

    # ==================== DEBUG SECTION ====================
    print("\n" + "🔍 " * 20)
    print("VIRTUAL FILESYSTEM DEBUG")
    print("🔍 " * 20 + "\n")

    files_count = len(result["files"])
    print(result["files"])
    # print(f"Total files created: {files_count}\n")

    # if files_count > 0:
    #     for filename, content in result["files"].items():
    #         line_count = len(content.splitlines())
    #         char_count = len(content)
            
    #         print(f"{'=' * 60}")
    #         print(f"📄 FILE: {filename}")
    #         print(f"{'=' * 60}")
    #         print(f"📊 Stats: {line_count} lines, {char_count} characters")
    #         print(f"{'-' * 60}")
    #         print(content)
    #         print(f"{'-' * 60}\n")
    # else:
    #     print("⚠️  No files were created in the virtual filesystem")
        
    # print("🔍 " * 20 + "\n")
    # ==================== END DEBUG SECTION ====================

    #format_messages(result["messages"])

    # for msg in result["messages"]:
    #     msg.pretty_print()

    
    #print(result["files"])


    
    
    #token by token
    # async for token, metadata in agent.astream(
    #     {
    #         "messages": [{
    #             "role": "user", 
    #             "content": "What time is it in London? and tell me 2 improvements in c# language latest version and Give me a short summary of the Model Context Protocol (MCP)."}],
    #         "todos": [],
    #     },
    #     stream_mode="messages",
    # ):
    #     #print (f"metadata: {metadata}")
    #     print(f"{token.content}", end="")          

if __name__ == "__main__":
    asyncio.run(main())
