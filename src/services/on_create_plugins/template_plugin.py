"""
Template für on_create Plugins.

Dieses Template zeigt, wie man ein neues Plugin für den `on_create`-Trigger erstellt.
Das Plugin wird aufgerufen, sobald ein neues Item in der Datenbank erstellt wird.

Wichtige Punkte:
1. Implementiere die Methoden: on_item_create() und apply_to_existing_items()
2. Rufe am Ende die register_on_create_plugin() Funktion auf
3. Fehlerbehandlung: Nutze try-except um zu verhindern, dass das Plugin den Haupt-Flow bricht
4. Die apply_to_existing_items() Methode ermöglicht es, das Plugin retroaktiv auf bestehende Items anzuwenden

Beispiel-Aufruf (nach Registrierung automatisch aufgerufen):
- Ein neues Item wird über POST /createItem erstellt
- on_item_create() wird sofort aufgerufen
- Entwickler kann Metadaten berechnen, validieren oder modifizieren
- Änderungen werden in die Datenbank geschrieben
"""

from typing import Any
from sqlmodel import select

from ...models.Tasks.tasks import Item
from ..PluginSystem import register_on_create_plugin


class TemplateOnCreatePlugin:
    """
    Template-Implementierung eines on_create Plugins.

    Ersetze diese Klasse mit deiner eigenen Logik.
    """

    def on_item_create(self, item: Any, session) -> None:
        """
        Wird aufgerufen, wenn ein neues Item erstellt wird.

        Args:
            item: Das neu erstellte Item-Objekt (SQLModel-Instanz)
            session: Die SQLModel Session für Datenbankzugriffe

        Beispiele:
        - Berechne Textstatistiken für die Fragestellung
        - Validiere die Item-Metadaten
        - Generiere automatisch Tags basierend auf dem Inhalt
        - Speichere Audit-Informationen
        """
        try:
            # Beispiel: Füge Metadaten hinzu
            if item.item_metadata is None:
                item.item_metadata = {}

            # Beispiel: Markiere als von diesem Plugin verarbeitet
            item.item_metadata["processed_by_template_plugin"] = True

            # Speichere die Änderungen
            session.add(item)
            session.commit()
            session.refresh(item)

        except Exception as e:
            # Fehler sollten das Plugin nicht brechen
            # TODO: Bei Bedarf Logging hinzufügen
            pass

    def apply_to_existing_items(self, session) -> None:
        """
        Wendet die Plugin-Logik retroaktiv auf alle bestehenden Items an.

        Diese Methode wird aufgerufen, wenn:
        - Ein Backfill über POST /runOnCreatePluginBackfill angefordert wird
        - Das Plugin eine Datenbereinigung oder Anpassung existierender Daten benötigt

        Wichtig:
        - Nutze Batch-Operations für bessere Performance
        - Implementiere Try-Catch um problematische Items zu überspringen
        - Nutze session.refresh() am Ende zur Konsistenz
        """
        try:
            # Lade alle Items
            items = session.exec(select(Item)).all()

            for item in items:
                try:
                    # Beispiel: Verarbeite jedes Item wie im on_item_create-Trigger
                    if item.item_metadata is None:
                        item.item_metadata = {}

                    item.item_metadata["processed_by_template_plugin"] = True
                    session.add(item)

                except Exception:
                    # Fehler bei einzelnem Item sollten nicht das ganze Backfill brechen
                    continue

            # Commit alle Änderungen auf einmal (bessere Performance)
            session.commit()

            # Refresh alle Items nach dem Commit
            for item in items:
                session.refresh(item)

        except Exception:
            # Fehler sollten das Plugin nicht brechen
            pass


# Registriere das Plugin im System
# Hinweis: Diese Zeile MUSS am Ende der Datei stehen,
# damit das Plugin beim Laden des Moduls automatisch registriert wird
register_on_create_plugin(TemplateOnCreatePlugin())