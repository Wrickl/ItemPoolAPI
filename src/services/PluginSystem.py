from typing import Protocol, List, Any

registry: List["PluginBase"] = []


class PluginBase(Protocol):
    def on_item_create(self, item: Any, session) -> None:
        """Called after an Item was created. Plugins may modify `item` and persist changes using `session`."""

    def on_solution_attempt_create(self, document: dict, session) -> None:
        """Called after a SolutionAttempt document was stored in MongoDB. `document` is the stored doc.

        Plugins may update related SQL rows via the provided `session`.
        """


def register_plugin(plugin: PluginBase) -> None:
    registry.append(plugin)


def run_on_item_create(item: Any, session) -> None:
    for plugin in registry:
        try:
            plugin.on_item_create(item, session)
        except Exception:
            # keep plugins isolated; swallow exceptions to avoid breaking the main flow
            # TODO Log Plugin Errors
            pass


def run_on_solution_attempt_create(document: dict, session) -> None:
    for plugin in registry:
        try:
            plugin.on_solution_attempt_create(document, session)
        except Exception:
            # siehe oben
            # TODO
            pass


# Optional: import bundled/default plugins so they register themselves on import.
try:
    # relative import of possible builtin plugins
    from . import SampleMetadataPlugin  # type: ignore
except Exception:
    # if the optional plugin is missing or fails, continue without it
    ...

