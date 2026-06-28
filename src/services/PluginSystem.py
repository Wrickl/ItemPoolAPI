from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path
from typing import Any, Protocol


class OnCreatePlugin(Protocol):
    def on_item_create(self, item: Any, session) -> None:
        """Called after a new Item was created."""

    def apply_to_existing_items(self, session) -> None:
        """Backfills the plugin behaviour to already stored Items."""


class OnSolutionAttemptCreatePlugin(Protocol):
    def on_solution_attempt_create(self, document: dict, session) -> None:
        """Called after a SolutionAttempt document was stored in MongoDB."""

    def apply_to_existing_solution_attempts(self, session) -> None:
        """Backfills the plugin behaviour to already stored SolutionAttempts."""


_on_create_plugins: list[OnCreatePlugin] = []
_on_solution_attempt_create_plugins: list[OnSolutionAttemptCreatePlugin] = []
_plugins_loaded = False


def register_on_create_plugin(plugin: OnCreatePlugin) -> None:
    _on_create_plugins.append(plugin)


def register_on_solution_attempt_create_plugin(plugin: OnSolutionAttemptCreatePlugin) -> None:
    _on_solution_attempt_create_plugins.append(plugin)


def register_plugin(plugin: OnCreatePlugin) -> None:
    """Compatibility alias for older on-create plugins."""
    register_on_create_plugin(plugin)


def _safe_call(callback, *args, **kwargs) -> None:
    try:
        callback(*args, **kwargs)
    except Exception:
        # keep plugins isolated; swallow exceptions to avoid breaking the main flow
        # TODO Log Plugin Errors
        pass


def run_on_item_create(item: Any, session) -> None:
    for plugin in _on_create_plugins:
        _safe_call(plugin.on_item_create, item, session)


def run_on_existing_items(session) -> None:
    for plugin in _on_create_plugins:
        _safe_call(plugin.apply_to_existing_items, session)


def run_on_solution_attempt_create(document: dict, session) -> None:
    for plugin in _on_solution_attempt_create_plugins:
        _safe_call(plugin.on_solution_attempt_create, document, session)


def run_on_existing_solution_attempts(session) -> None:
    for plugin in _on_solution_attempt_create_plugins:
        _safe_call(plugin.apply_to_existing_solution_attempts, session)


def get_active_plugins() -> dict[str, list[dict[str, str]]]:
    """Return active plugin instances grouped by trigger type."""

    def _plugin_info(plugin: Any) -> dict[str, str]:
        return {
            "name": plugin.__class__.__name__,
            "description": plugin.__doc__,
        }

    return {
        "on_create": [_plugin_info(plugin) for plugin in _on_create_plugins],
        "on_solution_attempt_create": [
            _plugin_info(plugin) for plugin in _on_solution_attempt_create_plugins
        ],
    }


def load_plugins() -> None:
    """Import all plugin modules from the dedicated trigger folders once."""
    global _plugins_loaded

    if _plugins_loaded:
        return

    package_root = Path(__file__).resolve().parent
    for package_name in ("on_create_plugins", "on_solutions_attempt_create_plugins"):
        package_path = package_root / package_name
        if not package_path.exists():
            continue

        full_package_name = f"{__package__}.{package_name}"
        try:
            importlib.import_module(full_package_name)
        except Exception:
            continue

        for module in pkgutil.iter_modules([str(package_path)]):
            if module.name.startswith("_"):
                continue
            try:
                importlib.import_module(f"{full_package_name}.{module.name}")
            except Exception:
                # keep optional plugins isolated; a broken plugin must not stop the app
                continue

    _plugins_loaded = True


load_plugins()
