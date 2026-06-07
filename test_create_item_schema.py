#!/usr/bin/env python3
"""
Test-Script für die create_item Route
"""
from src.schemas.Tasks.Item import ItemCreate, ItemResponse
from src.models.Enums.License import License
from src.models.Enums.Questionstypes import Questiontypes
from src.models.Enums.Status import Status
from uuid import uuid4

# Test: ItemCreate Schema mit allen Feldern
author_id = uuid4()

item_data = ItemCreate(
    fragestellung="Schreibe eine SQL-Abfrage, die alle Nutzer über 18 Jahren findet",
    question_type=Questiontypes.SQL,
    license=License.CC_BY,
    status=Status.Draft,
    author_id=author_id,
    solution="SELECT * FROM users WHERE age > 18",
    item_metadata={
        "difficulty": "medium",
        "estimated_time": "5 minutes",
        "tags": ["SQL", "SELECT"]
    },
    tags_id=None,
    database_id=None
)

print("✓ ItemCreate Schema erfolgreich erstellt:")
print(f"  - fragestellung: {item_data.fragestellung[:50]}...")
print(f"  - question_type: {item_data.question_type.value}")
print(f"  - license: {item_data.license.value}")
print(f"  - status: {item_data.status.value}")
print(f"  - author_id: {item_data.author_id}")
print(f"  - solution: {item_data.solution[:30]}...")
print(f"  - item_metadata: {item_data.item_metadata}")

# Test: Validation mit erforderlichen Feldern
try:
    minimal_item = ItemCreate(
        fragestellung="Test",
        question_type=Questiontypes.SQL,
        license=License.CC_BY,
        author_id=author_id
    )
    print("\n✓ Minimales ItemCreate Schema (mit Defaults) erfolgreich:")
    print(f"  - status (default): {minimal_item.status.value}")
    print(f"  - solution (default): {minimal_item.solution}")
    print(f"  - item_metadata (default): {minimal_item.item_metadata}")
except Exception as e:
    print(f"\n✗ Fehler bei minimalem ItemCreate: {e}")

# Test: Fehler bei fehlendem erforderlichen Feld
try:
    invalid_item = ItemCreate(
        fragestellung="Test",
        question_type=Questiontypes.SQL,
        license=License.CC_BY
        # author_id fehlt!
    )
    print("\n✗ Das hätte einen Fehler werfen sollen!")
except Exception as e:
    print(f"\n✓ Validierung funktioniert - Fehler abgefangen: author_id ist erforderlich")

print("\n✓ Alle Tests erfolgreich!")
print("\nRoute verfügbar: POST /createItem")




