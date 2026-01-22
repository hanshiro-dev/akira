"""Attack registry for discovering and loading attack modules"""

import importlib
from pathlib import Path

from akira.core.module import AttackCategory, Module


class ModuleRegistry:
    def __init__(self) -> None:
        self._modules: dict[str, type[Module]] = {}
        self._loaded = False

    def register(self, module_class: type[Module]) -> None:
        instance = module_class()
        self._modules[instance.info.name] = module_class

    def get(self, name: str) -> type[Module] | None:
        return self._modules.get(name)

    def list_all(self) -> list[str]:
        return sorted(self._modules.keys())

    def list_by_category(self, category: AttackCategory) -> list[str]:
        results = []
        for name, cls in self._modules.items():
            instance = cls()
            if instance.info.category == category:
                results.append(name)
        return sorted(results)

    def search(self, query: str) -> list[str]:
        query_lower = query.lower()
        results = []
        for name, cls in self._modules.items():
            instance = cls()
            if (
                query_lower in name.lower()
                or query_lower in instance.info.description.lower()
                or any(query_lower in tag.lower() for tag in instance.info.tags)
            ):
                results.append(name)
        return sorted(results)

    def load_builtin_attacks(self) -> None:
        if self._loaded:
            return

        import akira.attacks as attacks_pkg

        package_path = Path(attacks_pkg.__file__).parent

        # Load single-file attacks (attacks/<name>.py)
        for attack_file in package_path.glob("*.py"):
            if attack_file.name.startswith("_"):
                continue
            self._load_module(f"akira.attacks.{attack_file.stem}")

        # Load folder-based attacks (attacks/<name>/attack.py)
        for attack_dir in package_path.iterdir():
            if not attack_dir.is_dir() or attack_dir.name.startswith("_"):
                continue
            if (attack_dir / "attack.py").exists():
                self._load_module(f"akira.attacks.{attack_dir.name}.attack")

        self._loaded = True

    def _load_module(self, full_module_name: str) -> None:
        try:
            module = importlib.import_module(full_module_name)
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, Module)
                    and attr is not Module
                ):
                    self.register(attr)
        except Exception as e:
            print(f"Warning: Failed to load attack {full_module_name}: {e}")

    # Keep old method name for compatibility
    def load_builtin_modules(self) -> None:
        self.load_builtin_attacks()

    def load_external_attacks(self, path: Path) -> None:
        if not path.exists():
            return

        import sys
        sys.path.insert(0, str(path.parent))
        try:
            for attack_file in path.glob("*.py"):
                if attack_file.name.startswith("_"):
                    continue

                module_name = attack_file.stem
                try:
                    module = importlib.import_module(f"{path.name}.{module_name}")
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (
                            isinstance(attr, type)
                            and issubclass(attr, Module)
                            and attr is not Module
                        ):
                            self.register(attr)
                except Exception as e:
                    print(f"Warning: Failed to load external attack {module_name}: {e}")
        finally:
            sys.path.pop(0)


registry = ModuleRegistry()
