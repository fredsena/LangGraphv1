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
from langgraph.checkpoint.memory import MemorySaver, InMemorySaver
from typing_extensions import TypedDict
from pydantic import BaseModel

#  {'name': 'John Doe', 'email': 'john@example.com', 'phone': '555-123-4567'}
class ContactInfo(TypedDict):
    name: str
    email: str
    phone: str
    product: str
    quantity: int


llm = ChatOpenAI(
    model="qwen/qwen3-4b-2507", 
    #model="llama-3.2-3b-instruct",
    #model="qwen3-4b-instruct-2507-polaris-alpha-distill",
    base_url="http://127.0.0.1:1234/v1", 
    temperature=0.0, 
    api_key="11111111111111")

agent = create_agent(
    system_prompt="You are a helpful assistant. Extract only the contact information from the conversation.",
    model=llm,
    #checkpointer=InMemorySaver(),
    response_format=ContactInfo
)


# recorded_conversation = """We talked with John Doe. He works over at Example. His number is, let's see, 
# five, five, five, one two three, four, five, six seven. Did you get that?
# And, his email was john at example.com. He wanted to order 50 boxes of Captain Crunch."""

recorded_conversation = """We talked with John Doe. He works over at Example. His number is, let's see, 
five, five, five, one two three, four, five, six seven. Did you get that?
And, his email was john at example.com. """

result = agent.invoke(
    {"messages": [{"role": "user", "content": recorded_conversation}]}
)

print(result["structured_response"])

class ContactInfo2(BaseModel):
    name: str
    email: str
    phone: str
    product: str
    quantity: int

agent2 = create_agent(
    system_prompt="You are a helpful assistant. Extract only the contact information from the conversation.",
    model=llm,
    #checkpointer=InMemorySaver(),
    response_format=ContactInfo2
)

result2 = agent2.invoke(
    {"messages": [{"role": "user", "content": recorded_conversation}]}
)

print(result2["structured_response"])

# # Thread ID for maintaining conversation history
# thread_id = "conversation_1"

# print("=" * 60)
# print("Assistant Chat Bot")
# print("=" * 60)
# print("Type 'quit', 'exit', or 'bye' to end the conversation.\n")

# # Chat loop
# while True:
#     # Get user input
#     user_input = input("You: ").strip()
    
#     # Check for exit commands
#     if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
#         print("\n👋 Thanks for chatting! Goodbye!")
#         break
    
#     # Skip empty inputs
#     if not user_input:
#         continue
    
#     # Create human message
#     human_msg = HumanMessage(user_input)
    
#     # Invoke agent with thread configuration to maintain history
#     result = agent.invoke(
#         {"messages": [human_msg]},
#         config={"configurable": {"thread_id": thread_id}}
#     )
    
#     # Display the AI's response
#     ai_response = result["messages"][-1].content
#     print(f"\n🤖 Bot: {ai_response}\n")


