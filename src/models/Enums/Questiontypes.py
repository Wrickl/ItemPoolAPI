import enum


class QuestionTypes(str, enum.Enum):
    """Legt alle möglichen Fragenarten fest, z.B. Freitext, Programmierung (SQL), oder Multiple Choice"""
    Freitext = "Freitext"
    Programmierung = "Programmierung"
    SingleChoice = "SingleChoice"
    MultipleChoice = "MultipleChoice"
    ## TODO some more?


