import os
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver

research_instructions = """You are an expert."""

modelV1 = ChatOpenAI(
    model="qwen/qwen3-vl-4b",
    base_url="http://127.0.0.1:1234/v1",
    temperature=0.0,
    api_key="lm-studio"
)

@tool
def get_weather(city: str) -> str:
    """Get the weather in a city."""
    return f"The weather in {city} is sunny OXENTY."

@tool
def get_temperature(city: str) -> str:
    """Get the temperature in a city."""
    return f"The temperature in {city} is 70 degrees Fahrenheit."

memory = MemorySaver()

agent = create_deep_agent(
    system_prompt=research_instructions,
    model=modelV1,
    tools=[get_weather, get_temperature],
    checkpointer=memory,
        interrupt_on={
        "get_weather": {
            "allowed_decisions": ["approve", "edit", "reject"]
        },
    }
)

# query = "What's the weather and temperature in Fortaleza Ceara?"
query = "What's the weather in Fortaleza Ceara?"
config = {"configurable": {"thread_id": "1"}}

# First run - executes tools and stops
for event in agent.stream({"messages": [{"role": "user", "content": query}]}, config, stream_mode="values"):
    for message in event.get("messages", []):
        print(f"{message.__class__.__name__}: {message.content}")

# Check if interrupted
state = agent.get_state(config)
if state.next:
    decision = input("\nConfirm tool results? (yes/no): ").strip().lower()
    
    if decision == "yes":
        # Continue to get final AI response
        for event in agent.stream(None, config, stream_mode="values"):
            for message in event.get("messages", []):
                print(f"{message.__class__.__name__}: {message.content}")


