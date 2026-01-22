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


@main.command()
@click.option("--target", "-t", required=True, help="Target endpoint")
@click.option("--target-type", "-T", default="api", help="Target type")
@click.option("--api-key", "-k", envvar="API_KEY", help="API key")
@click.option("--model", "-m", help="Model to target")
@click.option("--category", "-c", help="Only run attacks in this category")
@click.option("--all", "run_all", is_flag=True, help="Run all attacks")
@click.option("--exclude", "-x", multiple=True, help="Exclude specific attacks")
@click.option("--stop-on-first", is_flag=True, help="Stop after first vulnerability")
@click.option("--output", "-o", help="Output file (JSON)")
@click.option("--quiet", "-q", is_flag=True, help="Minimal output")
@click.option("--json", "json_output", is_flag=True, help="JSON output to stdout")
def scan(
    target: str,
    target_type: str,
    api_key: str | None,
    model: str | None,
    category: str | None,
    run_all: bool,
    exclude: tuple[str, ...],
    stop_on_first: bool,
    output: str | None,
    quiet: bool,
    json_output: bool,
) -> None:
    """Scan a target with multiple attacks.

    Examples:
        akira scan -t https://api.anthropic.com/v1 -T anthropic -k $KEY --all
        akira scan -t $URL -T anthropic --category dos --json
        akira scan -t $URL -T api --all --quiet -o results.json
    """
    import asyncio
    import json

    from rich.console import Console
    from rich.table import Table

    from akira.core.target import TargetType
    from akira.scan import scan as run_scan
    from akira.targets import create_target

    console = Console(quiet=quiet)

    try:
        tgt = create_target(
            TargetType(target_type),
            endpoint=target,
            api_key=api_key,
            model=model,
        )
    except ValueError as e:
        if json_output:
            print(json.dumps({"error": str(e)}))
        else:
            console.print(f"[red][-] Invalid target: {e}[/red]")
        return

    async def execute():
        if not quiet and not json_output:
            console.print(f"[yellow][*] Scanning {target}...[/yellow]")

        if not await tgt.validate():
            if json_output:
                print(json.dumps({"error": "Target validation failed"}))
            else:
                console.print("[red][-] Target validation failed[/red]")
            return

        result = await run_scan(
            tgt,
            attacks=None if run_all or category else None,
            category=category,
            exclude=list(exclude),
            stop_on_first=stop_on_first,
        )

        if json_output:
            print(json.dumps(result.to_dict(), indent=2))
        else:
            table = Table(title="Scan Results")
            table.add_column("Attack", style="cyan")
            table.add_column("Result", justify="center")
            table.add_column("Confidence")
            table.add_column("Details")

            for name, r in result.results.items():
                if r.success:
                    status = "[bold green]VULN[/bold green]"
                    conf = f"{r.confidence:.0%}"
                else:
                    status = "[dim]safe[/dim]"
                    conf = "-"
                details = r.error or ""
                table.add_row(name, status, conf, details[:40])

            console.print(table)
            console.print(
                f"\n[bold]Summary:[/bold] {result.vulnerable}/{result.total} vulnerable"
            )

        if output:
            with open(output, "w") as f:
                json.dump(result.to_dict(), f, indent=2)
            if not quiet and not json_output:
                console.print(f"[green][+] Results saved to {output}[/green]")

    asyncio.run(execute())


@main.command()
@click.option("--target", "-t", required=True, help="Target endpoint")
@click.option("--target-type", "-T", default="api", help="Target type")
@click.option("--api-key", "-k", envvar="API_KEY", help="API key")
def fingerprint(target: str, target_type: str, api_key: str | None) -> None:
    """Detect model/provider behind an endpoint.

    Example:
        akira fingerprint -t https://myapp.com/chat -T api -k $KEY
    """
    import asyncio

    from rich.console import Console

    from akira.core.target import TargetType
    from akira.targets import create_target

    console = Console()

    try:
        tgt = create_target(TargetType(target_type), endpoint=target, api_key=api_key)
    except ValueError as e:
        console.print(f"[red][-] Invalid target: {e}[/red]")
        return

    async def execute():
        console.print(f"[yellow][*] Fingerprinting {target}...[/yellow]")

        if not await tgt.validate():
            console.print("[red][-] Target validation failed[/red]")
            return

        # Basic fingerprinting via response patterns
        probes = [
            ("What company created you?", ["anthropic", "openai", "google", "meta"]),
            ("What is your model name?", ["claude", "gpt", "gemini", "llama"]),
        ]

        detected = []
        for prompt, keywords in probes:
            try:
                resp = await tgt.send(prompt)
                resp_lower = resp.lower()
                for kw in keywords:
                    if kw in resp_lower:
                        detected.append(kw)
            except Exception:
                pass

        if detected:
            console.print(f"[green][+] Detected: {', '.join(set(detected))}[/green]")
        else:
            console.print("[yellow][*] Could not determine model/provider[/yellow]")

    asyncio.run(execute())


@main.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--output", "-o", default="report.html", help="Output file")
@click.option("--format", "-f", "fmt", type=click.Choice(["html", "json", "md"]), default="html")
def report(input_file: str, output: str, fmt: str) -> None:
    """Generate a report from scan results.

    Example:
        akira scan -t $URL -T anthropic --all -o results.json
        akira report results.json -o report.html
    """
    import json
    from pathlib import Path

    from rich.console import Console

    console = Console()

    with open(input_file) as f:
        data = json.load(f)

    if fmt == "json":
        Path(output).write_text(json.dumps(data, indent=2))
    elif fmt == "md":
        md = _generate_markdown_report(data)
        Path(output).write_text(md)
    else:
        html = _generate_html_report(data)
        Path(output).write_text(html)

    console.print(f"[green][+] Report saved to {output}[/green]")


def _generate_markdown_report(data: dict) -> str:
    lines = [
        "# Akira Security Scan Report",
        "",
        f"**Target:** {data.get('target', 'Unknown')}",
        f"**Vulnerabilities Found:** {data.get('vulnerable', 0)}/{data.get('total', 0)}",
        "",
        "## Results",
        "",
        "| Attack | Status | Confidence | Details |",
        "|--------|--------|------------|---------|",
    ]
    for name, r in data.get("results", {}).items():
        status = "VULNERABLE" if r.get("success") else "Safe"
        conf = f"{r.get('confidence', 0):.0%}" if r.get("success") else "-"
        err = r.get("error", "") or ""
        lines.append(f"| {name} | {status} | {conf} | {err[:30]} |")

    lines.extend(["", "---", "*Generated by Akira*"])
    return "\n".join(lines)


def _generate_html_report(data: dict) -> str:
    rows = []
    for name, r in data.get("results", {}).items():
        status = "VULNERABLE" if r.get("success") else "Safe"
        color = "#dc3545" if r.get("success") else "#28a745"
        conf = f"{r.get('confidence', 0):.0%}" if r.get("success") else "-"
        rows.append(f"""
        <tr>
            <td>{name}</td>
            <td style="color:{color};font-weight:bold">{status}</td>
            <td>{conf}</td>
            <td>{r.get('error', '') or ''}</td>
        </tr>""")

    return f"""<!DOCTYPE html>
<html>
<head>
    <title>Akira Security Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; background: #1a1a2e; color: #eee; }}
        h1 {{ color: #e94560; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ border: 1px solid #333; padding: 12px; text-align: left; }}
        th {{ background: #16213e; color: #e94560; }}
        tr:nth-child(even) {{ background: #16213e; }}
        .summary {{ background: #16213e; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <h1>Akira Security Scan Report</h1>
    <div class="summary">
        <p><strong>Target:</strong> {data.get('target', 'Unknown')}</p>
        <p><strong>Vulnerabilities:</strong> {data.get('vulnerable', 0)} / {data.get('total', 0)}</p>
        <p><strong>Success Rate:</strong> {data.get('success_rate', 0):.1%}</p>
    </div>
    <table>
        <tr><th>Attack</th><th>Status</th><th>Confidence</th><th>Details</th></tr>
        {''.join(rows)}
    </table>
    <p style="margin-top:40px;color:#666">Generated by Akira</p>
</body>
</html>"""


if __name__ == "__main__":
    main()
