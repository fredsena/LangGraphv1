import pathlib
import re
import time

import requests
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_community.utilities import SQLDatabase
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import tool
from langchain.agents import create_agent

from langchain.agents.middleware import PIIMiddleware, SummarizationMiddleware

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver, InMemorySaver
from typing import Literal
from langchain.tools import tool

from typing_extensions import NotRequired

from langchain.tools.tool_node import ToolCallRequest
from langchain.messages import ToolMessage
from langgraph.types import Command
from typing import Callable

from langchain.agents.middleware import wrap_tool_call

import os

from langchain.agents.middleware import (
    AgentMiddleware,
    AgentState,
    ModelRequest,
    ModelResponse,
)
from langgraph.runtime import Runtime
from typing import Any, Callable

# Rich library imports for beautiful terminal output
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.status import Status
from rich.syntax import Syntax
from rich.theme import Theme

# prompt_toolkit for cross-platform history support (arrow up/down)
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.formatted_text import HTML

# Initialize Rich console with custom theme
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "bot": "bold cyan",
    "user": "bold green"
})
console = Console(theme=custom_theme)

# Define allowed directories for file operations
ALLOWED_DIRS = [
    pathlib.Path.home() / "documents",  # /home/user/documents on Linux, C:\Users\user\documents on Windows
    pathlib.Path.home() / "Downloads",
    pathlib.Path("/tmp"),               # /tmp on Linux
    pathlib.Path("C:\\Users\\user\\AppData\\Local\\Temp") if os.name == 'nt' else pathlib.Path("/tmp")  # Temp on Windows
]

def is_path_allowed(file_path: str) -> bool:
    """Check if a file path is within allowed directories."""
    try:
        resolved = pathlib.Path(file_path).expanduser().resolve()
        return any(str(resolved).startswith(str(allowed.resolve())) for allowed in ALLOWED_DIRS)
    except Exception:
        return False

@tool(
    "find_file",
    parse_docstring=True,
    description=(
        "Find files by name or pattern across a directory tree. "
        "Works on both Linux and Windows. Returns the full paths of matching files."
    ),
)
def find_file(
    filename: str, 
    search_dir: str = ".",
    recursive: bool = True
) -> str:
    """Find files by name or pattern in a directory.

    Args:
        filename (str): The file name or pattern to search for (e.g., "*.txt", "config.json").
        search_dir (str): The directory to search in. Defaults to current directory.
        recursive (bool): Whether to search subdirectories. Defaults to True.

    Returns:
        str: Comma-separated list of full paths to matching files, or "No files found" if empty.

    Raises:
        ValueError: If the search directory doesn't exist.
    """
    console.print(f"🔍 Searching for '[cyan]{filename}[/cyan]' in '[blue]{search_dir}[/blue]'", style="info")
    
    # Convert to pathlib.Path for cross-platform compatibility
    search_path = pathlib.Path(search_dir).expanduser().resolve()
    
    if not search_path.exists():
        raise ValueError(f"Directory does not exist: {search_path}")
    
    if not search_path.is_dir():
        raise ValueError(f"Path is not a directory: {search_path}")
    
    # Search for matching files
    try:
        if recursive:
            # Recursive search using glob
            matches = list(search_path.glob(f"**/{filename}"))
        else:
            # Non-recursive search
            matches = list(search_path.glob(filename))
        
        if matches:
            # Convert to absolute paths and return as comma-separated string
            file_paths = [str(m.resolve()) for m in matches]
            return ", ".join(file_paths)
        else:
            return f"No files found matching '{filename}' in {search_path}"
    
    except Exception as e:
        return f"Error during search: {str(e)}"

@tool(
    "read_file",
    parse_docstring=True,
    description=(
        "Read the contents of a text file. "
        "Works on both Linux and Windows. Automatically detects encoding."
    ),
)
def read_file(
    file_path: str,
    max_lines: int = None
) -> str:
    """Read the contents of a text file.

    Args:
        file_path (str): The full path to the file to read.
        max_lines (int): Maximum number of lines to return. None means read entire file.

    Returns:
        str: The contents of the file, or an error message if file cannot be read.

    Raises:
        ValueError: If the file doesn't exist or cannot be read.
    """
    console.print(f"📄 Reading file: '[cyan]{file_path}[/cyan]'", style="info")
    
    # Convert to pathlib.Path for cross-platform compatibility
    path = pathlib.Path(file_path).expanduser().resolve()
    
    if not path.exists():
        raise ValueError(f"File does not exist: {path}")
    
    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")
    
    try:
        # Try to read with UTF-8 first (most common)
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        # Fall back to system default encoding if UTF-8 fails
        try:
            with open(path, 'r', encoding='latin-1') as f:
                lines = f.readlines()
        except Exception as e:
            raise ValueError(f"Cannot read file with UTF-8 or latin-1 encoding: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error reading file: {str(e)}")
    
    # Limit lines if specified
    if max_lines is not None:
        lines = lines[:max_lines]
    
    # Join and return content
    content = ''.join(lines)
    
    if not content:
        return f"File is empty: {path}"
    
    return content     

@tool(
    "write_file",
    parse_docstring=True,
    description=(
        "Write or create a text file with the given content. "
        "Works on both Linux and Windows. Creates parent directories if needed."
    ),
)
def write_file(
    file_path: str,
    content: str,
    append: bool = False
) -> str:
    """Write content to a text file.

    Args:
        file_path (str): The full path where the file should be written.
        content (str): The content to write to the file.
        append (bool): If True, append to existing file. If False, overwrite. Defaults to False.

    Returns:
        str: Success message with file path and size, or an error message.

    Raises:
        ValueError: If the file cannot be written.
    """
    console.print(f"✍️  Writing to file: '[cyan]{file_path}[/cyan]'", style="info")
    
    # Convert to pathlib.Path for cross-platform compatibility
    path = pathlib.Path(file_path).expanduser().resolve()
    
    try:
        # Create parent directories if they don't exist
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write or append to file
        mode = 'a' if append else 'w'
        with open(path, mode, encoding='utf-8') as f:
            f.write(content)
        
        # Get file size in bytes
        file_size = path.stat().st_size
        action = "appended to" if append else "written to"
        
        return f"✅ Content successfully {action} '{path}' ({file_size} bytes)"
    
    except PermissionError:
        raise ValueError(f"Permission denied: Cannot write to {path}")
    except IOError as e:
        raise ValueError(f"IO error while writing file: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error writing file: {str(e)}")

@tool(
    "list_files",
    parse_docstring=True,
    description="List all files and folders in a specified directory."
)
def list_files(folder_path: str, show_hidden: bool = False) -> str:
    """List all files and folders in a specified directory.
    
    Args:
        folder_path (str): The path to the folder to list.
                          Can be relative or absolute path.
                          Works on both Linux and Windows.
        show_hidden (bool): Whether to show hidden files (default: False).
                           On Linux, hidden files start with a dot.
    
    Returns:
        str: A formatted string listing all files and folders with their types.
    
    Raises:
        FileNotFoundError: If the folder does not exist.
        NotADirectoryError: If the path is not a directory.
    """
    print("📁 Invoking list_files tool")
    
    # Convert to pathlib Path for cross-platform compatibility
    path = pathlib.Path(folder_path).expanduser().resolve()
    
    # Validate the path exists and is a directory
    if not path.exists():
        raise FileNotFoundError(f"Folder does not exist: {folder_path}")
    
    if not path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {folder_path}")
    
    # List files and directories
    items = []
    try:
        for item in sorted(path.iterdir()):
            # Skip hidden files if show_hidden is False
            if not show_hidden and item.name.startswith('.'):
                continue
            
            # Determine if it's a file or directory
            item_type = "📁 [DIR]" if item.is_dir() else "📄 [FILE]"
            items.append(f"{item_type}  {item.name}")
    
    except PermissionError:
        raise PermissionError(f"Permission denied accessing folder: {folder_path}")
    
    if not items:
        return f"Folder is empty: {folder_path}"
    
    result = f"Contents of {path}:\n\n" + "\n".join(items)
    return result

# =============================================================================
# RICH HELPER FUNCTIONS
# =============================================================================

def type_print(text: str, style: str = "white", speed: float = 0.005):
    """Print text with typing effect character by character.
    
    Args:
        text: The text to print
        style: Rich style to apply (e.g., "bold cyan", "green")
        speed: Delay between characters in seconds
    """
    for char in text:
        console.print(char, end="", style=style)
        time.sleep(speed)
    console.print()  # New line at the end

def render_markdown_response(text: str, speed: float = 0):
    """Render response with optional typing effect for markdown.
    
    Args:
        text: The text to render (supports markdown)
        speed: Typing speed (0 for instant)
    """
    if speed > 0:
        # Type out plain text with effects
        type_print(text, style="white", speed=speed)
    else:
        # Instant markdown rendering
        console.print(Markdown(text))

def print_code_block(code: str, language: str = "python"):
    """Print code with syntax highlighting.
    
    Args:
        code: The code to display
        language: Programming language for syntax highlighting
    """
    syntax = Syntax(code, language, theme="monokai", line_numbers=True)
    console.print(syntax)

class LoggingMiddleware(AgentMiddleware):
    def before_agent(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        print(f"About to call model with {len(state['messages'])} messages")        
        return None

    def after_agent(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        print(f"Model returned: {state['messages'][-1].content}")
        return None

# class ToolMonitoringMiddleware(AgentMiddleware):
#     def wrap_tool_call(
#         self,
#         request: ToolCallRequest,
#         handler: Callable[[ToolCallRequest], ToolMessage | Command],
#     ) -> ToolMessage | Command:
#         print(f"Executing tool: {request.tool_call['name']}")
#         print(f"Arguments: {request.tool_call['args']}")
#         try:
#             result = handler(request)
#             print(f"Tool completed successfully")
#             return result
#         except Exception as e:
#             print(f"Tool failed: {e}")
#             raise

# class CustomState(AgentState):
#     model_call_count: NotRequired[int]
#     user_id: NotRequired[str]


# class CallCounterMiddleware(AgentMiddleware[CustomState]):
#     state_schema = CustomState

#     def before_model(self, state: CustomState, runtime) -> dict[str, Any] | None:
#         count = state.get("model_call_count", 0)
#         if count > 1:
#             print(f"user_id: {state['user_id']}")        
#             #return {"jump_to": "end"}
#         return None

#     def after_model(self, state: CustomState, runtime) -> dict[str, Any] | None:
#         return {"model_call_count": state.get("model_call_count", 0) + 1}

# =============================================================================
# LANGCHAIN SETUP
# =============================================================================

llm = ChatOpenAI(
    model="qwen/qwen3-4b-2507", 
    #model="openai/gpt-oss-20b",
    #model="qwen/qwen3-30b-a3b-2507",
    base_url="http://127.0.0.1:1234/v1", 
    temperature=0.0, 
    api_key="11111111111111")

agent = create_agent(
    system_prompt="You are a helpful assistant.",
    model=llm,
    checkpointer=InMemorySaver(),
    tools=[find_file,read_file,write_file,list_files],
    # middleware=[LoggingMiddleware()    
    #     # PIIMiddleware(
    #     #     "email", 
    #     #     strategy="redact", 
    #     #     #apply_to_input = True, 
    #     #     #apply_to_output = True
    #     #     ),
    # ],    
)

# =============================================================================
# ENHANCED CHAT LOOP WITH RICH UI
# =============================================================================

# Thread ID for maintaining conversation history
thread_id = "conversation_1"

# Display beautiful header
console.print()
console.print(Panel.fit(
    "[bold cyan]🤖 AI Assistant Chat Bot[/bold cyan]\n\n"
    "[dim]Features:[/dim]\n"
    "  • Terminal-like typing effects\n"
    "  • File operations (find, read, write)\n"
    "  • Conversation history\n\n"
    "[yellow]Type 'quit', 'exit', or 'bye' to end the conversation.[/yellow]",
    border_style="cyan",
    padding=(1, 2)
))
console.print()

# Initialize prompt session with persistent history file
history_file = pathlib.Path.home() / ".chat_history"
session = PromptSession(history=FileHistory(str(history_file)))

# Chat loop
while True:
    # Get user input with prompt_toolkit (supports arrow up/down history)
    try:
        user_input = session.prompt(HTML('\n<ansigreen><b>You:</b></ansigreen> ')).strip()
    except (KeyboardInterrupt, EOFError):
        console.print("\n[yellow]👋 Goodbye![/yellow]")
        break
    
    # Check for exit commands
    if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
        console.print("\n[bold yellow]👋 Thanks for chatting! Goodbye![/bold yellow]")
        break
    
    # Skip empty inputs
    if not user_input:
        continue
    
    # Create human message
    human_msg = HumanMessage(user_input)
    
    # Show status while AI is thinking
    with console.status("[bold cyan]🤖 Thinking...", spinner="dots"):
        # Invoke agent with thread configuration to maintain history
        result = agent.invoke(
            {"messages": [human_msg]},
            config={"configurable": {"thread_id": thread_id}}
        )
    
    # Get and display the AI's response with typing effect
    ai_response = result["messages"][-1].content
    console.print("\n[bold cyan]🤖 Bot:[/bold cyan] ", end="")
    #type_print(ai_response, style="white", speed=0)
    render_markdown_response(ai_response, speed=0)

console.print("\n")
