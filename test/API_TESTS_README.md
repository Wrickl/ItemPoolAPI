# API Test Cases

Dieses Verzeichnis enthält `.http` Dateien mit Test-Cases für die ItemPoolAPI.

## Tools zum Ausführen

### 1. **VS Code REST Client Extension** (Empfohlen)
- Extension: [REST Client](https://marketplace.visualstudio.com/items?itemName=humao.rest-client)
- Öffne die `.http` Datei und klicke auf "Send Request" über den Requests

### 2. **JetBrains IDEs** (WebStorm, IntelliJ IDEA, PyCharm Professional)
- Öffne die `.http` Datei → Klicke auf den "Run"-Button links neben den Requests
- Responses erscheinen in einem separaten Fenster

### 3. **Kommandozeile (curl)**
```bash
# Beispiel: Test 1 ausführen
curl -X POST http://localhost:8000/createItem \
  -H "Content-Type: application/json" \
  -d '{"fragestellung": "...", "question_type": "SQL", ...}'
```

### 4. **Postman**
- Importiere die `.http` Dateien oder kopiere die Requests manuell

---

## Voraussetzungen

1. **FastAPI Server läuft**: `fastapi dev src/main.py`
2. **Datenbank erreichbar**: PostgreSQL muss laufen (oder für Entwicklung SQLite verwenden)
3. **Creator/Author existiert**: 
   - Erstelle einen mit `POST /createCreator` (siehe `API_tests/TaskGeneration.http` oder unten)
   - Oder nutze eine existierende `author_id` UUID

---

## Creator erstellen (Prerequisite)

Falls noch keine Creators existieren, erstelle einen:

```http
POST http://localhost:8000/createCreator
Content-Type: application/json

{
  "email": "author@example.com",
  "name": "Test Author",
  "role": 0,
  "organisation_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

Die zurückgegebene `author_id` kannst du dann in den Item-Tests verwenden.

---

## Test-Dateien

### `Items.http`
Umfangreiche Test-Cases für die POST /createItem Route:

#### ✅ Erfolgreiche Tests
- **Test 1**: Create mit allen Feldern
- **Test 2**: Create mit Minimal-Feldern (Defaults)
- **Test 3**: Create mit komplexem JSON-Metadata
- **Test 4**: Create mit `database_id` (Link zu Datenbank)
- **Test 5**: Create mit `tags_id`

#### ❌ Fehler-Tests
- **Fehlertest 1**: Fehlender erforderlicher `author_id` → 422
- **Fehlertest 2**: Fehlender erforderlicher `fragestellung` → 422
- **Fehlertest 3**: Ungültiger `question_type` → 422
- **Fehlertest 4**: Ungültiger `license` → 422
- **Fehlertest 5**: Ungültiger `status` → 422
- **Fehlertest 6**: Nicht existierender `author_id` → 404
- **Fehlertest 7**: Leere `fragestellung` → 422
- **Fehlertest 8**: Ungültige UUID für `author_id` → 422

#### 🔍 Abfrage
- **GET /getAllItems**: Alle Items abrufen (zur Verifikation)

---

## Variablen in den Tests

Die `.http` Dateien unterstützen Variablen:

```http
@hostname = localhost
@port = 8000
@baseUrl = http://{{hostname}}:{{port}}
```

Diese kannst du anpassen:
- Für lokale Entwicklung: `localhost:8000`
- Für Production: `api.example.com:443`

### Variable austauschen
In VS Code/JetBrains Rest Client:
1. Öffne die `.http` Datei
2. Ändere `@hostname` oder `@port`
3. Neue Requests nutzen automatisch die neue URL

---

## Enum-Werte (für Referenz)

### `question_type`
```
- SQL
- Modellierung
```

### `license`
```
- CC_BY
- CC_BY_SA
- CC0
- (weitere, je nach Enum-Definition)
```

### `status`
```
- Draft
- Review
- Approved
- Productiv
- Retired
```

---

## Tipps

### 1. Eine UUID generieren (für author_id)
Bash:
```bash
uuidgen
# Beispiel Output: 550e8400-e29b-41d4-a716-446655440000
```

Python:
```python
from uuid import uuid4
print(uuid4())
```

### 2. Requests hintereinander ausführen
In VS Code REST Client:
- Nutze "Send Request" Button oder `Ctrl+Alt+R` / `Cmd+Alt+R`
- Im "REST Client" Output-Terminal siehst du die Response

### 3. Debugging
- Aktiviere Logging in der API: Setze `log_level=DEBUG` in FastAPI/Uvicorn
- Überprüfe die Datenbank direkt: `SELECT * FROM "Item";`

### 4. Responses speichern
Viele Tools erlauben, Responses zu speichern/exportieren:
- VS Code: Response ist im Output-Tab
- Postman: Export als Collection möglich

---

## Zusammenfassung der Test-Abdeckung

| Szenario | Status | Ergebnis |
|----------|--------|----------|
| Kompletter Create | ✅ | Item erstellt mit allen Feldern |
| Minimal-Create | ✅ | Item mit Defaults |
| Complex Metadata | ✅ | JSON bleibt erhalten |
| Mit DB-Link | ✅ | FK zu Database |
| Mit Tags | ✅ | FK zu Tags |
| Fehlender Auth | ❌ | 422 Validation Error |
| Invalid Enum | ❌ | 422 Validation Error |
| Auth nicht existierend | ❌ | 404 Not Found |
| Leere Felder | ❌ | 422 Validation Error |
| Invalid UUID | ❌ | 422 Validation Error |

---

## Nächste Schritte

1. Starte den Server: `fastapi dev src/main.py`
2. Öffne `Items.http` in VS Code / JetBrains
3. Ersetze placeholder `author_id` mit einer echten UUID
4. Starte die Tests durch Klick auf "Send Request"
5. Überprüfe die Responses

