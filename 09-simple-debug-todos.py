import asyncio
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient

from utils.prompts import TODO_USAGE_INSTRUCTIONS
from utils.state import DeepAgentState
from utils.todo_tools import read_todos, write_todos


async def main():
    """Simple TODO debugging - prints state after each step."""
    
    # Setup MCP client and tools
    mcp_client = MultiServerMCPClient({
        "time": {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@theo.foobar/mcp-time"],
        },
    })
    mcp_tools = await mcp_client.get_tools()

    # Mock search tool
    @tool
    def web_search(query: str) -> str:
        """Search the web for information."""
        return "MCP is an open standard protocol by Anthropic for AI integration."

    # Create agent
    llm = ChatOpenAI(
        model="qwen/qwen3-4b-2507", 
        base_url="http://127.0.0.1:1234/v1", 
        temperature=0.0, 
        api_key="11111111111111"
    )

    agent = create_agent(
        model=llm,
        tools=[write_todos, web_search, read_todos, *mcp_tools],
        system_prompt=TODO_USAGE_INSTRUCTIONS + "\n\n" + "=" * 80 + "\n\n",
        state_schema=DeepAgentState,
    )

    # User request
    query = "What time is it in London? Tell me about MCP. Search for C# improvements."
    
    print("="*80)
    print(f"USER REQUEST: {query}")
    print("="*80)

    # Stream and print each step
    step_num = 0
    async for state_update in agent.astream(
        {"messages": [{"role": "user", "content": query}], "todos": []},
        stream_mode="updates"
    ):
        step_num += 1
        
        for node_name, node_data in state_update.items():
            print(f"\n📍 STEP {step_num} - Node: {node_name}")
            
            # Show TODOs if present
            if "todos" in node_data:
                todos = node_data["todos"]
                if todos:
                    print("📝 TODO LIST:")
                    for i, todo in enumerate(todos, 1):
                        status_icon = {
                            "pending": "⏳", 
                            "in_progress": "🔄", 
                            "completed": "✅"
                        }.get(todo["status"], "❓")
                        
                        print(f"   {i}. {status_icon} {todo['content']} ({todo['status']})")
                else:
                    print("📝 TODO LIST: Empty")
            
            # Show last message
            if "messages" in node_data and node_data["messages"]:
                last_msg = node_data["messages"][-1]
                msg_type = type(last_msg).__name__
                
                # Show tool calls
                if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                    print(f"🔧 Tool Calls: {[tc['name'] for tc in last_msg.tool_calls]}")
                
                # Show content (truncated)
                if hasattr(last_msg, "content") and last_msg.content:
                    content = str(last_msg.content)
                    if len(content) > 150:
                        content = content[:150] + "..."
                    print(f"💬 {msg_type}: {content}")

    print("\n" + "="*80)
    print("AGENT EXECUTION COMPLETE")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
