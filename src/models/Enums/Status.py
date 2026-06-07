import enum


class Status(str, enum.Enum):
    Draft = "Draft"
    Review = "Review"
    Approved = "Approved"
    Productiv = "Productiv"
    Retired = "Retired"
    ## Todo Ausarbeitung/UI: Ist eine Beschreibung der  Status nötig?