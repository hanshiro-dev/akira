"""Module registry for discovering and loading attack modules"""

import importlib
from pathlib import Path
from typing import Type

from akira.core.module import AttackCategory, Module


class ModuleRegistry:
    def __init__(self) -> None:
        self._modules: dict[str, Type[Module]] = {}
        self._loaded = False

    def register(self, module_class: Type[Module]) -> None:
        instance = module_class()
        name = f"{instance.info.category.value}/{instance.info.name}"
        self._modules[name] = module_class

    def get(self, name: str) -> Type[Module] | None:
        return self._modules.get(name)

    def list_all(self) -> list[str]:
        return sorted(self._modules.keys())

    def list_by_category(self, category: AttackCategory) -> list[str]:
        prefix = f"{category.value}/"
        return sorted(name for name in self._modules if name.startswith(prefix))

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

    def load_builtin_modules(self) -> None:
        if self._loaded:
            return

        import akira.modules as modules_pkg

        package_path = Path(modules_pkg.__file__).parent

        for category_dir in package_path.iterdir():
            if category_dir.is_dir() and not category_dir.name.startswith("_"):
                self._load_category(category_dir, f"akira.modules.{category_dir.name}")

        self._loaded = True

    def _load_category(self, category_path: Path, package_name: str) -> None:
        for module_file in category_path.glob("*.py"):
            if module_file.name.startswith("_"):
                continue

            module_name = module_file.stem
            full_module_name = f"{package_name}.{module_name}"

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
                print(f"Warning: Failed to load module {full_module_name}: {e}")

    def load_external_modules(self, path: Path) -> None:
        if not path.exists():
            return

        for category_dir in path.iterdir():
            if category_dir.is_dir() and not category_dir.name.startswith("_"):
                import sys
                sys.path.insert(0, str(path))
                try:
                    self._load_category(category_dir, category_dir.name)
                finally:
                    sys.path.pop(0)


registry = ModuleRegistry()
