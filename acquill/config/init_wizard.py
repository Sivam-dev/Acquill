"""
Interactive initialization wizard for Acquill
Guides users through first-time setup
"""

from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from acquill.interface.ui_components import render_logo

from .settings import (
    SHARED_SUPABASE_URL,
    SHARED_SUPABASE_ANON_KEY,
    config_exists,
    save_config,
    migrate_from_env,
    get_config_path
)
from .validators import (
    validate_groq_key,
    validate_jina_key
)

console = Console()


def _prompt_with_default(prompt: str, default: str = "", password: bool = False) -> str:
    """Prompt user with optional default value"""
    if default and not password:
        display_prompt = f"{prompt} [{default}]: "
    else:
        display_prompt = f"{prompt}: "
    
    if password:
        value = console.input(f"[cyan]{display_prompt}[/cyan]", password=True).strip()
    else:
        value = console.input(f"[cyan]{display_prompt}[/cyan]").strip()
    
    return value if value else default


def _check_env_file() -> bool:
    """Check if .env file exists in current directory"""
    return Path(".env").exists()


def run_init_wizard(interactive: bool = True, force: bool = False) -> bool:
    """
    Run the interactive initialization wizard.
    
    Args:
        interactive: If False, use non-interactive mode (read from env)
        force: If True, overwrite existing config without confirmation
    
    Returns:
        bool: True if initialization succeeded, False otherwise
    """
    console.print()
    
    render_logo(console, show_tagline=False)
    
    console.print()
    console.print("[bold cyan]Initialization Wizard[/bold cyan]", justify="center")
    console.print("[dim]Your AI companion with persistent memory[/dim]", justify="center")
    console.print()
    
    if config_exists() and not force:
        console.print("[yellow]⚠️  Configuration already exists.[/yellow]")
        reconfigure = console.input("[cyan]Do you want to reconfigure? (y/N):[/cyan] ").strip().lower()
        
        if reconfigure not in ['y', 'yes']:
            console.print("[dim]Initialization cancelled.[/dim]\n")
            return False
        
        console.print()
    
    env_exists = _check_env_file()
    import_from_env = False
    
    if env_exists and interactive:
        console.print("[green]✓[/green] Found existing .env file")
        import_choice = console.input("[cyan]Import credentials from .env? (Y/n):[/cyan] ").strip().lower()
        import_from_env = import_choice not in ['n', 'no']
        console.print()
    
    config = {
        "version": "1.0",
        "providers": {
            "groq": {"model": "openai/gpt-oss-20b"},
            "jina": {"model": "jina-embeddings-v2-base-en"}
        },
        "database": {},
        "git_check_interval": 300
    }
    
    if import_from_env:
        env_config = migrate_from_env()
        config["providers"]["groq"]["api_key"] = env_config["providers"]["groq"]["api_key"]
        config["providers"]["jina"]["api_key"] = env_config["providers"]["jina"]["api_key"]
        config["database"] = env_config["database"]
        config["git_check_interval"] = env_config["git_check_interval"]
    
    if not interactive:
        if not import_from_env:
            env_config = migrate_from_env()
            config = env_config
        
        console.print("[dim]Validating credentials...[/dim]\n")
        
        groq_valid, groq_msg = validate_groq_key(config["providers"]["groq"]["api_key"])
        if not groq_valid:
            console.print(f"[red]✗ {groq_msg}[/red]\n")
            return False
        
        jina_valid, jina_msg = validate_jina_key(config["providers"]["jina"]["api_key"])
        if not jina_valid:
            console.print(f"[red]✗ {jina_msg}[/red]\n")
            return False
        
        save_config(config)
        console.print(f"[green]✓ Configuration saved to {get_config_path()}[/green]\n")
        return True
    
    console.print("[bold]Step 1: Groq API Configuration[/bold]")
    console.print("[dim]Groq provides the LLM for chat and analysis[/dim]\n")
    
    while True:
        groq_key = _prompt_with_default(
            "Groq API Key",
            default=config["providers"]["groq"].get("api_key", ""),
            password=True
        )
        
        if not groq_key:
            console.print("[red]✗ Groq API key is required[/red]\n")
            continue
        
        console.print("[dim]Validating Groq API key...[/dim]")
        valid, message = validate_groq_key(groq_key)
        
        if valid:
            console.print(f"[green]✓ {message}[/green]\n")
            config["providers"]["groq"]["api_key"] = groq_key
            break
        else:
            console.print(f"[red]✗ {message}[/red]")
            retry = console.input("[cyan]Try again? (Y/n):[/cyan] ").strip().lower()
            if retry in ['n', 'no']:
                console.print("[yellow]Initialization cancelled.[/yellow]\n")
                return False
            console.print()
    
    console.print("[bold]Step 2: Jina AI API Configuration[/bold]")
    console.print("[dim]Jina AI provides embeddings for semantic search[/dim]\n")
    
    while True:
        jina_key = _prompt_with_default(
            "Jina AI API Key",
            default=config["providers"]["jina"].get("api_key", ""),
            password=True
        )
        
        if not jina_key:
            console.print("[red]✗ Jina AI API key is required[/red]\n")
            continue
        
        console.print("[dim]Validating Jina AI API key...[/dim]")
        valid, message = validate_jina_key(jina_key)
        
        if valid:
            console.print(f"[green]✓ {message}[/green]\n")
            config["providers"]["jina"]["api_key"] = jina_key
            break
        else:
            console.print(f"[red]✗ {message}[/red]")
            retry = console.input("[cyan]Try again? (Y/n):[/cyan] ").strip().lower()
            if retry in ['n', 'no']:
                console.print("[yellow]Initialization cancelled.[/yellow]\n")
                return False
            console.print()
    
    console.print("[bold]Step 3: Shared Database[/bold]")
    console.print("[dim]Acquill stores learning history in a shared Supabase project.[/dim]")
    console.print("[dim]Your Groq and Jina keys stay yours - only the database is shared.[/dim]\n")
    config["database"]["supabase_url"] = SHARED_SUPABASE_URL
    config["database"]["supabase_key"] = SHARED_SUPABASE_ANON_KEY
    config["database"]["checkpoint_db_url"] = ""
    console.print("[green]✓ Using shared Acquill database[/green]\n")
    
    try:
        save_config(config)
        console.print(Panel.fit(
            f"[green]✓ Configuration saved successfully![/green]\n\n"
            f"[dim]Location: {get_config_path()}[/dim]\n\n"
            f"[cyan]Next steps:[/cyan]\n"
            f"  1. Run [bold]acquill login[/bold] to authenticate\n"
            f"  2. Run [bold]acquill chat[/bold] to start learning\n\n"
            f"[dim]Note: Your .env file was not modified.[/dim]",
            border_style="green",
            title="🎉 Setup Complete"
        ))
        return True
    
    except Exception as e:
        console.print(f"\n[red]✗ Failed to save configuration: {e}[/red]\n")
        return False
