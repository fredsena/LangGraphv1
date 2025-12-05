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

from langgraph.checkpoint.memory import MemorySaver, InMemorySaver

async def main():
    # Connect to MCP servers
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

    # Load tools from the MCP servers
    mcp_tools = await mcp_client.get_tools()
    print(f"Loaded {len(mcp_tools)} MCP tools: {[t.name for t in mcp_tools]}\n")

    llm = ChatOpenAI(
        model="qwen/qwen3-4b-2507", 
        #model="llama-3.2-3b-instruct",
        #model="qwen3-4b-instruct-2507-polaris-alpha-distill",
        base_url="http://127.0.0.1:1234/v1", 
        temperature=0.0, 
        api_key="11111111111111"
    )

    agent = create_agent(
        system_prompt="You are a helpful assistant. Use only tools to answer the user.",
        model=llm,
        tools=mcp_tools,  # Add MCP tools to the agent
        checkpointer=InMemorySaver(),
    )

    # Thread ID for maintaining conversation history
    thread_id = "conversation_1"

    print("=" * 60)
    print("Assistant Chat Bot (with MCP Tools)")
    print("=" * 60)
    print("Type 'quit', 'exit', or 'bye' to end the conversation.\n")

    # Chat loop
    while True:
        # Get user input
        user_input = input("You: ").strip()
        
        # Check for exit commands
        if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
            print("\n👋 Thanks for chatting! Goodbye!")
            break
        
        # Skip empty inputs
        if not user_input:
            continue
        
        # Create human message
        human_msg = HumanMessage(user_input)
        
        print(f"\n🤖 Bot: ", end="", flush=True)
        
        # Stream the agent's response token by token
        full_response = ""
        async for event in agent.astream_events(
            {"messages": [human_msg]},
            config={"configurable": {"thread_id": thread_id}},
            version="v2"
        ):
            kind = event["event"]
            
            # Display streaming tokens from the LLM
            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    print(content, end="", flush=True)
                    full_response += content
            
            # Show when MCP tools are being called
            elif kind == "on_tool_start":
                tool_name = event["name"]
                print(f"\n\n🔧 [Calling MCP tool: {tool_name}]", end="", flush=True)
            
            # Show tool results
            elif kind == "on_tool_end":
                tool_name = event["name"]
                print(f"\n✅ [Tool {tool_name} completed]\n\n🤖 Bot: ", end="", flush=True)
        
        print("\n")  # Add newline after response


# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())
