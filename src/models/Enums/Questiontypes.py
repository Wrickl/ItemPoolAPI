import enum


class QuestionTypes(str, enum.Enum):
    """Legt alle möglichen Fragenarten fest, z.B. FREITEXT, PROGRAMMIERUNG (SQL), oder Multiple Choice"""
    FREITEXT = "Freitext"
    PROGRAMMIERUNG = "Programmierung"
    SINGLECHOICE = "Single Choice"
    MULTIPLECHOICE = "Multiple Choice"
    # TODO some more?
