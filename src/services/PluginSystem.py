from __future__ import annotations

import json
import logging
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

from sqlmodel import select

from models.items.content_piece import ContentPiece
from models.items.content_section_item import ContentSectionItem
from models.items.content_types import DataType
from models.items.content_section import ContentSection
from models.items.item_content_piece_value import ItemContentPieceValue
from models.items.item_type_plugin import ItemTypePlugin
from services.data_type_registry import validate_value_against_data_type

if TYPE_CHECKING:
    from sqlmodel import Session
    from models.items.tasks import Item

class ItemPlugin(Protocol):
    name: str
    description: str
    return_description: str
    supported_data_types: tuple[str, ...] | list[str]

    def execute(self, value: Any) -> Any:
        """Return a JSON-compatible result for the selected content value."""


logger = logging.getLogger(__name__)
plugins: dict[str, ItemPlugin] = {}
METADATA_SECTION_NAME = "Plugin_Created_Metadata"
PLUGIN_ROOT_ENV = "ITEMPOOL_PLUGIN_ROOT"
PLUGIN_TIMEOUT_SECONDS = 300
_WORKER = Path(__file__).with_name("plugin_worker.py").resolve()


def _call_plugin(python: Path, request: dict[str, Any]) -> Any:
    try:
        completed = subprocess.run(
            [str(python), "-I", "-X", "utf8", str(_WORKER)],
            input=json.dumps(request, allow_nan=False),
            capture_output=True,
            encoding="utf-8",
            timeout=PLUGIN_TIMEOUT_SECONDS,
            check=True,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"Plugin process timed out: {python}") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"Plugin process failed: {python}\n{exc.stderr}") from exc
    except OSError as exc:
        raise RuntimeError(f"Could not start plugin process: {python}") from exc
    if completed.stderr:
        logger.info("Plugin process %s: %s", python, completed.stderr.rstrip())
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid plugin response from {python}") from exc


class IsolatedItemPlugin:
    def __init__(self, python: Path, info: dict[str, Any]) -> None:
        self.python = python
        self.entry_point = info["entry_point"]
        self.name = info["name"]
        self.description = info["description"]
        self.return_description = info["return_description"]
        self.supported_data_types = info["supported_data_types"]

    def execute(self, value: Any) -> Any:
        return _call_plugin(self.python, {
            "operation": "execute",
            "entry_point": self.entry_point,
            "value": value,
        })


def register_plugin(plugin: ItemPlugin) -> None:
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
    if plugin.name in plugins:
        raise ValueError(f"Duplicate plugin name: {plugin.name}")
    plugins[plugin.name] = plugin


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
    if not root:
        return
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
            entries = _call_plugin(python, {"operation": "list"})
            if not isinstance(entries, list) or len(entries) != 1:
                raise ValueError("Plugin environment must contain exactly one entry point")
            for info in entries:
                register_plugin(IsolatedItemPlugin(python, info))
        except Exception:
            logger.exception("Could not load plugin environment %s", environment)
            raise


def run_item_plugins(item: Item, session: Session) -> None:
    assignments = session.exec(
        select(ItemTypePlugin).where(ItemTypePlugin.item_type_id == item.item_type_id)
    ).all()
    if not assignments:
        return
    metadata_section = session.exec(
        select(ContentSection).where(ContentSection.name == METADATA_SECTION_NAME)
    ).one()
    section_link = session.get(ContentSectionItem, (metadata_section.id, item.item_id))
    if section_link is None:
        session.add(ContentSectionItem(content_section_id=metadata_section.id, item_id=item.item_id))
    for assignment in assignments:
        plugin = plugins.get(assignment.plugin_name)
        if plugin is None:
            raise RuntimeError(f"Plugin {assignment.plugin_name} is not available")
        input_value = session.get(
            ItemContentPieceValue,
            (item.item_id, assignment.content_section_id, assignment.content_piece_id),
        )
        if input_value is None:
            raise RuntimeError(f"Input for plugin {plugin.name} is missing")
        try:
            piece = session.get(ContentPiece, assignment.content_piece_id)
            data_type = session.get(DataType, piece.data_type_id) if piece else None
            if data_type is None or data_type.name.upper() not in {
                name.upper() for name in plugin.supported_data_types
            }:
                raise ValueError(f"Unsupported data type for plugin {plugin.name}")
            validate_value_against_data_type(data_type.name, input_value.value)
            result = plugin.execute(input_value.value)
            json.dumps(result, allow_nan=False)
        except Exception as exc:
            logger.exception("Plugin %s failed for item %s", plugin.name, item.item_id)
            raise RuntimeError(f"Plugin {plugin.name} failed") from exc
        key = (item.item_id, metadata_section.id, assignment.output_content_piece_id)
        output = session.get(ItemContentPieceValue, key)
        value = {
            "plugin_name": plugin.name,
            "executed_at": datetime.now(UTC).isoformat(),
            "result": result,
        }
        if output is None:
            session.add(ItemContentPieceValue(
                item_id=item.item_id,
                content_section_id=metadata_section.id,
                content_piece_id=assignment.output_content_piece_id,
                value=value,
            ))
        else:
            output.value = value
            session.add(output)


load_plugins()
