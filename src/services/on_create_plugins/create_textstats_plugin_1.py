from typing import Any

from sqlalchemy.orm.attributes import flag_modified
from sqlmodel import select
from textstat import textstat

from ...models.Tasks.tasks import Item
from ..PluginSystem import register_on_create_plugin


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
        "osman": textstat.osman(text),
    }


def _ensure_metadata_dict(item: Item) -> None:
    if getattr(item, "item_metadata", None) is None:
        item.item_metadata = {}
        return

    if not isinstance(item.item_metadata, dict):
        try:
            item.item_metadata = dict(item.item_metadata)
        except Exception:
            item.item_metadata = {}


class CreateTextStatsPlugin:
    """Erstellt die TextStat für den Fragentext beim Einfügen eines Items."""

    def _apply(self, item: Any) -> None:
        _ensure_metadata_dict(item)
        item.item_metadata["textstats"] = _generate_textstats(item.fragestellung)

    def on_item_create(self, item: Any, session) -> None:
        self._apply(item)
        flag_modified(item, "item_metadata")
        session.add(item)
        session.commit()
        session.refresh(item)

    def apply_to_existing_items(self, session) -> None:
        items = session.exec(select(Item)).all()
        for item in items:
            try:
                self._apply(item)
                flag_modified(item, "item_metadata")
                session.add(item)
            except Exception:
                continue
        session.commit()
        for item in items:
            session.refresh(item)


register_on_create_plugin(CreateTextStatsPlugin())
