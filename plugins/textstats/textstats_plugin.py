from typing import Any

from textstat import textstat


class TextStatisticsPlugin:
    name = "textstats"
    description = "Berechnet Lesbarkeitsstatistiken für einen Text."
    return_description = "JSON-Objekt mit Lesbarkeitswerten und Wortanzahl."
    supported_data_types = ("TEXT", "VARCHAR", "CHAR", "BPCHAR")

    def execute(self, value: Any) -> dict[str, Any]:
        if not isinstance(value, str):
            raise ValueError("Textstatistiken benötigen einen Text")
        return {
            "flesch_reading_ease": textstat.flesch_reading_ease(value),
            "flesch_kincaid_grade": textstat.flesch_kincaid_grade(value),
            "word_count": textstat.lexicon_count(value),
            "difficult_words": textstat.difficult_words(value),
        }