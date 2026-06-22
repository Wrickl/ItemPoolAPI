from datetime import datetime, timezone

from sqlmodel import Session

from ...database.MongoConnection import get_solution_attempt_collection
from ...models.Tasks.Tasks import Item
from ..PluginSystem import register_on_solution_attempt_create_plugin


def _ensure_metadata_dict(item: Item) -> None:
    if getattr(item, "item_metadata", None) is None:
        item.item_metadata = {}
        return

    if not isinstance(item.item_metadata, dict):
        try:
            item.item_metadata = dict(item.item_metadata)
        except Exception:
            item.item_metadata = {}


class SampleMetadataOnSolutionAttemptCreatePlugin:
    """Beispiel-Plugin für den `on_solutions_attempt_create`-Trigger."""

    def _ensure_counter(self, item: Item) -> int:
        _ensure_metadata_dict(item)

        counter = item.item_metadata.get("solution_attempts_seen_by_plugin", 0)
        try:
            return int(counter)
        except Exception:
            return 0

    def _increment_item_counter(self, item: Item, increment: int, *, timestamp: str | None = None) -> None:
        counter = self._ensure_counter(item)
        item.item_metadata["solution_attempts_seen_by_plugin"] = counter + increment
        if timestamp is not None:
            item.item_metadata["last_solution_attempt_plugin_ts"] = timestamp

    def _set_item_counter(self, item: Item, value: int) -> None:
        _ensure_metadata_dict(item)
        item.item_metadata["solution_attempts_seen_by_plugin"] = value

    def on_solution_attempt_create(self, document: dict, session) -> None:
        item_id = document.get("item_id")
        if item_id is None:
            return

        try:
            item_id = int(item_id)
        except Exception:
            return

        item = session.get(Item, item_id)
        if item is None:
            return

        self._increment_item_counter(item, increment=1, timestamp=datetime.now(timezone.utc).isoformat())
        session.add(item)
        session.commit()
        session.refresh(item)

    def apply_to_existing_solution_attempts(self, session: Session) -> None:
        collection = get_solution_attempt_collection()
        counts: dict[int, int] = {}

        for document in collection.find({}, {"item_id": 1}):
            item_id = document.get("item_id")
            if item_id is None:
                continue
            try:
                item_id = int(item_id)
                counts[item_id] = counts.get(item_id, 0) + 1
            except Exception:
                continue

        if not counts:
            return

        for item_id, count in counts.items():
            try:
                item_record = session.get(Item, item_id)
                if item_record is None:
                    continue
                self._set_item_counter(item_record, count)
                session.add(item_record)
            except Exception:
                continue

        session.commit()

    def apply_to_existing_items(self, session: Session) -> None:
        """Alias für den generischen Backfill-Zugriff."""
        self.apply_to_existing_solution_attempts(session)


register_on_solution_attempt_create_plugin(SampleMetadataOnSolutionAttemptCreatePlugin())






