"""Interactive msfconsole-style interface for Akira"""

import asyncio
import shlex
from typing import Callable

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from akira.core.session import Session
from akira.core.registry import registry
from akira.core.module import Module, AttackCategory
from akira.core.target import TargetType
from akira.targets import create_target


BANNER = r"""
    ___    __   _
   /   |  / /__(_)________ _
  / /| | / //_/ / ___/ __ `/
 / ___ |/ ,< / / /  / /_/ /
/_/  |_/_/|_/_/_/   \__,_/

[bold cyan]LLM Security Testing Framework[/bold cyan]
Type 'help' for available commands
"""


class AkiraConsole:
    """Interactive console for Akira - similar to msfconsole"""

    def __init__(self) -> None:
        self.console = Console()
        self.session = Session()
        self._running = True

        # Command handlers
        self._commands: dict[str, Callable[..., None]] = {
            "help": self._cmd_help,
            "use": self._cmd_use,
            "info": self._cmd_info,
            "show": self._cmd_show,
            "set": self._cmd_set,
            "setg": self._cmd_setg,
            "options": self._cmd_options,
            "run": self._cmd_run,
            "exploit": self._cmd_run,  # Alias
            "check": self._cmd_check,
            "back": self._cmd_back,
            "search": self._cmd_search,
            "targets": self._cmd_targets,
            "target": self._cmd_target,
            "history": self._cmd_history,
            "exit": self._cmd_exit,
            "quit": self._cmd_exit,
        }

        # Load modules
        registry.load_builtin_modules()

        # Setup prompt
        self._setup_prompt()

    def _setup_prompt(self) -> None:
        """Setup prompt toolkit with completions"""
        commands = list(self._commands.keys())
        modules = registry.list_all()
        target_types = [t.value for t in TargetType]

        # Dynamic completions
        self._completer = WordCompleter(
            commands + modules + target_types,
            ignore_case=True,
        )

        self._style = Style.from_dict({
            "prompt": "ansicyan bold",
        })

        history_path = ".akira_history"
        self._prompt_session: PromptSession[str] = PromptSession(
            history=FileHistory(history_path),
            completer=self._completer,
            style=self._style,
        )

    def _get_prompt(self) -> str:
        """Generate the prompt string"""
        if self.session.module:
            return f"akira({self.session.module.info.name}) > "
        return "akira > "

    def run(self) -> None:
        """Main console loop"""
        self.console.print(Panel(BANNER, border_style="cyan"))

        while self._running:
            try:
                user_input = self._prompt_session.prompt(self._get_prompt())
                if user_input.strip():
                    self._execute_command(user_input.strip())
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Use 'exit' to quit[/yellow]")
            except EOFError:
                break

    def _execute_command(self, line: str) -> None:
        """Parse and execute a command"""
        try:
            parts = shlex.split(line)
        except ValueError:
            parts = line.split()

        if not parts:
            return

        cmd = parts[0].lower()
        args = parts[1:]

        if cmd in self._commands:
            try:
                self._commands[cmd](*args)
            except TypeError as e:
                self.console.print(f"[red]Invalid arguments: {e}[/red]")
        else:
            self.console.print(f"[red]Unknown command: {cmd}[/red]")

    # === Command Implementations ===

    def _cmd_help(self, *args: str) -> None:
        """Show help information"""
        table = Table(title="Available Commands")
        table.add_column("Command", style="cyan")
        table.add_column("Description")

        help_text = [
            ("use <module>", "Select an attack module"),
            ("info", "Show info about current module"),
            ("show modules", "List all available modules"),
            ("show options", "Show module options"),
            ("search <term>", "Search for modules"),
            ("set <option> <value>", "Set a module option"),
            ("setg <option> <value>", "Set a global option"),
            ("options", "Show current module options"),
            ("target <type> <endpoint>", "Set target"),
            ("targets", "List available target types"),
            ("check", "Check if target is vulnerable"),
            ("run / exploit", "Execute the attack"),
            ("back", "Deselect current module"),
            ("history", "Show attack history"),
            ("exit / quit", "Exit Akira"),
        ]

        for cmd, desc in help_text:
            table.add_row(cmd, desc)

        self.console.print(table)

    def _cmd_use(self, module_name: str = "") -> None:
        """Select a module to use"""
        if not module_name:
            self.console.print("[red]Usage: use <module_name>[/red]")
            return

        module_cls = registry.get(module_name)
        if not module_cls:
            # Try partial match
            matches = registry.search(module_name)
            if len(matches) == 1:
                module_cls = registry.get(matches[0])
                module_name = matches[0]
            elif matches:
                self.console.print("[yellow]Did you mean one of these?[/yellow]")
                for m in matches[:5]:
                    self.console.print(f"  {m}")
                return
            else:
                self.console.print(f"[red]Module not found: {module_name}[/red]")
                return

        if module_cls:
            self.session.module = module_cls()
            self.console.print(f"[green]Using module: {module_name}[/green]")

    def _cmd_info(self, *args: str) -> None:
        """Show module information"""
        if not self.session.module:
            self.console.print("[red]No module selected[/red]")
            return

        info = self.session.module.info
        self.console.print(Panel(
            f"""[bold]{info.name}[/bold]

[cyan]Category:[/cyan] {info.category.value}
[cyan]Severity:[/cyan] {info.severity.value}
[cyan]Author:[/cyan] {info.author}

[cyan]Description:[/cyan]
{info.description}

[cyan]References:[/cyan]
{chr(10).join('  - ' + ref for ref in info.references) if info.references else '  None'}

[cyan]Tags:[/cyan] {', '.join(info.tags) if info.tags else 'None'}
""",
            title="Module Info",
            border_style="cyan",
        ))

    def _cmd_show(self, what: str = "") -> None:
        """Show various information"""
        if what == "modules":
            self._show_modules()
        elif what == "options":
            self._cmd_options()
        elif what == "targets":
            self._cmd_targets()
        else:
            self.console.print("[yellow]Usage: show [modules|options|targets][/yellow]")

    def _show_modules(self, category: str | None = None) -> None:
        """Display available modules"""
        table = Table(title="Available Modules")
        table.add_column("Name", style="cyan")
        table.add_column("Severity", style="red")
        table.add_column("Description")

        modules = registry.list_all()
        if category:
            try:
                cat = AttackCategory(category)
                modules = registry.list_by_category(cat)
            except ValueError:
                pass

        for name in modules:
            cls = registry.get(name)
            if cls:
                mod = cls()
                table.add_row(
                    name,
                    mod.info.severity.value,
                    mod.info.description[:60],
                )

        self.console.print(table)

    def _cmd_set(self, option: str = "", *value_parts: str) -> None:
        """Set a module option"""
        if not self.session.module:
            self.console.print("[red]No module selected[/red]")
            return

        if not option:
            self.console.print("[red]Usage: set <option> <value>[/red]")
            return

        value = " ".join(value_parts)

        # Handle target specially
        if option.lower() == "target":
            self.console.print("[yellow]Use 'target <type> <endpoint>' to set target[/yellow]")
            return

        try:
            self.session.module.set_option(option, value)
            self.console.print(f"[green]{option} => {value}[/green]")
        except ValueError as e:
            self.console.print(f"[red]{e}[/red]")

    def _cmd_setg(self, option: str = "", *value_parts: str) -> None:
        """Set a global option"""
        if not option:
            self.console.print("[red]Usage: setg <option> <value>[/red]")
            return

        value = " ".join(value_parts)
        self.session.set_global(option, value)
        self.console.print(f"[green]Global: {option} => {value}[/green]")

    def _cmd_options(self, *args: str) -> None:
        """Show current module options"""
        if not self.session.module:
            self.console.print("[red]No module selected[/red]")
            return

        table = Table(title="Module Options")
        table.add_column("Name", style="cyan")
        table.add_column("Current", style="green")
        table.add_column("Required", style="yellow")
        table.add_column("Description")

        for name, opt in self.session.module.options.items():
            table.add_row(
                name,
                str(opt.get_value()) if opt.get_value() is not None else "",
                "Yes" if opt.required else "No",
                opt.description,
            )

        self.console.print(table)

        # Also show target
        if self.session.target:
            self.console.print(f"\n[cyan]Target:[/cyan] {self.session.target}")
        else:
            self.console.print("\n[yellow]Target not set. Use 'target <type> <endpoint>'[/yellow]")

    def _cmd_run(self, *args: str) -> None:
        """Execute the current attack"""
        if not self.session.module:
            self.console.print("[red]No module selected[/red]")
            return

        if not self.session.target:
            self.console.print("[red]No target set. Use 'target <type> <endpoint>'[/red]")
            return

        # Validate options
        errors = self.session.module.validate_options()
        if errors:
            for err in errors:
                self.console.print(f"[red]{err}[/red]")
            return

        self.console.print(f"[yellow]Executing {self.session.module.info.name}...[/yellow]")

        async def run_attack() -> None:
            target = self.session.target
            module = self.session.module

            if not target or not module:
                return

            # Validate target first
            if not target.is_validated:
                self.console.print("[cyan]Validating target...[/cyan]")
                if not await target.validate():
                    self.console.print("[red]Target validation failed[/red]")
                    return

            result = await module.run(target)
            self.session.log_attack(module, result)

            if result.success:
                self.console.print(
                    f"\n[bold green]VULNERABLE[/bold green] "
                    f"(confidence: {result.confidence:.0%})"
                )
                if result.details:
                    self.console.print("[cyan]Details:[/cyan]")
                    for k, v in result.details.items():
                        self.console.print(f"  {k}: {v}")
            else:
                self.console.print("\n[blue]Target does not appear vulnerable[/blue]")
                if result.error:
                    self.console.print(f"[yellow]Note: {result.error}[/yellow]")

        asyncio.run(run_attack())

    def _cmd_check(self, *args: str) -> None:
        """Quick check if target might be vulnerable"""
        if not self.session.module:
            self.console.print("[red]No module selected[/red]")
            return

        if not self.session.target:
            self.console.print("[red]No target set[/red]")
            return

        self.console.print("[cyan]Checking vulnerability...[/cyan]")

        async def run_check() -> None:
            target = self.session.target
            module = self.session.module

            if not target or not module:
                return

            if not target.is_validated:
                if not await target.validate():
                    self.console.print("[red]Target validation failed[/red]")
                    return

            is_vuln = await module.check(target)
            if is_vuln:
                self.console.print("[yellow]Target appears potentially vulnerable[/yellow]")
            else:
                self.console.print("[blue]Target does not appear vulnerable[/blue]")

        asyncio.run(run_check())

    def _cmd_back(self, *args: str) -> None:
        """Deselect current module"""
        if self.session.module:
            self.console.print(f"[yellow]Deselected {self.session.module.info.name}[/yellow]")
            self.session.module = None  # type: ignore[assignment]

    def _cmd_search(self, *terms: str) -> None:
        """Search for modules"""
        if not terms:
            self.console.print("[red]Usage: search <term>[/red]")
            return

        query = " ".join(terms)
        results = registry.search(query)

        if not results:
            self.console.print(f"[yellow]No modules found matching '{query}'[/yellow]")
            return

        table = Table(title=f"Search Results: {query}")
        table.add_column("Name", style="cyan")
        table.add_column("Description")

        for name in results:
            cls = registry.get(name)
            if cls:
                mod = cls()
                table.add_row(name, mod.info.description[:60])

        self.console.print(table)

    def _cmd_targets(self, *args: str) -> None:
        """List available target types"""
        table = Table(title="Target Types")
        table.add_column("Type", style="cyan")
        table.add_column("Description")

        targets = [
            ("api", "Generic LLM API endpoint"),
            ("openai", "OpenAI API"),
            ("anthropic", "Anthropic Claude API"),
            ("hf", "HuggingFace local model"),
            ("hf_inference", "HuggingFace Inference API"),
            ("bedrock", "AWS Bedrock"),
            ("sagemaker", "AWS SageMaker endpoint"),
        ]

        for t, desc in targets:
            table.add_row(t, desc)

        self.console.print(table)
        self.console.print("\n[cyan]Usage:[/cyan] target <type> <endpoint> [--key KEY] [--model MODEL]")

    def _cmd_target(self, *args: str) -> None:
        """Set the target"""
        if len(args) < 2:
            self.console.print("[red]Usage: target <type> <endpoint> [--key KEY] [--model MODEL][/red]")
            return

        target_type = args[0]
        endpoint = args[1]

        # Parse optional args
        api_key = None
        model = None
        i = 2
        while i < len(args):
            if args[i] in ("--key", "-k") and i + 1 < len(args):
                api_key = args[i + 1]
                i += 2
            elif args[i] in ("--model", "-m") and i + 1 < len(args):
                model = args[i + 1]
                i += 2
            else:
                i += 1

        try:
            target = create_target(
                target_type,
                endpoint=endpoint,
                api_key=api_key,
                model=model,
            )
            self.session.target = target
            self.console.print(f"[green]Target set: {target}[/green]")
        except ValueError as e:
            self.console.print(f"[red]Invalid target: {e}[/red]")

    def _cmd_history(self, *args: str) -> None:
        """Show attack history"""
        history = self.session.history

        if not history:
            self.console.print("[yellow]No attacks executed yet[/yellow]")
            return

        table = Table(title="Attack History")
        table.add_column("Time", style="dim")
        table.add_column("Module", style="cyan")
        table.add_column("Target")
        table.add_column("Result", style="green")

        for log in history[-20:]:  # Last 20
            result_str = "VULNERABLE" if log.result.success else "Not vulnerable"
            result_style = "green" if log.result.success else "blue"
            table.add_row(
                log.timestamp.strftime("%H:%M:%S"),
                log.module_name,
                log.target_repr[:30],
                f"[{result_style}]{result_str}[/{result_style}]",
            )

        self.console.print(table)

        stats = self.session.stats
        self.console.print(f"\n[cyan]Total:[/cyan] {stats['total_attacks']} | "
                          f"[green]Successful:[/green] {stats['successful_attacks']} | "
                          f"[blue]Failed:[/blue] {stats['failed_attacks']}")

    def _cmd_exit(self, *args: str) -> None:
        """Exit Akira"""
        self.console.print("[yellow]Goodbye![/yellow]")
        self._running = False
