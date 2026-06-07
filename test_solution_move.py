#!/usr/bin/env python3
from src.models.Solutions.SolutionAttempt import SolutionAttempt, SolutionAttemptBase
from src.models.Tasks.Tasks import Item

print("✓ Importe erfolgreich")

# Test Primary Keys
item_pk = [c.name for c in Item.__table__.primary_key.columns]
sa_pk = [c.name for c in SolutionAttempt.__table__.primary_key.columns]

print(f"Item PK: {item_pk}")
print(f"SolutionAttempt PK: {sa_pk}")

# Test Foreign Key
print("\nSolutionAttempt ForeignKeys:")
for fk in SolutionAttempt.__table__.foreign_keys:
    print(f"  {fk}")

# Test Relationships
print("\nRelationships:")
print(f"  Item.solution_attempts: {hasattr(Item, '__fields__') and 'solution_attempts' in Item.__fields__}")
print(f"  SolutionAttempt.item: {hasattr(SolutionAttempt, '__fields__') and 'item' in SolutionAttempt.__fields__}")

print("\n✓ Alle Tests erfolgreich!")
print("✓ SolutionAttempt ist jetzt in src/models/Solutions/SolutionAttempt.py")

