from fastapi import APIRouter

from services.PluginSystem import get_active_plugins

router = APIRouter()


@router.get("/getActivePlugins", tags=["Plugins"])
def get_active_plugins_endpoint():
    """Liefert verfügbare Item-Plugins und ihre Eingabe- und Ausgabebeschreibungen."""
    return get_active_plugins()
