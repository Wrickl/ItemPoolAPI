from datetime import datetime, timezone
from typing import Any

from textstat import textstat

from .PluginSystem import register_plugin
from ..models.Tasks.Tasks import Item


def _generate_textstats(text: str) -> dict:
    return {
        "flesch_reading_ease": textstat.flesch_reading_ease(text),
        "flesch_kincaid_grade": textstat.flesch_kincaid_grade(text),
        "smog_index": textstat.smog_index(text),
        "coleman_liau_index": textstat.coleman_liau_index(text),
        "automated_readability_index": textstat.automated_readability_index(text),
        "dale_chall_readability_score": textstat.dale_chall_readability_score(text),
        "difficult_words": textstat.difficult_words(text),
        "linsear_write_formula": textstat.linsear_write_formula(text),
        "gunning_fog": textstat.gunning_fog(text),
        "text_standard": textstat.text_standard(text),
        "fernandez_huerta": textstat.fernandez_huerta(text),
        "szigriszt_pazos": textstat.szigriszt_pazos(text),
        "gutierrez_polini": textstat.gutierrez_polini(text),
        "crawford": textstat.crawford(text),
        "gulpease_index": textstat.gulpease_index(text),
        "osman": textstat.osman(text)
    }


class SampleMetadataPlugin:
    """Ein Beispiel-Plugin, das ein Feld in `item.item_metadata` setzt bzw. inkrementiert.

    Verhalten:
    - on_item_create: setzt item.item_metadata['created_by_plugin'] = True und `created_by_plugin_ts`.
    - on_solution_attempt_create: erhöht item.item_metadata['solution_attempts_seen_by_plugin'] um 1
    """

    def on_item_create(self, item: Any, session) -> None:
        if getattr(item, "item_metadata", None) is None:
            item.item_metadata = {}
        if not isinstance(item.item_metadata, dict):
            # wenn jemand ungewöhnliche Daten gespeichert hat, überschreibe nicht-dikt
            item.item_metadata = dict(item.item_metadata)

        item.item_metadata["created_by_plugin"] = True
        item.item_metadata["created_by_plugin_ts"] = datetime.now(timezone.utc).isoformat()
        item.item_metadata["textstats"] = _generate_textstats(item.fragestellung)
        session.add(item)
        session.commit()
        session.refresh(item)

    def on_solution_attempt_create(self, document: dict, session) -> None:
        item_id = document.get("item_id")
        if item_id is None:
            return
        item = session.get(Item, item_id)
        if item is None:
            return

        if getattr(item, "item_metadata", None) is None:
            item.item_metadata = {}
        if not isinstance(item.item_metadata, dict):
            item.item_metadata = dict(item.item_metadata)

        counter = item.item_metadata.get("solution_attempts_seen_by_plugin", 0)
        try:
            counter = int(counter)
        except Exception:
            counter = 0
        counter += 1
        item.item_metadata["solution_attempts_seen_by_plugin"] = counter
        item.item_metadata["last_solution_attempt_plugin_ts"] = datetime.now(timezone.utc).isoformat()

        session.add(item)
        session.commit()
        session.refresh(item)


# Register this plugin on import so the default system has at least one plugin.
register_plugin(SampleMetadataPlugin())

if __name__ == '__main__':
    print(_generate_textstats(
        "Eine Fragestellung um die Textstat funktion, meines Plugin Ansatzes zu testen. Mal sehen ob das klappt!"))
