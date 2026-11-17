#!/usr/bin/env python3
"""
Rich-powered wrapper around Aerich migration commands.

Never manually edit migration files in migrations/models/.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()
ROOT = Path(__file__).resolve().parent.parent
MIGRATION_WARNING = (
    "[bold red]Never manually edit migration files in migrations/models/.[/bold red]\n"
    "Change Tortoise models, then run [cyan]uv run aerich migrate[/cyan] and "
    "[cyan]uv run aerich upgrade[/cyan]."
)

ACTIONS = {
    "upgrade": ("upgrade", "Apply pending migrations (default)"),
    "migrate": ("migrate", "Generate a new migration from model changes"),
    "init": ("init", "Initialize Aerich (fresh repo)"),
    "init-db": ("init-db", "Create initial database from models"),
    "heads": ("heads", "Show current migration heads"),
    "history": ("history", "Show migration history"),
}


def _run_aerich(command: str, extra_args: list[str] | None = None) -> int:
    args = ["uv", "run", "aerich", command, *(extra_args or [])]
    console.print(f"[dim]$ {' '.join(args)}[/dim]\n")
    result = subprocess.run(args, cwd=ROOT)
    return result.returncode


def _show_menu() -> str:
    console.print(Panel(MIGRATION_WARNING, title="Migration safety", border_style="yellow"))
    console.print("\n[bold]Aerich actions:[/bold]")
    for key, (_, description) in ACTIONS.items():
        console.print(f"  [cyan]{key:8}[/cyan] {description}")
    choice = Prompt.ask(
        "\nAction",
        choices=list(ACTIONS.keys()),
        default="upgrade",
        show_choices=False,
    )
    return choice


def main() -> None:
    parser = argparse.ArgumentParser(description="Aerich migration helper with safety warnings.")
    parser.add_argument(
        "action",
        nargs="?",
        choices=list(ACTIONS.keys()),
        help="Aerich command to run (default: upgrade, or interactive menu)",
    )
    parser.add_argument(
        "--name",
        dest="migrate_name",
        help="Migration name suffix for 'migrate' (passed as --name)",
    )
    parser.add_argument(
        "-t",
        "--tortoise-orm",
        default="app.config.database.TORTOISE_ORM",
        help="Tortoise config path for init (default: app.config.database.TORTOISE_ORM)",
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip interactive menu when action is omitted",
    )
    args = parser.parse_args()

    action = args.action
    if action is None:
        if args.yes:
            action = "upgrade"
        else:
            action = _show_menu()

    console.print(Panel(MIGRATION_WARNING, border_style="yellow"))

    extra: list[str] = []
    if action == "init":
        extra = ["-t", args.tortoise_orm]
    elif action == "migrate" and args.migrate_name:
        extra = ["--name", args.migrate_name]

    exit_code = _run_aerich(action, extra)
    if exit_code == 0:
        console.print("\n[green]Done.[/green]")
    else:
        console.print(f"\n[red]Aerich exited with code {exit_code}.[/red]")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
