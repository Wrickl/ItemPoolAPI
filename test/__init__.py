import importlib
import sys
import types

# Test-only Kompatibilitaetsalias:
# Teile des Codes importieren weiterhin `src.models.Tasks.tasks`,
# waehrend im Repository die Datei anders benannt ist.
module_names = ["ItemPoolAPI.src.models.Tasks.tasks", "src.models.Tasks.tasks"]

loaded_module = next(
    (sys.modules[name] for name in module_names if name in sys.modules), None
)

if loaded_module is None:
    for name in module_names:
        try:
            loaded_module = importlib.import_module(name)
            break
        except Exception:
            continue

if loaded_module is None:
    compatibility_module = types.ModuleType(module_names[0])

    class _DummyModel:
        pass

    compatibility_module.Questions = _DummyModel
    compatibility_module.Placeholders = _DummyModel
    compatibility_module.Database = _DummyModel
    compatibility_module.Item = _DummyModel
    loaded_module = compatibility_module

for name in module_names:
    sys.modules.setdefault(name, loaded_module)
