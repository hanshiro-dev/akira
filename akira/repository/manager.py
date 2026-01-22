"""Attack repository manager - similar to exploitdb for Metasploit"""

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class AttackDefinition:
    """Definition of an attack loaded from YAML"""
    id: str
    name: str
    description: str
    category: str
    severity: str
    author: str
    payloads: list[str]
    success_indicators: list[str] = field(default_factory=list)
    failure_indicators: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    target_types: list[str] = field(default_factory=list)
    options: dict[str, Any] = field(default_factory=dict)


class RepoManager:
    """Manages attack repositories - local and remote"""

    DEFAULT_REPO = "https://github.com/akira-sec/attack-db.git"  # Placeholder

    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = data_dir or Path.home() / ".akira"
        self.attacks_dir = self.data_dir / "attacks"
        self.config_file = self.data_dir / "config.json"
        self._ensure_dirs()
        self._config = self._load_config()

    def _ensure_dirs(self) -> None:
        """Create necessary directories"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.attacks_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self) -> dict[str, Any]:
        """Load repository configuration"""
        if self.config_file.exists():
            return json.loads(self.config_file.read_text())
        return {
            "repositories": [self.DEFAULT_REPO],
            "last_update": None,
        }

    def _save_config(self) -> None:
        """Save repository configuration"""
        self.config_file.write_text(json.dumps(self._config, indent=2))

    def add_repository(self, url: str) -> None:
        """Add a new attack repository"""
        if url not in self._config["repositories"]:
            self._config["repositories"].append(url)
            self._save_config()

    def remove_repository(self, url: str) -> bool:
        """Remove an attack repository"""
        if url in self._config["repositories"]:
            self._config["repositories"].remove(url)
            self._save_config()
            return True
        return False

    def update(self) -> bool:
        """Update all repositories"""
        success = True
        for repo_url in self._config["repositories"]:
            try:
                self._update_repo(repo_url)
            except Exception as e:
                print(f"Failed to update {repo_url}: {e}")
                success = False

        if success:
            from datetime import datetime
            self._config["last_update"] = datetime.now().isoformat()
            self._save_config()

        return success

    def _update_repo(self, url: str) -> None:
        """Update a single repository"""
        # Extract repo name from URL
        repo_name = url.rstrip("/").split("/")[-1].replace(".git", "")
        repo_path = self.attacks_dir / repo_name

        if repo_path.exists():
            # Pull latest
            subprocess.run(
                ["git", "pull"],
                cwd=repo_path,
                check=True,
                capture_output=True,
            )
        else:
            # Clone
            subprocess.run(
                ["git", "clone", url, str(repo_path)],
                check=True,
                capture_output=True,
            )

    def load_attack(self, attack_id: str) -> AttackDefinition | None:
        """Load an attack definition by ID"""
        # Search in all repo directories
        for repo_dir in self.attacks_dir.iterdir():
            if not repo_dir.is_dir():
                continue

            for yaml_file in repo_dir.rglob("*.yaml"):
                try:
                    data = yaml.safe_load(yaml_file.read_text())
                    if data.get("id") == attack_id:
                        return self._parse_attack(data)
                except Exception:
                    continue

        return None

    def search_attacks(self, query: str) -> list[AttackDefinition]:
        """Search attacks by name, description, or tags"""
        results = []
        query_lower = query.lower()

        for attack in self.list_attacks():
            if (
                query_lower in attack.name.lower()
                or query_lower in attack.description.lower()
                or any(query_lower in tag.lower() for tag in attack.tags)
            ):
                results.append(attack)

        return results

    def list_attacks(self) -> list[AttackDefinition]:
        """List all available attacks"""
        attacks = []

        for repo_dir in self.attacks_dir.iterdir():
            if not repo_dir.is_dir():
                continue

            for yaml_file in repo_dir.rglob("*.yaml"):
                try:
                    data = yaml.safe_load(yaml_file.read_text())
                    if "id" in data and "payloads" in data:
                        attacks.append(self._parse_attack(data))
                except Exception:
                    continue

        return attacks

    def list_by_category(self, category: str) -> list[AttackDefinition]:
        """List attacks by category"""
        return [a for a in self.list_attacks() if a.category == category]

    def _parse_attack(self, data: dict[str, Any]) -> AttackDefinition:
        """Parse attack definition from YAML data"""
        return AttackDefinition(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            category=data.get("category", "unknown"),
            severity=data.get("severity", "medium"),
            author=data.get("author", "unknown"),
            payloads=data.get("payloads", []),
            success_indicators=data.get("success_indicators", []),
            failure_indicators=data.get("failure_indicators", []),
            references=data.get("references", []),
            tags=data.get("tags", []),
            target_types=data.get("target_types", []),
            options=data.get("options", {}),
        )

    def import_local(self, path: Path) -> int:
        """Import attacks from a local directory"""
        if not path.exists():
            raise ValueError(f"Path does not exist: {path}")

        dest = self.attacks_dir / "local"
        dest.mkdir(exist_ok=True)

        count = 0
        for yaml_file in path.rglob("*.yaml"):
            try:
                # Validate it's a valid attack definition
                data = yaml.safe_load(yaml_file.read_text())
                if "id" in data and "payloads" in data:
                    shutil.copy(yaml_file, dest / yaml_file.name)
                    count += 1
            except Exception:
                continue

        return count

    def export_attack(self, attack: AttackDefinition, path: Path) -> None:
        """Export an attack definition to YAML"""
        data = {
            "id": attack.id,
            "name": attack.name,
            "description": attack.description,
            "category": attack.category,
            "severity": attack.severity,
            "author": attack.author,
            "payloads": attack.payloads,
            "success_indicators": attack.success_indicators,
            "failure_indicators": attack.failure_indicators,
            "references": attack.references,
            "tags": attack.tags,
            "target_types": attack.target_types,
            "options": attack.options,
        }
        path.write_text(yaml.dump(data, default_flow_style=False))
