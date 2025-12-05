# Deep Agents State Management Guide

A comprehensive guide to understanding state management in LangGraph agents, focusing on reducers, TODOs, and virtual file systems.

---

## Table of Contents

1. [Overview](#overview)
2. [File Reducer](#file-reducer)
3. [Type Annotations Deep Dive](#type-annotations-deep-dive)
4. [TODO System](#todo-system)
5. [TODO Removal](#todo-removal)
6. [Debugging TODOs](#debugging-todos)
7. [Best Practices](#best-practices)

---

## Overview

The Deep Agents pattern extends LangGraph's base `AgentState` with two key capabilities:

- **TODO Management**: Task planning and progress tracking
- **Virtual File System**: Context offloading through in-state file storage

### State Schema

From [`utils/state.py`](file:///home/fredsena/FredCodes/GIT/LangGraphv1/utils/state.py):

```python
class DeepAgentState(AgentState):
    """Extended agent state with task tracking and virtual file system."""
    
    todos: NotRequired[list[Todo]]
    files: Annotated[NotRequired[dict[str, str]], file_reducer]
```

**Key Difference:**
- `todos`: No reducer → **complete replacement** on update
- `files`: Has reducer → **incremental merging** on update

---

## File Reducer

### What is a Reducer?

A **reducer** is a function that defines how state updates should be merged when multiple nodes update the same state field.

### The `file_reducer` Function

```python
def file_reducer(left, right):
    """Merge two file dictionaries, with right side taking precedence.
    
    Args:
        left: Existing files in state
        right: New/updated files
        
    Returns:
        Merged dictionary with right values overriding left values
    """
    if left is None:
        return right
    elif right is None:
        return left
    else:
        return {**left, **right}
```

### Why is it Needed?

**Without a reducer:**
- State fields are **completely overwritten** on each update
- Previous data is **lost**

**With `file_reducer`:**
- Files are **incrementally added** or updated
- Existing files **remain** unless explicitly overwritten
- Agent builds up a virtual file system over multiple steps

### How is it Used?

The reducer is attached to the `files` field via type annotation:

```python
files: Annotated[NotRequired[dict[str, str]], file_reducer]
```

The `Annotated` wrapper tells LangGraph to use `file_reducer` when merging updates.

### Practical Example

**Step 1:** Tool creates `{"todo.txt": "Buy groceries"}`  
**Step 2:** Tool creates `{"notes.txt": "Meeting at 3pm"}`  
**Step 3:** Tool updates `{"todo.txt": "Buy groceries and milk"}`

**Without reducer:**
```python
# State after Step 3
{"todo.txt": "Buy groceries and milk"}  # Lost notes.txt!
```

**With `file_reducer`:**
```python
# State after Step 3
{
    "todo.txt": "Buy groceries and milk",  # Updated
    "notes.txt": "Meeting at 3pm"           # Preserved
}
```

### Is the Reducer Being Used?

In [`09.deep-agents-todo.py`](file:///home/fredsena/FredCodes/GIT/LangGraphv1/09.deep-agents-todo.py#L106):

```python
agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=TODO_USAGE_INSTRUCTIONS + "\n\n" + "=" * 80 + "\n\n",
    state_schema=DeepAgentState,  # ← Configured to use file_reducer
)
```

**Status:** The reducer is **configured** but **not actively used** because:
- No tools write to `state["files"]`
- Only `todos` are initialized in the invocation
- Current tools (`write_todos`, `read_todos`, `web_search`) don't interact with files

The reducer would execute if tools wrote to the `files` field.

---

## Type Annotations Deep Dive

### Understanding `Annotated[NotRequired[dict[str, str]], file_reducer]`

This combines three Python typing features:

#### 1. Base Type: `dict[str, str]`

```python
dict[str, str]  # Dictionary with string keys → string values
```

**Example:**
```python
{"readme.txt": "Hello World", "data.json": "{...}"}
```

#### 2. Optional Field: `NotRequired[...]`

```python
NotRequired[dict[str, str]]  # Field can be omitted from TypedDict
```

**Yes, it's an optional parameter!**

✅ **Valid:** `{"messages": [...], "todos": []}`  
✅ **Also Valid:** `{"messages": [...], "todos": [], "files": {"note.txt": "content"}}`

Without `NotRequired`, you'd be **required** to provide the `files` field every time.

#### 3. Metadata: `Annotated[..., file_reducer]`

```python
Annotated[NotRequired[dict[str, str]], file_reducer]
```

The `Annotated` wrapper attaches **metadata** (the `file_reducer` function) to the type.  
LangGraph reads this metadata to know **how to merge** updates to this field.

### Complete Translation

```python
files: Annotated[NotRequired[dict[str, str]], file_reducer]
```

Means:
- **Type:** Dictionary mapping strings to strings
- **Optional:** Can be omitted from state initialization
- **Reducer:** When updated, use `file_reducer` to merge old and new values

### Comparison

```python
class DeepAgentState(AgentState):
    todos: NotRequired[list[Todo]]                              # Optional, NO reducer
    files: Annotated[NotRequired[dict[str, str]], file_reducer] # Optional WITH reducer
```

- **`todos`**: Optional, but updates **replace** the entire list
- **`files`**: Optional, but updates **merge** using `file_reducer`

---

## TODO System

### The `Todo` Class

From [`utils/state.py`](file:///home/fredsena/FredCodes/GIT/LangGraphv1/utils/state.py#L15-L24):

```python
class Todo(TypedDict):
    """A structured task item for tracking progress through complex workflows."""
    
    content: str
    status: Literal["pending", "in_progress", "completed"]
```

**Structure:**
- **`content`**: Task description (e.g., "Search for MCP documentation")
- **`status`**: One of three states → `"pending"`, `"in_progress"`, or `"completed"`

### Why Does the Agent Need TODOs?

The TODO system enables **task planning and progress tracking** for complex multi-step workflows.

**Problem it solves:**
- Complex user requests require multiple steps
- Without structure, agents can lose track of what they've done
- Agents need to break down big tasks into manageable pieces

**Solution:**
- Provides agents with **working memory** for their plan
- Enables **systematic execution** of multi-step tasks
- Allows **progress tracking** through status updates

### TODO Tools

From [`utils/todo_tools.py`](file:///home/fredsena/FredCodes/GIT/LangGraphv1/utils/todo_tools.py):

#### Tool 1: `write_todos`

```python
@tool(description=WRITE_TODOS_DESCRIPTION, parse_docstring=True)
def write_todos(
    todos: list[Todo], 
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command:
    """Create or update the agent's TODO list."""
    return Command(
        update={
            "todos": todos,  # Updates the state
            "messages": [
                ToolMessage(f"Updated todo list to {todos}", tool_call_id=tool_call_id)
            ]
        }
    )
```

**Purpose:** Agent calls this to **create or update** its TODO list in state.

#### Tool 2: `read_todos`

```python
@tool(parse_docstring=True)
def read_todos(
    state: Annotated[DeepAgentState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> str:
    """Read the current TODO list from the agent state."""
    todos = state.get("todos", [])
    if not todos:
        return "No todos currently in the list."
    
    result = "Current TODO List:\n"
    for i, todo in enumerate(todos, 1):
        status_emoji = {"pending": "⏳", "in_progress": "🔄", "completed": "✅"}
        emoji = status_emoji.get(todo["status"], "❓")
        result += f"{i}. {emoji} {todo['content']} ({todo['status']})\n"
    
    return result.strip()
```

**Purpose:** Agent calls this to **review** its current plan and track progress.

**Output Format:**
```
Current TODO List:
1. ⏳ Get current time in London (pending)
2. 🔄 Research C# improvements (in_progress)
3. ✅ Summarize Model Context Protocol (completed)
```

### Agent Workflow with TODOs

From [`utils/prompts.py`](file:///home/fredsena/FredCodes/GIT/LangGraphv1/utils/prompts.py#L36-L45):

```
1. User makes complex request
2. Agent calls write_todos to create initial plan
3. Agent works on first TODO
4. Agent calls read_todos to check progress
5. Agent reflects on what's done
6. Agent calls write_todos to mark task completed
7. Agent moves to next TODO
8. Repeat until all TODOs completed
```

### Real-World Example

From [`09.deep-agents-todo.py`](file:///home/fredsena/FredCodes/GIT/LangGraphv1/09.deep-agents-todo.py#L114-L124):

```python
result = await agent.ainvoke(
    {
        "messages": [{
            "role": "user",
            "content": "What time is it in London? Tell me 2 C# improvements. Summarize MCP.",
        }],
        "todos": [],  # Starts empty
    }
)
```

**Expected internal workflow:**

**Step 1 - Create Plan:**
```python
write_todos([
    {"content": "Get current time in London", "status": "pending"},
    {"content": "Research C# latest version improvements", "status": "pending"},
    {"content": "Summarize Model Context Protocol", "status": "pending"}
])
```

**Step 2 - Start First Task:**
```python
write_todos([
    {"content": "Get current time in London", "status": "in_progress"},
    {"content": "Research C# latest version improvements", "status": "pending"},
    {"content": "Summarize Model Context Protocol", "status": "pending"}
])
```

**Step 3 - Check Progress:**
```python
read_todos()
# Returns: "1. 🔄 Get current time in London (in_progress), ..."
```

**Step 4 - Complete Task:**
```python
write_todos([
    {"content": "Get current time in London", "status": "completed"},
    {"content": "Research C# latest version improvements", "status": "in_progress"},
    {"content": "Summarize Model Context Protocol", "status": "pending"}
])
```

**Step 5 - Continue** until all marked `"completed"`

### Design Principles

From [`utils/prompts.py`](file:///home/fredsena/FredCodes/GIT/LangGraphv1/utils/prompts.py#L7-L34):

- ✅ **Only one `in_progress` task at a time** (focused execution)
- ✅ **Mark completed immediately** (real-time tracking)
- ✅ **Always send full updated list** (state consistency)
- ✅ **Prune irrelevant items** (keep list focused)

---

## TODO Removal

### Key Mechanism: Complete Replacement

TODOs are removed through **complete list replacement**, NOT individual removal.

```python
class DeepAgentState(AgentState):
    todos: NotRequired[list[Todo]]  # ← NO reducer!
    files: Annotated[NotRequired[dict[str, str]], file_reducer]  # ← HAS reducer
```

**`todos`** has **NO reducer function**, which means:
- Each update **replaces the entire list**
- Unlike `files` which **merges** updates

### The Removal Process

From [`utils/todo_tools.py`](file:///home/fredsena/FredCodes/GIT/LangGraphv1/utils/todo_tools.py#L32-L38):

```python
return Command(
    update={
        "todos": todos,  # ← Completely replaces the list
        ...
    }
)
```

### Practical Examples

#### Example 1: Removing Completed Tasks

**Current state:**
```python
[
    {"content": "Search for info", "status": "completed"},
    {"content": "Write report", "status": "in_progress"},
    {"content": "Send email", "status": "pending"}
]
```

**Agent calls:**
```python
write_todos([
    {"content": "Write report", "status": "in_progress"},
    {"content": "Send email", "status": "pending"}
])
# Completed task is removed by not including it
```

#### Example 2: Pruning Irrelevant Tasks

From the tool description:
> **"Prune irrelevant items to keep list focused"**

The agent can remove tasks that are no longer relevant by sending a new list without them.

#### Example 3: Clearing All TODOs

```python
write_todos([])  # Empty list removes all TODOs
```

### Why This Design?

**Advantages:**
- ✅ Simple and explicit - no confusion about state
- ✅ Allows pruning/reorganizing the entire list
- ✅ Prevents accumulation of old tasks

**Contrast with `files`:**
- **Files** (with reducer) → accumulate - new files merge with old ones
- **TODOs** (no reducer) → replace - new list overwrites old list

---

## Debugging TODOs

### Debug Scripts

Two debugging scripts are available:

#### 1. Simple Debug Script (Recommended)

[`09-simple-debug-todos.py`](file:///home/fredsena/FredCodes/GIT/LangGraphv1/09-simple-debug-todos.py)

A clean, easy-to-read script showing:
- Each step the agent takes
- Current TODO list with status icons
- Tool calls being made
- Key messages

**Run it:**
```bash
cd /home/fredsena/FredCodes/GIT/LangGraphv1
python 09-simple-debug-todos.py
```

#### 2. Comprehensive Debug Script

[`09-debug-todos.py`](file:///home/fredsena/FredCodes/GIT/LangGraphv1/09-debug-todos.py)

Demonstrates three debugging methods:
- **Method 1**: Event streaming with detailed tracking
- **Method 2**: Step-by-step state inspection
- **Method 3**: Final state inspection

### Manual Debugging Techniques

#### Technique 1: Stream Updates

```python
async for state_update in agent.astream(
    {"messages": [...], "todos": []},
    stream_mode="updates"
):
    for node_name, node_data in state_update.items():
        if "todos" in node_data:
            print(f"TODOs: {node_data['todos']}")
```

#### Technique 2: Event Streaming

```python
async for event in agent.astream_events(
    {"messages": [...], "todos": []},
    version="v2"
):
    if event["event"] == "on_tool_start":
        if event["name"] == "write_todos":
            todos = event["data"].get("input", {}).get("todos", [])
            print(f"Writing TODOs: {todos}")
```

#### Technique 3: Final State Inspection

```python
result = await agent.ainvoke({"messages": [...], "todos": []})
print(f"Final TODOs: {result.get('todos', [])}")
```

### Expected Output Format

```
================================================================================
USER REQUEST: What time is it in London? Tell me about MCP...
================================================================================

📍 STEP 1 - Node: agent
🔧 Tool Calls: ['write_todos']

📍 STEP 2 - Node: tools
📝 TODO LIST:
   1. ⏳ Get current time in London (pending)
   2. ⏳ Research Model Context Protocol (pending)
   3. ⏳ Search for C# improvements (pending)

📍 STEP 3 - Node: agent
📝 TODO LIST:
   1. 🔄 Get current time in London (in_progress)
   2. ⏳ Research Model Context Protocol (pending)
   3. ⏳ Search for C# improvements (pending)
```

### Status Icons

- ⏳ **Pending**: Task not started
- 🔄 **In Progress**: Currently working on task
- ✅ **Completed**: Task finished

---

## Best Practices

### State Management

1. **Use reducers for accumulating data** (like files)
2. **Don't use reducers for planned data** (like todos)
3. **Keep state fields optional** when appropriate with `NotRequired`
4. **Attach metadata** with `Annotated` for custom merge behavior

### TODO Management

1. **Create TODOs for complex multi-step tasks**
   - Single trivial actions don't need TODOs
   - Multi-step workflows benefit from structure

2. **Keep only one task in_progress at a time**
   - Maintains focus
   - Easier to track progress

3. **Mark tasks completed immediately**
   - Real-time tracking
   - Clear progress visibility

4. **Prune completed or irrelevant tasks**
   - Keep list focused
   - Prevent state bloat

5. **Use descriptive content**
   - Clear, actionable descriptions
   - Helps agent stay on track

### Debugging

1. **Use streaming for real-time visibility**
   - See state updates as they happen
   - Catch issues early

2. **Inspect state at key checkpoints**
   - After tool calls
   - Between major steps

3. **Add visual indicators**
   - Status emojis for quick scanning
   - Clear separators between steps

4. **Log tool calls**
   - Track which tools are invoked
   - Understand agent decision-making

---

## Summary

### Key Concepts

| Concept | Purpose | Behavior |
|---------|---------|----------|
| **File Reducer** | Merge file updates | Accumulates files, merges new with old |
| **TODO System** | Task planning & tracking | Replaces entire list on update |
| **Annotated Type** | Attach metadata to types | Tells LangGraph how to merge state |
| **NotRequired** | Optional fields | State initialization can omit field |

### State Field Comparison

| Field | Type | Reducer | Update Behavior |
|-------|------|---------|-----------------|
| `todos` | `list[Todo]` | ❌ None | **Replace** entire list |
| `files` | `dict[str, str]` | ✅ `file_reducer` | **Merge** dictionaries |

### Tools

| Tool | Purpose | Updates State |
|------|---------|---------------|
| `write_todos` | Create/update TODO list | Replaces `todos` field |
| `read_todos` | Read current TODO list | Read-only, no state changes |

---

## References

### Source Files

- [`utils/state.py`](file:///home/fredsena/FredCodes/GIT/LangGraphv1/utils/state.py) - State definitions
- [`utils/todo_tools.py`](file:///home/fredsena/FredCodes/GIT/LangGraphv1/utils/todo_tools.py) - TODO management tools
- [`utils/prompts.py`](file:///home/fredsena/FredCodes/GIT/LangGraphv1/utils/prompts.py) - System prompts and instructions
- [`09.deep-agents-todo.py`](file:///home/fredsena/FredCodes/GIT/LangGraphv1/09.deep-agents-todo.py) - Main agent implementation
- [`09-simple-debug-todos.py`](file:///home/fredsena/FredCodes/GIT/LangGraphv1/09-simple-debug-todos.py) - Simple debugging script
- [`09-debug-todos.py`](file:///home/fredsena/FredCodes/GIT/LangGraphv1/09-debug-todos.py) - Comprehensive debugging script

---

**Last Updated:** 2025-11-29  
**Author:** Based on conversation with Fred Sena
