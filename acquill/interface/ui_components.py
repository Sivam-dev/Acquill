"""
UI Components for Acquill Terminal Interface
Provides consistent branding, styling, and visual elements
"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.markdown import Markdown
import random
import time

# Color scheme
BRAND_PRIMARY = "bright_cyan"
BRAND_SECONDARY = "bright_magenta"
SUCCESS_COLOR = "bright_green"
WARNING_COLOR = "yellow"
ERROR_COLOR = "bright_red"
MUTED_COLOR = "dim"
CODE_STYLE = "monokai"

# ASCII logo: banner("ACQUILL", { shadow: "rounded", effect: "still", fill: "█" })
# from the ascii-rest skill (.agents/skills/ascii-rest). Solid fill because
# some terminal fonts render the default ▓ shade as sparse dots.
# Still frame baked in so startup needs no Node at runtime.
ACQUILL_LOGO = """
  ████╮     ██████╮   ████╮   ██╮   ██╮ ██╮ ██╮       ██╮
██╭───██╮ ██╭─────╯ ██╭───██╮ ██│   ██│ ██│ ██│       ██│
████████│ ██│       ██│   ██│ ██│   ██│ ██│ ██│       ██│
██╭───██│ ██│       ██│ ██╭─╯ ██│   ██│ ██│ ██│       ██│
      ██│   ██│ ╰─██████╮ ╰─██╭─██╮ ╰─████╭─╯ ██│ ████████╮ ████████╮
      ╰─╯   ╰─╯   ╰─────╯   ╰─╯ ╰─╯   ╰───╯   ╰─╯ ╰───────╯ ╰───────╯
"""

GLITCH_JUNK = "█▓▒░<>[]{}=+*#%@&01"

TAGLINE = "Your AI companion with persistent memory."


def render_logo(console: Console, show_tagline: bool = True):
    """Display the ACQUILL ASCII logo with tagline"""
    logo_text = Text()
    
    # Add logo in gradient effect (cyan to magenta)
    for i, line in enumerate(ACQUILL_LOGO.strip("\n").split('\n')):
        if i < 3:
            logo_text.append(line + "\n", style=BRAND_PRIMARY)
        else:
            logo_text.append(line + "\n", style=BRAND_SECONDARY)
    
    if show_tagline:
        logo_text.append("\n")
        logo_text.append(TAGLINE, style="italic dim")
    
    console.print(logo_text, justify="center")


def _glitch_line(line, width):
    """One flicker row: random cells flipped to junk, padded to width."""
    chars = [
        random.choice(GLITCH_JUNK) if ch != " " and random.random() < 0.12 else ch
        for ch in line
    ]
    return "".join(chars).ljust(width)


def _glitch_reveal(console: Console):
    """Reveal the banner line by line with a junk flicker.

    Uses only carriage returns, no screen clears, so terminals that
    ignore clear-screen codes still show exactly 6 lines, never a stack.
    """
    lines = [line.rstrip() for line in ACQUILL_LOGO.strip("\n").split("\n")]
    width = max(len(line) for line in lines)
    indent = " " * max((console.width - width) // 2, 0)
    stream = console.file
    for i, line in enumerate(lines):
        for _ in range(2):
            stream.write(indent + _glitch_line(line, width) + "\r")
            stream.flush()
            time.sleep(0.05)
        row = Text()
        row.append(line, style=BRAND_PRIMARY if i < 3 else BRAND_SECONDARY)
        console.print(row, justify="center")
    tagline = Text()
    tagline.append(TAGLINE, style="italic dim")
    console.print(tagline, justify="center")


def render_startup_screen(console: Console):
    """Display the startup screen with logo and status"""
    console.clear()
    console.print()

    # Flicker reveal on real terminals; one still frame in pipes/logs.
    try:
        if console.is_terminal:
            _glitch_reveal(console)
        else:
            render_logo(console, show_tagline=True)
    except Exception:
        render_logo(console, show_tagline=True)
    console.print()
    
    # Status indicators
    status_text = Text()
    status_text.append("  ◉ ", style=SUCCESS_COLOR)
    status_text.append("Initializing session...", style=MUTED_COLOR)
    console.print(status_text)
    
    status_text = Text()
    status_text.append("  ◉ ", style=SUCCESS_COLOR)
    status_text.append("Loading your learning history", style=MUTED_COLOR)
    console.print(status_text)
    
    status_text = Text()
    status_text.append("  ◉ ", style=SUCCESS_COLOR)
    status_text.append("Ready to continue your journey", style=MUTED_COLOR)
    console.print(status_text)
    
    console.print()


def render_welcome_panel(console: Console, check_interval: int = 300, git_enabled: bool = True):
    """Display the main chat welcome panel"""
    welcome_content = Text()
    welcome_content.append("ACQUILL", style=f"bold {BRAND_PRIMARY}")
    welcome_content.append(" - Your AI Learning Companion\n\n", style="bold")
    welcome_content.append("I'm here to help you master DSA and ace your placement interviews.\n", style="dim")
    welcome_content.append("Share your code, ask questions, or tell me what you're working on.\n\n", style="dim")
    welcome_content.append("Commands: ", style="bold")
    welcome_content.append("Type ", style="dim")
    welcome_content.append("exit", style=f"bold {BRAND_SECONDARY}")
    welcome_content.append(" to quit", style="dim")
    
    panel = Panel(
        welcome_content,
        border_style=BRAND_PRIMARY,
        padding=(1, 2)
    )
    
    console.print(panel)
    
    # Git monitoring status
    status_line = Text()
    if git_enabled:
        status_line.append("◉ ", style=SUCCESS_COLOR)
        status_line.append("Git monitoring: ", style="dim")
        status_line.append(f"ON (every {check_interval}s)", style=BRAND_SECONDARY)
    else:
        status_line.append("○ ", style=MUTED_COLOR)
        status_line.append("Git monitoring: ", style="dim")
        status_line.append("OFF", style=MUTED_COLOR)
    status_line.append("  •  ", style="dim")
    status_line.append("Session: ", style="dim")
    status_line.append("active", style=SUCCESS_COLOR)
    
    console.print(status_line)
    console.print()


def render_user_message(console: Console, message: str):
    """Display a user message with consistent styling"""
    panel = Panel(
        message,
        title="[bold]You[/bold]",
        title_align="left",
        border_style="bright_white",
        padding=(0, 1)
    )
    console.print(panel)


def render_assistant_message(console: Console, message: str):
    """Display an assistant message with markdown support"""
    # Try to render as markdown, fall back to plain text
    try:
        content = Markdown(message)
    except Exception:
        content = message
    
    panel = Panel(
        content,
        title=f"[bold {BRAND_PRIMARY}]Acquill[/bold {BRAND_PRIMARY}]",
        title_align="left",
        border_style=BRAND_PRIMARY,
        padding=(1, 2)
    )
    console.print(panel)
    console.print()


def render_thinking_indicator(console: Console, message: str = "Acquill is thinking"):
    """Display a thinking/processing indicator"""
    text = Text()
    text.append("▸ ", style=BRAND_SECONDARY)
    text.append(message, style="dim")
    text.append("...", style=BRAND_SECONDARY)
    console.print(text)


def render_git_analysis(console: Console, files_changed: int, files_summary: str, 
                       topic: str, event_type: str, analysis: str):
    """Display git diff analysis in a structured format"""
    # Create analysis content
    content = Text()
    
    # Files changed
    content.append("📁 Modified Files\n", style=f"bold {BRAND_SECONDARY}")
    content.append(f"   {files_changed} file(s): ", style="dim")
    content.append(f"{files_summary}\n\n", style="")
    
    # Topic and event
    content.append("📚 Topic: ", style=f"bold {WARNING_COLOR}")
    content.append(f"{topic}\n", style="")
    content.append("⚡ Event: ", style=f"bold {BRAND_PRIMARY}")
    content.append(f"{event_type}\n\n", style="")
    
    # Analysis
    content.append("💬 Analysis\n", style=f"bold {SUCCESS_COLOR}")
    content.append(f"{analysis}", style="")
    
    panel = Panel(
        content,
        title="[bold]Code Analysis[/bold]",
        title_align="left",
        border_style=MUTED_COLOR,
        padding=(1, 2)
    )
    
    console.print(panel)
    console.print()


def render_error_message(console: Console, error: str, details: str = None):
    """Display an error message with consistent styling"""
    content = Text()
    content.append("⚠ ", style=ERROR_COLOR)
    content.append(error, style=f"bold {ERROR_COLOR}")
    
    if details:
        content.append("\n\n", style="")
        content.append(details, style="dim")
    
    panel = Panel(
        content,
        title="[bold red]Error[/bold red]",
        title_align="left",
        border_style=ERROR_COLOR,
        padding=(1, 2)
    )
    
    console.print(panel)
    console.print()


def render_success_message(console: Console, message: str, details: str = None):
    """Display a success message"""
    content = Text()
    content.append("✓ ", style=SUCCESS_COLOR)
    content.append(message, style=f"bold {SUCCESS_COLOR}")
    
    if details:
        content.append("\n\n", style="")
        content.append(details, style="dim")
    
    panel = Panel(
        content,
        title="[bold green]Success[/bold green]",
        title_align="left",
        border_style=SUCCESS_COLOR,
        padding=(1, 2)
    )
    
    console.print(panel)
    console.print()


def render_config_display(console: Console, config: dict):
    """Display configuration in a structured table"""
    console.print()
    console.print(Panel(
        "[bold cyan]ACQUILL Configuration[/bold cyan]",
        border_style=BRAND_PRIMARY
    ))
    console.print()
    
    # LLM Provider
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="bold")
    table.add_column("Value")
    
    console.print("[bold]LLM Provider: Groq[/bold]")
    table.add_row("API Key", config['providers']['groq']['api_key'])
    table.add_row("Model", config['providers']['groq']['model'])
    console.print(table)
    console.print()
    
    # Embedding Provider
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="bold")
    table.add_column("Value")
    
    console.print("[bold]Embedding Provider: Jina AI[/bold]")
    table.add_row("API Key", config['providers']['jina']['api_key'])
    table.add_row("Model", config['providers']['jina']['model'])
    console.print(table)
    console.print()
    
    # Database
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="bold")
    table.add_column("Value")
    
    console.print("[bold]Database[/bold]")
    table.add_row("Supabase URL", config['database']['supabase_url'])
    table.add_row("Supabase Key", config['database']['supabase_key'])
    table.add_row("Checkpoint DB", config['database']['checkpoint_db_url'])
    console.print(table)
    console.print()


def render_nudge_message(console: Console, message: str):
    """Display a subtle nudge message"""
    text = Text()
    text.append("💡 ", style=MUTED_COLOR)
    text.append(message, style="dim italic")
    console.print(text)


def render_separator(console: Console, style: str = "dim"):
    """Display a visual separator"""
    console.print("─" * console.width, style=style)


def get_input_prompt() -> Text:
    """Get styled input prompt"""
    prompt = Text()
    prompt.append("▸ ", style=BRAND_PRIMARY)
    return prompt
