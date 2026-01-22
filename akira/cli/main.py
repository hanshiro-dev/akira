"""Main entry point for Akira CLI"""

import click
from rich.console import Console

from akira.cli.console import AkiraConsole


@click.group(invoke_without_command=True)
@click.option("--version", "-v", is_flag=True, help="Show version")
@click.pass_context
def main(ctx: click.Context, version: bool) -> None:
    """Akira - LLM Security Testing Framework

    Launch the interactive console or run specific commands.
    """
    console = Console()

    if version:
        from akira import __version__
        console.print(f"Akira v{__version__}")
        return

    if ctx.invoked_subcommand is None:
        # Launch interactive console
        akira = AkiraConsole()
        akira.run()


@main.command()
@click.argument("module")
@click.option("--target", "-t", required=True, help="Target specification")
@click.option("--target-type", "-T", default="api", help="Target type")
@click.option("--api-key", "-k", envvar="API_KEY", help="API key")
@click.option("--model", "-m", help="Model to target")
@click.option("--output", "-o", help="Output file for results")
def run(
    module: str,
    target: str,
    target_type: str,
    api_key: str | None,
    model: str | None,
    output: str | None,
) -> None:
    """Run a specific attack module non-interactively.

    Example:
        akira run dos/magic_string -t https://api.example.com -T openai
    """
    import asyncio

    from rich.console import Console

    from akira.core.registry import registry
    from akira.core.target import TargetType
    from akira.targets import create_target

    console = Console()

    # Load modules
    registry.load_builtin_modules()

    # Get module
    module_cls = registry.get(module)
    if not module_cls:
        console.print(f"[red]Module not found: {module}[/red]")
        console.print("Use 'akira list' to see available modules")
        return

    # Create target
    try:
        tgt = create_target(
            TargetType(target_type),
            endpoint=target,
            api_key=api_key,
            model=model,
        )
    except ValueError as e:
        console.print(f"[red]Invalid target: {e}[/red]")
        return

    # Run the attack
    mod = module_cls()
    console.print(f"[yellow]Running {mod.info.name}...[/yellow]")

    async def execute() -> None:
        if not await tgt.validate():
            console.print("[red]Target validation failed[/red]")
            return

        result = await mod.run(tgt)

        if result.success:
            console.print(f"[green]VULNERABLE[/green] (confidence: {result.confidence:.0%})")
        else:
            console.print("[blue]Not vulnerable[/blue]")

        if output:
            import json
            with open(output, "w") as f:
                json.dump({
                    "module": module,
                    "target": target,
                    "success": result.success,
                    "confidence": result.confidence,
                    "details": result.details,
                }, f, indent=2)
            console.print(f"Results saved to {output}")

    asyncio.run(execute())


@main.command("list")
@click.option("--category", "-c", help="Filter by category")
def list_modules(category: str | None) -> None:
    """List available attack modules."""
    from rich.console import Console
    from rich.table import Table

    from akira.core.module import AttackCategory
    from akira.core.registry import registry

    console = Console()
    registry.load_builtin_modules()

    table = Table(title="Available Modules")
    table.add_column("Name", style="cyan")
    table.add_column("Category", style="yellow")
    table.add_column("Severity", style="red")
    table.add_column("Description")

    modules = registry.list_all()
    if category:
        try:
            cat = AttackCategory(category)
            modules = registry.list_by_category(cat)
        except ValueError:
            console.print(f"[red]Unknown category: {category}[/red]")
            return

    for name in modules:
        cls = registry.get(name)
        if cls:
            mod = cls()
            table.add_row(
                name,
                mod.info.category.value,
                mod.info.severity.value,
                (mod.info.description[:50] + "...") if len(mod.info.description) > 50
                else mod.info.description,
            )

    console.print(table)


if __name__ == "__main__":
    main()
