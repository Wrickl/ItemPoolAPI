"""Communication with plugins running in separate Python environments."""

import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Literal, Protocol, TypedDict

from pydantic import TypeAdapter


class ItemPlugin(Protocol):
    name: str
    description: str
    return_description: str
    supported_data_types: tuple[str, ...] | list[str]

    def execute(self, value: Any) -> Any:
        """Return a JSON-compatible result for the selected content value."""


class PluginInfo(TypedDict):
    entry_point: str
    name: str
    description: str
    return_description: str
    supported_data_types: list[str]


class ListRequest(TypedDict):
    operation: Literal["list"]


class ExecuteRequest(TypedDict):
    operation: Literal["execute"]
    entry_point: str
    value: Any


_plugin_info_adapter = TypeAdapter(PluginInfo)
logger = logging.getLogger(__name__)
PLUGIN_TIMEOUT_SECONDS = 300
_WORKER = Path(__file__).with_name("plugin_worker.py").resolve()


def call_plugin(python: Path, request: ListRequest | ExecuteRequest) -> Any:
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
    def __init__(self, python: Path, raw_info: object) -> None:
        info = _plugin_info_adapter.validate_python(raw_info, strict=True)
        if not info["entry_point"].strip():
            raise ValueError("Plugin needs a non-empty entry point")
        self.python = python
        self.entry_point = info["entry_point"]
        self.name = info["name"]
        self.description = info["description"]
        self.return_description = info["return_description"]
        self.supported_data_types = info["supported_data_types"]

    def execute(self, value: Any) -> Any:
        return call_plugin(self.python, {
            "operation": "execute",
            "entry_point": self.entry_point,
            "value": value,
        })
