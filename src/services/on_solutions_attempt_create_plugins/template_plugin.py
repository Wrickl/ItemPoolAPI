"""
Template für on_solution_attempt_create Plugins.

Dieses Template zeigt, wie man ein neues Plugin für den `on_solution_attempt_create`-Trigger erstellt.
Das Plugin wird aufgerufen, sobald ein neuer Lösungsversuch (SolutionAttempt) gespeichert wird.

Wichtige Punkte:
1. Implementiere die Methoden: on_solution_attempt_create() und apply_to_existing_solution_attempts()
2. Rufe am Ende die register_on_solution_attempt_create_plugin() Funktion auf
3. SolutionAttempt wird in MongoDB gespeichert (nicht in PostgreSQL)
4. Das Plugin hat Zugriff auf Item-Daten in PostgreSQL über session
5. Fehlerbehandlung: Nutze try-except um zu verhindern, dass das Plugin den Haupt-Flow bricht

Beispiel-Aufruf (nach Registrierung automatisch aufgerufen):
- Ein neuer SolutionAttempt wird über POST /createSolutionAttempt erstellt (in MongoDB)
- on_solution_attempt_create() wird sofort aufgerufen
- Entwickler kann Statistiken aktualisieren, Validierungen durchführen, etc.
- Änderungen können in PostgreSQL-Items oder MongoDB-SolutionAttempts gespeichert werden

Unterschied zu on_create Plugins:
- SolutionAttempt ist ein MongoDB-Dokument (document: dict)
- Item ist ein SQLModel-Objekt, kann aber über session.get(Item, item_id) geladen werden
- Typischerweise wird über den SolutionAttempt auf das Item zugegriffen (via item_id)
"""

from sqlmodel import Session

from ...database.mongo_connection import get_solution_attempt_collection
from ...models.Tasks.tasks import Item
from ..PluginSystem import register_on_solution_attempt_create_plugin


class TemplateOnSolutionAttemptCreatePlugin:
    """
    Template-Implementierung eines on_solution_attempt_create Plugins.

    Ersetze diese Klasse mit deiner eigenen Logik.
    """

    def on_solution_attempt_create(self, document: dict, session) -> None:
        """
        Wird aufgerufen, wenn ein neuer SolutionAttempt erstellt wird.

        Args:
            document: Das MongoDB-Dokument mit den Lösungsdaten (dict)
                      Typisch enthält es: _id, item_id, user_id, solution, timestamp, etc.
            session: Die SQLModel Session für Datenbankzugriffe

        Beispiele:
        - Aktualisiere einen Zähler im Item (z.B. "solution_attempts_count")
        - Validiere die Lösung gegen die Musterlösung
        - Berechne Metriken (z.B. Erfolgsquote, Bearbeitungszeit)
        - Triggere Benachrichtigungen bei bestimmten Bedingungen
        - Speichere Audit-Logs
        """
        try:
            # Extrahiere die Item-ID aus dem SolutionAttempt-Dokument
            item_id = document.get("item_id")
            if item_id is None:
                return

            # Konvertiere zu Integer falls nötig
            try:
                item_id = int(item_id)  # type: ignore[arg-type]
            except Exception:
                return

            # Lade das entsprechende Item aus PostgreSQL
            item = session.get(Item, item_id)
            if item is None:
                return

            # Beispiel: Erhöhe einen Zähler in den Item-Metadaten
            if item.item_metadata is None:
                item.item_metadata = {}

            current_count = item.item_metadata.get("solution_attempt_count", 0)
            item.item_metadata["solution_attempt_count"] = current_count + 1
            item.item_metadata["last_solution_attempt_by_plugin"] = True

            # Speichere die Änderungen am Item
            session.add(item)
            session.commit()
            session.refresh(item)

        except Exception as e:
            # Fehler sollten das Plugin nicht brechen
            # TODO: Bei Bedarf Logging hinzufügen
            pass

    def apply_to_existing_solution_attempts(self, session: Session) -> None:
        """
        Wendet die Plugin-Logik retroaktiv auf alle bestehenden SolutionAttempts an.

        Diese Methode wird aufgerufen, wenn:
        - Ein Backfill über POST /runOnSolutionAttemptCreatePluginBackfill angefordert wird
        - Das Plugin eine Datenbereinigung oder Anpassung existierender Daten benötigt

        Wichtig:
        - Zugiff auf MongoDB-Daten via get_solution_attempt_collection()
        - Nutze Batch-Operations und Aggregationen für bessere Performance
        - Implementiere Try-Catch um problematische Items zu überspringen
        - Speichere Ergebnisse in PostgreSQL-Items

        Typisches Muster:
        1. Hole alle SolutionAttempts aus MongoDB
        2. Gruppiere nach item_id und berechne Statistiken
        3. Aktualisiere die Items in PostgreSQL
        """
        try:
            # Hole die MongoDB-Collection mit SolutionAttempts
            collection = get_solution_attempt_collection()

            # Beispiel: Zähle SolutionAttempts pro Item
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

            # Aktualisiere alle betroffenen Items in PostgreSQL
            for item_id, count in counts.items():
                try:
                    item = session.get(Item, item_id)
                    if item is None:
                        continue

                    if item.item_metadata is None:
                        item.item_metadata = {}

                    # Speichere den Zähler aus dem Backfill
                    item.item_metadata["solution_attempt_count"] = count
                    session.add(item)

                except Exception:
                    # Fehler bei einzelnem Item sollten nicht das ganze Backfill brechen
                    continue

            # Commit alle Änderungen auf einmal (bessere Performance)
            session.commit()

        except Exception as e:
            # Fehler sollten das Plugin nicht brechen
            # TODO: Bei Bedarf Logging hinzufügen
            pass


# Registriere das Plugin im System
# Hinweis: Diese Zeile MUSS am Ende der Datei stehen,
# damit das Plugin beim Laden des Moduls automatisch registriert wird
register_on_solution_attempt_create_plugin(TemplateOnSolutionAttemptCreatePlugin())
