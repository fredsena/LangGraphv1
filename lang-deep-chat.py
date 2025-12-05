import os
import getpass
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import tool
from deepagents import create_deep_agent

from langchain.agents import create_agent

from langgraph.checkpoint.memory import MemorySaver


research_instructions = """You are an expert ."""

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

query = "What's the weather and temperature in Fortaleza Ceara?"
config = {"configurable": {"thread_id": "1"}}

# Stream events to handle interrupts
for event in agent.stream({"messages": [{"role": "user", "content": query}]}, config):
    for message in event.get("messages", []):
        if hasattr(message, "content"):
            print(f"{message.__class__.__name__}: {message.content}")
    
    # Check for interrupt
    if "__interrupt__" in event:
        print("\n--- Tool call requires approval ---")
        interrupt_info = event["__interrupt__"]
        print(f"Tool: {interrupt_info}")
        
        decision = input("\nDecision (approve/edit/reject): ").strip().lower()
        
        if decision == "approve":
            agent.update_state(config, {"decision": "approve"})
        elif decision == "edit":
            new_city = input("Enter new city: ")
            agent.update_state(config, {"decision": "edit", "tool_args": {"city": new_city}})
        elif decision == "reject":
            agent.update_state(config, {"decision": "reject"})
        
        # Continue execution
        for event in agent.stream(None, config):
            for message in event.get("messages", []):
                if hasattr(message, "content"):
                    print(f"{message.__class__.__name__}: {message.content}")
            final_result = event

print("\n" + "="*50)
print("FINAL RESULT:")
print("="*50)
if final_result:
    for key, value in final_result.items():
        print(f"\n{key}: {value}")
