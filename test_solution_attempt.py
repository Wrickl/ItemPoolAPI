#!/usr/bin/env python3
from src.models.Tasks.Tasks import Item, SolutionAttempt

# Test Primary Keys
item_pk = [c.name for c in Item.__table__.primary_key.columns]
sa_pk = [c.name for c in SolutionAttempt.__table__.primary_key.columns]

print(f"Item PK: {item_pk}")
print(f"SolutionAttempt PK: {sa_pk}")

# Test Foreign Key
print(f"\nSolutionAttempt ForeignKeys:")
for fk in SolutionAttempt.__table__.foreign_keys:
    print(f"  {fk}")

# Test Schema / Spalten
print("\nSolutionAttempt Spalten:")
for col in SolutionAttempt.__table__.columns:
    print(f"  {col.name}: {col.type}")

print("\n✓ Modell erfolgreich geladen!")

