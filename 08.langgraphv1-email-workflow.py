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
from typing import Literal
from langchain.tools import tool

# app.py

import os
import uuid
from typing import Literal, TypedDict
from dotenv import load_dotenv

# Optional: remove if you don't use this in plain Python
# from IPython.display import Image, display

# Load .env variables
load_dotenv()

# -------------------------------
# ENV CHECKER OPTIONAL
# -------------------------------
try:
    from env_utils import doublecheck_env
    doublecheck_env("example.env")
except:
    print("env_utils not found; skipping environment validation")

# -------------------------------
# State Definitions
# -------------------------------

class EmailClassification(TypedDict):
    intent: Literal["question", "bug", "billing", "feature", "complex"]
    urgency: Literal["low", "medium", "high", "critical"]
    topic: str
    summary: str

class EmailAgentState(TypedDict):
    email_content: str
    sender_email: str
    email_id: str

    classification: EmailClassification | None
    ticket_id: str | None

    search_results: list[str] | None
    customer_history: dict | None

    draft_response: str | None


# -------------------------------
# LangGraph Nodes
# -------------------------------

from langchain_openai import ChatOpenAI
from langgraph.types import Command, interrupt
from langgraph.graph import END, START, StateGraph

def read_email(state: EmailAgentState) -> EmailAgentState:
    # Placeholder – usually you'd parse HTML, attachments, etc.
    return {}

#llm = ChatOpenAI(model="gpt-5-mini")

llm = ChatOpenAI(
    model="qwen/qwen3-4b-2507", 
    #model="llama-3.2-3b-instruct",
    #model="qwen3-4b-instruct-2507-polaris-alpha-distill",
    base_url="http://127.0.0.1:1234/v1", 
    temperature=0.0, 
    api_key="11111111111111")

def classify_intent(state: EmailAgentState) -> EmailAgentState:
    structured_llm = llm.with_structured_output(EmailClassification)

    prompt = f"""
    Analyze this customer email and classify it.

    Email: {state['email_content']}
    From: {state['sender_email']}

    Provide intent, urgency, topic, and summary.
    """

    classification = structured_llm.invoke(prompt)
    return {"classification": classification}


def search_documentation(state: EmailAgentState) -> EmailAgentState:
    classification = state.get("classification", {})
    query = f"{classification.get('intent', '')} {classification.get('topic', '')}"

    try:
        results = [
            "--Search_result_1--",
            "--Search_result_2--",
            "--Search_result_3--"
        ]
    except Exception as e:
        results = [f"Search temporarily unavailable: {str(e)}"]

    return {"search_results": results}


def bug_tracking(state: EmailAgentState) -> EmailAgentState:
    ticket_id = f"BUG_{uuid.uuid4()}"
    return {"ticket_id": ticket_id}


def write_response(state: EmailAgentState) -> Command[Literal["human_review", "send_reply"]]:
    classification = state.get("classification", {})

    context_parts = []

    if state.get("search_results"):
        formatted = "\n".join(f"- {d}" for d in state["search_results"])
        context_parts.append(f"Relevant documentation:\n{formatted}")

    if state.get("customer_history"):
        context_parts.append(f"Customer tier: {state['customer_history'].get('tier', 'standard')}")

    draft_prompt = f"""
    Draft a response to this customer email:
    {state['email_content']}

    Intent: {classification.get('intent', 'unknown')}
    Urgency: {classification.get('urgency', 'medium')}

    {'\n'.join(context_parts)}

    Guidelines:
    - Be professional
    - Address their concern
    - Use documentation if relevant
    - Keep it brief
    """

    response = llm.invoke(draft_prompt)

    needs_review = (
        classification.get("urgency") in ["high", "critical"] or
        classification.get("intent") == "complex"
    )

    goto = "human_review" if needs_review else "send_reply"

    if needs_review:
        print("Needs approval")

    return Command(
        update={"draft_response": response.content},
        goto=goto
    )


def human_review(state: EmailAgentState):
    classification = state.get("classification", {})

    human_decision = interrupt({
        "email_id": state["email_id"],
        "original_email": state["email_content"],
        "draft_response": state.get("draft_response", ""),
        "urgency": classification.get("urgency"),
        "intent": classification.get("intent"),
        "action": "Please review and approve/edit this response"
    })

    if human_decision.get("approved"):
        return Command(
            update={"draft_response": human_decision.get("edited_response", state["draft_response"])},
            goto="send_reply"
        )
    else:
        return Command(update={}, goto=END)


def send_reply(state: EmailAgentState) -> EmailAgentState:
    print(f"Sending reply: {state['draft_response'][:60]}...")
    return {}


# ----------------------------------
# Build Graph
# ----------------------------------

builder = StateGraph(EmailAgentState)

builder.add_node("read_email", read_email)
builder.add_node("classify_intent", classify_intent)
builder.add_node("search_documentation", search_documentation)
builder.add_node("bug_tracking", bug_tracking)
builder.add_node("write_response", write_response)
builder.add_node("human_review", human_review)
builder.add_node("send_reply", send_reply)

builder.add_edge(START, "read_email")
builder.add_edge("read_email", "classify_intent")
builder.add_edge("classify_intent", "search_documentation")
builder.add_edge("classify_intent", "bug_tracking")
builder.add_edge("search_documentation", "write_response")
builder.add_edge("bug_tracking", "write_response")
builder.add_edge("send_reply", END)

from langgraph.checkpoint.memory import InMemorySaver
memory = InMemorySaver()

app = builder.compile(checkpointer=memory)


# ----------------------------------
# Example Test Run
# ----------------------------------

def run_interactive():
    """
    Interactive human-in-the-loop email processing.
    User can enter emails, review drafts, and approve/edit responses.
    """
    email_counter = 0
    
    print("=== Email Processing Workflow (Human-in-the-Loop) ===")
    print("Enter email content or 'q' to quit\n")
    
    while True:
        # Get email input from user
        user_input = input('\nEnter email content (or "q" to quit): ')
        
        if user_input.lower() == 'q':
            print("Exiting email workflow...")
            break
        
        # Create state for this email
        email_counter += 1
        initial_state = {
            "email_content": user_input,
            "sender_email": f"customer{email_counter}@example.com",
            "email_id": f"email_{email_counter}"
        }
        
        # Use unique thread for each email
        config = {"configurable": {"thread_id": f"thread_{email_counter}"}}
        
        print(f"\n📧 Processing email #{email_counter}...")
        result = app.invoke(initial_state, config)
        
        # Handle interrupt (human review needed)
        if '__interrupt__' in result:
            print("\n" + "="*60)
            print("🔔 HUMAN REVIEW REQUIRED")
            print("="*60)
            
            interrupt_data = result['__interrupt__'][-1].value
            
            print(f"\n📋 Email ID: {interrupt_data['email_id']}")
            print(f"📊 Intent: {interrupt_data['intent']}")
            print(f"⚠️  Urgency: {interrupt_data['urgency']}")
            print(f"\n📝 Original Email:\n{interrupt_data['original_email']}\n")
            print(f"✍️  Draft Response:\n{interrupt_data['draft_response']}\n")
            print("="*60)
            
            # Get human decision
            decision = input("\nApprove this response? (y/n/edit): ").lower()
            
            if decision == 'y':
                # Approve as-is
                human_response = Command(
                    resume={"approved": True}
                )
                final_result = app.invoke(human_response, config)
                print("✅ Email sent successfully!")
                
            elif decision == 'edit':
                # Allow editing
                print("\nEnter your edited response:")
                edited_text = input("> ")
                human_response = Command(
                    resume={
                        "approved": True,
                        "edited_response": edited_text
                    }
                )
                final_result = app.invoke(human_response, config)
                print("✅ Edited email sent successfully!")
                
            else:
                # Reject/skip
                human_response = Command(
                    resume={"approved": False}
                )
                app.invoke(human_response, config)
                print("❌ Email rejected - no response sent")
        else:
            # No interrupt needed - email sent automatically
            print("✅ Email processed and sent automatically (low priority)")


def run_test():
    """Original test function - single email test"""
    initial_state = {
        "email_content": "I was charged twice for my subscription! This is urgent!",
        "sender_email": "customer@example.com",
        "email_id": "email_123"
    }

    config = {"configurable": {"thread_id": "customer_123"}}
    result = app.invoke(initial_state, config)

    if "__interrupt__" in result:
        print("\nDraft ready for review:")
        print(result["draft_response"][:100], "...\n")

        human = Command(resume={"approved": True})
        final = app.invoke(human, config)

        print("Email sent successfully!")


if __name__ == "__main__":
    # Choose which mode to run
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("Running single test...")
        run_test()
    else:
        # Default: interactive mode
        run_interactive()
