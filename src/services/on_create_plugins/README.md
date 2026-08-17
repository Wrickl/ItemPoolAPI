# On-Create Plugins

Plugins in diesem Verzeichnis werden aufgerufen, sobald ein neues **Item** erstellt wird.

## Schnelleinstieg

1. **Template als Basis nutzen**: Kopiere `template_plugin.py` und benenne sie um (z.B. `my_plugin.py`)
2. **Klasse umbenennen**: Ändere `TemplateOnCreatePlugin` zu deinem Namen (z.B. `MyCustomPlugin`)
3. **Logik implementieren**:
   - `on_item_create(item, session)`: Wird sofort nach Item-Erstellung aufgerufen
   - `apply_to_existing_items(session)`: Wendet das Plugin retroaktiv auf bestehende Items an
4. **Registrieren**: Am Ende der Datei `register_on_create_plugin(MyCustomPlugin())` aufrufen

## Anwendungsbeispiele

- **Textstatistiken berechnen**: Automatisch Lesbarkeitsmetriken berechnen
- **Metadaten generieren**: Tags, Schwierigkeitsgrad, Domäne automatisch ableiten
- **Validierungen**: Items gegen Schema oder Geschäftsregeln prüfen
- **Audit-Logs**: Erstellung tracken
- **Externe APIs**: Item an externe Systeme synchronisieren

## Best Practices

✅ **DO**
- Fehlerbehandlung mit Try-Catch implementieren
- `session.commit()` und `session.refresh()` nutzen
- Bei Backfills Batch-Operations für Performance nutzen
- Aussagekräftige Klassennamen verwenden
- Dokumentation/Docstrings schreiben

❌ **DON'T**
- Das Plugin nicht registrieren (die Datei wird dann ignoriert)
- Fehler nicht abfangen (bricht den Haupt-Flow)
- Datenbankzugriffe ohne Fehlerbehandlung durchführen
- Blocking I/O ohne Async-Handling (deprecated aber möglich)

## Struktur einer Plugin-Datei

```python
from ...models.Tasks.Tasks import Item
from ..PluginSystem import register_on_create_plugin

class MyPlugin:
    def on_item_create(self, item: Any, session) -> None:
        # Wird sofort nach Item-Erstellung aufgerufen
        pass
    
    def apply_to_existing_items(self, session) -> None:
        # Wird bei manuellen Backfills aufgerufen
        pass

# Registriere das Plugin
register_on_create_plugin(MyPlugin())
```

## Verifizierung

Nach dem Erstellen einer neuen Plugin-Datei kannst du prüfen, ob es korrekt geladen wurde:

```bash
curl http://localhost:8000/getActivePlugins
```

Dein Plugin sollte in der Liste unter `on_create` auftauchen.

## Dateiberennung

⚠️ **Wichtig**: Dateien die mit `_` beginnen (z.B. `_template.py`) werden nicht geladen.
Das Template ist daher bewusst als `template_plugin.py` benannt. Verwende einen anderen Namen für deine Plugins.

