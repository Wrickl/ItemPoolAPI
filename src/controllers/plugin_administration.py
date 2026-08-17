from fastapi import APIRouter, Depends
from sqlmodel import Session

from ..database.dao_connection import get_session
from ..services.PluginSystem import (
    get_active_plugins,
    run_on_existing_items,
    run_on_existing_solution_attempts,
)

router = APIRouter()


@router.get("/getActivePlugins", tags=["Plugins"])
def get_active_plugins_endpoint():
    """Gibt alle aktuell geladenen Plugins je Trigger zurück."""
    plugins = get_active_plugins()
    return {
        "on_create": plugins["on_create"],
        "on_solution_attempt_create": plugins["on_solution_attempt_create"],
        "total": len(plugins["on_create"]) + len(plugins["on_solution_attempt_create"]),
    }


@router.post("/runOnCreatePluginBackfill", tags=["Plugins"])
def run_on_create_plugin_backfill(session: Session = Depends(get_session)):
    """Wendet alle `on_create`-Plugins auf bereits bestehende Items an."""
    run_on_existing_items(session)
    return {"message": "on_create plugins were applied to all existing items"}


@router.post("/runOnSolutionAttemptCreatePluginBackfill", tags=["Plugins"])
def run_on_solution_attempt_create_plugin_backfill(session: Session = Depends(get_session)):
    """Wendet alle `on_solutions_attempt_create`-Plugins auf bereits vorhandene Daten an."""
    run_on_existing_solution_attempts(session)
    return {"message": "on_solutions_attempt_create plugins were applied to existing solution attempts"}
