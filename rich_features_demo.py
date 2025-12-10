"""
Rich Library Features Demo - All Terminal Features

This script demonstrates all the Rich library features available in your chatbot:
1. Typing effects
2. Status spinners
3. Panels and formatted text
4. Markdown rendering
5. Syntax highlighting
6. Custom themes
"""

import time
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.status import Status
from rich.syntax import Syntax
from rich.theme import Theme
from rich.table import Table
from rich.progress import track

# Initialize Rich console with custom theme
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
})
console = Console(theme=custom_theme)

def demo_header():
    """Show beautiful header panel"""
    console.print()
    console.print(Panel.fit(
        "[bold cyan]🎨 Rich Library Features Demo[/bold cyan]\n\n"
        "[dim]Demonstrating all terminal features:[/dim]\n"
        "  • Typing effects\n"
        "  • Status spinners\n"
        "  • Panels & themes\n"
        "  • Markdown rendering\n"
        "  • Syntax highlighting",
        border_style="cyan",
        padding=(1, 2)
    ))
    console.print()

def demo_typing_effect():
    """Demonstrate typing effect"""
    console.rule("[bold cyan]1. Typing Effect Demo")
    console.print("\n[bold]Normal print:[/bold]")
    console.print("This appears instantly!")
    
    console.print("\n[bold]Typing effect:[/bold]")
    text = "This text appears character by character, like a terminal! ⌨️"
    for char in text:
        console.print(char, end="", style="bold green")
        time.sleep(0.0005)
    console.print("\n")

def demo_status_spinner():
    """Demonstrate status spinner"""
    console.rule("[bold cyan]2. Status Spinner Demo")
    console.print()
    
    with console.status("[bold cyan]🔄 Processing...", spinner="dots"):
        time.sleep(2)
    console.print("[success]✅ Processing complete!\n")
    
    with console.status("[bold yellow]⏳ Loading data...", spinner="bouncingBall"):
        time.sleep(2)
    console.print("[success]✅ Data loaded!\n")

def demo_panels():
    """Demonstrate panels and formatting"""
    console.rule("[bold cyan]3. Panels & Formatting Demo")
    console.print()
    
    # Info panel
    console.print(Panel(
        "[cyan]This is an informational panel with a cyan border.[/cyan]",
        title="ℹ️ Info",
        border_style="cyan"
    ))
    
    # Warning panel
    console.print(Panel(
        "[yellow]This is a warning panel. Pay attention![/yellow]",
        title="⚠️ Warning",
        border_style="yellow"
    ))
    
    # Success panel
    console.print(Panel(
        "[green]Operation completed successfully! ✨[/green]",
        title="✅ Success",
        border_style="green"
    ))
    console.print()

def demo_markdown():
    """Demonstrate markdown rendering"""
    console.rule("[bold cyan]4. Markdown Rendering Demo")
    console.print()
    
    markdown_text = """
# This is a Heading

This is **bold text** and this is *italic text*.

## Features List:
- Item 1
- Item 2
- Item 3

### Code Example:
```python
def hello_world():
    print("Hello, World!")
```

> This is a blockquote!
"""
    console.print(Markdown(markdown_text))
    console.print()

def demo_syntax_highlighting():
    """Demonstrate syntax highlighting"""
    console.rule("[bold cyan]5. Syntax Highlighting Demo")
    console.print()
    
    python_code = '''
def fibonacci(n):
    """Calculate Fibonacci sequence"""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Calculate first 10 numbers
for i in range(10):
    print(f"F({i}) = {fibonacci(i)}")
'''
    
    syntax = Syntax(python_code, "python", theme="monokai", line_numbers=True)
    console.print(syntax)
    console.print()

def demo_table():
    """Demonstrate rich tables"""
    console.rule("[bold cyan]6. Table Demo")
    console.print()
    
    table = Table(title="🎨 Rich Features Comparison", show_header=True, header_style="bold magenta")
    table.add_column("Feature", style="cyan", width=20)
    table.add_column("Standard Print", style="red")
    table.add_column("Rich Library", style="green")
    
    table.add_row("Colors", "❌ No", "✅ Yes")
    table.add_row("Typing Effect", "❌ No", "✅ Yes")
    table.add_row("Spinners", "❌ No", "✅ Yes")
    table.add_row("Markdown", "❌ No", "✅ Yes")
    table.add_row("Syntax Highlight", "❌ No", "✅ Yes")
    
    console.print(table)
    console.print()

def demo_progress():
    """Demonstrate progress bars"""
    console.rule("[bold cyan]7. Progress Bar Demo")
    console.print()
    
    console.print("[cyan]Processing items...[/cyan]")
    for i in track(range(20), description="[green]Loading..."):
        time.sleep(0.1)
    console.print("[success]✅ All items processed!\n")

def main():
    """Run all demos"""
    demo_header()
    time.sleep(1)
    
    demo_typing_effect()
    time.sleep(1)
    
    demo_status_spinner()
    time.sleep(1)
    
    demo_panels()
    time.sleep(1)
    
    demo_markdown()
    time.sleep(1)
    
    demo_syntax_highlighting()
    time.sleep(1)
    
    demo_table()
    time.sleep(1)
    
    demo_progress()
    
    # Final message
    console.print(Panel.fit(
        "[bold green]🎉 Demo Complete![/bold green]\n\n"
        "[cyan]All these features are now available in your chatbot![/cyan]",
        border_style="green",
        padding=(1, 2)
    ))

if __name__ == "__main__":
    main()
