import enum


class Fragenbereich(str, enum.Enum):
    """Legt die möglichen Fachbereiche fest aus denen eine Frage kommen kann"""
    SQL = "SQL"
    Modellierung = "Modellierung"
    Technik = "Technik"
    ## TODO some more?


