"""Interactive msfconsole-style interface for Akira"""

import asyncio
import shlex
from collections.abc import Callable

from prompt_toolkit import PromptSession
from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import FormattedTextControl, HSplit, Layout, Window
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from akira.core.fuzzy import fuzzy_rank
from akira.core.module import AttackCategory, Severity
from akira.core.registry import registry
from akira.core.session import Session
from akira.core.storage import get_storage
from akira.core.target import TargetType
from akira.targets import create_target

BANNER = """
[dim]                       _,.    [/dim]
[dim]                     o  //    [/dim]
[dim]                    /| ./     [/dim]          [bold cyan]~====[/bold cyan][dim]────────────[/dim]
[dim]                   /#|/  [/dim]    [bold cyan]_____[/bold cyan]   [bold cyan]_.o)[/bold cyan][dim]____[/dim][bold cyan]~~[/bold cyan][bold red]>>>[/bold red]
[dim]                  .##/  [/dim]    [bold cyan]`───'[/bold cyan]   [dim]`──'[/dim]
[bold red]   ###   [/bold red] [bold cyan]##  ##[/bold cyan] [bold red] ####  [/bold red] [bold cyan]#####     ###[/bold cyan]
[bold red]  ## ##  [/bold red] [bold cyan]## ##[/bold cyan]  [bold red]  ##   [/bold red] [bold cyan]##  ##   ## ##[/bold cyan]
[bold red] ##   ## [/bold red] [bold cyan]####[/bold cyan]   [bold red]  ##   [/bold red] [bold cyan]#####   ##   ##[/bold cyan]
[bold red] ####### [/bold red] [bold cyan]## ##[/bold cyan]  [bold red]  ##   [/bold red] [bold cyan]##  ##  #######[/bold cyan]
[bold red] ##   ## [/bold red] [bold cyan]##  ##[/bold cyan] [bold red] ####  [/bold red] [bold cyan]##   ## ##   ##[/bold cyan]

[bold cyan]LLM Security Testing Framework[/bold cyan]
[dim]'help' for commands | 'show modules' to list attacks[/dim]
"""



SEVERITY_COLORS = {
    Severity.CRITICAL: "bold red",
    Severity.HIGH: "red",
    Severity.MEDIUM: "yellow",
    Severity.LOW: "blue",
    Severity.INFO: "dim",
}


class AkiraConsole:
    def __init__(self) -> None:
        self.console = Console()
        self.session = Session()
        self._running = True

        self._commands: dict[str, Callable[..., None]] = {
            "help": self._cmd_help,
            "use": self._cmd_use,
            "info": self._cmd_info,
            "show": self._cmd_show,
            "set": self._cmd_set,
            "setg": self._cmd_setg,
            "options": self._cmd_options,
            "run": self._cmd_run,
            "exploit": self._cmd_run,
            "check": self._cmd_check,
            "back": self._cmd_back,
            "search": self._cmd_search,
            "targets": self._cmd_targets,
            "target": self._cmd_target,
            "history": self._cmd_history,
            "profile": self._cmd_profile,
            "profiles": self._cmd_profiles,
            "stats": self._cmd_stats,
            "exit": self._cmd_exit,
            "quit": self._cmd_exit,
        }

        registry.load_builtin_modules()
        self._setup_prompt()

    def _setup_prompt(self) -> None:
        commands = list(self._commands.keys())
        modules = registry.list_all()
        target_types = [t.value for t in TargetType]

        self._completer = WordCompleter(
            commands + modules + target_types,
            ignore_case=True,
        )

        self._style = Style.from_dict({
            "prompt": "ansicyan bold",
        })

        self._prompt_session: PromptSession[str] = PromptSession(
            history=FileHistory(".akira_history"),
            completer=self._completer,
            style=self._style,
        )

    def _get_prompt(self) -> str:
        if self.session.module:
            return f"akira([bold magenta]{self.session.module.info.name}[/]) > "
        return "[bold cyan]akira[/] > "

    def run(self) -> None:
        self.console.print(Panel(BANNER, border_style="red", padding=(0, 2)))

        while self._running:
            try:
                prompt_text = self._get_prompt()
                user_input = self._prompt_session.prompt(
                    Text.from_markup(prompt_text).plain
                )
                if user_input.strip():
                    self._execute_command(user_input.strip())
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Use 'exit' to quit[/yellow]")
            except EOFError:
                break

    def _execute_command(self, line: str) -> None:
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
                self.console.print(f"[bold red][-][/] Invalid arguments: {e}")
        else:
            self.console.print(f"[bold red][-][/] Unknown command: {cmd}")

    def _cmd_help(self, *args: str) -> None:
        table = Table(title="[bold]Commands[/bold]", border_style="dim")
        table.add_column("Command", style="cyan bold")
        table.add_column("Description", style="white")

        help_text = [
            ("use <module>", "Select an attack module"),
            ("info", "Show current module details"),
            ("show modules", "List all attack modules"),
            ("show options", "Show module options"),
            ("search [term]", "Fuzzy search (interactive if no term)"),
            ("set <opt> <val>", "Set module option"),
            ("setg <opt> <val>", "Set global option"),
            ("target <type> <url>", "Set target endpoint"),
            ("targets", "List target types"),
            ("profile <action> <name>", "Save/load/delete target profiles"),
            ("profiles", "List saved profiles"),
            ("check", "Quick vulnerability probe"),
            ("run", "Execute attack"),
            ("back", "Deselect module"),
            ("history", "Show attack history"),
            ("stats", "Show session and database stats"),
            ("exit", "Quit"),
        ]

        for cmd, desc in help_text:
            table.add_row(cmd, desc)

        self.console.print(table)

    def _cmd_use(self, module_name: str = "") -> None:
        if not module_name:
            self.console.print("[bold red][-][/] Usage: use <module_name>")
            return

        module_cls = registry.get(module_name)
        if not module_cls:
            matches = registry.search(module_name)
            if len(matches) == 1:
                module_cls = registry.get(matches[0])
                module_name = matches[0]
            elif matches:
                self.console.print("[yellow][*][/] Did you mean:")
                for m in matches[:5]:
                    self.console.print(f"    [cyan]{m}[/]")
                return
            else:
                self.console.print(f"[bold red][-][/] Module not found: {module_name}")
                return

        if module_cls:
            self.session.module = module_cls()
            info = self.session.module.info
            severity_color = SEVERITY_COLORS.get(info.severity, "white")
            self.console.print(f"[bold green][+][/] Using [bold magenta]{module_name}[/]")
            self.console.print(f"    [dim]Severity:[/] [{severity_color}]{info.severity.value.upper()}[/]")

    def _cmd_info(self, *args: str) -> None:
        if not self.session.module:
            self.console.print("[bold red][-][/] No module selected")
            return

        info = self.session.module.info
        severity_color = SEVERITY_COLORS.get(info.severity, "white")

        content = f"""[bold white]{info.name}[/bold white]

[cyan]Category:[/]    {info.category.value}
[cyan]Severity:[/]    [{severity_color}]{info.severity.value.upper()}[/{severity_color}]
[cyan]Author:[/]      {info.author}

[cyan]Description:[/]
{info.description}

[cyan]References:[/]
{chr(10).join('[dim]  • ' + ref + '[/dim]' for ref in info.references) if info.references else '  [dim]None[/dim]'}

[cyan]Tags:[/] [dim]{', '.join(info.tags) if info.tags else 'None'}[/dim]"""

        self.console.print(Panel(content, title="[bold]Module Info[/]", border_style="cyan"))

    def _cmd_show(self, what: str = "") -> None:
        if what == "modules":
            self._show_modules()
        elif what == "options":
            self._cmd_options()
        elif what == "targets":
            self._cmd_targets()
        else:
            self.console.print("[yellow][*][/] Usage: show [modules|options|targets]")

    def _show_modules(self, category: str | None = None) -> None:
        table = Table(title="[bold]Attack Modules[/bold]", border_style="dim")
        table.add_column("Module", style="cyan bold")
        table.add_column("Severity", justify="center")
        table.add_column("Description", style="white")

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
                severity_color = SEVERITY_COLORS.get(mod.info.severity, "white")
                table.add_row(
                    name,
                    f"[{severity_color}]{mod.info.severity.value.upper()}[/{severity_color}]",
                    mod.info.description[:55] + "..." if len(mod.info.description) > 55 else mod.info.description,
                )

        self.console.print(table)

    def _cmd_set(self, option: str = "", *value_parts: str) -> None:
        if not self.session.module:
            self.console.print("[bold red][-][/] No module selected")
            return

        if not option:
            self.console.print("[bold red][-][/] Usage: set <option> <value>")
            return

        value = " ".join(value_parts)

        if option.lower() == "target":
            self.console.print("[yellow][*][/] Use 'target <type> <endpoint>' instead")
            return

        try:
            self.session.module.set_option(option, value)
            self.console.print(f"[bold green][+][/] {option} => [cyan]{value}[/]")
        except ValueError as e:
            self.console.print(f"[bold red][-][/] {e}")

    def _cmd_setg(self, option: str = "", *value_parts: str) -> None:
        if not option:
            self.console.print("[bold red][-][/] Usage: setg <option> <value>")
            return

        value = " ".join(value_parts)
        self.session.set_global(option, value)
        self.console.print(f"[bold green][+][/] Global: {option} => [cyan]{value}[/]")

    def _cmd_options(self, *args: str) -> None:
        if not self.session.module:
            self.console.print("[bold red][-][/] No module selected")
            return

        table = Table(title="[bold]Module Options[/bold]", border_style="dim")
        table.add_column("Option", style="cyan bold")
        table.add_column("Value", style="green")
        table.add_column("Required", justify="center")
        table.add_column("Description", style="white")

        for name, opt in self.session.module.options.items():
            req_str = "[red]Yes[/]" if opt.required else "[dim]No[/]"
            val = str(opt.get_value()) if opt.get_value() is not None else "[dim]<not set>[/]"
            table.add_row(name, val, req_str, opt.description)

        self.console.print(table)

        if self.session.target:
            self.console.print(f"\n[cyan]Target:[/] [green]{self.session.target}[/]")
        else:
            self.console.print("\n[yellow][*][/] Target not set. Use 'target <type> <endpoint>'")

    def _cmd_run(self, *args: str) -> None:
        if not self.session.module:
            self.console.print("[bold red][-][/] No module selected")
            return

        if not self.session.target:
            self.console.print("[bold red][-][/] No target set")
            return

        errors = self.session.module.validate_options()
        if errors:
            for err in errors:
                self.console.print(f"[bold red][-][/] {err}")
            return

        self.console.print(f"[bold yellow][*][/] Executing [magenta]{self.session.module.info.name}[/]...")

        async def run_attack() -> None:
            target = self.session.target
            module = self.session.module

            if not target or not module:
                return

            if not target.is_validated:
                self.console.print("[cyan][*][/] Validating target...")
                if not await target.validate():
                    self.console.print("[bold red][-][/] Target validation failed")
                    return

            result = await module.run(target)
            self.session.log_attack(module, result)

            if result.success:
                self.console.print(
                    f"\n[bold green][+] VULNERABLE[/] "
                    f"[dim](confidence: {result.confidence:.0%})[/]"
                )
                if result.details:
                    for k, v in result.details.items():
                        self.console.print(f"    [cyan]{k}:[/] {v}")
            else:
                self.console.print("\n[bold blue][*][/] Target does not appear vulnerable")
                if result.error:
                    self.console.print(f"    [dim]{result.error}[/]")

        asyncio.run(run_attack())

    def _cmd_check(self, *args: str) -> None:
        if not self.session.module:
            self.console.print("[bold red][-][/] No module selected")
            return

        if not self.session.target:
            self.console.print("[bold red][-][/] No target set")
            return

        self.console.print("[cyan][*][/] Running quick check...")

        async def run_check() -> None:
            target = self.session.target
            module = self.session.module

            if not target or not module:
                return

            if not target.is_validated:
                if not await target.validate():
                    self.console.print("[bold red][-][/] Target validation failed")
                    return

            is_vuln = await module.check(target)
            if is_vuln:
                self.console.print("[bold yellow][!][/] Target appears potentially vulnerable")
            else:
                self.console.print("[bold blue][*][/] Target does not appear vulnerable")

        asyncio.run(run_check())

    def _cmd_back(self, *args: str) -> None:
        if self.session.module:
            self.console.print(f"[yellow][*][/] Deselected {self.session.module.info.name}")
            self.session.module = None  # type: ignore[assignment]

    def _cmd_search(self, *terms: str) -> None:
        if terms:
            # Non-interactive search with provided term
            self._search_static(" ".join(terms))
        else:
            # Interactive fuzzy search
            self._search_interactive()

    def _search_static(self, query: str) -> None:
        """Static search with a fixed query"""
        modules_data = self._get_modules_data()
        results = fuzzy_rank(query, modules_data)

        if not results:
            self.console.print(f"[yellow][*][/] No modules found matching '{query}'")
            return

        table = Table(title=f"[bold]Search: {query}[/bold]", border_style="dim")
        table.add_column("Module", style="cyan bold")
        table.add_column("Score", style="yellow", justify="right")
        table.add_column("Description", style="white")

        module_names = registry.list_all()
        max_score = results[0][1] if results else 1.0
        for idx, score in results[:10]:
            name = module_names[idx]
            cls = registry.get(name)
            if cls:
                mod = cls()
                normalized = (score / max_score) * 100
                score_pct = f"{normalized:.0f}%"
                table.add_row(name, score_pct, mod.info.description[:50])

        self.console.print(table)

    def _get_modules_data(self) -> list[tuple[str, str, list[str]]]:
        """Get all modules as (name, description, tags) tuples for fuzzy search"""
        data = []
        for name in registry.list_all():
            cls = registry.get(name)
            if cls:
                mod = cls()
                data.append((name, mod.info.description, list(mod.info.tags)))
        return data

    def _search_interactive(self) -> None:
        """Real-time interactive fuzzy search"""
        modules_data = self._get_modules_data()
        module_names = registry.list_all()
        selected_idx = 0
        current_results: list[tuple[int, float]] = [(i, 1.0) for i in range(len(modules_data))]

        kb = KeyBindings()

        @kb.add("c-c")
        @kb.add("escape")
        def _exit(event):
            event.app.exit(result=None)

        @kb.add("enter")
        def _select(event):
            if current_results:
                idx = current_results[min(selected_idx, len(current_results) - 1)][0]
                event.app.exit(result=module_names[idx])

        @kb.add("up")
        def _up(event):
            nonlocal selected_idx
            selected_idx = max(0, selected_idx - 1)

        @kb.add("down")
        def _down(event):
            nonlocal selected_idx
            selected_idx = min(len(current_results) - 1, selected_idx + 1)

        @kb.add("tab")
        def _tab(event):
            nonlocal selected_idx
            selected_idx = (selected_idx + 1) % max(1, len(current_results))

        def get_results_text():
            nonlocal current_results, selected_idx
            query = search_buffer.text

            if query:
                current_results = fuzzy_rank(query, modules_data)
            else:
                current_results = [(i, 1.0) for i in range(min(10, len(modules_data)))]

            selected_idx = min(selected_idx, max(0, len(current_results) - 1))

            lines = []
            lines.append(("class:header", " Fuzzy Search (ESC to cancel, Enter to select)\n"))
            lines.append(("class:header", " " + "─" * 60 + "\n"))

            max_score = current_results[0][1] if current_results else 1.0
            for display_idx, (mod_idx, score) in enumerate(current_results[:10]):
                name = module_names[mod_idx]
                cls = registry.get(name)
                desc = cls().info.description[:40] if cls else ""
                normalized = (score / max_score) * 100 if max_score > 0 else 0
                score_str = f"{normalized:3.0f}%"

                if display_idx == selected_idx:
                    lines.append(("class:selected", f" ▶ {name:<35} {score_str}  {desc}\n"))
                else:
                    lines.append(("class:item", f"   {name:<35} "))
                    lines.append(("class:score", f"{score_str}  "))
                    lines.append(("class:desc", f"{desc}\n"))

            if not current_results:
                lines.append(("class:dim", "   No matches\n"))

            return lines

        search_buffer = Buffer(on_text_changed=lambda _: None)

        layout = Layout(
            HSplit([
                Window(FormattedTextControl(get_results_text), height=13),
                Window(height=1, char="─", style="class:separator"),
                Window(
                    content=FormattedTextControl(lambda: [("class:prompt", " Search: "), ("", search_buffer.text)]),
                    height=1,
                ),
            ])
        )

        style = Style.from_dict({
            "header": "bold cyan",
            "selected": "bold reverse cyan",
            "item": "white",
            "score": "yellow",
            "desc": "gray",
            "dim": "gray italic",
            "prompt": "bold green",
            "separator": "gray",
        })

        app: Application[str | None] = Application(
            layout=layout,
            key_bindings=kb,
            style=style,
            full_screen=False,
            mouse_support=True,
        )

        # Custom key handling for typing
        @kb.add("<any>")
        def _type_char(event):
            char = event.data
            if char.isprintable() and len(char) == 1:
                search_buffer.insert_text(char)

        @kb.add("backspace")
        def _backspace(event):
            search_buffer.delete_before_cursor(1)

        result = app.run()

        if result:
            self.console.print(f"\n[bold green][+][/] Selected: [bold magenta]{result}[/]")
            self._cmd_use(result)

    def _cmd_targets(self, *args: str) -> None:
        table = Table(title="[bold]Target Types[/bold]", border_style="dim")
        table.add_column("Type", style="cyan bold")
        table.add_column("Description", style="white")

        targets = [
            ("api", "Any LLM-powered endpoint (custom format)"),
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
        self.console.print("""
[bold cyan]Usage:[/] target <type> <endpoint> [options]

[bold]Options:[/]
  [cyan]--key, -k[/] KEY           API key
  [cyan]--model, -m[/] MODEL       Model identifier
  [cyan]--request-template[/] TPL  JSON with $payload placeholder
  [cyan]--response-path[/] PATH    Dot-notation response path
  [cyan]--auth-type[/] TYPE        bearer | header | query | basic
  [cyan]--auth-header[/] NAME      Custom header name

[bold]Examples:[/]
  [dim]target openai https://api.openai.com/v1/chat/completions -k $KEY[/]
  [dim]target api https://xyz.com/chat --request-template '{"msg": "$payload"}'[/]
""")

    def _cmd_target(self, *args: str) -> None:
        if len(args) < 2:
            self.console.print("[bold red][-][/] Usage: target <type> <endpoint> [options]")
            self.console.print("[dim]    Run 'targets' for help[/]")
            return

        target_type = args[0]
        endpoint = args[1]

        api_key = None
        model = None
        extra: dict[str, object] = {}

        i = 2
        while i < len(args):
            if args[i] in ("--key", "-k") and i + 1 < len(args):
                api_key = args[i + 1]
                i += 2
            elif args[i] in ("--model", "-m") and i + 1 < len(args):
                model = args[i + 1]
                i += 2
            elif args[i] == "--request-template" and i + 1 < len(args):
                extra["request_template"] = args[i + 1]
                i += 2
            elif args[i] == "--response-path" and i + 1 < len(args):
                extra["response_path"] = args[i + 1]
                i += 2
            elif args[i] == "--auth-type" and i + 1 < len(args):
                extra["auth_type"] = args[i + 1]
                i += 2
            elif args[i] == "--auth-header" and i + 1 < len(args):
                extra["auth_header"] = args[i + 1]
                i += 2
            elif args[i] == "--method" and i + 1 < len(args):
                extra["method"] = args[i + 1]
                i += 2
            else:
                i += 1

        try:
            target = create_target(
                target_type,
                endpoint=endpoint,
                api_key=api_key,
                model=model,
                **extra,
            )
            self.session.target = target
            self.console.print(f"[bold green][+][/] Target set: [green]{target}[/]")
            if extra:
                self.console.print(f"    [dim]{extra}[/]")
        except ValueError as e:
            self.console.print(f"[bold red][-][/] Invalid target: {e}")

    def _cmd_history(self, *args: str) -> None:
        history = self.session.history

        if not history:
            self.console.print("[yellow][*][/] No attacks executed yet")
            return

        table = Table(title="[bold]Attack History[/bold]", border_style="dim")
        table.add_column("Time", style="dim")
        table.add_column("Module", style="cyan")
        table.add_column("Target", style="white")
        table.add_column("Result", justify="center")

        for log in history[-20:]:
            if log.result.success:
                result_str = "[bold green]VULN[/]"
            else:
                result_str = "[dim]safe[/]"
            table.add_row(
                log.timestamp.strftime("%H:%M:%S"),
                log.module_name,
                log.target_repr[:30],
                result_str,
            )

        self.console.print(table)

        stats = self.session.stats
        self.console.print(
            f"\n[bold]Total:[/] {stats['total_attacks']} | "
            f"[bold green]Vulnerable:[/] {stats['successful_attacks']} | "
            f"[dim]Safe:[/] {stats['failed_attacks']}"
        )

    def _cmd_profile(self, *args: str) -> None:
        if not args:
            self.console.print("[bold red][-][/] Usage: profile <save|load|delete> <name>")
            return

        action = args[0].lower()
        storage = get_storage()

        if action == "save" and len(args) >= 2:
            name = args[1]
            if not self.session.target:
                self.console.print("[bold red][-][/] No target configured")
                return
            target = self.session.target
            target_type = target.target_type.value
            url = getattr(target, "url", "") or getattr(target, "endpoint", "") or ""
            config = getattr(target, "config", {}) or {}
            storage.save_target_profile(name, target_type, str(url), config)
            self.console.print(f"[bold green][+][/] Saved profile: [cyan]{name}[/]")

        elif action == "load" and len(args) >= 2:
            name = args[1]
            profile = storage.get_target_profile(name)
            if not profile:
                self.console.print(f"[bold red][-][/] Profile not found: {name}")
                return
            try:
                target = create_target(profile.target_type, profile.url, **profile.config)
                self.session.target = target
                self.console.print(f"[bold green][+][/] Loaded profile: [cyan]{name}[/]")
                self.console.print(f"    [dim]Type:[/] {profile.target_type} | [dim]URL:[/] {profile.url}")
            except Exception as e:
                self.console.print(f"[bold red][-][/] Failed to load profile: {e}")

        elif action == "delete" and len(args) >= 2:
            name = args[1]
            if storage.delete_target_profile(name):
                self.console.print(f"[bold green][+][/] Deleted profile: [cyan]{name}[/]")
            else:
                self.console.print(f"[bold red][-][/] Profile not found: {name}")

        else:
            self.console.print("[bold red][-][/] Usage: profile <save|load|delete> <name>")

    def _cmd_profiles(self, *args: str) -> None:
        storage = get_storage()
        profiles = storage.list_target_profiles()

        if not profiles:
            self.console.print("[yellow][*][/] No saved profiles")
            return

        table = Table(title="[bold]Saved Target Profiles[/bold]", border_style="dim")
        table.add_column("Name", style="cyan bold")
        table.add_column("Type", style="white")
        table.add_column("URL", style="dim")
        table.add_column("Created", style="dim")

        for p in profiles:
            table.add_row(p.name, p.target_type, p.url[:40], p.created_at.strftime("%Y-%m-%d"))

        self.console.print(table)
        self.console.print("\n[dim]Usage: profile load <name>[/]")

    def _cmd_stats(self, *args: str) -> None:
        storage = get_storage()
        stats = storage.get_stats()

        content = f"""[bold cyan]Session Stats[/bold cyan]
  Attacks this session:  {self.session.stats['total_attacks']}
  Successful this session: {self.session.stats['successful_attacks']}

[bold cyan]Database Stats[/bold cyan]
  Total history entries: {stats['history_entries']}
  Successful attacks:    {stats['successful_attacks']}
  Overall success rate:  {stats['success_rate']:.1f}%
  Cached prompts:        {stats['cached_prompts']}
  Target profiles:       {stats['target_profiles']}
  Cached responses:      {stats['cached_responses']}
  Database size:         {stats['db_size_kb']} KB"""

        self.console.print(Panel(content, title="[bold]Akira Stats[/]", border_style="cyan"))

    def _cmd_exit(self, *args: str) -> None:
        self.console.print("[bold yellow][*][/] Goodbye!")
        self._running = False
