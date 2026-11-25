"""Run one plugin in its own Python environment using a JSON protocol."""

import contextlib
import json
import sys
from importlib.metadata import entry_points
from pathlib import Path


def main() -> None:
    if sys.prefix == sys.base_prefix:
        raise RuntimeError("Plugin must run in a virtual environment")
    config = (Path(sys.prefix) / "pyvenv.cfg").read_text(encoding="utf-8")
    settings = dict(
        line.split("=", 1) for line in config.splitlines() if "=" in line
    )
    if any(
            key.strip().lower() == "include-system-site-packages" and value.strip().lower() == "true"
            for key, value in settings.items()
    ):
        raise RuntimeError("Plugin virtual environment must not include system site-packages")
    request = json.load(sys.stdin)
    with contextlib.redirect_stdout(sys.stderr):
        entries = entry_points(group="itempoolapi.plugins")
        if request["operation"] == "list":
            result = []
            for entry in entries:
                plugin = entry.load()()
                if not callable(getattr(plugin, "execute", None)):
                    raise ValueError(f"Plugin {entry.name} needs an execute method")
                result.append({
                    "entry_point": entry.name,
                    "name": plugin.name,
                    "description": plugin.description,
                    "return_description": plugin.return_description,
                    "supported_data_types": plugin.supported_data_types,
                })
        elif request["operation"] == "execute":
            matches = entries.select(name=request["entry_point"])
            if len(matches) != 1:
                raise ValueError(f"Expected exactly one entry point: {request['entry_point']}")
            result = next(iter(matches)).load()().execute(request["value"])
        else:
            raise ValueError("Unknown plugin operation")
        output = json.dumps(result, allow_nan=False)
    sys.stdout.write(output)


if __name__ == "__main__":
    main()
