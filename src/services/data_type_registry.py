from typing import Any

from sqlalchemy import text
from sqlmodel import Session, select

from ..models.Tasks.content_types import DataType, ItemTypeContentPiece


def _discover_types_from_dialect(session: Session) -> list[tuple[str, str]]:
    bind = session.get_bind()
    if bind is None:
        return []

    dialect_name = bind.dialect.name
    if dialect_name == "postgresql":
        rows = session.execute(text(
            """
            SELECT DISTINCT t.typname, pg_catalog.format_type(t.oid, NULL)
            FROM pg_catalog.pg_type AS t
            JOIN pg_catalog.pg_namespace AS n ON n.oid = t.typnamespace
            WHERE n.nspname NOT IN ('pg_toast', 'information_schema')
            ORDER BY t.typname
            """
        ))
        return [(row[0].upper(), row[1]) for row in rows]

    ischema_names = getattr(bind.dialect, "ischema_names", {}) or {}
    colspecs = getattr(bind.dialect, "colspecs", {}) or {}

    discovered = {(str(name).upper(), str(name).upper()) for name in ischema_names.keys()}
    discovered.update((type_cls.__name__.upper(), type_cls.__name__) for type_cls in colspecs.keys())
    return sorted(discovered, key=lambda entry: entry[0])


def sync_database_types(session: Session) -> list[DataType]:
    discovered = _discover_types_from_dialect(session)
    existing = {
        data_type.name: data_type
        for data_type in session.exec(select(DataType)).all()
    }

    for name, description in discovered:
        if name in existing:
            continue
        session.add(
            DataType(
                name=name,
                description=description,
                source="database",
            )
        )

    session.commit()
    return list(session.exec(select(DataType).order_by(DataType.name)).all())


def validate_value_against_data_type(type_name: str, value: Any) -> None:
    if value is None:
        return

    normalized = type_name.upper()

    if any(token in normalized for token in ["INT", "SERIAL"]):
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"Datentyp {type_name} erwartet eine Ganzzahl")
        return

    if any(token in normalized for token in ["NUMERIC", "DECIMAL", "FLOAT", "DOUBLE", "REAL"]):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"Datentyp {type_name} erwartet eine Zahl")
        return

    if any(token in normalized for token in ["BOOL"]):
        if not isinstance(value, bool):
            raise ValueError(f"Datentyp {type_name} erwartet einen Boolean")
        return

    if any(token in normalized for token in ["JSON"]):
        if not isinstance(value, (dict, list)):
            raise ValueError(f"Datentyp {type_name} erwartet ein JSON-Objekt oder JSON-Array")
        return

    if any(token in normalized for token in ["CHAR", "TEXT", "CLOB"]):
        if not isinstance(value, str):
            raise ValueError(f"Datentyp {type_name} erwartet Text")
        return

    if any(token in normalized for token in ["DATE", "TIME"]):
        if not isinstance(value, str):
            raise ValueError(f"Datentyp {type_name} erwartet eine Zeichenkette im Datums-/Zeitformat")
        return


def ensure_assignment_belongs_to_item_type(assignment: ItemTypeContentPiece, item_type_id: int) -> None:
    if assignment.item_type_id != item_type_id:
        raise ValueError("Das ContentPiece gehoert nicht zum ausgewaehlten ItemType")
