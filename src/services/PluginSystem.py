"""Registry and discovery of installed item plugins."""

import logging
import os
from pathlib import Path
from typing import Any

from services.plugin_process import ItemPlugin, IsolatedItemPlugin, call_plugin

logger = logging.getLogger(__name__)
plugins: dict[str, ItemPlugin] = {}
METADATA_SECTION_NAME = "Plugin_Created_Metadata"
PLUGIN_ROOT_ENV = "ITEMPOOL_PLUGIN_ROOT"


def register_plugin(plugin: ItemPlugin, registry: dict[str, ItemPlugin] | None = None) -> None:
    registry = plugins if registry is None else registry
    for field in ("name", "description", "return_description"):
        value = getattr(plugin, field, None)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Plugin needs a non-empty {field}")
    if len(plugin.name) > 255:
        raise ValueError("Plugin name must not exceed 255 characters")
    types = getattr(plugin, "supported_data_types", None)
    if not isinstance(types, (tuple, list)) or not types or any(
        not isinstance(value, str) or not value.strip() for value in types
    ):
        raise ValueError(f"Plugin {plugin.name} needs supported data types")
    if not callable(getattr(plugin, "execute", None)):
        raise ValueError(f"Plugin {plugin.name} needs an execute method")
    if plugin.name in registry:
        raise ValueError(f"Duplicate plugin name: {plugin.name}")
    registry[plugin.name] = plugin


def get_active_plugins() -> list[dict[str, Any]]:
    return [
        {
            "name": plugin.name,
            "description": plugin.description,
            "return_description": plugin.return_description,
            "supported_data_types": list(plugin.supported_data_types),
        }
        for plugin in sorted(plugins.values(), key=lambda entry: entry.name)
    ]


def load_plugins() -> None:
    root = os.environ.get(PLUGIN_ROOT_ENV)
    loaded: dict[str, ItemPlugin] = {}
    if root:
        root_path = Path(root)
        if not root_path.is_dir():
            raise RuntimeError(f"Plugin environment directory does not exist: {root_path}")
        for environment in sorted(root_path.iterdir()):
            if not environment.is_dir():
                continue
            python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            if not python.is_file():
                raise RuntimeError(f"Plugin environment has no Python interpreter: {environment}")
            try:
                entries = call_plugin(python, {"operation": "list"})
                if not isinstance(entries, list) or len(entries) != 1:
                    raise ValueError("Plugin environment must contain exactly one entry point")
                register_plugin(IsolatedItemPlugin(python, entries[0]), loaded)
            except Exception:
                logger.exception("Could not load plugin environment %s", environment)
                raise
    # Keep the registry object shared by controllers while publishing only a complete load.
    plugins.clear()
    plugins.update(loaded)
