from fastapi import APIRouter
from starlette.responses import RedirectResponse



router = APIRouter()
@router.get("/ui/dashboard", include_in_schema=False)
async def ui_dashboard():
    """Startseite mit Schnellzugriff und Übersicht."""
    return RedirectResponse(url="/static/ui/dashboard.html")


@router.get("/ui/items", include_in_schema=False)
async def ui_items():
    """Aufgaben durchsuchen und verwalten."""
    return RedirectResponse(url="/static/ui/index.html")


@router.get("/ui/new/items", include_in_schema=False)
async def ui_create():
    """Neue Aufgabe erstellen."""
    return RedirectResponse(url="/static/ui/create_form.html")


@router.get("/ui/new/solutionAttempts", include_in_schema=False)
async def ui_create_solution_attempt():
    """Neue Lösung versuchen."""
    return RedirectResponse(url="/static/ui/solution_content-attempt-create.html")


@router.get("/ui/items/new", include_in_schema=False)
async def ui_create_legacy_items_new():
    """Legacy redirect."""
    return RedirectResponse(url="/ui/new/items")


@router.get("/ui/items/{item_id}", include_in_schema=False)
async def ui_item_detail(item_id: str):
    """Detail-Ansicht einer Aufgabe."""
    return RedirectResponse(url="/static/ui/item-detail.html")


@router.get("/ui/items/{item_id}/attempts", include_in_schema=False)
async def ui_solution_attempt(item_id: str):
    """Lösungsversuch eingeben."""
    return RedirectResponse(url="/static/ui/solution_content-attempt.html")


@router.get("/ui/collections", include_in_schema=False)
async def ui_collections():
    """Sammlungen verwalten."""
    return RedirectResponse(url="/static/ui/collections.html")


@router.get("/ui/export", include_in_schema=False)
async def ui_export():
    """Export-Assistent."""
    return RedirectResponse(url="/static/ui/export.html")


@router.get("/ui/settings", include_in_schema=False)
async def ui_settings():
    """Einstellungen und Verwaltung."""
    return RedirectResponse(url="/static/ui/settings.html")


@router.get("/ui/settings/itemtypes", include_in_schema=False)
async def ui_settings_itemtypes():
    """Aufgabentypen verwalten."""
    return RedirectResponse(url="/static/ui/settings-itemtypes.html")


@router.get("/ui/settings/contenttypes", include_in_schema=False)
async def ui_settings_contenttypes():
    """Inhaltsbausteine verwalten."""
    return RedirectResponse(url="/static/ui/contenttypes.html")


@router.get("/ui/settings/creators", include_in_schema=False)
async def ui_settings_creators():
    """Autoren verwalten."""
    return RedirectResponse(url="/static/ui/settings-creators.html")


@router.get("/ui/settings/licenses", include_in_schema=False)
async def ui_settings_licenses():
    """Lizenzen verwalten."""
    return RedirectResponse(url="/static/ui/settings-licenses.html")


@router.get("/ui/settings/statuses", include_in_schema=False)
async def ui_settings_statuses():
    """Status verwalten."""
    return RedirectResponse(url="/static/ui/settings-statuses.html")


@router.get("/ui/settings/organizations", include_in_schema=False)
async def ui_settings_organizations():
    """Organisationen verwalten."""
    return RedirectResponse(url="/static/ui/organizations.html")


@router.get("/ui/settings/plugins", include_in_schema=False)
async def ui_settings_plugins():
    """Plugin-Verwaltung."""
    return RedirectResponse(url="/static/ui/settings-plugins.html")


@router.get("/ui/create", include_in_schema=False)
async def ui_create_legacy():
    return RedirectResponse(url="/ui/new/items")


@router.get("/ui/create_form", include_in_schema=False)
async def ui_create_form_legacy():
    return RedirectResponse(url="/static/ui/create_form.html")
