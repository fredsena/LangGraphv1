import asyncio
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient

from utility import format_messages
from utils.prompts import TODO_USAGE_INSTRUCTIONS
from utils.state import DeepAgentState
from utils.todo_tools import read_todos, write_todos


def print_separator(title=""):
    """Print a visual separator with optional title."""
    if title:
        print(f"\n{'='*80}\n{title.center(80)}\n{'='*80}")
    else:
        print(f"\n{'-'*80}")


def print_todos(state):
    """Pretty print the current TODO list from state."""
    todos = state.get("todos", [])
    
    if not todos:
        print("📝 No TODOs in state")
        return
    
    print("\n📝 Current TODO List:")
    status_emoji = {
        "pending": "⏳",
        "in_progress": "🔄", 
        "completed": "✅"
    }
    
    for i, todo in enumerate(todos, 1):
        emoji = status_emoji.get(todo["status"], "❓")
        print(f"  {i}. {emoji} [{todo['status'].upper()}] {todo['content']}")


async def main():
    # Connect to the MCP servers
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

    # Load tools from the MCP server
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

        Args:
            query: The search query string.

        Returns:
            Search results from search engine.
        """
        return search_result

    # Create the agent
    llm = ChatOpenAI(
        model="qwen/qwen3-4b-2507", 
        base_url="http://127.0.0.1:1234/v1", 
        temperature=0.0, 
        api_key="11111111111111"
    )

    tools = [write_todos, web_search, read_todos, *mcp_tools]

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=TODO_USAGE_INSTRUCTIONS + "\n\n" + "=" * 80 + "\n\n",
        state_schema=DeepAgentState,
    )

    # Complex user request that should trigger TODO creation
    user_query = (
        "What time is it in London? and tell me 2 improvements in "
        "c# language latest version and Give me a short summary of "
        "the Model Context Protocol (MCP)."
    )
    
    print_separator("STARTING AGENT EXECUTION")
    print(f"🎯 User Request:\n{user_query}")

    # ============================================================
    # METHOD 1: Stream events and track TODO updates
    # ============================================================
    print_separator("METHOD 1: Streaming with Event Tracking")
    
    event_count = 0
    async for event in agent.astream_events(
        {
            "messages": [{"role": "user", "content": user_query}],
            "todos": [],
        },
        version="v2"
    ):
        event_count += 1
        
        # Track tool calls
        if event["event"] == "on_tool_start":
            tool_name = event["name"]
            print(f"\n🔧 Tool Called: {tool_name}")
            
            if tool_name == "write_todos":
                # Show the TODOs being written
                todos = event["data"].get("input", {}).get("todos", [])
                if todos:
                    print("   Writing TODOs:")
                    for i, todo in enumerate(todos, 1):
                        print(f"     {i}. [{todo['status']}] {todo['content']}")
        
        # Track tool completion
        if event["event"] == "on_tool_end":
            tool_name = event["name"]
            if tool_name in ["write_todos", "read_todos"]:
                print(f"✓ {tool_name} completed")

    print(f"\n📊 Total events processed: {event_count}")

    # ============================================================
    # METHOD 2: Step-by-step execution with state inspection
    # ============================================================
    print_separator("METHOD 2: Step-by-Step State Inspection")
    
    config = {"recursion_limit": 50}
    step_count = 0
    
    async for step in agent.astream(
        {
            "messages": [{"role": "user", "content": user_query}],
            "todos": [],
        },
        config=config,
        stream_mode="updates"  # Get state updates
    ):
        step_count += 1
        print_separator(f"Step {step_count}")
        
        # Extract state from the step
        for node_name, node_state in step.items():
            print(f"🔹 Node: {node_name}")
            
            # Print TODOs if they exist in this update
            if "todos" in node_state:
                print_todos(node_state)
            
            # Print last message if available
            if "messages" in node_state and node_state["messages"]:
                last_msg = node_state["messages"][-1]
                msg_type = type(last_msg).__name__
                
                if hasattr(last_msg, "content"):
                    content = str(last_msg.content)[:200]  # Truncate long content
                    print(f"💬 Message ({msg_type}): {content}...")

    # ============================================================
    # METHOD 3: Final state inspection
    # ============================================================
    print_separator("METHOD 3: Final State Inspection")
    
    result = await agent.ainvoke(
        {
            "messages": [{"role": "user", "content": user_query}],
            "todos": [],
        }
    )
    
    print_todos(result)
    
    # Show final answer
    print_separator("FINAL ANSWER")
    if result.get("messages"):
        final_message = result["messages"][-1]
        print(f"🤖 Agent Response:\n{final_message.content}")
    
    print_separator()


if __name__ == "__main__":
    asyncio.run(main())
