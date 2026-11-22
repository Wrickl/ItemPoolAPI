# Item Pool API

## Dev-Setup

1. **Add .env-File**
   Add a file in the root directory called `.env` and add the content of the `.demo-env`-file. Change the values if required.

2. **Install dependencies**

   - [Python Installation Guide](https://wiki.python.org/moin/BeginnersGuide/Download)
   - [uv Installation Guide](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer)
   - [Docker Installation Guide](https://docs.docker.com/engine/install/)

3. **Start mongoDB via Docker**
   Start docker daemon if not already started. Then run the following cmd in a shell.

   ```bash
   docker-compose up
   ```

4. **Start API**
   Run this cmd in a shell in the project root repository:
   ```bash
   uv run fastapi dev src/main.py
   ```

## **Tests**

### **Manual API Tests**

    Manual API tests are implemented via HTTP Files in the "tests" directory.
    When using VSCode as an IDE, the REST Client extension is recommended.

### **UI**

- Item-Suche und JSON-Export: `/ui`
- Item-Anlage mit Dropdowns für Creator, License, Status und Datenbank: `/ui/create`

### **Unit Tests**

Pytest is used for unit testing. Run the following cmd to execute the tests.

```bash
uv run pytest
```

Or the following to create a coverage report.

```bash
uv run pytest --cov=.
```

### **Linting / Pre-Commit**

Das Projekt nutzt `pylint` als Pre-Commit-Hook.
Der Hook ist bewusst auf die aktiven Python-Bereiche des Projekts zugeschnitten; Legacy-/Experimental-Code unter
`src/services/TaskRegistration/`, `src/services/MetaDataInference/` und statische UI-Dateien werden dabei ausgespart.
Aktuell prüft der Hook vor allem `src/controllers/`, `src/database/`, `src/models/`, `src/schemas/`,
die Plugin-Ordner sowie `test/`.

#### Hook einmalig installieren

```bash
uv sync --dev
uv run pre-commit install
```

#### Hook manuell auf allen Dateien ausführen

```bash
uv run pre-commit run --all-files
```

#### `pylint` direkt starten

```bash
uv run pylint src test
```

## Debugger (VSCode Example)

Add the following code to the `launch.json` in the .vscode-folder (create if it doesn't exist):

```json
{
	"version": "0.2.0",
	"configurations": [
		{
			"name": "api",
			"type": "debugpy",
			"request": "launch",
			"python": ".venv/bin/python",
			"console": "integratedTerminal",
			"program": ".venv/bin/fastapi",
			"args": ["dev", "src/main.py"],
			"justMyCode": true
		}
	]
}
```

## Feature-List

See this [wiki-entry](https://github.com/plc-dev/ItemPoolAPI/wiki/ToDo%E2%80%90List).
