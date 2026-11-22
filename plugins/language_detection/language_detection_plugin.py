from typing import Any

from langdetect import DetectorFactory, LangDetectException, detect


class LanguageDetectionPlugin:
    name = "Languages detection"
    description = "Erkennt die Sprache eines Textes ."
    return_description = "JSON-Objekt mit dem erkannten Sprachcode im Feld language."
    supported_data_types = ("TEXT", "VARCHAR", "CHAR", "BPCHAR")

    def execute(self, value: Any) -> dict[str, str]:
        if not isinstance(value, str):
            raise ValueError("Die Spracherkennung benötigt einen Text")
        if not value.strip():
            raise ValueError("Die Spracherkennung benötigt einen nicht leeren Text")

        DetectorFactory.seed = 0
        try:
            language = detect(value)
        except LangDetectException as exc:
            raise ValueError("Für diesen Text konnte keine Sprache erkannt werden") from exc
        return {"language": language}
